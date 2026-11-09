#!/usr/bin/env python3
"""Puede x (solucion Toeplitz) recuperarse de p (predictor) + O(1) escalares?
Se prueba si x es combinacion lineal de p y reverso(p) (2 escalares), o de
p y sus shifts. Si si, el algoritmo de Schur es: mantener solo p, recuperar
x al final. Si no, se necesita otra estructura.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_toeplitz import syndrome, toeplitz_solve_direct, levinson_toeplitz, trim

def solve_2x2(a11, a12, a21, a22, b1, b2):
    """Resuelve [[a11,a12],[a21,a22]] [u,v]^T = [b1,b2]^T sobre GF(2^12). Devuelve (u,v) o None."""
    det = G.mul(a11, a22) ^ G.mul(a12, a21)
    if det == 0:
        return None
    invd = G.inv(det)
    u = G.mul(G.mul(b1, a22) ^ G.mul(b2, a12), invd)
    v = G.mul(G.mul(a11, b2) ^ G.mul(a21, b1), invd)
    return u, v

rng = np.random.default_rng(7)
for (k_err, n) in [(2, 6), (5, 20), (8, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    L = L_bm
    x_lev, p_lev, gammas = levinson_toeplitz(S, L)
    if x_lev is None:
        print(f"k={k_err}: levinson fallo"); continue
    x = x_lev; p = p_lev; revp = list(reversed(p))
    # x = a*p + b*revp ? Resolver con las 2 primeras componentes (si L>=2)
    if L >= 2:
        sol = solve_2x2(p[0], revp[0], p[1], revp[1], x[0], x[1])
        if sol is None:
            print(f"k={k_err} L={L}: sistema 2x2 singular, no se puede probar")
            continue
        a, b = sol
        recon = [G.mul(a, p[i]) ^ G.mul(b, revp[i]) for i in range(L)]
        print(f"k={k_err} n={n} L={L}: x == a*p + b*revp? {recon == x}  (a={a}, b={b})")
    # x = a*p (un escalar)?
    if p[0] != 0:
        a = G.mul(x[0], G.inv(p[0]))
        recon = [G.mul(a, v) for v in p]
        print(f"   x == a*p? {recon == x} (a={a})")
    print(f"   x={x}")
    print(f"   p={p}")
    print(f"   revp={revp}")
