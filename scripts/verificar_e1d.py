#!/usr/bin/env python3
"""Verificar la etapa BM fusionada CON E1d por simulador a n=6 (LS=6).

Replica verificar_fusion.py (fusion_mul_inv) con BMStageFused como baseline
y BMStageFusedE1d como candidata.

Test A: fusionada forward vs fusionada+E1d forward (mismo S) -> S/sigma/tau/d/H identicos.
Test B: fusionada+E1d forward+reverse -> estado final == estado inicial (restauracion).
Test C: fusionada forward+reverse vs fusionada+E1d forward+reverse -> estados finales identicos.

Uso: python3 -u scripts/verificar_e1d.py  (desde la raiz del repo)
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import numpy as np
import kickmix as km
from bm_fused import BMStageFused
from bm_fused_e1d import BMStageFusedE1d

DEG, LS, N = 12, 6, 6
B = 64
rng = np.random.default_rng(7)
# Misma semilla y mismo S que verificar_fusion.py (comparabilidad directa)
Svals = rng.integers(1, 4096, size=(N, B), dtype=np.int64)


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

c_fus_fwd = build(BMStageFused, False)
c_e1d_fwd = build(BMStageFusedE1d, False)
print(f"forward solo: fusionada Q={c_fus_fwd.num_qubits} T={c_fus_fwd.operation_statistics().num_toffoli_like} ; "
      f"fusionada+E1d Q={c_e1d_fwd.num_qubits} T={c_e1d_fwd.operation_statistics().num_toffoli_like}", flush=True)
out_f, ph_f = run(c_fus_fwd)
out_e, ph_e = run(c_e1d_fwd)
print(f"fase volteada: fusionada={ph_f} fusionada+E1d={ph_e}", flush=True)
ok = True
for name, st, nb in [("S", S0, DEG * N), ("sigma", SG0, DEG * LS), ("tau", TA0, DEG * LS), ("d", D0, 8), ("H", H0, 12)]:
    vf, ve = reg(out_f, st, nb), reg(out_e, st, nb)
    same = bool((vf == ve).all())
    ok &= same
    print(f"Test A {name}: fusionada==fusionada+E1d: {same} (ej. fus={vf[:4]} e1d={ve[:4]})", flush=True)
# (los qubits del pool incluyen las flags p/t, que legitimamente valen 0/1; no se chequean)
print(f"Test A (forward identico, S/sigma/tau/d/H): {'PASA' if ok else 'FALLA'}", flush=True)

# Test B: fusionada+E1d ida+vuelta -> restauracion
c_e1d_rv = build(BMStageFusedE1d, True)
print(f"ida+vuelta fusionada+E1d: Q={c_e1d_rv.num_qubits} T={c_e1d_rv.operation_statistics().num_toffoli_like}", flush=True)
out_rv, ph_rv = run(c_e1d_rv)
print(f"fase volteada ida+vuelta: {ph_rv}", flush=True)
# estado inicial: S como entrada; sigma[0]=1; tau[1]=1; d=1; resto 0
init = np.zeros((c_e1d_rv.num_qubits, B), dtype=bool)
init[:DEG * N] = bits_mat(Svals)
init[SG0 + 0] = True            # sigma[0][0]=1
init[TA0 + DEG + 0] = True      # tau[1][0]=1
init[D0 + 0] = True             # d[0]=1
restored = bool((out_rv == init).all())
print(f"Test B (ida+vuelta restaura estado inicial): {restored}", flush=True)
if not restored:
    diff = np.where(out_rv != init)
    print(f"  qubits que difieren: {sorted(set(diff[0].tolist()))[:20]} (n={len(set(diff[0].tolist()))})", flush=True)

# Test C: fusionada ida+vuelta vs fusionada+E1d ida+vuelta
c_fus_rv = build(BMStageFused, True)
out_frv, _ = run(c_fus_rv)
# comparar solo registros persistentes (0..235); el resto es pool (Q puede diferir)
same_rv = bool((out_frv[:H0 + 12] == out_rv[:H0 + 12]).all())
print(f"Test C (fusionada ida+vuelta == fusionada+E1d ida+vuelta, regs persistentes): {same_rv}", flush=True)
print(f"VEREDICTO: {'TODOS PASAN' if (ok and restored and same_rv) else 'HAY FALLOS'}", flush=True)
