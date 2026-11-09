#!/usr/bin/env python3
"""Validacion del diagnostico de ceros del q-d via determinantes de Hankel.
La columna n=0 (q_k^(0), e_k^(0)) se calcula DIRECTO desde H_k^(0), H_k^(1):
  q_k^(0) = H_k^(1) H_{k-1}^(0) / (H_k^(0) H_{k-1}^(1))
  e_k^(0) = H_{k+1}^(0) H_{k-1}^(1) / (H_k^(0) H_k^(1))
con H_0=1. Los H se calculan por eliminacion gaussiana exacta con pivoteo
(solo validacion clasica, O(n^3)). Si el cero del q-d estaba en n>=2, la
columna n=0 no lo toca y el (q,e) sale bien -> el cero era artefacto de
propagacion de la tabla. Si el cero es H_K^(0)=0 o H_K^(1)=0 (n=0,1), es
bloque singular real y hace falta el salto 2x2.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_bloques_qd2 import syndrome, jfrac_convergents, pmul, trim, pdeg

def hankel_det(S, k, n0):
    """det de la matriz kxk M_ij = S_{n0+i+j}. Eliminacion gaussiana con
    pivoteo parcial sobre GF(2^12). Devuelve 0 si singular."""
    if k == 0:
        return 1
    n = len(S)
    # matriz kxk
    M = [[0]*k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            idx = n0+i+j
            M[i][j] = S[idx] if idx < n else 0
    det = 1
    for col in range(k):
        # pivote
        piv = -1
        for r in range(col, k):
            if M[r][col] != 0:
                piv = r; break
        if piv == -1:
            return 0
        if piv != col:
            M[col], M[piv] = M[piv], M[col]
            # en car 2 el intercambio no cambia el signo (det igual)
        pv = M[col][col]
        det = G.mul(det, pv)
        iv = G.inv(pv)
        for r in range(col+1, k):
            f = G.mul(M[r][col], iv)
            if f == 0:
                continue
            for c in range(col, k):
                M[r][c] ^= G.mul(f, M[col][c])
    return det

def qe_from_hankel(S, L):
    """(q0,e0) para la columna n=0 desde Hankel. Devuelve (q0,e0,info)."""
    H0 = [1]*(L+3); H1 = [1]*(L+3)
    for k in range(1, L+3):
        H0[k] = hankel_det(S, k, 0)
        H1[k] = hankel_det(S, k, 1)
    # ceros en H0/H1
    ceros = [k for k in range(1, L+3) if H0[k]==0] 
    ceros1 = [k for k in range(1, L+3) if H1[k]==0]
    q0 = [None]*(L+1); e0 = [None]*(L+1)
    for k in range(1, L+1):
        # q_k = H_k^(1) H_{k-1}^(0) / (H_k^(0) H_{k-1}^(1))
        den = G.mul(H0[k], H1[k-1])
        if den == 0:
            return None, None, ("q", k, "den0", ceros, ceros1)
        q0[k] = G.mul(G.mul(H1[k], H0[k-1]), G.inv(den))
        # e_k = H_{k+1}^(0) H_{k-1}^(1) / (H_k^(0) H_k^(1))
        den2 = G.mul(H0[k], H1[k])
        if den2 == 0:
            return None, None, ("e", k, "den0", ceros, ceros1)
        e0[k] = G.mul(G.mul(H0[k+1], H1[k-1]), G.inv(den2))
    return q0, e0, ("ok", ceros, ceros1)

rng = np.random.default_rng(2026)
# Reproducir los 11 casos que fallaron en el barrido
fail_cases = []
for trial in range(120):
    k_err = int(rng.integers(1, 36)); n = 70
    S = syndrome(rng, k_err, n)
    stats = {"mac":0,"div":0,"cambios":0}
    sig_bm, L = G.bm(S, stats)
    if L == 0 or L > 34:
        continue
    # checar si el q-d escalar falla
    from schur_bloques_qd2 import qd_col0
    q0, e0, info = qd_col0(S, L)
    if q0 is None:
        fail_cases.append((S, sig_bm, L, info))
print(f"casos que fallan en q-d escalar: {len(fail_cases)}")
for (S, sig_bm, L, info) in fail_cases:
    q0, e0, hinfo = qe_from_hankel(S, L)
    if q0 is None:
        print(f"  L={L} qd_fallo={info} | Hankel TAMBIEN falla: {hinfo}")
        continue
    conv = jfrac_convergents(S[0], q0, e0, 2*L+1)
    found = False
    for kk, (p, q) in enumerate(conv):
        if len(q)-1 == L and q[0] != 0:
            inv0 = G.inv(q[0]); qn = [G.mul(c, inv0) for c in q]
            if trim(qn) == trim(sig_bm):
                pn = [G.mul(c, inv0) for c in p]
                prod = pmul(qn, S); lhs = trim(prod[:70])
                if lhs == trim(pn) and pdeg(pn) < L:
                    found = True; break
    print(f"  L={L} qd_fallo={info} | Hankel: {'sigma OK ec_clave OK' if found else 'NO da sigma'} | H0_ceros={hinfo[1]} H1_ceros={hinfo[2]}")
