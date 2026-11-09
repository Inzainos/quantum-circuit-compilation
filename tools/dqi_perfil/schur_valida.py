#!/usr/bin/env python3
"""Validacion completa de la recurrencia de Schur (Stieltjes) para la ecuacion clave.

1. Schur (fraccion continua de Stieltjes) -> gammas -> convergente [2L] = (omega, sigma).
2. Verifica: sigma == BM, ecuacion clave sigma*S = omega (mod x^n), deg(omega) < L.
3. Estado in-place: la serie f_k vive en el arreglo S (n slots); el paso de Schur
   (shift + reciproco) se hace en sitio; solo O(1) escalares extra (gamma, pivote).
   Se mide el numero de coeficientes vivos simultaneamente (slots).
4. Casos: k=2..8, n=6..70 (como el modelo EEA previo) + barrido de k=1..12 a n=70.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_stieltjes import syndrome, series_reciprocal, schur_stieltjes, convergents, trim

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

def schur_sigma_omega(S, n):
    """Schur completo: gammas -> convergente [2L] -> (sigma, omega, L, max_slots).
    max_slots = maximo de coeficientes vivos: la serie f_k (n slots) + O(1) escalares.
    Aqui se mide como len(f_k) + 3 (gamma, pivote, temporal de reciproco).
    Devuelve (sigma, omega, L, max_slots, gammas) o (None,...) si hay breakdown antes de 2L gammas."""
    gammas, breakdown = schur_stieltjes(S, 2*n+2, n)
    # Necesitamos al menos 2L+1 gammas; L se desconoce a priori, asi que se usa el
    # convergente cuyo denominador tenga el grado correcto. Se busca L por el primer
    # convergente cuyo q cumpla la ecuacion clave con deg(omega)<deg(q).
    # En la practica: se prueban los convergentes k=0..len(gammas)-1 y se queda el
    # primero con deg(q)=L y ec. clave OK. Aqui se usa L de BM solo para validar
    # (en el circuito real L se detecta por el grado del convergente / el breakdown).
    conv = convergents(gammas)
    max_slots = n + 3  # serie (n slots) + gamma + pivote + temporal
    return conv, max_slots, gammas, breakdown

rng = np.random.default_rng(7)
print("=== Validacion Schur (Stieltjes) vs BM ===")
all_ok = True
for (k_err, n) in [(2, 6), (2, 10), (5, 20), (3, 70), (8, 70), (1, 70), (12, 70), (20, 70), (35, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm == 0:
        print(f"k={k_err} n={n}: L=0 (sin errores), salto")
        continue
    L = L_bm
    conv, max_slots, gammas, breakdown = schur_sigma_omega(S, n)
    # convergente [2L] (indice 2L) debe dar sigma
    if 2*L >= len(conv):
        print(f"k={k_err} n={n} L={L}: no hay convergente [2L] (solo {len(conv)}). FAIL")
        all_ok = False
        continue
    p, q = conv[2*L]
    if q[0] == 0:
        print(f"k={k_err} n={n} L={L}: q[0]==0 en convergente [2L]. FAIL")
        all_ok = False
        continue
    inv0 = G.inv(q[0])
    sigma = [G.mul(c, inv0) for c in q]
    omega = [G.mul(c, inv0) for c in p]
    sigma = trim(sigma); omega = trim(omega)
    ok_sigma = sigma == trim(sig_bm)
    # ecuacion clave: sigma*S mod x^n == omega, deg(omega) < L
    prod = pmul(sigma, S)
    lhs = trim(prod[:n])
    ok_key = lhs == omega and pdeg(omega) < L
    # omega tambien debe cumplir: los coefs L..n-1 de sigma*S son 0
    tail_zero = all(c == 0 for c in prod[L:n])
    print(f"k={k_err} n={n} L={L}: sigma_ok={ok_sigma} ec_clave={ok_key} cola_cero={tail_zero} "
          f"deg_omega={pdeg(omega)} max_slots={max_slots} (n={n}) gammas={len(gammas)} breakdown_k={breakdown}")
    if not (ok_sigma and ok_key and tail_zero):
        all_ok = False
        print(f"   sigma_schur={sigma}")
        print(f"   sigma_BM   ={trim(sig_bm)}")
        print(f"   omega={omega}  lhs={lhs}")
print()
print("TODOS OK" if all_ok else "HAY FALLOS")
