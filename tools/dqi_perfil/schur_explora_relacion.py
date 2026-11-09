#!/usr/bin/env python3
"""Explora la relacion entre predictor f y solucion u en Levinson (Hankel simetrico).

Pregunta: se puede derivar u^{(L)} de f (predictor) sin mantener u por separado?
Se prueban relaciones candidatas: u = f_{L+1}[0..L-1], u = reverso, u = shift, etc.
Tambien se examina w = M_k^{-1} c (el vector auxiliar de Levinson) vs f.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_levinson import syndrome, solve_hankel_w, levinson_hankel, trim

def predictor_full(S, K):
    """Calcula f^{(k)} para k=1..K (predictor M_k f = e_0) por Levinson, sin u.
    Devuelve lista de f^{(k)}."""
    # f^{(1)} = [inv(S_0)]
    if S[0] == 0:
        return None
    fs = [[G.inv(S[0])]]
    f = fs[0]
    for k in range(1, K):
        c = [S[k+i] for i in range(k)]
        w = solve_hankel_w(S, k, c)
        if w is None:
            return None
        cTf = 0
        for i in range(k):
            cTf ^= G.mul(c[i], f[i])
        cTw = 0
        for i in range(k):
            cTw ^= G.mul(c[i], w[i])
        denom = S[2*k] ^ cTw
        if denom == 0:
            return None
        alpha = G.mul(cTf, G.inv(denom))
        f_new = [0]*(k+1)
        for i in range(k):
            f_new[i] = f[i] ^ G.mul(alpha, w[i])
        f_new[k] = alpha
        f = f_new
        fs.append(list(f))
    return fs

rng = np.random.default_rng(7)
for (k_err, n) in [(2, 6), (5, 20), (8, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    L = L_bm
    u_lev, f_lev, hist = levinson_hankel(S, L)
    fs = predictor_full(S, L+1)
    print(f"=== k={k_err} n={n} L={L} ===")
    print(f"  BM sigma={trim(sig_bm)}")
    print(f"  u^{(L)} (Levinson)={u_lev}")
    print(f"  f^{(L)}={f_lev}")
    if fs is not None and len(fs) > L:
        fLp1 = fs[L]
        print(f"  f^{{(L+1)}}={fLp1}")
        print(f"  f^{{(L+1)}}[0..L-1] == u? {fLp1[:L] == u_lev}")
        print(f"  reverso(f^{{(L+1)}})[0..L-1] == u? {list(reversed(fLp1))[:L] == u_lev}")
        print(f"  reverso(f^{{(L)}}) == u? {list(reversed(f_lev)) == u_lev}")
        # w en el ultimo paso vs f
        c = [S[L-1+i] for i in range(L-1)]
        w = solve_hankel_w(S, L-1, c)
        print(f"  w (ultimo paso, k=L-1)={w}")
        print(f"  w == reverso(f^{{(L-1)}})? {w == list(reversed(fs[L-2])) if len(fs)>L-1 else 'n/a'}")
        print(f"  w == f^{{(L-1)}}? {w == fs[L-2] if len(fs)>L-1 else 'n/a'}")
    # Relacion entre u y f: u = a*f + b*reverso(f)? Resolver por coeficientes en un caso chico
    # Se verifica si u es combinacion lineal de f y reverso(f) (2 escalares)
    # (solo diagnostico, no es la recurrencia)
    print()
