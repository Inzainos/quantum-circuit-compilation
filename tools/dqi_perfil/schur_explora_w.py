#!/usr/bin/env python3
"""Comprueba si w = T_k^{-1} c se deriva del predictor p (Schur).
Candidatos: w = reverso(p), w = p, w = reverso(p) escalado, w = shift.
Si w = reverso(p), el Levinson Toeplitz es una recursion de UN solo vector
(propiedad Schur) para el predictor; falta ver como se recupera x (sigma).
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_toeplitz import syndrome, toeplitz_solve_vec, trim

rng = np.random.default_rng(7)
for (k_err, n) in [(2, 6), (5, 20), (8, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    L = L_bm
    # Reconstruye p^{(k)} paso a paso (solo predictor) y compara w con reverso(p)
    if S[L-1] == 0:
        print(f"k={k_err}: S[L-1]==0, salto"); continue
    p = [G.inv(S[L-1])]
    print(f"=== k={k_err} n={n} L={L} ===")
    for k in range(1, L):
        c = [S[L+a-k-1] for a in range(k)]
        w = toeplitz_solve_vec(S, L, k, c)
        rev_p = list(reversed(p))
        print(f"  k={k}: w={w}")
        print(f"        reverso(p)={rev_p}  w==rev(p)? {w == rev_p}")
        print(f"        p={p}  w==p? {w == p}")
        # w = reverso(p) * escalar? w[0]/rev_p[0] constante?
        if w is not None and rev_p[0] != 0:
            s = G.mul(w[0], G.inv(rev_p[0]))
            scaled = [G.mul(s, v) for v in rev_p]
            print(f"        w == reverso(p)*{s}? {w == scaled}")
        # avanza p con la recursion de Levinson (usando w, como antes)
        r = [S[L+k-b-1] for b in range(k)]
        rTp = 0
        for i in range(k):
            rTp ^= G.mul(r[i], p[i])
        rTw = 0
        for i in range(k):
            rTw ^= G.mul(r[i], w[i])
        denom = S[L-1] ^ rTw
        gamma = G.mul(rTp, G.inv(denom))
        p_new = [0]*(k+1)
        for i in range(k):
            p_new[i] = p[i] ^ G.mul(gamma, w[i])
        p_new[k] = gamma
        p = p_new
    print()
