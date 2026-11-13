#!/usr/bin/env python3
"""Medir Q y T del bloque alpha fusionado (F1b) vs original, y el pico fino a n=70.

Uso: python3 scripts/medir_fusion.py [n]  (desde la raiz del repo)
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

# --- (1) bloque alpha fusionado solo (misma base que medir_andamios.py (c)) ---
b = km.CircuitBuilder()
X = b.create_quantum_register(DEG, name='X'); D = b.create_quantum_register(DEG, name='D')
alpha = b.create_quantum_register(DEG, name='alpha'); p = b.alloc_qubits(1)[0]
base = int(b.num_allocated_qubits)
print(f"F1b solo: base (X+D+alpha+p) live={base}", flush=True)
P = b.init_gf2_mul(X, D, field=km.GF2Field(DEG))
print(f"F1b solo: tras init_gf2_mul live={int(b.num_allocated_qubits)} (+{int(b.num_allocated_qubits)-base})", flush=True)
from dqi_tower_inv3 import ValueInv3
inv = ValueInv3(b, P, alpha); inv.forward()
print(f"F1b solo: tras inv forward (en alpha) live={int(b.num_allocated_qubits)} (+{int(b.num_allocated_qubits)-base})", flush=True)
b.x(p); b.cswap(p, P, alpha); b.x(p)
print(f"F1b solo: tras CSWAP(!p) live={int(b.num_allocated_qubits)} (+{int(b.num_allocated_qubits)-base})", flush=True)
b.x(p); b.cswap(p, P, alpha); b.x(p)
inv.undo()
b.del_gf2_mul(X, D, target=P, field=km.GF2Field(DEG)); b.free(P)
print(f"F1b solo: tras undo live={int(b.num_allocated_qubits)} (base={base})", flush=True)
c = b.finish_circuit()
print(f"F1b solo: ida+vuelta toffoli-like={c.operation_statistics().num_toffoli_like} Q={c.num_qubits} (original: 162 / 82)", flush=True)

# --- (2) pico fino a n=70 con la etapa fusionada ---
n = int(sys.argv[1]) if len(sys.argv) > 1 else 70
b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(n)]
bm = BMStageFused(b, gf, S, 36, n)
base0 = int(b.num_allocated_qubits)
print(f"n={n} fusionada: live inicial = {base0}", flush=True)
for r in range(n - 1):
    bm.forward_round(r)
print(f"tras {n-1} rondas normales live={int(b.num_allocated_qubits)}", flush=True)
# ultima ronda con logging fino
base = int(b.num_allocated_qubits)
mx = base
def snap(tag):
    global mx
    v = int(b.num_allocated_qubits); mx = max(mx, v)
    print(f"  {tag:38s} live={v} (+{v-base})", flush=True)
print(f"--- ronda {n-1} fusionada (base live={base}) ---", flush=True)
p = b.alloc_qubits(1)[0]
D = b.alloc_qubits(DEG); X = b.alloc_qubits(DEG); alpha = b.alloc_qubits(DEG)
snap("alloc p,D,X,alpha")
bm._disc(n-1, D); snap("tras _disc")
bm._flags(D, p, inverse=False); snap("tras _flags")
b.cx(bm.sigma[0], X); snap("tras cx sigma0->X")
with b.mark('bm_alpha'):
    P = b.init_gf2_mul(X, D, field=bm.f)
    scaf = bm._inv_init(P, alpha)
    bm._alpha_sel_fused(P, alpha, p)
snap("tras alpha fusionado (P,alpha)")
with b.mark('bm_swap'):
    for i in range(bm.bu(n-1) + 1):
        b.cswap(p, bm.sigma[i], bm.tau[i])
snap("tras swap")
with b.mark('bm_update'):
    for i in range(bm.bu(n-1) + 1):
        bm._mul(alpha, bm.tau[i], bm.sigma[i])
snap("tras update")
bm._dupd(p, inverse=False); snap("tras _dupd")
with b.mark('bm_alpha'):
    bm._alpha_sel_fused(P, alpha, p)
    bm._inv_del(scaf, P, alpha)
    b.del_gf2_mul(X, D, target=P, field=bm.f); b.free(P)
snap("tras alpha undo (P liberado)")
bm._xmux(X, p); snap("tras _xmux")
bm._dclear(D, p); snap("tras _dclear")
b.free(alpha); b.free(X); b.free(D)
snap("tras free alpha,X,D (fin ronda)")
bm.tau = [bm.tau[-1]] + bm.tau[:-1]
bm.flags.append(p)
c = b.finish_circuit()
print(f"RESULTADO n={n} FUSIONADA: pico_ronda={mx} Q_circuito={c.num_qubits} T={c.operation_statistics().num_toffoli_like}", flush=True)
print(f"  live final={int(b.num_allocated_qubits)} (base {base} + 1 flag = {base+1})", flush=True)
print(f"  BASELINE n=70: pico_ronda=1942 Q_circuito=1949 T=185034", flush=True)
