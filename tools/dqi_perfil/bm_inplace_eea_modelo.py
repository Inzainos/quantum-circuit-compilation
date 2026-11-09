#!/usr/bin/env python3
"""Modelo clasico del decodificador in-place (EEA/Schur) para la ecuacion clave.

Resuelve la ecuacion clave sigma(x)*S(x) = omega(x) (mod x^n) con el
algoritmo de Euclides extendido (EEA), y verifica que el sigma obtenido
coincide con el del modelo BM clasico (dqi_bm_model.bm).

La propiedad in-place: el estado del EEA es el par (r, t) con
deg(r) + deg(t) ~= n, i.e. ~n coeficientes en total, que caben en el
arreglo del sindrome S (n slots). El sindrome se CONSUME (se transforma
en sitio en el estado (r,t)) en vez de leerse como en BM v1, donde S
queda intacto y sigma/tau necesitan registros separados. Por eso el
Q del in-place es S (840) + O(1) trabajo, no S + sigma + tau.

Se verifica contra dqi_bm_model.bm en varios sindromes (k=2 y k=5).
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import dqi_bm_model as G

DEG = 12

def padd(a, b):
    n = max(len(a), len(b))
    a = list(a) + [0] * (n - len(a))
    b = list(b) + [0] * (n - len(b))
    return [x ^ y for x, y in zip(a, b)]

def pmul(a, b):
    if not a or not b:
        return [0]
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] ^= G.mul(x, y)
    return out

def pdivmod(a, b):
    """Divide a entre b (polinomios sobre GF(2^12)). Devuelve (q, r)."""
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    b = list(b)
    while len(b) > 1 and b[-1] == 0:
        b.pop()
    if len(a) < len(b):
        return [0], a
    q = [0] * (len(a) - len(b) + 1)
    inv_lead = G.inv(b[-1])
    while len(a) >= len(b) and not (len(a) == 1 and a[0] == 0):
        k = len(a) - len(b)
        c = G.mul(a[-1], inv_lead)
        q[k] = c
        for j in range(len(b)):
            a[k + j] ^= G.mul(c, b[j])
        while len(a) > 1 and a[-1] == 0:
            a.pop()
    return q, a

def pdeg(a):
    d = len(a) - 1
    while d > 0 and a[d] == 0:
        d -= 1
    return d

def pscale(a, c):
    return [G.mul(x, c) for x in a]

def eea_key_equation(Svals, n):
    """EEA sobre (x^n, S(x)). Devuelve (sigma, omega, L, max_slots).

    max_slots = maximo numero de coeficientes almacenados simultaneamente
    en el estado (r_prev, r, t_prev, t) durante la iteracion, medido como
    la suma de longitudes (sin ceros de cola). Es la cota del almacenamiento
    in-place: si max_slots <= n, el estado cabe en el arreglo S (n slots).
    """
    # r_prev = x^n, r = S(x); s_prev=1, s=0; t_prev=0, t=1
    r_prev = [0] * n + [1]
    r = list(Svals) + [0] * max(0, n - len(Svals))
    t_prev, t = [0], [1]
    max_slots = 0
    it = 0
    while True:
        # estado persistente: (r_prev, r, t_prev, t); el transitorio es q
        slots = len(r_prev) + len(r) + len(t_prev) + len(t)
        max_slots = max(max_slots, slots)
        dr, dt = pdeg(r), pdeg(t)
        # regla de parada estandar RS: deg(r) < deg(t)  (o deg(r) < L)
        if dr < dt:
            break
        q, r_next = pdivmod(r_prev, r)
        t_next = padd(t_prev, pmul(q, t))
        r_prev, r = r, r_next
        t_prev, t = t, t_next
        it += 1
        if it > 2 * n:
            raise RuntimeError("EEA no converge")
    # sigma = t normalizado a sigma_0 = 1 ; omega = r
    # t[0] debe ser != 0 (t es el cofactor de S). Normalizar por inv(t[0]).
    if t[0] == 0:
        raise RuntimeError("t[0]==0, no se puede normalizar")
    inv0 = G.inv(t[0])
    sigma = pscale(t, inv0)
    omega = pscale(r, inv0)
    L = pdeg(sigma)
    return sigma, omega, L, max_slots

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

def check_bm(Svals, n):
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig, L = G.bm(Svals, stats)
    return sig, L

rng = np.random.default_rng(7)
for (k, n) in [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70)]:
    Svals = syndrome(rng, k, n)
    sig_bm, L_bm = check_bm(Svals, n)
    sigma, omega, L_eea, slots = eea_key_equation(Svals, n)
    # comparar sigma (recortar ceros de cola)
    def trim(a):
        a = list(a)
        while len(a) > 1 and a[-1] == 0:
            a.pop()
        return a
    ok = trim(sigma) == trim(sig_bm)
    # verificar ecuacion clave: sigma*S mod x^n == omega (deg omega < L)
    prod = pmul(trim(sigma), Svals)
    lhs = prod[:n]
    ok2 = trim(lhs) == trim(omega) and pdeg(omega) < L_eea
    print(f"k={k} n={n}: BM L={L_bm} EEA L={L_eea} sigma_igual={ok} ec_clave={ok2} max_slots={slots} (n={n})")
    if not ok:
        print("  BM sigma:", trim(sig_bm))
        print("  EEA sigma:", trim(sigma))
    print(f"  sigma={trim(sigma)} omega={trim(omega)}")
