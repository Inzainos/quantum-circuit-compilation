#!/usr/bin/env python3
"""Medir ValueInv3 baseline vs ValueInv3E1d: andamios vivos, pico (Q), T, correctitud.

Base: a(12) + w(12) + keep(12) = 36. Pico = Q - 36 (el pool no tiene overhead aqui).
Uso: python3 -u scripts/medir_torre_e1d.py  (desde la raiz del repo)
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
from tower_inv3_e1d import ValueInv3E1d

Bn = 4096
vals = np.arange(Bn)
exp = np.array([0 if v == 0 else G.inv(int(v)) for v in vals])


def bits(v):
    return ((v[None, :] >> np.arange(12)[:, None]) & 1) == 1


def medir(nombre, cls, **kw):
    t0 = time.time()
    b = km.CircuitBuilder()
    a = b.create_quantum_register(12, name='a')
    w = b.create_quantum_register(12, name='w')
    keep = b.create_quantum_register(12, name='keep')
    live_antes = int(b.num_allocated_qubits)
    inv = cls(b, a, w, **kw)
    inv.forward()
    live_fwd = int(b.num_allocated_qubits)
    for k in range(12):
        b.cx(w[k], keep[k])
    inv.undo()
    c = b.finish_circuit()
    t = int(c.operation_statistics().num_toffoli_like)
    q = int(c.num_qubits)
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
    print(f"[{nombre}] base={live_antes} live_tras_fwd={live_fwd} (andamios tras fwd={live_fwd - 24}) "
          f"Q={q} (pico sobre base={q - live_antes}) T(fwd+undo)={t} | "
          f"correcto={int((kept == exp).sum())}/{Bn} basura={int(sucio.sum())} fase_volteada={fase} "
          f"({time.time()-t0:.1f}s)", flush=True)
    return q, t


print("=== ValueInv3 baseline vs E1d (liberar N' antes de los productos) ===", flush=True)
qb, tb = medir('baseline', ValueInv3)
qe, te = medir('E1d', ValueInv3E1d)
print(f"=== Resumen ===\n  baseline: Q={qb} (pico={qb - 36}) T={tb}\n  E1d:      Q={qe} (pico={qe - 36}) T={te}", flush=True)
print(f"  E1d: pico {qb - 36}->{qe - 36} ({qe - qb:+d}), T {tb}->{te} ({te - tb:+d})", flush=True)
