#!/usr/bin/env python3
"""Verificar la etapa BM fusionada por simulador a n=6 (LS=6).

Test A: baseline forward vs fusionada forward (mismo S) -> sigma/tau/d/H identicos.
Test B: fusionada forward+reverse -> estado final == estado inicial (restauracion).
Test C: baseline forward+reverse vs fusionada forward+reverse -> estados finales identicos.

Uso: PYTHONPATH=... python3 verificar_fusion.py
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv")
import numpy as np
import kickmix as km
from dqi_bm_stage_v1 import BMStageV1
from bm_fused import BMStageFused

DEG, LS, N = 12, 6, 6
B = 64
rng = np.random.default_rng(7)
# S aleatorio: n=6 sindromes de 12 bits (evitar S=0 en todas partes; BM maneja D=0, pero queremos casos con p=1)
Svals = rng.integers(1, 4096, size=(N, B), dtype=np.int64)
# forzar algunos sindromes con estructura (L alto): usar valores del baseline si hace falta
# (el baseline n=6 usa S de dqi_bm_model; aqui aleatorio es suficiente para comparar baseline vs fusionada)

def bits_mat(vals):
    # vals: (n, B) -> (12*n, B) bool, bit j de vals[i] en fila 12*i+j
    out = np.zeros((DEG * vals.shape[0], vals.shape[1]), dtype=bool)
    for i in range(vals.shape[0]):
        for j in range(DEG):
            out[DEG * i + j] = ((vals[i] >> j) & 1) == 1
    return out

def build(cls, ida_y_vuelta):
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(N)]
    bm = cls(b, gf, S, LS, N)
    bm.forward()
    if ida_y_vuelta:
        bm.reverse()
    return b.finish_circuit()

def run(c, seed=1):
    sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=seed)
    sim.use_same_registers_as(c)
    nq = c.num_qubits
    inp = np.zeros((nq, B), dtype=bool)
    inp[:DEG * N] = bits_mat(Svals)
    # estado inicial: sigma[0][0]=1, tau[1][0]=1, d[0]=1 (los pone el constructor con X)
    sim.write_across_shots(km.array([km.q(i) for i in range(nq)]), inp)
    sim.do(c)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(nq)]))
    return out, int(sim.read_phase_flipped_across_shots().sum())

def reg(out, start, nbits):
    v = np.zeros(out.shape[1], dtype=np.int64)
    for j in range(nbits):
        v |= out[start + j].astype(np.int64) << j
    return v

# layout: S 0..71, sigma 72..143, tau 144..215, d 216..223, H 224..235
S0, SG0, TA0, D0, H0 = 0, DEG * N, DEG * N + DEG * LS, DEG * N + 2 * DEG * LS, DEG * N + 2 * DEG * LS + 8
print(f"layout: S@{S0} sigma@{SG0} tau@{TA0} d@{D0} H@{H0} (nq base={H0+12})", flush=True)

c_base_fwd = build(BMStageV1, False)
c_fus_fwd = build(BMStageFused, False)
print(f"forward solo: baseline Q={c_base_fwd.num_qubits} T={c_base_fwd.operation_statistics().num_toffoli_like} ; "
      f"fusionada Q={c_fus_fwd.num_qubits} T={c_fus_fwd.operation_statistics().num_toffoli_like}", flush=True)
out_b, ph_b = run(c_base_fwd)
out_f, ph_f = run(c_fus_fwd)
print(f"fase volteada: baseline={ph_b} fusionada={ph_f}", flush=True)
ok = True
for name, st, nb in [("S", S0, DEG * N), ("sigma", SG0, DEG * LS), ("tau", TA0, DEG * LS), ("d", D0, 8), ("H", H0, 12)]:
    vb, vf = reg(out_b, st, nb), reg(out_f, st, nb)
    same = bool((vb == vf).all())
    ok &= same
    print(f"Test A {name}: baseline==fusionada: {same} (ej. base={vb[:4]} fus={vf[:4]})", flush=True)
# (los qubits del pool incluyen las flags p/t, que legitimamente valen 0/1; no se chequean)
print(f"Test A (forward identico, S/sigma/tau/d/H): {'PASA' if ok else 'FALLA'}", flush=True)

# Test B: fusionada ida+vuelta -> restauracion
c_fus_rv = build(BMStageFused, True)
print(f"ida+vuelta fusionada: Q={c_fus_rv.num_qubits} T={c_fus_rv.operation_statistics().num_toffoli_like}", flush=True)
out_rv, ph_rv = run(c_fus_rv)
print(f"fase volteada ida+vuelta: {ph_rv}", flush=True)
# estado inicial: S como entrada; sigma[0]=1; tau[1]=1; d=1; resto 0
init = np.zeros((c_fus_rv.num_qubits, B), dtype=bool)
init[:DEG * N] = bits_mat(Svals)
init[SG0 + 0] = True            # sigma[0][0]=1
init[TA0 + DEG + 0] = True      # tau[1][0]=1
init[D0 + 0] = True             # d[0]=1
restored = bool((out_rv == init).all())
print(f"Test B (ida+vuelta restaura estado inicial): {restored}", flush=True)
if not restored:
    diff = np.where(out_rv != init)
    print(f"  qubits que difieren: {sorted(set(diff[0].tolist()))[:20]} (n={len(set(diff[0].tolist()))})", flush=True)

# Test C: baseline ida+vuelta vs fusionada ida+vuelta
c_base_rv = build(BMStageV1, True)
out_brv, _ = run(c_base_rv)
# comparar solo registros persistentes (0..235); el resto es pool (Q difiere en 12 por Pinv)
same_rv = bool((out_brv[:H0 + 12] == out_rv[:H0 + 12]).all())
print(f"Test C (baseline ida+vuelta == fusionada ida+vuelta, regs persistentes): {same_rv}", flush=True)
print(f"VEREDICTO: {'TODOS PASAN' if (ok and restored and same_rv) else 'HAY FALLOS'}", flush=True)
