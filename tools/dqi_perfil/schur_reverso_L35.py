#!/usr/bin/env python3
"""Arreglo del borde L=35: sindrome revertido (ecuacion clave dual).
Idea: si sigma*S = omega (mod x^n), el polinomio revertido sigma* (x^L sigma(1/x))
satisface una ecuacion clave dual con el sindrome revertido S* (x^{n-1} S(1/x)).
Se prueba si el Schur de Stieltjes sobre S* da sigma* (y por tanto sigma) a L=35.
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

def rev_poly(p, deg):
    """Reverso de un polinomio de grado <= deg: rev[i] = p[deg-i]."""
    return [p[deg-i] if deg-i < len(p) else 0 for i in range(deg+1)]

rng = np.random.default_rng(123)
n = 70
# Reproduce el caso k=35 (mismo orden de draws que schur_umbral)
S35 = None
for k_err in range(1, 36):
    S = syndrome(rng, k_err, n)
    if k_err == 35:
        S35 = S
S = S35
stats = {"mac": 0, "div": 0, "cambios": 0}
sig_bm, L_bm = G.bm(S, stats)
L = L_bm
print(f"L={L}")
# Sindrome revertido: S*[i] = S[n-1-i]
S_star = [S[n-1-i] for i in range(n)]
# BM sobre S* (para saber el L* y el sigma* esperado)
sig_star_bm, L_star = G.bm(S_star, stats)
print(f"L* (BM sobre S*) = {L_star}")
print(f"sigma*_BM = {trim(sig_star_bm)}")
# sigma revertido (deberia ser sigma* si la dualidad es correcta)
sig_rev = rev_poly(trim(sig_bm), L)
print(f"rev(sigma_BM) = {sig_rev}")
print(f"rev(sigma_BM)==sigma*_BM? {sig_rev == trim(sig_star_bm)}")
# Schur sobre S*
gammas, breakdown = schur_stieltjes(S_star, 2*n+2, n)
print(f"Schur sobre S*: {len(gammas)} gammas, breakdown_k={breakdown}")
conv = convergents(gammas)
found = []
for k, (p, q) in enumerate(conv):
    if q[0] == 0:
        continue
    inv0 = G.inv(q[0])
    qn = [G.mul(c, inv0) for c in q]
    if trim(qn) == trim(sig_star_bm):
        found.append(k)
print(f"Convergentes de S* que dan sigma*_BM: {found}")
# Tambien prueba el convergente [2L*]
if 2*L_star < len(conv):
    p, q = conv[2*L_star]
    if q[0] != 0:
        inv0 = G.inv(q[0])
        qn = trim([G.mul(c, inv0) for c in q])
        print(f"conv*[2L*] q = {qn}  == sigma*_BM? {qn == trim(sig_star_bm)}")
