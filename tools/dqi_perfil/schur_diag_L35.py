#!/usr/bin/env python3
"""Diagnostico del caso limite L=35 (k=35, 2L=n=70) para la recurrencia de Schur.
Preguntas: (1) es correcto el sigma de BM ahi? (2) que convergente (si alguno)
da el sigma correcto? (3) es un problema de indice o de las gammas?
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_stieltjes import syndrome, schur_stieltjes, convergents, trim
from schur_valida import pmul, pdeg

rng = np.random.default_rng(7)
# Reproduce el mismo caso k=35 que en schur_valida (mismo orden de draws)
cases = [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70), (1, 70), (12, 70), (20, 70), (35, 70)]
S35 = None
for (k_err, n) in cases:
    S = syndrome(rng, k_err, n)
    if k_err == 35:
        S35 = S
        n35 = n
S = S35; n = n35
stats = {"mac": 0, "div": 0, "cambios": 0}
sig_bm, L_bm = G.bm(S, stats)
L = L_bm
print(f"L={L} (BM)")
# Verifica BM: sigma*S mod x^n, deg omega < L?
prod_bm = pmul(trim(sig_bm), S)
lhs_bm = trim(prod_bm[:n])
print(f"BM: deg(omega_BM)={pdeg(lhs_bm)}, cola_cero={all(c==0 for c in prod_bm[L:n])}")
print(f"BM sigma[:5]={trim(sig_bm)[:5]}")
# Schur gammas
gammas, breakdown = schur_stieltjes(S, 2*n+2, n)
print(f"Schur: {len(gammas)} gammas, breakdown_k={breakdown}")
conv = convergents(gammas)
# Busca en TODOS los convergentes el que de sigma_BM
found = []
for k, (p, q) in enumerate(conv):
    if q[0] == 0:
        continue
    inv0 = G.inv(q[0])
    qn = [G.mul(c, inv0) for c in q]
    if trim(qn) == trim(sig_bm):
        found.append(k)
print(f"Convergentes que dan sigma_BM: {found}")
# Para cada convergente cerca de 2L, muestra deg(q), deg(p) y si cumple ec. clave con deg<L
for k in range(max(0, 2*L-3), min(len(conv), 2*L+4)):
    p, q = conv[k]
    if q[0] == 0:
        print(f"  conv[{k}]: q[0]==0")
        continue
    inv0 = G.inv(q[0])
    qn = trim([G.mul(c, inv0) for c in q])
    pn = trim([G.mul(c, inv0) for c in p])
    prod = pmul(qn, S)
    lhs = trim(prod[:n])
    ok_key = lhs == pn and pdeg(pn) < len(qn)-1
    print(f"  conv[{k}]: deg(q)={len(qn)-1} deg(p)={len(pn)-1} q==BM? {qn==trim(sig_bm)} ec_clave_deg<L? {ok_key}")
# Tambien: el convergente [2L-1] y [2L+1]?
print(f"Total convergentes: {len(conv)}")
