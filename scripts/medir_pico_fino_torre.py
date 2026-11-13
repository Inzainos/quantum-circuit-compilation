#!/usr/bin/env python3
"""Medir el vivo real dentro del forward de la torre (ValueInv3) en la ronda 69 a n=70, paso a paso.

Reproduce el forward de la torre manualmente con logging de live despues de cada alloc,
para ver el pico real (incluidos transitorios tx/ty/t) y de donde salen los 7 de sobrecarga del pool
(Q=1937 vs pico_ronda=1930).

Uso: python3 scripts/medir_pico_fino_torre.py  (desde la raiz del repo)
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import kickmix as km
from dqi_bm_stage_v1 import BMStageV1, DEG
from bm_fused import BMStageFused
import dqi_tower_inv3 as T3
import dqi_tower_inv as T1
import dqi_tower_inv2 as T2

n = 70
b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(n)]
bm = BMStageFused(b, gf, S, 36, n)
for r in range(n - 1):
    bm.forward_round(r)
base = int(b.num_allocated_qubits)
print(f"base ronda 69 = {base} (esperado 1793)", flush=True)
mx = base
def snap(tag):
    global mx
    v = int(b.num_allocated_qubits); mx = max(mx, v)
    print(f"  {tag:44s} live={v} (+{v-base})", flush=True)

r = n - 1
p = b.alloc_qubits(1)[0]
D = b.alloc_qubits(DEG); X = b.alloc_qubits(DEG); alpha = b.alloc_qubits(DEG)
snap("alloc p,D,X,alpha")
bm._disc(r, D); snap("tras _disc")
bm._flags(D, p, inverse=False); snap("tras _flags")
b.cx(bm.sigma[0], X); snap("tras cx sigma0->X")
# --- alpha fusionado, torre manual ---
P = b.init_gf2_mul(X, D, field=bm.f)
snap("tras init_gf2_mul (P)")
# ValueInv3.forward manual sobre (P -> alpha)
a, w = P, alpha
T3.apply_inplace(b, T3.OPS_V2C, a); snap("tras V2C en P")
# TowerInv3.forward manual
a0, a1 = a[0:6], a[6:12]
N = b.alloc_qubits(6); snap("tras alloc N(6) torre")
T1.mul6_init(b, a0, a1, N); snap("tras mul6_init (N=norma)")
T2._lin(b, T1.SQ, a0, N); T2._lin(b, T1.NUSQ, a1, N)
T3.apply_inplace(b, T3.OPS_P2C, N); snap("tras P2C en N")
rc = b.alloc_qubits(6); snap("tras alloc rc(6)")
# Inner6.forward manual
x6, y6 = N, rc
ia0, ia1 = x6[0:3], x6[3:6]
N2 = b.alloc_qubits(3); snap("tras alloc N'(3) inner")
T2.mulN_init(b, T2.PLAN3, 3, ia0, ia1, N2); snap("tras mulN_init inner (N')")
T2._lin(b, T2.SQ8, ia0, N2); T2._lin(b, T2.NUSQ8, ia1, N2)
r3 = b.alloc_qubits(3); snap("tras alloc r(3) inner")
T2.inv8_init(b, N2, r3); snap("tras inv8_init (r=N'^-1)")
T3._xor_in(b, ia1, ia0)
T2.mulN_init(b, T2.PLAN3, 3, r3, ia0, y6[0:3]); snap("tras mulN r*a0 -> rc[0:3]")
T2.mulN_init(b, T2.PLAN3, 3, r3, ia1, y6[3:6]); snap("tras mulN r*a1 -> rc[3:6]")
T3._xor_in(b, ia1, ia0)
T3.apply_inplace(b, T3.OPS_C2P, rc); snap("tras C2P en rc")
T3._xor_in(b, a1, a0)
T3._mulN_to(b, None, 6, rc, a0, T3.W0, w); snap("tras _mulN_to rc*a0 -> alpha (W0)")
T3._mulN_to(b, None, 6, rc, a1, T3.W1, w); snap("tras _mulN_to rc*a1 -> alpha (W1)")
T3._xor_in(b, a1, a0)
T3.apply_inplace(b, T3.OPS_V2C, a, inverse=True); snap("tras V2C inverso en P (fin forward torre)")
bm._alpha_sel_fused(P, alpha, p); snap("tras CSWAP(!p) select")
print(f"PICO MAXIMO en la ronda 69 (incluye transitorios) = {mx}", flush=True)
print(f"Q del circuito si se terminara aqui seria >= {mx} (el pool suma sobrecarga)", flush=True)
