#!/usr/bin/env python3
"""Modelo clasico de Berlekamp-Massey sobre GF(2^12) para el decodificador DQI (solo conteo y validacion).

Forma con division unica por iteracion: sigma += (delta/b) x^m B; en cambio de longitud B <- sigma_antiguo, b <- delta.
Cuenta: multiplicaciones-acumulacion (ixor_gf2_mul = 63 Toffoli medidos), divisiones y eventos de cambio de longitud
(historial que haria falta para invertir el algoritmo). No es un circuito: es la base para decidir si vale la pena.
"""
from __future__ import annotations
import sys, math, logging
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifiers" / "dqi"))
import verify_submission_dqi as v

log = logging.getLogger("bm_model")
DEG, POLY = 12, 0x1053  # x^12+x^6+x^4+x+1 (primitivo)
Q = 1 << DEG
EXP = np.zeros(2 * Q, dtype=np.int64); LOG = np.zeros(Q, dtype=np.int64)
_x = 1
for i in range(Q - 1):
    EXP[i] = _x; LOG[_x] = i
    _x <<= 1
    if _x & Q: _x ^= POLY
assert _x == 1, "polinomio no primitivo"
EXP[Q - 1:2 * (Q - 1)] = EXP[:Q - 1]


def mul(a, b):
    return 0 if a == 0 or b == 0 else int(EXP[LOG[a] + LOG[b]])


def inv(a):
    return int(EXP[(Q - 1 - LOG[a]) % (Q - 1)])


def bm(S, stats):
    n = len(S)
    sig = [1] + [0] * n; B = [1] + [0] * n
    L, m, b = 0, 1, 1
    for r in range(n):
        d = 0
        for i in range(0, min(L, r) + 1):
            d ^= mul(sig[i], S[r - i]); stats["mac"] += 1
        if d == 0:
            m += 1; continue
        c = mul(d, inv(b)); stats["div"] += 1
        T = sig[:]
        for i in range(0, n + 1 - m):
            sig[i + m] ^= mul(c, B[i]); stats["mac"] += 1
        if 2 * L <= r:
            L = r + 1 - L; B = T; b = d; m = 1; stats["cambios"] += 1
        else:
            m += 1
    return sig[:L + 1], L


def trial(rng, k, n=70, m_pos=4095):
    pos = rng.choice(m_pos, size=k, replace=False)
    vals = rng.integers(1, Q, size=k)
    X = [int(EXP[p % (Q - 1)]) for p in pos]          # localizadores alpha^pos
    S = []
    for t in range(n):
        s = 0
        for xj, e in zip(X, vals):
            s ^= mul(int(e), int(EXP[(LOG[xj] * t) % (Q - 1)]))
        S.append(s)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig, L = bm(S, stats)
    ok = (L == k)
    for xj in X:  # sigma(x_j^-1) = 0
        xi = int(EXP[(-LOG[xj]) % (Q - 1)]); acc = 0
        for i, s in enumerate(sig):
            acc ^= mul(s, int(EXP[(LOG[xi] * i) % (Q - 1)]) if xi else 0)
        ok &= acc == 0
    return ok, stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rng = np.random.default_rng(1)
    r = v.default_num_accepted_values(12)
    p = v.optimal_dqi_weights(4095, 35, 12, r) ** 2
    tot = {"mac": 0, "div": 0, "cambios": 0}; fails = 0; N = 60
    for _ in range(N):
        k = int(rng.choice(36, p=p))
        ok, st = trial(rng, k)
        fails += (not ok)
        for kk in tot: tot[kk] += st[kk]
    log.info("ensayos=%d fallos=%d  media por tiro: mac=%.0f div=%.1f cambios=%.1f",
             N, fails, tot["mac"] / N, tot["div"] / N, tot["cambios"] / N)
    # cota estatica de un circuito: por iteracion r, hasta min(r,35)+1 mac en delta y min(r,35)+1 en la actualizacion
    est = sum(2 * (min(r_, 35) + 1) for r_ in range(70))
    log.info("cota estatica de mac por pasada: %d  -> ~%d Toffoli (63 c/u), ida+vuelta ~%d", est, est * 63, 2 * est * 63)
