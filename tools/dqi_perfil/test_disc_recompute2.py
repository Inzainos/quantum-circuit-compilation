#!/usr/bin/env python3
"""Prueba empirica v2: ¿_disc en la vuelta devuelve D_old? (varias rondas)

Para cada ronda objetivo r con D_old != 0: forward completo, luego reverse
normal de las rondas N-1..r+1 (con banderas guardadas), y en el punto donde
empezaria reverse_round(r) compara:
  D1 = D reconstruida por _dclear (correcta, usa p/t guardadas)
  D2 = D calculada por _disc sobre el sigma post-update (candidata a recomputo)
D1^D2 == 0 -> _disc devuelve D_old. != 0 -> _disc es incorrecto.
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

def test_round(r):
    bld = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    S = [bld.create_quantum_register(DEG, name=f"S{i}") for i in range(N)]
    bm = BMStageV1(bld, gf, S, LS, N)
    bm.forward()
    # reverse normal de las rondas posteriores a r
    for rr in reversed(range(r + 1, N)):
        bm.reverse_round(rr)
    p, t = bm.flags[r]
    D1 = bld.alloc_qubits(DEG)
    D2 = bld.alloc_qubits(DEG)
    bm._dclear(D1, p, t)
    bm._disc(r, D2)
    for i in range(DEG):
        bld.cx(D2[i], D1[i])
    circ = bld.finish_circuit()
    sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(circ)
    s_qubits = []
    for reg in S:
        s_qubits.extend(list(reg))
    sim.write_across_shots(km.array(s_qubits), bits_of(Svals))
    sim.do(circ)
    d1 = sim.read_across_shots(km.array(list(D1)))
    return sum(int(d1[j, 0]) << j for j in range(DEG))

print("sindrome S:", Svals)
for r in [5, 3, 2, 1, 0]:
    diff = test_round(r)
    print(f"ronda {r}: D1^D2 = {diff}  -> {'_disc == D_old' if diff == 0 else '_disc != D_old (INCORRECTO)'}")
