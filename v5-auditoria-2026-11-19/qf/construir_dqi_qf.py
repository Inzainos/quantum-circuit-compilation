#!/usr/bin/env python3
"""Construir el DQI COMPLETO con el parche QF de Claude (-7 qubits).

Replica construir_dqi_omega.py (swap42) pero con sys.path apuntando al
worktree local/claude-qf-minus7-2026-11-19 (src parcheado, main 64d4cec).
Esperado: Q=1,857 (1,864 - 7), T=710,312 (sin cambio).
Uso: /home/deamon/quantum-circuit-compilation/.venv/bin/python -u construir_dqi_qf.py
"""
import sys, os, time, hashlib
sys.path.insert(0, "/home/deamon/quantum-circuit-compilation-qf/src")
import kickmix as km
import dqi_bm_stage_v1, bm_fused, bm_fused_e1d
import dqi_decoder_v1 as D
from bm_fused_e1d import BMStageFusedE1d

DEG = 12
OUT = "/home/deamon/workspace/qcc-data/claude-qf/dqi_qf.kmb"


def main():
    print(f"modulos: dqi_bm_stage_v1={dqi_bm_stage_v1.__file__}", flush=True)
    print(f"modulos: bm_fused={bm_fused.__file__}", flush=True)
    print(f"modulos: bm_fused_e1d={bm_fused_e1d.__file__}", flush=True)
    print(f"modulos: dqi_decoder_v1={D.__file__}", flush=True)
    t0 = time.time()
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(70)]
    E = [b.create_classical_register(DEG, name=f"E{j}") for j in range(4095)]
    bm = BMStageFusedE1d(b, gf, S, 36, 70)
    bm.forward()
    print(f"[bm_forward] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    D.build_omega_tmp(b, gf, bm.sigma, S, 35, adjoint=False)
    print(f"[omega_fwd] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    D.build_scan_inv(b, gf, bm.sigma, S[:35], E, None)
    print(f"[scan] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    D.build_omega_tmp(b, gf, bm.sigma, S, 35, adjoint=True)
    print(f"[omega_rev] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    bm.reverse()
    b.x(bm.sigma[0][0]); b.x(bm.tau[1][0]); b.x(bm.d[0])
    print(f"[bm_reverse] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    c = b.finish_circuit()
    q = int(c.num_qubits); t = int(c.operation_statistics().num_toffoli_like)
    print(f"TOTAL QF Q={q} T={t} en {time.time()-t0:.0f}s", flush=True)
    print(f"SWAP42 (referencia): Q=1864 T=710312", flush=True)
    print(f"Delta Q={q-1864} Delta T={t-710312} (esperado Delta Q=-7 Delta T=0)", flush=True)
    ratio_dqi = 7.48129 * (774932 / t)
    g_calc = (5.32 * ratio_dqi * 1.00583) ** (1/3)
    g_esc = 3.42920 * (774932 / t) ** (1/3)
    print(f"DQI ratio nuevo = {ratio_dqi:.5f}x", flush=True)
    print(f"geomean calculado = {g_calc:.5f}x ; geomean escalando Kaggle 3.42920x = {g_esc:.5f}x", flush=True)
    c.to_file(OUT, format="kmb")
    h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    print(f"guardado {OUT} sha256={h}", flush=True)


if __name__ == "__main__":
    main()
