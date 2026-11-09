#!/usr/bin/env python3
"""Prueba de la recurrencia de Szego/Schur para la ecuacion clave.

Idea: los polinomios ortogonales respecto al funcional de momentos L(x^j)=S_j
satisfacen una recurrencia de Szego (dos terminos, con reversion):
    phi_{k+1}(x) = x*phi_k(x) + gamma_k * phi_k^*(x)
donde phi_k^*(x) = x^k phi_k(1/x) es el polinomio revertido.
Solo se necesita UN polinomio (phi_k) + O(1) escalares: la propiedad Schur.
phi_L deberia ser sigma (salvo normalizacion).

Se prueba gamma_k impuesto por ortogonalidad L(phi_{k+1}) = 0, y se verifica
ortogonalidad completa y que phi_L == sigma de BM.
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

def L_moment(S, poly):
    """L(p) = sum_i p_i * S_i (funcional de momentos). poly es lista de coefs."""
    acc = 0
    for i, c in enumerate(poly):
        if i < len(S):
            acc ^= G.mul(c, S[i])
    return acc

def reverse_poly(p):
    """p^*(x) = x^{deg} p(1/x): coeficientes revertidos (sin ceros de cola)."""
    p = trim(p)
    return list(reversed(p))

def schur_szego(S, L):
    """Recurrencia de Szego. Devuelve (phis, gammas, ok_orto).
    phi_0 = [1]. phi_{k+1} = x*phi_k + gamma_k * phi_k^*.
    gamma_k se elige para que L(phi_{k+1}) = 0."""
    phis = [[1]]
    gammas = []
    for k in range(L):
        phi = phis[-1]
        # x*phi_k
        xphi = [0] + phi
        # phi_k^*
        phistar = reverse_poly(phi)
        # L(x*phi_k) y L(phi_k^*)
        Lxphi = L_moment(S, xphi)
        Lphistar = L_moment(S, phistar)
        if Lphistar == 0:
            return phis, gammas, False, f"gamma indefinido en k={k} (L(phi*)==0)"
        gamma = G.mul(Lxphi, G.inv(Lphistar))
        gammas.append(gamma)
        # phi_{k+1} = x*phi_k + gamma*phi_k^* (alineados por grado)
        n = max(len(xphi), len(phistar))
        nxt = [0]*n
        for i in range(len(xphi)):
            nxt[i] ^= xphi[i]
        for i in range(len(phistar)):
            nxt[i] ^= G.mul(gamma, phistar[i])
        phis.append(trim(nxt))
    # verificar ortogonalidad de cada phi_k: L(phi_k * x^j) = 0 para j<k
    ok_orto = True
    for k, phi in enumerate(phis):
        for j in range(k):
            # L(phi_k * x^j) = sum_i phi_i * S_{i+j}
            acc = 0
            for i, c in enumerate(phi):
                if i+j < len(S):
                    acc ^= G.mul(c, S[i+j])
            if acc != 0:
                ok_orto = False
    return phis, gammas, ok_orto, ""

rng = np.random.default_rng(7)
for (k_err, n) in [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm == 0:
        print(f"k={k_err} n={n}: L=0, salto")
        continue
    L = L_bm
    phis, gammas, ok_orto, msg = schur_szego(S, L)
    phi_L = trim(phis[-1]) if len(phis) > L else None
    ok_sigma = phi_L is not None and phi_L == trim(sig_bm)
    print(f"k={k_err} n={n} L={L}: ortogonal={ok_orto} phi_L==sigma_BM={ok_sigma} {msg}")
    if phi_L is not None:
        print(f"   phi_L={phi_L}")
        print(f"   BM   ={trim(sig_bm)}")
        print(f"   gammas={gammas}")
