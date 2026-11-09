#!/usr/bin/env python3
"""Verifica el invariante BM que decide si D se puede recomputar en la vuelta.

Pregunta: despues de la actualizacion de la ronda r, ¿la discrepancia del
nuevo sigma en la posicion r es 0?  Si es 0, entonces _disc(r, D) calculado
sobre el sigma post-update (el estado al inicio de reverse_round) da 0 y NO
D_old -> recomputar D via _disc en la vuelta es INCORRECTO (no solo caro).

Usa el modelo clasico de dqi_bm_model.py (mismo algoritmo BM), replicando el
bucle paso a paso para inspeccionar el estado tras cada actualizacion.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
import numpy as np
import dqi_bm_model as G

rng = np.random.default_rng(7)
# Sindrome aleatorio valido (k=6 errores, como en el modelo)
k, n = 6, 70
pos = rng.choice(4095, size=k, replace=False)
vals = rng.integers(1, 4096, size=k)
X = [int(G.EXP[p % 4095]) for p in pos]
S = []
for t in range(n):
    s = 0
    for xj, e in zip(X, vals):
        s ^= G.mul(int(e), int(G.EXP[(G.LOG[xj] * t) % 4095]))
    S.append(s)

sig = [1] + [0] * n
B = [1] + [0] * n
L, m, b = 0, 1, 1
bad = 0
for r in range(n):
    d = 0
    for i in range(0, min(L, r) + 1):
        d ^= G.mul(sig[i], S[r - i])
    d_old = d
    if d == 0:
        m += 1
        continue
    c = G.mul(d, G.inv(b))
    T = sig[:]
    for i in range(0, n + 1 - m):
        sig[i + m] ^= G.mul(c, B[i])
    if 2 * L <= r:
        L = r + 1 - L
        B = T
        b = d
        m = 1
    else:
        m += 1
    # discrepancia del NUEVO sigma en la posicion r (esto es lo que _disc
    # calcularia en la vuelta, sobre el sigma post-update):
    d_new = 0
    for i in range(0, min(L, r) + 1):
        d_new ^= G.mul(sig[i], S[r - i])
    if d_new != 0:
        bad += 1
        print(f"ronda {r}: D_old={d_old}  D(post-update)={d_new}  != 0  <-- NO es cero")
print(f"rondas con actualizacion: verificadas; D(post-update)!=0 en {bad} rondas")
print("CONCLUSION: _disc sobre sigma post-update da 0 siempre -> recomputar D via _disc en la vuelta es INCORRECTO" if bad == 0 else "CONCLUSION: hay rondas donde D(post-update)!=0 -> revisar")
