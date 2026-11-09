#!/usr/bin/env python3
"""Cuantificacion del costo del Schur (Stieltjes) y distribucion real de L.
1. Cuenta multiplicaciones/divisiones de campo del Schur vs BM (n=70, varios L).
2. Distribucion de L con el muestreador del verificador DQI (pesos optimos, 2000 tiros).
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_stieltjes import syndrome, schur_stieltjes, convergents, trim

# --- 1. Conteo de operaciones de campo ---
class Counter:
    def __init__(self):
        self.mul = 0; self.inv = 0; self.add = 0
CNT = Counter()
_orig_mul = G.mul; _orig_inv = G.inv
def mul_c(a, b):
    CNT.mul += 1
    return _orig_mul(a, b)
def inv_c(a):
    CNT.inv += 1
    return _orig_inv(a)
G.mul = mul_c; G.inv = inv_c

def series_reciprocal_cnt(g, n):
    """Reciproco contando ops (copia de schur_explora_stieltjes.series_reciprocal)."""
    if g[0] == 0:
        return None
    inv0 = G.inv(g[0])
    h = [0]*n
    h[0] = inv0
    for k in range(1, n):
        acc = 0
        for i in range(1, k+1):
            if i < len(g):
                acc ^= G.mul(g[i], h[k-i])
        h[k] = G.mul(inv0, acc)  # en GF(2), -x = x
    return h

def schur_cnt(S, nsteps, n):
    f = list(S) + [0]*max(0, n-len(S))
    gammas = []
    for k in range(nsteps):
        gamma = f[0]
        gammas.append(gamma)
        g = f[1:] + [0]
        if g[0] == 0:
            break
        f = series_reciprocal_cnt(g, n)
        if f is None:
            break
    return gammas

print("=== Conteo de operaciones de campo (Schur Stieltjes vs BM) ===")
rng = np.random.default_rng(7)
for (k_err, n) in [(2, 6), (5, 20), (8, 70), (20, 70), (35, 70)]:
    S = syndrome(rng, k_err, n)
    stats = {"mac": 0, "div": 0, "cambios": 0}
    # BM count
    CNT.mul = 0; CNT.inv = 0
    sig_bm, L_bm = G.bm(S, stats)
    bm_mul, bm_inv = CNT.mul, CNT.inv
    # Schur count (2L+1 pasos, cada uno un reciproco de longitud ~n)
    CNT.mul = 0; CNT.inv = 0
    gammas = schur_cnt(S, 2*L_bm+2, n)
    sch_mul, sch_inv = CNT.mul, CNT.inv
    print(f"k={k_err} n={n} L={L_bm}: BM mul={bm_mul} inv={bm_inv} | "
          f"Schur mul={sch_mul} inv={sch_inv} | ratio_mul={sch_mul/max(bm_mul,1):.1f}x")
    print(f"    Schur a 42 ANDs/mul -> ~{sch_mul*42:,} Toffoli (solo multiplicaciones)")
    print(f"    BM    a 42 ANDs/mul -> ~{bm_mul*42:,} Toffoli (solo multiplicaciones)")

# --- 2. Distribucion real de L ---
print("\n=== Distribucion de L (muestreador del verificador, 2000 tiros) ===")
from verify_submission_dqi import optimal_dqi_weights, default_num_accepted_values, sample_shots, ProblemSpecDQI, FieldTables
import kickmix as km
r = default_num_accepted_values(12)
spec = ProblemSpecDQI.benchmark_instance(m=4095, n=70, degree=12, r=r, num_shots=2000)
field = km.GF2Field(12, 0x1053)
tables = FieldTables(field)
weight_probs = optimal_dqi_weights(spec.m, spec.max_errors, spec.degree, spec.r) ** 2
rng2 = np.random.default_rng(20261108)
N = 2000
syndromes, mbuc, phases = sample_shots(spec, tables, rng2, N, weight_probs)
# L por tiro (BM)
from collections import Counter as C
Lc = C()
for i in range(N):
    S = [int(v) for v in syndromes[i]]
    stats = {"mac": 0, "div": 0, "cambios": 0}
    sig, L = G.bm(S, stats)
    Lc[L] += 1
print("L : count (frac)")
for L in sorted(Lc):
    print(f"  L={L:2d} : {Lc[L]:4d}  ({Lc[L]/N:.4f})")
print(f"P(L=35) = {Lc.get(35,0)/N:.4f}   P(L>=34) = {(Lc.get(34,0)+Lc.get(35,0))/N:.4f}")
print(f"P(L<=34) = {sum(v for k,v in Lc.items() if k<=34)/N:.4f}")
