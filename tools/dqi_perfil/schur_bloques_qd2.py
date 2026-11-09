#!/usr/bin/env python3
"""Algoritmo q-d (Rutishauser) para los coeficientes de la fraccion continua
de la serie de sindromes S, y convergentes de la J-fraccion -> sigma.

El q-d calcula los coeficientes con reglas rombo O(1) por entrada:
O(n^2) TOTAL, estado O(n) (una fila), vs el Stieltjes que hace un
reciproco de serie O(n^2) POR PASO (2L+1 pasos -> O(L*n^2) ~ 179k muls).

q-d estandar (serie f(z) = sum c_n z^n, c_0 != 0):
  e_0^(n) = 0
  q_1^(n) = c_{n+1} / c_n
  e_k^(n) = q_k^(n+1) - q_k^(n) + e_{k-1}^(n+1)
  q_{k+1}^(n) = e_k^(n+1) * q_k^(n+1) / e_k^(n)
J-fraccion: f = c_0 / (1 - q_1^(0) z / (1 - e_1^(0) z / (1 - q_2^(0) z / (...))))
Convergentes por recurrencia de fraccion continua (ver schur_bloques_qd.py
original para la derivacion). Se busca convergente con deg(q)=L, q==sigma.

Region valida: la entrada (k,n) necesita c_{n+k} (aprox); con N=70 coefs,
la columna n=0 llega hasta k ~ N-1. Para L=35 se necesitarian 2L+1=71 > 69:
el q-d se queda sin coeficientes EXACTAMENTE en el bloque singular L=35.
Para L<=34 debe funcionar (si no hay ceros en S).
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

def qd_col0(c, kmax):
    """Tabla q-d: solo la region necesaria para la columna n=0 hasta k=kmax.
    En nivel k se necesita n <= 2*(kmax-k). e_{kmax+1}=0 es la terminacion
    natural (serie racional, denominador grado kmax) -> se para en kmax.
    Devuelve (q0, e0, info) o (None,None,razon).
    Cuenta multiplicaciones/divisiones de campo."""
    N = len(c)
    nmul = 0; ndiv = 0
    q = {}; e = {}
    def get_q(k, n):
        return q.get((k, n))
    def get_e(k, n):
        if k == 0:
            return 0
        return e.get((k, n))
    # q_1^(n) = c_{n+1}/c_n, n=0..min(N-2, 2*kmax)
    nmax_q1 = min(N-2, 2*kmax)
    for n in range(nmax_q1+1):
        if c[n] == 0:
            return None, None, ("q1", n, "c==0")
        q[(1, n)] = G.mul(c[n+1], G.inv(c[n])); ndiv += 1
    # k=1..kmax: e_k^(n) n=0..2*(kmax-k); q_{k+1}^(n) n=0..2*(kmax-k)-1 (si k<kmax)
    for k in range(1, kmax+1):
        nmax_e = min(N-2*k-1, 2*(kmax-k))
        for n in range(nmax_e+1):
            qkn1 = get_q(k, n+1); qkn = get_q(k, n); ekm1 = get_e(k-1, n+1)
            if qkn1 is None or qkn is None or ekm1 is None:
                return None, None, ("e", k, n, "sin_coefs")
            e[(k, n)] = qkn1 ^ qkn ^ ekm1
        if k < kmax:
            nmax_q = min(N-2*(k+1), 2*(kmax-k)-1)
            for n in range(nmax_q+1):
                ekn1 = get_e(k, n+1); qkn1 = get_q(k, n+1); ekn = get_e(k, n)
                if ekn1 is None or qkn1 is None or ekn is None:
                    return None, None, ("q", k+1, n, "sin_coefs")
                if ekn == 0:
                    return None, None, ("q", k+1, n, "e==0")
                q[(k+1, n)] = G.mul(G.mul(ekn1, qkn1), G.inv(ekn)); nmul += 2; ndiv += 1
    q0 = [None]
    e0 = [None]
    for kk in range(1, kmax+1):
        vq = get_q(kk, 0); ve = get_e(kk, 0)
        if vq is None:
            return None, None, ("col0", kk, "q_falta")
        q0.append(vq)
        e0.append(ve if ve is not None else 0)
    return q0, e0, ("ok", nmul, ndiv)

def jfrac_convergents(c0, q0, e0, nconv):
    """Convergentes de la J-fraccion.
    f = 0 + c_0/(1 + (-q_1 z)/(1 + (-e_1 z)/(1 + (-q_2 z)/(...)))).
    A_0=0, B_1=c_0; A_k=1; B_{2k}=-q_k z, B_{2k+1}=-e_k z (k>=1).
    p_{-1}=1, p_0=0; q_{-1}=0, q_0=1.
    p_k = A_k p_{k-1} + B_k p_{k-2}; q_k = A_k q_{k-1} + B_k q_{k-2}."""
    def padd(a, b):
        n = max(len(a), len(b))
        out = [0]*n
        for i, c in enumerate(a):
            out[i] ^= c
        for i, c in enumerate(b):
            out[i] ^= c
        return trim(out)
    def B(k):
        if k == 1:
            return [c0]
        if k % 2 == 0:
            return [0, q0[k//2]]
        return [0, e0[(k-1)//2]]
    p_prev2 = [1]; p_prev1 = [0]
    q_prev2 = [0]; q_prev1 = [1]
    conv = []
    for k in range(1, nconv+1):
        Bk = B(k)
        if len(Bk) == 1:
            addp = [G.mul(Bk[0], c) for c in p_prev2]
            addq = [G.mul(Bk[0], c) for c in q_prev2]
        else:
            addp = [0] + [G.mul(Bk[1], c) for c in p_prev2]
            addq = [0] + [G.mul(Bk[1], c) for c in q_prev2]
        pk = padd(list(p_prev1), addp)
        qk = padd(list(q_prev1), addq)
        conv.append((trim(pk), trim(qk)))
        p_prev2, p_prev1 = p_prev1, trim(pk)
        q_prev2, q_prev1 = q_prev1, trim(qk)
    return conv

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

rng = np.random.default_rng(7)
print("=== q-d (triangular) + J-fraccion vs BM ===")
for (k_err, n) in [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70), (12, 70), (20, 70), (34, 70), (35, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm == 0:
        print(f"k={k_err} n={n}: L=0, salto")
        continue
    L = L_bm
    kmax = L
    q0, e0, info = qd_col0(S, kmax)
    if q0 is None:
        print(f"k={k_err} n={n} L={L}: q-d BREAKDOWN en {info}")
        continue
    conv = jfrac_convergents(S[0], q0, e0, 2*L+1)
    found = None
    for k, (p, q) in enumerate(conv):
        if len(q)-1 == L and q[0] != 0:
            inv0 = G.inv(q[0])
            qn = [G.mul(c, inv0) for c in q]
            if trim(qn) == trim(sig_bm):
                found = (k, p, q)
                break
    if found is None:
        print(f"k={k_err} n={n} L={L}: ningun convergente J da sigma. degs q: {[len(q)-1 for p,q in conv][:10]}")
        continue
    k, p, q = found
    inv0 = G.inv(q[0])
    qn = [G.mul(c, inv0) for c in q]
    pn = [G.mul(c, inv0) for c in p]
    prod = pmul(qn, S)
    lhs = trim(prod[:n])
    ok_key = lhs == trim(pn) and pdeg(pn) < L
    print(f"k={k_err} n={n} L={L}: convergente J[{k}] q==sigma_BM! ec_clave={ok_key} qd={info}")
