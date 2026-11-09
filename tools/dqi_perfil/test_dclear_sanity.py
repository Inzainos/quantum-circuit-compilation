#!/usr/bin/env python3
"""Sanity check del harness: ¿D1 (via _dclear) == D_old clasico?

Para la ronda 3: forward, reverse normal de 5..4, luego _dclear -> D1.
Si D1 == 2712 (D_old clasico de la ronda 3), el harness es correcto y
_dclear es la referencia valida. Entonces D1^D2 != 0 (test anterior)
prueba que _disc es incorrecto.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_bm_stage_v1 import BMStageV1

DEG = 12
N, LS, K = 6, 6, 2

rng = np.random.default_rng(7)
pos = rng.choice(4095, size=K, replace=False)
vals = rng.integers(1, 4096, size=K)
X = [int(G.EXP[p % 4095]) for p in pos]
Svals = []
for t in range(N):
    s = 0
    for xj, e in zip(X, vals):
        s ^= G.mul(int(e), int(G.EXP[(G.LOG[xj] * t) % 4095]))
    Svals.append(s)

def bits_of(vals_list, deg=DEG):
    out = np.zeros((len(vals_list) * deg, 1), dtype=bool)
    for idx, v in enumerate(vals_list):
        for j in range(deg):
            out[idx * deg + j, 0] = bool((v >> j) & 1)
    return out

for r, d_clasico in [(3, 2712), (1, 2975), (0, 1818)]:
    bld = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    S = [bld.create_quantum_register(DEG, name=f"S{i}") for i in range(N)]
    bm = BMStageV1(bld, gf, S, LS, N)
    bm.forward()
    for rr in reversed(range(r + 1, N)):
        bm.reverse_round(rr)
    p, t = bm.flags[r]
    D1 = bld.alloc_qubits(DEG)
    bm._dclear(D1, p, t)
    circ = bld.finish_circuit()
    sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(circ)
    s_qubits = []
    for reg in S:
        s_qubits.extend(list(reg))
    sim.write_across_shots(km.array(s_qubits), bits_of(Svals))
    sim.do(circ)
    d1 = sim.read_across_shots(km.array(list(D1)))
    d1v = sum(int(d1[j, 0]) << j for j in range(DEG))
    print(f"ronda {r}: D1(_dclear)={d1v}  D_old clasico={d_clasico}  -> {'COINCIDE (harness OK)' if d1v == d_clasico else 'DIFIERE'}")
