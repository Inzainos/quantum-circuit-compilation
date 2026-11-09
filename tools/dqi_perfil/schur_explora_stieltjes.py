#!/usr/bin/env python3
"""Algoritmo de Schur (fraccion continua de Stieltjes) para la ecuacion clave.

f(x) = gamma_0 + x/(gamma_1 + x/(gamma_2 + ...))
Pasos de Schur (en sitio sobre la serie):
  f_0 = S
  gamma_k = f_k(0)
  f_{k+1} = x / (f_k - gamma_k)   [= 1 / ((f_k - gamma_k)/x)]
Los gamma_k son escalares; el estado es la serie (en sitio) + O(1).
Los convergentes (recurrencia de fraccion continua) deben dar omega/sigma.

Se verifica que el convergente [L-1/L] da sigma == BM.
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

def series_reciprocal(f, n):
    """Reciproco de una serie f (f[0] != 0), truncado a n terminos.
    g[0] = inv(f[0]); g[k] = -inv(f[0]) * sum_{i=1..k} f[i]*g[k-i]."""
    if f[0] == 0:
        return None
    inv0 = G.inv(f[0])
    g = [0]*n
    g[0] = inv0
    for k in range(1, n):
        acc = 0
        for i in range(1, k+1):
            if i < len(f):
                acc ^= G.mul(f[i], g[k-i])
        g[k] = G.mul(acc, inv0)
    return g

def schur_stieltjes(S, nsteps, n):
    """Algoritmo de Schur. Devuelve (gammas, f_series_list, breakdown_k).
    f_0 = S. gamma_k = f_k[0]. f_{k+1} = 1 / ((f_k - gamma_k)/x).
    Si hay breakdown, devuelve las gammas parciales y el k del breakdown."""
    f = list(S) + [0]*max(0, n-len(S))
    gammas = []
    breakdown = None
    for k in range(nsteps):
        gamma = f[0]
        gammas.append(gamma)
        # g = (f - gamma)/x  -> g[i] = f[i+1]
        g = f[1:] + [0]
        # f_{k+1} = 1/g (reciproco). Necesita g[0] != 0, i.e. f[1] != 0.
        if g[0] == 0:
            breakdown = k
            break
        f = series_reciprocal(g, n)
        if f is None:
            breakdown = k
            break
    return gammas, breakdown

def convergents(gammas):
    """Convergentes de la fraccion continua f = gamma_0 + x/(gamma_1 + x/(gamma_2+...)).
    p_{-1}=1, p_0=gamma_0; p_k = gamma_k*p_{k-1} + x*p_{k-2}  (polinomios en x)
    q_{-1}=0, q_0=1;   q_k = gamma_k*q_{k-1} + x*q_{k-2}
    Devuelve lista de (p_k, q_k) como polinomios (listas de coefs)."""
    # p y q son polinomios en x; la recurrencia es p_k = gamma_k*p_{k-1} + x*p_{k-2}
    p_prev2 = [1]      # p_{-1}
    p_prev1 = [gammas[0]]  # p_0
    q_prev2 = [0]      # q_{-1}
    q_prev1 = [1]      # q_0
    conv = [(list(p_prev1), list(q_prev1))]
    for k in range(1, len(gammas)):
        g = gammas[k]
        # p_k = g*p_{k-1} + x*p_{k-2}
        n = max(len(p_prev1), len(p_prev2)+1)
        pk = [0]*n
        for i, c in enumerate(p_prev1):
            pk[i] ^= G.mul(g, c)
        for i, c in enumerate(p_prev2):
            pk[i+1] ^= c
        # q_k = g*q_{k-1} + x*q_{k-2}
        nq = max(len(q_prev1), len(q_prev2)+1)
        qk = [0]*nq
        for i, c in enumerate(q_prev1):
            qk[i] ^= G.mul(g, c)
        for i, c in enumerate(q_prev2):
            qk[i+1] ^= c
        conv.append((trim(pk), trim(qk)))
        p_prev2, p_prev1 = p_prev1, trim(pk)
        q_prev2, q_prev1 = q_prev1, trim(qk)
    return conv

rng = np.random.default_rng(7)
for (k_err, n) in [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm == 0:
        print(f"k={k_err} n={n}: L=0, salto")
        continue
    L = L_bm
    gammas, breakdown = schur_stieltjes(S, 2*L+2, n)
    print(f"k={k_err} n={n} L={L}: gammas_parciales={len(gammas)} breakdown_k={breakdown}")
    conv = convergents(gammas)
    # Busca CUALQUIER convergente (p,q) con deg(q)=L que de q==sigma (normalizado)
    found = None
    for k, (p, q) in enumerate(conv):
        if len(q)-1 == L and q[0] != 0:
            inv0 = G.inv(q[0])
            qn = [G.mul(c, inv0) for c in q]
            if trim(qn) == trim(sig_bm):
                found = (k, p, q)
                break
    if found is None:
        print(f"   ningun convergente da sigma. Convergentes (deg p, deg q): {[(len(p)-1, len(q)-1) for p,q in conv]}")
        # muestra el convergente con deg q = L si existe
        for k, (p, q) in enumerate(conv):
            if len(q)-1 == L:
                inv0 = G.inv(q[0]) if q[0] != 0 else None
                qn = [G.mul(c, inv0) for c in q] if inv0 else q
                print(f"   conv[{k}] q_norm={trim(qn)} vs BM={trim(sig_bm)}")
        continue
    k, p, q = found
    inv0 = G.inv(q[0])
    qn = [G.mul(c, inv0) for c in q]
    pn = [G.mul(c, inv0) for c in p]
    print(f"   convergente [{k}] q==sigma_BM! q_norm={trim(qn)}")
    print(f"   p_norm={trim(pn)} (omega?)")
