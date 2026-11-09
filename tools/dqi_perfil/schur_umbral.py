#!/usr/bin/env python3
"""Umbral de la recurrencia de Schur (Stieltjes): para k=1..35 a n=70, en que L falla?
Se usa un solo draw por k (semilla fija) para ver el patron de fallo vs L.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_stieltjes import syndrome, schur_stieltjes, convergents, trim

def pmul(a, b):
    if not a or not b:
        return [0]
    out = [0]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] ^= G.mul(x, y)
    return out

def pdeg(a):
    d = len(a)-1
    while d > 0 and a[d] == 0:
        d -= 1
    return d

rng = np.random.default_rng(123)
n = 70
print("k   L   sigma_ok  ec_clave  deg_omega  gammas  breakdown")
for k_err in range(1, 36):
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm == 0:
        print(f"{k_err:3d}   0   (sin errores)")
        continue
    L = L_bm
    gammas, breakdown = schur_stieltjes(S, 2*n+2, n)
    conv = convergents(gammas)
    ok = False; ok_key = False; degw = -1
    if 2*L < len(conv):
        p, q = conv[2*L]
        if q[0] != 0:
            inv0 = G.inv(q[0])
            sigma = trim([G.mul(c, inv0) for c in q])
            omega = trim([G.mul(c, inv0) for c in p])
            ok = sigma == trim(sig_bm)
            prod = pmul(sigma, S)
            lhs = trim(prod[:n])
            ok_key = lhs == omega and pdeg(omega) < L
            degw = pdeg(omega)
    print(f"{k_err:3d} {L:3d}   {str(ok):5s}  {str(ok_key):5s}  {degw:3d}      {len(gammas):4d}  {breakdown}")
