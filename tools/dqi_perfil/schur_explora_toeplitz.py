#!/usr/bin/env python3
"""Levinson para el sistema Toeplitz de la ecuacion clave.

Sistema: T sigma' = b, T_{a,b} = S_{L+a-b-1} (a,b=0..L-1), b_a = S_{L+a}.
T es Toeplitz y persimetrica (T_{a,b} = T_{L-1-b,L-1-a}).
Pregunta: el predictor y la solucion, estan relacionados? Se puede mantener
un solo vector (propiedad Schur)?

Levinson Toeplitz: se mantiene el predictor p^{(k)} (solucion de T_k p = e_0
o del sistema de Yule-Walker) y la solucion x^{(k)}. Se examina si x se
deriva de p (p. ej., x = combinacion de p y su reverso).
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

def toeplitz_solve_direct(S, L):
    """Resuelve T x = b por eliminacion directa (referencia)."""
    A = [[0]*(L+1) for _ in range(L)]
    for a in range(L):
        for b in range(L):
            A[a][b] = S[L+a-b-1]
        A[a][L] = S[L+a]
    for col in range(L):
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
    x = [0]*L
    for a in range(L):
        x[a] = G.mul(A[a][L], G.inv(A[a][a]))
    return x

def levinson_toeplitz(S, L):
    """Levinson para T x = b (Toeplitz persimetrico).
    Mantiene predictor p^{(k)} (T_k p = e_0) y solucion x^{(k)} (T_k x = b_k).
    Devuelve (x, p, gammas) o (None,...) si hay breakdown (denom 0).
    La recursion usa la persimetria: el predictor 'hacia atras' es el reverso.
    """
    # T_1 = [S_{L-1}]. p^{(1)} = [inv(S_{L-1})]. x^{(1)} = [S_L * inv(S_{L-1})].
    if S[L-1] == 0:
        return None, None, None
    inv_T0 = G.inv(S[L-1])
    p = [inv_T0]
    x = [G.mul(S[L], inv_T0)]
    gammas = []
    for k in range(1, L):
        # T_{k+1} = [[T_k, c],[r^T, S_{L-1}]] donde:
        # c (ultima columna, sin diagonal) = (S_{L-k-1}..S_{L-2})? Verificar:
        # T_{k+1}[a][k] = S_{L+a-k-1} para a=0..k-1, y T_{k+1}[k][k] = S_{L-1}.
        # r (ultima fila, sin diagonal) = (S_{L+k-1}..S_{L})? T_{k+1}[k][b] = S_{L+k-b-1} para b=0..k-1.
        c = [S[L+a-k-1] for a in range(k)]  # columna k (sin diagonal)
        r = [S[L+k-b-1] for b in range(k)]  # fila k (sin diagonal)
        # Por persimetria, r = reverso(c)? c_a = S_{L+a-k-1}; r_b = S_{L+k-b-1}.
        # reverso(c)_b = c_{k-1-b} = S_{L+(k-1-b)-k-1} = S_{L-b-2}. r_b = S_{L+k-b-1}.
        # No son iguales en general. Hmm, la persimetria relaciona T con su reverso,
        # pero c y r son distintos. Se necesita el predictor 'hacia atras' tambien?
        # Para Toeplitz persimetrico, el sistema T_k p = e_0 y T_k q = e_{k-1} cumplen q = reverso(p).
        # El vector auxiliar para extender es w = T_k^{-1} c. Por persimetria, w = reverso(T_k^{-1} r) = reverso(q') donde q' resuelve T_k q' = r.
        # r es la fila k = (S_{L+k-1},...,S_L). Esto es un 'shift' de b_k.
        # Calculamos w por resolucion directa (exploracion; la recursion final lo derivara de p).
        w = toeplitz_solve_vec(S, L, k, c)
        if w is None:
            return None, None, None
        # gamma (reflexion) para el predictor: se impone que p' = (p,0) - gamma*(0,reverso(p)) resuelva T_{k+1} p' = e_0.
        # Condicion en la ultima ecuacion: r^T p_tilde + gamma*... (se deriva abajo)
        # p_tilde = p - gamma * w  (para que la parte superior de T_{k+1} p' = e_0)
        # Ultima ecuacion: r^T (p - gamma w) + gamma' * S_{L-1} = 0, donde gamma' es la ultima componente de p'.
        # Sea p' = (p - gamma*w, gamma). Ultima ecuacion: r^T(p - gamma w) + gamma*S_{L-1} = 0.
        # -> gamma*(S_{L-1} - r^T w) = -r^T p = r^T p (char 2).
        rTp = 0
        for i in range(k):
            rTp ^= G.mul(r[i], p[i])
        rTw = 0
        for i in range(k):
            rTw ^= G.mul(r[i], w[i])
        denom = S[L-1] ^ rTw
        if denom == 0:
            return None, None, None
        gamma = G.mul(rTp, G.inv(denom))
        gammas.append(gamma)
        p_new = [0]*(k+1)
        for i in range(k):
            p_new[i] = p[i] ^ G.mul(gamma, w[i])
        p_new[k] = gamma
        # Solucion: x' = (x - beta*w, beta). Ultima ecuacion: r^T(x - beta w) + beta*S_{L-1} = S_{L+k}.
        rTx = 0
        for i in range(k):
            rTx ^= G.mul(r[i], x[i])
        beta = G.mul(S[L+k] ^ rTx, G.inv(denom))
        x_new = [0]*(k+1)
        for i in range(k):
            x_new[i] = x[i] ^ G.mul(beta, w[i])
        x_new[k] = beta
        p, x = p_new, x_new
    return x, p, gammas

def toeplitz_solve_vec(S, L, k, c):
    """Resuelve T_k w = c (T_k es kxk, (T_k)_{a,b} = S_{L+a-b-1}) por eliminacion directa."""
    A = [[0]*(k+1) for _ in range(k)]
    for a in range(k):
        for b in range(k):
            A[a][b] = S[L+a-b-1]
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
    x_ref = toeplitz_solve_direct(S, L)
    x_lev, p_lev, gammas = levinson_toeplitz(S, L)
    ok_ref = x_ref is not None and [1]+x_ref == trim(sig_bm)
    ok_lev = x_lev is not None and [1]+x_lev == trim(sig_bm)
    print(f"k={k_err} n={n} L={L}: toeplitz_directo sigma_ok={ok_ref} levinson sigma_ok={ok_lev}")
    if x_lev is not None:
        print(f"   x={x_lev}")
        print(f"   p={p_lev}")
        print(f"   gammas={gammas}")
        # Relacion x vs p: es x = reverso(p) escalado? es x = p * algo?
        print(f"   reverso(p)={list(reversed(p_lev))}")
