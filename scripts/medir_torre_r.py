#!/usr/bin/env python3
"""Medir ValueInv3 baseline vs ValueInv3R (E1='N', E2='all'): andamios vivos, T, correctitud.

Uso: python3 -u scripts/medir_torre_r.py  (desde la raiz del repo)
"""
import sys, time
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_tower_inv3 import ValueInv3
from tower_inv3r import ValueInv3R

Bn = 4096
vals = np.arange(Bn)
exp = np.array([0 if v == 0 else G.inv(int(v)) for v in vals])


def bits(v):
    return ((v[None, :] >> np.arange(12)[:, None]) & 1) == 1


def medir(modo, cls):
    t0 = time.time()
    b = km.CircuitBuilder()
    a = b.create_quantum_register(12, name='a')
    w = b.create_quantum_register(12, name='w')
    keep = b.create_quantum_register(12, name='keep')
    live_antes = int(b.num_allocated_qubits)
    if modo == 'none':
        inv = cls(b, a, w)
    else:
        inv = cls(b, a, w, recompute=modo)
    inv.forward()
    live_fwd = int(b.num_allocated_qubits)
    for k in range(12):
        b.cx(w[k], keep[k])
    live_keep = int(b.num_allocated_qubits)
    inv.undo()
    live_undo = int(b.num_allocated_qubits)
    c = b.finish_circuit()
    t = int(c.operation_statistics().num_toffoli_like)
    q = int(c.num_qubits)
    # simulador: 4096 tiros, a = 0..4095
    sim = km.Simulator(batch_size=Bn, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(c)
    sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(vals))
    sim.do(c)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
    kept = np.zeros(Bn, dtype=np.int64)
    for k in range(12):
        kept |= out[24 + k].astype(np.int64) << k
    sucio = out[12:24].any(axis=0) | out[36:].any(axis=0)
    fase = int(sim.read_phase_flipped_across_shots().sum())
    print(f"[{modo}] live_antes={live_antes} live_fwd={live_fwd} andamios={live_fwd - 24} "
          f"live_keep={live_keep} live_undo={live_undo} T(fwd+undo)={t} Q={q} | "
          f"correcto={int((kept == exp).sum())}/{Bn} basura={int(sucio.sum())} fase_volteada={fase} "
          f"({time.time()-t0:.1f}s)", flush=True)
    return live_fwd - 24, t


print("=== ValueInv3 / ValueInv3R (a 12 + w 12 = 24 base) ===", flush=True)
res = {}
res['none'] = medir('none', ValueInv3)
res['N'] = medir('N', ValueInv3R)
res['all'] = medir('all', ValueInv3R)
print("=== Resumen ===", flush=True)
for k, (sc, t) in res.items():
    print(f"  {k}: andamios={sc} T={t}", flush=True)
print(f"  E1 (N): andamios 18->{res['N'][0]} (-{18-res['N'][0]}), T 75->{res['N'][1]} (+{res['N'][1]-75})", flush=True)
print(f"  E2 (all): andamios 18->{res['all'][0]} (-{18-res['all'][0]}), T 75->{res['all'][1]} (+{res['all'][1]-75})", flush=True)
