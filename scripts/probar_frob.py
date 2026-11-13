#!/usr/bin/env python3
"""Probar frob_sq aislado: cur = a^2 para a=0..4095."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import numpy as np
import kickmix as km
import dqi_bm_model as G

Bn = 4096
vals = np.arange(Bn)


def bits(v):
    return ((v[None, :] >> np.arange(12)[:, None]) & 1) == 1


def _matriz_frob():
    F = [G.mul(1 << j, 1 << j) for j in range(12)]
    aug = [(F[j] | (1 << (12 + j))) for j in range(12)]
    for col in range(12):
        piv = next(r for r in range(col, 12) if (aug[r] >> col) & 1)
        aug[col], aug[piv] = aug[piv], aug[col]
        for r in range(12):
            if r != col and ((aug[r] >> col) & 1):
                aug[r] ^= aug[col]
    Finv = [(aug[j] >> 12) & 0xFFF for j in range(12)]
    for j in range(12):
        acc = 0
        for k in range(12):
            if (Finv[j] >> k) & 1:
                acc ^= F[k]
        assert acc == (1 << j), f"Finv incorrecta en fila {j}"
    return F, Finv


FROB, FROB_INV = _matriz_frob()


def frob_sq(b, reg):
    tmp = b.alloc_qubits(12)
    for j in range(12):
        for k in range(12):
            if (FROB[j] >> k) & 1:
                b.cx(reg[j], tmp[k])
    for k in range(12):
        b.swap(reg[k], tmp[k])
    for j in range(12):
        for k in range(12):
            if (FROB_INV[j] >> k) & 1:
                b.cx(reg[j], tmp[k])
    b.free(tmp)


b = km.CircuitBuilder()
a = b.create_quantum_register(12, name='a')
w = b.create_quantum_register(12, name='w')
keep = b.create_quantum_register(12, name='keep')
cur = b.alloc_qubits(12)
for k in range(12):
    b.cx(a[k], cur[k])
frob_sq(b, cur)
for k in range(12):
    b.cx(cur[k], w[k])
for k in range(12):
    b.cx(w[k], keep[k])
c = b.finish_circuit()
sim = km.Simulator(batch_size=Bn, debug_print=False, counting_operations=True, seed=1)
sim.use_same_registers_as(c)
sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(vals))
sim.do(c)
out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
got = np.zeros(Bn, dtype=np.int64)
for k in range(12):
    got |= out[24 + k].astype(np.int64) << k
exp2 = np.array([G.mul(int(v), int(v)) for v in vals])
print(f"frob_sq a^2 correcto={int((got == exp2).sum())}/{Bn} fase={int(sim.read_phase_flipped_across_shots().sum())}", flush=True)
bad = np.where(got != exp2)[0][:5]
for v in bad:
    print(f"  a={v} got={got[v]} exp={exp2[v]}", flush=True)
