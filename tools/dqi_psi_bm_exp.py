#!/usr/bin/env python3
"""Experimento: Psi = 1/sigma' en las raices via BM sobre la secuencia de sumas de potencias p_t = sum_j X_j^t.
Comprueba si sigma*omega_tau + sigma'*tau~ = c*x^n (relacion de Bezout del BM) para el par final (sigma, tau~)."""
import sys, logging
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import dqi_bm_model as G
import dqi_phase_model as PM
mul, inv = G.mul, G.inv
trim, padd, pmul, pderiv, peval = PM.trim, PM.padd, PM.pmul, PM.pderiv, PM.peval

def bm_paper(S):
    n = len(S)
    sig = [1] + [0] * (n + 1); tau = [1] + [0] * (n + 1)
    dl, s, Ls, Lt = 1, 1, 0, 0
    for r in range(n):
        D = 0
        for i in range(0, min(Ls, r) + 1): D ^= mul(sig[i], S[r - i])
        if D == 0: s += 1; continue
        c = mul(D, inv(dl)); viejo = sig[:]
        for i in range(0, n + 1 - s): sig[i + s] ^= mul(c, tau[i])
        if Lt + s >= Ls:
            Ln = max(Ls, Lt + s); tau = viejo; dl = D; Lt = Ls; s = 1; Ls = Ln
        else: s += 1
    return trim(sig), trim(tau), s, Ls, Lt, dl

rng = np.random.default_rng(2)
ok = 0; tot = 0
for L in (1, 2, 3, 5, 9, 17, 35):
    for rep in range(6):
        pos = [int(x) for x in rng.choice(4095, size=L, replace=False)]
        X = [int(G.EXP[q]) for q in pos]
        for n in (2 * L + 2, 70):
            q = [0] * n
            for t in range(1, n + 1):
                v = 0
                for x in X: v ^= int(G.EXP[(G.LOG[x] * t) % 4095]) if hasattr(G, 'LOG') else 0
                q[t - 1] = v
            sg, tu, s, Ls, Lt, dl = bm_paper(q)
            assert Ls == L, (L, Ls)
            om_s = trim(pmul(q, sg)[:n]); om_t = trim(pmul(q, tu)[:n])
            # x^s tau
            tt = [0] * s + tu
            om_tt = trim(pmul(q, tt)[:n])
            rel = padd(pmul(sg, om_tt), pmul(om_s, tt))
            tot += 1
            print(f"L={L} n={n} s={s} Lt={Lt} rel={'monomio x^%d c=%d' % (len(rel)-1, rel[-1]) if rel and not any(rel[:-1]) else 'NO monomio deg=%d nterm=%d' % (len(rel)-1, sum(1 for z in rel if z))}")
