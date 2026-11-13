#!/usr/bin/env python3
"""Norma cubica GF(2^12)/GF(2^4): N(a) = a * a^16 * a^256, contada por ANF (Mobius sobre 4096 valores).

La torre GF(2^4)^3 invertiria con a^-1 = (a^16 * a^256) * N(a)^-1.
  - Numerador P = a^16*a^256: 12 bits vivos mientras se invierte N (4 bits) por la torre interna.
  - Andamios >= 12 (P) + 4 (N) + 4 (interna) = 20 > 18 de la torre cuadratica.
  - La norma es una forma CUBICA (grado 3) en 12 variables: cada bit de salida tiene monomios
    de grado 3 (2 ANDs c/u) vs la norma cuadratica de la torre actual (grado 2, 1 AND c/u).
Se mide la ANF exacta de cada bit de salida de N(a) (en una base del subcuerpo GF(16)).
Uso: PYTHONPATH=~/workspace/qcc-data/kickmix:~/workspace/qcc-dqi/src python3 -u medir_norma_cubica.py
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import dqi_bm_model as G


def frob(a, k):
    """a^(2^k) en GF(2^12)."""
    r = a
    for _ in range(k):
        r = G.mul(r, r)
    return r


# 1) Norma N(a) = a * a^16 * a^256 para los 4096 valores
Nvals = np.zeros(4096, dtype=np.int64)
for a in range(4096):
    a16 = frob(a, 4)
    a256 = frob(a, 8)
    Nvals[a] = G.mul(G.mul(a, a16), a256)

# verificar que N(a) cae en el subcuerpo GF(16): x^16 == x
sub = [x for x in range(4096) if frob(x, 4) == x]
print(f"subcuerpo GF(16) tiene {len(sub)} elementos (esperado 16)", flush=True)
assert len(sub) == 16
assert set(Nvals.tolist()) <= set(sub), "la norma no cae en GF(16)"
# base del subcuerpo (4 elementos linealmente independientes sobre GF(2))
basis = []
for x in sub:
    if x == 0:
        continue
    # independencia: x no esta en el span de basis
    span = {0}
    for b in basis:
        span |= {s ^ b for s in list(span)}
    if x not in span:
        basis.append(x)
    if len(basis) == 4:
        break
print(f"base GF(16) (12 bits): {[hex(b) for b in basis]}", flush=True)


def coords(y):
    """Coordenadas de y (en GF(16)) en la base. Devuelve entero de 4 bits."""
    # resolver por fuerza bruta (16 combinaciones)
    for mask in range(16):
        acc = 0
        for j in range(4):
            if (mask >> j) & 1:
                acc ^= basis[j]
        if acc == y:
            return mask
    raise ValueError(y)


out_bits = np.zeros((4, 4096), dtype=np.int64)
for a in range(4096):
    m = coords(int(Nvals[a]))
    for j in range(4):
        out_bits[j, a] = (m >> j) & 1


def anf(f):
    """ANF (Mobius) de una funcion booleana de 12 vars dada por su tabla de verdad (4096 bits).
    Devuelve lista de mascaras de monomios presentes."""
    a = f.astype(np.int64).copy()
    n = 12
    for i in range(n):
        step = 1 << i
        for base in range(0, 4096, step * 2):
            for j in range(step):
                a[base + step + j] ^= a[base + j]
    return [m for m in range(4096) if a[m]]


print("=== ANF de cada bit de la norma cubica N(a) ===", flush=True)
tot_cubic = 0
tot_cuad = 0
tot_lin = 0
for j in range(4):
    mons = anf(out_bits[j])
    bydeg = {}
    for m in mons:
        d = bin(m).count('1')
        bydeg[d] = bydeg.get(d, 0) + 1
    tot_cubic += bydeg.get(3, 0)
    tot_cuad += bydeg.get(2, 0)
    tot_lin += bydeg.get(1, 0)
    print(f"  bit {j}: {len(mons)} monomios por grado {dict(sorted(bydeg.items()))}", flush=True)
print(f"TOTAL norma cubica: {tot_cubic} monomios cubicos (grado 3), {tot_cuad} cuadraticos, {tot_lin} lineales", flush=True)
print(f"  -> cada monomio cubico necesita 2 ANDs (si no se comparten): >= {2 * tot_cubic} ANDs solo la norma", flush=True)
print(f"  -> mas el numerador P (12 bits, producto ~63 T) y la inversion interna de N (4 bits).", flush=True)
print(f"  Andamios minimos: P(12) + N(4) + interna(4) = 20 > 18 (torre cuadratica).", flush=True)
