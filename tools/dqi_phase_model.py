#!/usr/bin/env python3
"""Modelo clasico bit-exacto de la tuberia completa del decodificador DQI al estilo BM (arXiv 2610.22367):

  S (t=1..n)  --BM(variante empate->replace, reescalado)-->  sigma
  omega = S(x)*sigma(x) mod x^n            (evaluador; solo se usan los coeficientes < L)
  Psi   = (sigma')^{-1} mod sigma           (reciproco precalculado: evita dividir por posicion)
  fase  = sum_{raices r de sigma} Tr( mu(M_p) * omega(r) * Psi(r) ),   p = -log(r) mod (q-1)

con paridad(v & M) = Tr(v * mu(M)) y mu = conversion a base dual (lineal, constante, gratis como CNOTs).
Verifica contra la fase directa del verificador: paridad( sum_j popcount(v_j & M_{p_j}) ).
Log: logs/dqi_phase_model.log
"""
from __future__ import annotations
import sys, logging, argparse
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import dqi_bm_model as G
from dqi_bm_forecast import traza_empate_replace
v = G.v
log = logging.getLogger("phase_model")
mul, inv = G.mul, G.inv
Q, DEG = G.Q, G.DEG


def tr(a):  # traza absoluta GF(2^12)->GF(2)
    t, x = 0, a
    for _ in range(DEG):
        t ^= x
        x = mul(x, x)
    assert t in (0, 1)
    return t


# base dual: beta_b con Tr(alpha^a * beta_b) = delta_ab ; entonces paridad(v&M) = Tr(v * sum_b M_b beta_b)
def base_dual():
    basis = [1 << b for b in range(DEG)]          # base polinomial {alpha^b}= bits (alpha=2 es x del polinomio 0x1053)
    A = [[tr(mul(basis[a], e)) for e in range(1, Q)] for a in range(DEG)]  # no se usa; resolvemos por busqueda lineal
    # resolver: para cada b hallar beta con Tr(basis[a]*beta)=delta_ab; Tr es lineal => matriz 12x12 sobre GF(2)
    rows = []
    for a in range(DEG):
        rows.append([tr(mul(basis[a], 1 << c)) for c in range(DEG)])   # fila a: Tr(alpha^a * e_c)
    M = [r[:] + [1 if i == a else 0 for i in range(DEG)] for a, r in enumerate(rows)]
    n = DEG
    for c in range(n):
        p = next(r for r in range(c, n) if M[r][c])
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[r][c]:
                M[r] = [x ^ y for x, y in zip(M[r], M[c])]
    # M[:, n:] = inversa; beta_b = sum_c Inv[c][b] e_c
    beta = []
    for b in range(DEG):
        val = 0
        for c in range(DEG):
            if M[c][n + b]:
                val |= 1 << c
        beta.append(val)
    return beta


BETA = base_dual()


def mu(Mv):
    out = 0
    for b in range(DEG):
        if (Mv >> b) & 1:
            out ^= BETA[b]
    return out


# ---- polinomios sobre GF(2^12): listas de coeficientes (indice = grado) ----
def trim(p):
    while p and p[-1] == 0:
        p = p[:-1]
    return p


def padd(a, b):
    n = max(len(a), len(b))
    return trim([(a[i] if i < len(a) else 0) ^ (b[i] if i < len(b) else 0) for i in range(n)])


def pmul(a, b):
    if not a or not b:
        return []
    r = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                r[i + j] ^= mul(x, y)
    return trim(r)


def pdivmod(a, b):
    a = a[:]; q = [0] * max(1, len(a) - len(b) + 1)
    ib = inv(b[-1])
    while len(trim(a)) >= len(b):
        a = trim(a)
        d = len(a) - len(b)
        c = mul(a[-1], ib)
        q[d] = c
        for i, y in enumerate(b):
            a[i + d] ^= mul(c, y)
    return trim(q), trim(a)


def pinvmod(a, m):
    """inverso de a modulo m (ext. Euclides). Devuelve None si no es coprimo."""
    r0, r1 = m[:], trim(a[:])
    s0, s1 = [], [1]
    while r1:
        q, r = pdivmod(r0, r1)
        r0, r1 = r1, r
        s0, s1 = s1, padd(s0, pmul(q, s1))
    if len(r0) != 1:
        return None
    c = inv(r0[0])
    return pmul(s0, [c])


def peval(p, x):
    acc = 0
    for c in reversed(p):
        acc = mul(acc, x) ^ c
    return acc


def pderiv(p):  # caracteristica 2: solo sobreviven los terminos de grado impar
    return trim([p[i] if i % 2 == 1 else 0 for i in range(1, len(p))])


def fase_directa(pos, vals, Ms):
    return sum(int(x).bit_count() for x, p in zip(vals, pos) for x in [x & Ms[p]]) & 1


def fase_pipeline(S, Ms, n):
    sig, L, ev = traza_empate_replace(S)
    sig = trim(sig)
    omega = trim(pmul(S[:n], sig)[:n])              # S(x)=sum_{t>=1} S_t x^{t-1}  => S[t-1]; mod x^n
    dsig = pderiv(sig)
    psi = pinvmod(dsig, sig) if dsig else None
    if psi is None:
        return None, L
    phi = pdivmod(pmul(omega, psi), sig)[1]
    fase = 0
    for p in range(4095):
        r = int(G.EXP[(-p) % 4095])                  # r = X^{-1}, X = alpha^p
        if peval(sig, r) == 0:
            fase ^= tr(mul(mu(Ms[p]), peval(phi, r)))
    return fase, L


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--muestras", type=int, default=40)
    ap.add_argument("--seed", type=int, default=3); ap.add_argument("--n", type=int, default=70)
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "dqi_phase_model.log", mode="w")])
    rng = np.random.default_rng(a.seed)
    # sanidad de la base dual
    for b in range(DEG):
        for c in range(DEG):
            assert tr(mul(1 << c, BETA[b])) == (1 if b == c else 0)
    r = v.default_num_accepted_values(12)
    p = v.optimal_dqi_weights(4095, a.n // 2, 12, r) ** 2; p /= p.sum()
    mal = 0; omit = 0
    for it in range(a.muestras):
        k = int(rng.choice(len(p), p=p))
        pos = rng.choice(4095, size=k, replace=False); vals = [int(x) for x in rng.integers(1, 4096, size=k)]
        Ms = [int(x) for x in rng.integers(0, 4096, size=4095)]
        S = []
        for t in range(1, a.n + 1):
            s = 0
            for q, e in zip(pos, vals):
                s ^= mul(e, int(G.EXP[(int(q) * t) % 4095]))
            S.append(s)
        ref = fase_directa([int(x) for x in pos], vals, Ms)
        got, L = fase_pipeline(S, Ms, a.n)
        if got is None:
            omit += 1; log.info("k=%d: sigma' no invertible mod sigma (k=0 o degenerado)", k); continue
        if got != ref:
            mal += 1
        log.info("k=%2d L=%2d fase directa=%d pipeline=%d %s", k, L, ref, got, "OK" if got == ref else "DIFIERE")
    log.info("RESUMEN muestras=%d  difieren=%d  omitidas=%d", a.muestras, mal, omit)


if __name__ == "__main__":
    main()
