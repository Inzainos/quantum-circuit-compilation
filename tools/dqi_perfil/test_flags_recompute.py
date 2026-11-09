#!/usr/bin/env python3
"""Prueba empirica v3: ¿las banderas p/t se pueden recomputar en la vuelta
si D fuera correcta? (aisla el problema de d)

Para cada ronda r con D_old != 0: forward, reverse normal de N-1..r+1, y en
el punto de reverse_round(r):
  D1 = D_old correcta (via _dclear con p/t guardadas)
  p2,t2 = _flags(D1, ...) sobre la d ACTUAL (d_new, post-update)
  compara p2 vs p guardada, t2 vs t guardada.
Si p2^p == 0 y t2^t == 0 -> con D correcta, _flags recomputa bien.
Si != 0 -> el signo de d_new difiere del de d_old y _flags da banderas malas.
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
    for rr in reversed(range(r + 1, N)):
        bm.reverse_round(rr)
    p, t = bm.flags[r]
    D1 = bld.alloc_qubits(DEG)
    bm._dclear(D1, p, t)                       # D1 = D_old correcta
    p2 = bld.alloc_qubits(1)[0]
    t2 = bld.alloc_qubits(1)[0]
    bm._flags(D1, p2, t2, inverse=False)       # p2/t2 desde D_old y d_new
    bld.cx(p, p2)                              # p2 ^= p
    bld.cx(t, t2)                              # t2 ^= t
    # leer tambien d_new (8 bits) para ver su signo
    dreg = bm.d
    circ = bld.finish_circuit()
    sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(circ)
    s_qubits = []
    for reg in S:
        s_qubits.extend(list(reg))
    sim.write_across_shots(km.array(s_qubits), bits_of(Svals))
    sim.do(circ)
    p2v = int(sim.read_across_shots(km.array([p2]))[0, 0])
    t2v = int(sim.read_across_shots(km.array([t2]))[0, 0])
    dbits = sim.read_across_shots(km.array(list(dreg)))
    dval = sum(int(dbits[j, 0]) << j for j in range(8))
    # d es entero con signo de 8 bits (complemento a 2)
    d_signed = dval - 256 if dval >= 128 else dval
    return p2v, t2v, d_signed

print("sindrome S:", Svals)
for r in [5, 3, 2, 1, 0]:
    p2v, t2v, dnew = test_round(r)
    ok = (p2v == 0 and t2v == 0)
    print(f"ronda {r}: p2^p={p2v} t2^t={t2v} d_new={dnew} -> {'_flags recomputa BIEN' if ok else '_flags recomputa MAL (d_new != d_old en signo)'}")
