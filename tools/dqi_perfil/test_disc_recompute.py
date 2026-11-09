#!/usr/bin/env python3
"""Prueba empirica: ¿_disc en la vuelta devuelve D_old?

Construye el BM v1 a escala chica (n rondas), corre el forward, y en el punto
donde empezaria la vuelta compara:
  D1 = D reconstruida por _dclear (correcta, usa p/t guardadas)
  D2 = D calculada por _disc sobre el sigma post-update (candidata a recomputo)
Si D1 ^ D2 == 0 -> _disc devuelve D_old (recomputo posible).
Si D1 ^ D2 != 0 -> _disc NO devuelve D_old (recomputo incorrecto).

Sindrome valido generado con el modelo clasico (k errores).
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
print("sindrome S:", Svals)

# Referencia clasica: D_old de cada ronda (con el modelo estandar, para contexto)
sig = [1] + [0] * N
B = [1] + [0] * N
L, m, b = 0, 1, 1
Dolds = []
for r in range(N):
    d = 0
    for i in range(0, min(L, r) + 1):
        d ^= G.mul(sig[i], Svals[r - i])
    Dolds.append(d)
    if d == 0:
        m += 1
        continue
    c = G.mul(d, G.inv(b))
    T = sig[:]
    for i in range(0, N + 1 - m):
        sig[i + m] ^= G.mul(c, B[i])
    if 2 * L <= r:
        L = r + 1 - L
        B = T
        b = d
        m = 1
    else:
        m += 1
print("D_old clasico por ronda:", Dolds)

# --- Circuito: forward completo, luego comparar D1 vs D2 en la ultima ronda ---
bld = km.CircuitBuilder()
gf = km.GF2Field(DEG)
S = [bld.create_quantum_register(DEG, name=f"S{i}") for i in range(N)]
bm = BMStageV1(bld, gf, S, LS, N)
bm.forward()
r = N - 1
p, t = bm.flags[r]
D1 = bld.alloc_qubits(DEG)
D2 = bld.alloc_qubits(DEG)
bm._dclear(D1, p, t)          # D1 = D_old (reconstruccion correcta)
bm._disc(r, D2)               # D2 = _disc sobre sigma post-update
for i in range(DEG):
    bld.cx(D2[i], D1[i])      # D1 ^= D2
circ = bld.finish_circuit()
print(f"circuito: Q={circ.num_qubits} T={circ.operation_statistics().num_toffoli_like}")

# --- Simular con el sindrome escrito en S ---
BATCH = 1
sim = km.Simulator(batch_size=BATCH, debug_print=False, counting_operations=True, seed=1)
sim.use_same_registers_as(circ)
# escribir S: concatenar los registros S en orden
s_qubits = []
for reg in S:
    s_qubits.extend(list(reg))
s_bits = np.zeros((N * DEG, BATCH), dtype=bool)
for idx, v in enumerate(Svals):
    for j in range(DEG):
        s_bits[idx * DEG + j, 0] = bool((v >> j) & 1)
sim.write_across_shots(km.array(s_qubits), s_bits)
sim.do(circ)
d1_bits = sim.read_across_shots(km.array(list(D1)))
d1_val = sum(int(d1_bits[j, 0]) << j for j in range(DEG))
print(f"D1^D2 (ronda {r}) = {d1_val}  (0 => _disc devuelve D_old; !=0 => _disc es incorrecto)")
print("RESULTADO:", "RECOMPUTO POSIBLE" if d1_val == 0 else "RECOMPUTO INCORRECTO: _disc en la vuelta NO devuelve D_old")
