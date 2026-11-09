#!/usr/bin/env python3
"""Baseline BM v1 a escala chica + perfil de coeficientes vivos de sigma/tau.

Mide Q y T del BM v1 (forward+reverse) a escala chica (n=6, LS=6) y el
perfil de coeficientes vivos por ronda (cuantos coeficientes de sigma y
tau son no-cero / estan activos en cada ronda). Esto fundamenta el
argumento estructural de que BM v1 necesita dos polinomios completos.
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

# --- modelo clasico: perfil de grados L y L' por ronda ---
sig = [1] + [0] * N
B = [1] + [0] * N
L, m, b = 0, 1, 1
print("ronda | L(sigma) | L'(tau) | L+L'+2 | bu(r)+1 | 2*(bu+1)")
for r in range(N):
    d = 0
    for i in range(0, min(L, r) + 1):
        d ^= G.mul(sig[i], Svals[r - i])
    bu = min(LS - 1, r // 2 + 2)
    print(f"{r:5d} | {L:8d} | {L:7d} | {L+L+2:7d} | {bu+1:7d} | {2*(bu+1):8d}")
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
print("sigma final:", sig[:L + 1], "L =", L)
print("S:", Svals)

# --- circuito BM v1 a escala chica: Q y T ---
bld = km.CircuitBuilder()
gf = km.GF2Field(DEG)
S = [bld.create_quantum_register(DEG, name=f"S{i}") for i in range(N)]
bm = BMStageV1(bld, gf, S, LS, N)
bm.forward()
bm.reverse()
circ = bld.finish_circuit()
print(f"BM v1 n={N} LS={LS} forward+reverse: Q={circ.num_qubits} T={circ.operation_statistics().num_toffoli_like}")

# solo forward
bld2 = km.CircuitBuilder()
S2 = [bld2.create_quantum_register(DEG, name=f"S{i}") for i in range(N)]
bm2 = BMStageV1(bld2, gf, S2, LS, N)
bm2.forward()
circ2 = bld2.finish_circuit()
print(f"BM v1 n={N} LS={LS} forward solo: Q={circ2.num_qubits} T={circ2.operation_statistics().num_toffoli_like}")
print("composicion Q forward: S", N * DEG, "+ sigma", LS * DEG, "+ tau", LS * DEG, "+ d 8 + H 12 + flags", 2 * N)
