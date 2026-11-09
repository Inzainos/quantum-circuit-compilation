#!/usr/bin/env python3
"""Algoritmo q-d (Rutishauser) para los coeficientes de la fraccion continua
de la serie de sindromes S, y convergentes de la J-fraccion -> sigma.

Motivacion: el Stieltjes calcula los gamma_k con un reciproco de serie
O(n^2) POR PASO (2L+1 pasos -> O(L*n^2) ~ 179k muls). El q-d calcula los
coeficientes de la fraccion continua con reglas rombo O(1) por entrada
de tabla: O(n^2) TOTAL, estado O(n) (una fila). Es el candidato a
"Schur por bloques" en el sentido de costo: si el q-d da los mismos
convergentes (sigma) que el Stieltjes, el costo baja de O(L*n^2) a O(n^2).

q-d estandar (serie f(z) = sum c_n z^n, c_0 != 0):
  e_0^(n) = 0
  q_1^(n) = c_{n+1} / c_n
  e_k^(n) = q_k^(n+1) - q_k^(n) + e_{k-1}^(n+1)
  q_{k+1}^(n) = e_k^(n+1) * q_k^(n+1) / e_k^(n)
J-fraccion: f = c_0 / (1 - q_1^(0) z / (1 - e_1^(0) z / (1 - q_2^(0) z / (...))))
Convergentes por recurrencia de fraccion continua:
  f = 0 + c_0 / (1 + (-q_1 z)/(1 + (-e_1 z)/(1 + (-q_2 z)/(...))))
  A_0=0, B_1=c_0; A_k=1 (k>=1); B_2=-q_1 z, B_3=-e_1 z, B_4=-q_2 z, ...
  p_{-1}=1, p_0=A_0; p_k = A_k p_{k-1} + B_k p_{k-2}
  q_{-1}=0, q_0=1;   q_k = A_k q_{k-1} + B_k q_{k-2}
Se busca el convergente con deg(q_k)=L y q_k == sigma (normalizado).

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

def qd_table(c, kmax):
    """Tabla q-d. c = coeficientes de la serie (c[0] != 0).
    Devuelve (qs, es) donde qs[k][n] = q_k^(n), es[k][n] = e_k^(n).
    Cuenta multiplicaciones/divisiones de campo. Devuelve None si hay
    division por cero (e_k^(n)==0 o c_n==0) -> breakdown (bloque singular)."""
    n = len(c)
    # q_1^(n) = c_{n+1}/c_n ; e_0^(n) = 0
    qs = [None]  # qs[0] sin uso
    es = [[0]*(n+1)]  # es[0][n] = 0
    q1 = [0]*(n+1)
    for i in range(n):
        if c[i] == 0:
            return None, None, ("q1", i, "c==0")
        q1[i] = G.mul(c[i+1] if i+1 < n else 0, G.inv(c[i]))
    qs.append(q1)
    nmul = n  # divisiones de q1
    ndiv = n
    for k in range(1, kmax+1):
        # e_k^(n) = q_k^(n+1) - q_k^(n) + e_{k-1}^(n+1)
        ek = [0]*(n+1)
        qk = qs[k]
        ekm1 = es[k-1]
        for i in range(n):
            ek[i] = qk[i+1] ^ qk[i] ^ ekm1[i+1]
        es.append(ek)
        # q_{k+1}^(n) = e_k^(n+1) * q_k^(n+1) / e_k^(n)
        qkp1 = [0]*(n+1)
        for i in range(n):
            if ek[i] == 0:
                return None, None, ("q", k+1, i, "e==0")
            qkp1[i] = G.mul(G.mul(ek[i+1], qk[i+1]), G.inv(ek[i]))
            nmul += 2; ndiv += 1
        qs.append(qkp1)
    return qs, es, ("ok", nmul, ndiv)

def jfrac_convergents(c0, qs, es, nconv):
    """Convergentes de la J-fraccion con coeficientes (q_k^(0), e_k^(0)).
    f = 0 + c_0/(1 + (-q_1 z)/(1 + (-e_1 z)/(1 + (-q_2 z)/(...)))).
    A_0=0, B_1=c_0; A_k=1; B_{2k}=-q_k z, B_{2k+1}=-e_k z (k>=1).
    Devuelve lista de (p_k, q_k) polinomios."""
    # Coeficientes B_k (k>=1): B_1 = c_0 (constante); B_{2k} = -q_k*z ; B_{2k+1} = -e_k*z
    # A_k = 1 para k>=1, A_0 = 0.
    # p_{-1}=1, p_0=0 ; q_{-1}=0, q_0=1.
    # p_k = A_k*p_{k-1} + B_k*p_{k-2}; q_k = A_k*q_{k-1} + B_k*q_{k-2}.
    # B_k es polinomio: B_1=[c_0]; B_{2k}=[0, -q_k] = [0, q_k] (car 2); B_{2k+1}=[0, e_k].
    def pmul_scalar_poly(s, p):
        return [G.mul(s, c) for c in p]
    def padd(a, b):
        n = max(len(a), len(b))
        out = [0]*n
        for i, c in enumerate(a):
            out[i] ^= c
        for i, c in enumerate(b):
            out[i] ^= c
        return trim(out)
    def pmul_x(p):
        return [0] + list(p)
    def B(k):
        if k == 1:
            return [c0]
        if k % 2 == 0:
            qk = qs[k//2][0]
            return [0, qk]
        else:
            ek = es[(k-1)//2][0]
            return [0, ek]
    p_prev2 = [1]   # p_{-1}
    p_prev1 = [0]   # p_0 = A_0 = 0
    q_prev2 = [0]   # q_{-1}
    q_prev1 = [1]   # q_0
    conv = []
    for k in range(1, nconv+1):
        Ak = 1  # A_k = 1 para k>=1
        Bk = B(k)
        # p_k = Ak*p_{k-1} + Bk*p_{k-2} ; Bk es [c] o [0, c]
        pk = list(p_prev1)  # Ak=1
        if len(Bk) == 1:
            add = pmul_scalar_poly(Bk[0], p_prev2)
        else:
            add = pmul_x(pmul_scalar_poly(Bk[1], p_prev2))
        pk = padd(pk, add)
        qk = list(q_prev1)
        if len(Bk) == 1:
            addq = pmul_scalar_poly(Bk[0], q_prev2)
        else:
            addq = pmul_x(pmul_scalar_poly(Bk[1], q_prev2))
        qk = padd(qk, addq)
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
print("=== q-d + J-fraccion vs BM ===")
for (k_err, n) in [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70), (12, 70), (20, 70), (35, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm == 0:
        print(f"k={k_err} n={n}: L=0, salto")
        continue
    L = L_bm
    qs, es, info = qd_table(S, 2*L+2)
    if qs is None:
        print(f"k={k_err} n={n} L={L}: q-d BREAKDOWN en {info}")
        continue
    # convergentes de la J-fraccion
    conv = jfrac_convergents(S[0], qs, es, 4*L+4)
    found = None
    for k, (p, q) in enumerate(conv):
        if len(q)-1 == L and q[0] != 0:
            inv0 = G.inv(q[0])
            qn = [G.mul(c, inv0) for c in q]
            if trim(qn) == trim(sig_bm):
                found = (k, p, q)
                break
    if found is None:
        print(f"k={k_err} n={n} L={L}: ningun convergente J da sigma. degs q: {[len(q)-1 for p,q in conv][:12]}")
        continue
    k, p, q = found
    inv0 = G.inv(q[0])
    qn = [G.mul(c, inv0) for c in q]
    pn = [G.mul(c, inv0) for c in p]
    # ecuacion clave: sigma*S mod x^n == omega?
    prod = pmul(qn, S)
    lhs = trim(prod[:n])
    ok_key = lhs == trim(pn) and pdeg(pn) < L
    print(f"k={k_err} n={n} L={L}: convergente J[{k}] q==sigma_BM! ec_clave={ok_key} qd_info={info}")
