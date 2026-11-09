#!/usr/bin/env python3
"""Exploracion de la recurrencia de Schur para la ecuacion clave.

Objetivo: encontrar una recurrencia que resuelva sigma*S = omega (mod x^n)
con estado O(1) ademas del arreglo S (consumiendo S una sola vez).

Estrategia: sistema Hankel simetrico M u = b' (M_{a,i} = S_{a+i}, b'_a = S_{L+a},
u_i = sigma_{L-i}) y algoritmo de Levinson/Schur. Se examina si la recursion
de Levinson se reduce a un solo vector (propiedad Schur) y si el estado cabe
en el arreglo S (slots libres = valores consumidos).

Se valida contra dqi_bm_model.bm.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G

def trim(a):
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a

def syndrome(rng, k, n):
    pos = rng.choice(4095, size=k, replace=False)
    vals = rng.integers(1, 4096, size=k)
    X = [int(G.EXP[p % 4095]) for p in pos]
    S = []
    for t in range(n):
        s = 0
        for xj, e in zip(X, vals):
            s ^= G.mul(int(e), int(G.EXP[(G.LOG[xj] * t) % 4095]))
        S.append(s)
    return S

def solve_hankel(S, L):
    """Resuelve M u = b' por eliminacion gaussiana directa (referencia).
    M_{a,i} = S_{a+i}, b'_a = S_{L+a}, a,i = 0..L-1. Devuelve u (u_i = sigma_{L-i})."""
    import copy
    # matriz aumentada sobre GF(2^12)
    A = [[0]*(L+1) for _ in range(L)]
    for a in range(L):
        for i in range(L):
            A[a][i] = S[a+i]
        A[a][L] = S[L+a]
    # eliminacion
    for col in range(L):
        # pivote
        piv = None
        for r in range(col, L):
            if A[r][col] != 0:
                piv = r; break
        if piv is None:
            return None
        A[col], A[piv] = A[piv], A[col]
        invp = G.inv(A[col][col])
        for r in range(L):
            if r != col and A[r][col] != 0:
                f = G.mul(A[r][col], invp)
                for c in range(col, L+1):
                    A[r][c] ^= G.mul(f, A[col][c])
    u = [0]*L
    for a in range(L):
        u[a] = G.mul(A[a][L], G.inv(A[a][a]))
    return u

def levinson_hankel(S, L):
    """Levinson para el sistema Hankel simetrico M u = b'.
    Mantiene el predictor f^{(k)} (solucion de M_k f = e_0) y la solucion u^{(k)}.
    Devuelve (u, f, historial) donde historial registra longitudes de estado.
    """
    # M_k es kxk, (M_k)_{a,i} = S_{a+i}. b'_k = (S_L..S_{L+k-1}).
    # Predictor: M_k f = e_0 = (1,0,...,0). Solucion: M_k u = b'_k.
    # Levinson: se extiende de k a k+1 con el coeficiente de reflexion.
    # Para Hankel simetrico, el predictor "hacia atras" es el reverso del "hacia adelante".
    f = [1]  # f^{(1)}: M_1 = [S_0], M_1 f = [1] -> f = [inv(S_0)]
    if S[0] == 0:
        return None, None, None
    f = [G.inv(S[0])]
    u = [G.mul(S[L], G.inv(S[0]))]  # u^{(1)}: M_1 u = S_L
    hist = [(1, len(f), len(u))]
    for k in range(1, L):
        # Queremos f^{(k+1)} y u^{(k+1)}.
        # M_{k+1} = [[M_k, c],[c^T, S_{2k}]] con c = (S_k..S_{2k-1}).
        # Predictor: M_{k+1} f' = e_0 (longitud k+1).
        # Sea f' = (f_tilde, alpha). M_k f_tilde + alpha*c = e_0 (k vec), c^T f_tilde + alpha*S_{2k} = 0.
        # f_tilde = f - alpha * w, donde w = M_k^{-1} c.
        # Por simetria Hankel, w = reverso de algo relacionado con f. Calculamos w por resolucion directa
        # (solo para explorar la estructura; la recursion final no debe necesitarlo).
        # Resolvemos M_k w = c por eliminacion directa.
        c = [S[k+i] for i in range(k)]
        w = solve_hankel_w(S, k, c)
        if w is None:
            return None, None, None
        # gamma (reflexion) para el predictor: c^T f + alpha*(S_{2k} - c^T w) = 0
        # c^T f:
        cTf = 0
        for i in range(k):
            cTf ^= G.mul(c[i], f[i])
        cTw = 0
        for i in range(k):
            cTw ^= G.mul(c[i], w[i])
        denom = S[2*k] ^ cTw
        if denom == 0:
            return None, None, None
        alpha = G.mul(cTf, G.inv(denom))
        f_new = [0]*(k+1)
        for i in range(k):
            f_new[i] = f[i] ^ G.mul(alpha, w[i])
        f_new[k] = alpha
        # Solucion: u' = (u_tilde, beta). M_k u_tilde + beta*c = b'_k, c^T u_tilde + beta*S_{2k} = S_{L+k}.
        # u_tilde = u - beta*w. beta = (S_{L+k} - c^T u)/(S_{2k} - c^T w).
        cTu = 0
        for i in range(k):
            cTu ^= G.mul(c[i], u[i])
        beta = G.mul(S[L+k] ^ cTu, G.inv(denom))
        u_new = [0]*(k+1)
        for i in range(k):
            u_new[i] = u[i] ^ G.mul(beta, w[i])
        u_new[k] = beta
        f, u = f_new, u_new
        hist.append((k+1, len(f), len(u)))
    return u, f, hist

def solve_hankel_w(S, k, c):
    """Resuelve M_k w = c (M_k Hankel simetrico, (M_k)_{a,i}=S_{a+i}) por eliminacion directa."""
    A = [[0]*(k+1) for _ in range(k)]
    for a in range(k):
        for i in range(k):
            A[a][i] = S[a+i]
        A[a][k] = c[a]
    for col in range(k):
        piv = None
        for r in range(col, k):
            if A[r][col] != 0:
                piv = r; break
        if piv is None:
            return None
        A[col], A[piv] = A[piv], A[col]
        invp = G.inv(A[col][col])
        for r in range(k):
            if r != col and A[r][col] != 0:
                f = G.mul(A[r][col], invp)
                for cc in range(col, k+1):
                    A[r][cc] ^= G.mul(f, A[col][cc])
    w = [0]*k
    for a in range(k):
        w[a] = G.mul(A[a][k], G.inv(A[a][a]))
    return w

rng = np.random.default_rng(7)
for (k_err, n) in [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm == 0:
        print(f"k={k_err} n={n}: L=0, salto")
        continue
    L = L_bm
    u_ref = solve_hankel(S, L)
    u_lev, f_lev, hist = levinson_hankel(S, L)
    # sigma desde u: u_i = sigma_{L-i} -> sigma = [1] + [u_{L-1},...,u_0]
    def sigma_from_u(u):
        sig = [1] + [u[L-1-i] for i in range(L)]
        return trim(sig)
    ok_ref = u_ref is not None and sigma_from_u(u_ref) == trim(sig_bm)
    ok_lev = u_lev is not None and sigma_from_u(u_lev) == trim(sig_bm)
    print(f"k={k_err} n={n} L={L}: hankel_directo sigma_ok={ok_ref} levinson sigma_ok={ok_lev}")
    if u_lev is not None:
        print(f"   historial Levinson (k, |f|, |u|): {hist}")
        # relacion entre w y f? (se explora en el siguiente script)
    if not ok_ref:
        print("   BM sigma:", trim(sig_bm), " hankel u:", u_ref)
