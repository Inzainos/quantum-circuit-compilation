#!/usr/bin/env python3
"""Medir andamios (qubits vivos) de init_gf2_mul y ValueInv3 por separado, y del bloque alpha tal cual.

Uso: python3 scripts/medir_andamios.py  (desde la raiz del repo)
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import kickmix as km
from dqi_tower_inv3 import ValueInv3

DEG = 12
gf = km.GF2Field(DEG)

def live(b):
    return int(b.num_allocated_qubits)

# --- (a) mul builtin solo ---
b = km.CircuitBuilder()
X = b.create_quantum_register(DEG, name='X'); D = b.create_quantum_register(DEG, name='D')
print(f"(a) mul: antes init_gf2_mul live={live(b)} (X+D=24)", flush=True)
P = b.init_gf2_mul(X, D, field=gf)
print(f"(a) mul: despues init_gf2_mul live={live(b)}  -> andamios mul = {live(b)-36}", flush=True)
print(f"(a) mul: toffoli-like init = {b.finish_circuit().operation_statistics().num_toffoli_like if False else '?'}", flush=True)
b2 = km.CircuitBuilder()
X2 = b2.create_quantum_register(DEG, name='X'); D2 = b2.create_quantum_register(DEG, name='D')
P2 = b2.init_gf2_mul(X2, D2, field=gf)
b2.del_gf2_mul(X2, D2, target=P2, field=gf); b2.free(P2)
c2 = b2.finish_circuit()
print(f"(a) mul: ida+vuelta toffoli-like={c2.operation_statistics().num_toffoli_like} Q={c2.num_qubits}", flush=True)

# --- (b) inv torre sola ---
b = km.CircuitBuilder()
A = b.create_quantum_register(DEG, name='A'); W = b.create_quantum_register(DEG, name='W')
print(f"(b) inv: antes ValueInv3 live={live(b)} (A+W=24)", flush=True)
inv = ValueInv3(b, A, W)
inv.forward()
print(f"(b) inv: despues forward live={live(b)}  -> andamios inv = {live(b)-24}", flush=True)
inv.undo()
print(f"(b) inv: despues undo live={live(b)}", flush=True)
c = b.finish_circuit()
print(f"(b) inv: ida+vuelta toffoli-like={c.operation_statistics().num_toffoli_like} Q={c.num_qubits}", flush=True)

# --- (c) bloque alpha tal cual (como forward_round) ---
b = km.CircuitBuilder()
X = b.create_quantum_register(DEG, name='X'); D = b.create_quantum_register(DEG, name='D')
alpha = b.create_quantum_register(DEG, name='alpha'); p = b.alloc_qubits(1)[0]
base = live(b)
print(f"(c) alpha: base (X+D+alpha+p) live={base}", flush=True)
P = b.init_gf2_mul(X, D, field=gf)
print(f"(c) alpha: tras init_gf2_mul live={live(b)} (+{live(b)-base})", flush=True)
Pinv = b.alloc_qubits(DEG)
print(f"(c) alpha: tras alloc Pinv live={live(b)} (+{live(b)-base})", flush=True)
inv = ValueInv3(b, P, Pinv)
inv.forward()
print(f"(c) alpha: tras inv forward live={live(b)} (+{live(b)-base})  -> andamios mul+inv = {live(b)-base-24}", flush=True)
# mux _alpha_sel
b.cx(P, alpha); b.cx(Pinv, P); b.ccx(p, P, alpha); b.cx(Pinv, P)
print(f"(c) alpha: tras _alpha_sel live={live(b)} (+{live(b)-base})", flush=True)
# undo
b.cx(P, alpha); b.cx(Pinv, P); b.ccx(p, P, alpha); b.cx(Pinv, P)
inv.undo()
b.free(Pinv)
b.del_gf2_mul(X, D, target=P, field=gf); b.free(P)
print(f"(c) alpha: tras undo live={live(b)} (base={base})", flush=True)
c = b.finish_circuit()
print(f"(c) alpha: ida+vuelta toffoli-like={c.operation_statistics().num_toffoli_like} Q={c.num_qubits}", flush=True)
