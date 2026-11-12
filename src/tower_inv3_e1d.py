#!/usr/bin/env python3
"""ValueInv3 E1d: liberar N' (3) TEMPRANO — tras computar r, antes de los productos en rc.

Analisis del pico (medido: Q=57 standalone, base 36 -> pico 21 = 18 andamios + 3 temps):
- Los productos y ^= r*N0, y ^= r*N1 necesitan N (6), rc (6), r (3) y 3 temps -> 18.
  N' (3) NO se usa en los productos (solo para deshacer r en el undo).
- E1 liberaba N tras inner.forward(): el pico (durante los productos) ya estaba en 21.
  E1c (liberar N antes de los productos) es INVALIDO: los productos usan N.
- E1d libera N' tras computar r (mulN_del con N, 0 T) y lo recomputa en el undo (6 T).
  Pico: 21 -> 18 (-3). T: 75 -> 81 (+6/inv). Live tras forward: 18 -> 15.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import kickmix as km
import dqi_tower_inv as T1
import dqi_tower_inv2 as T2
from dqi_tower_inv3 import Inner6, OPS_P2C, OPS_C2P, OPS_V2C, apply_inplace, _xor_in, _mulN_to, _phase_terms, W0, W1, _bits
from tower_inv3r import _recompute_inner_scaffolds  # noqa: F401  (no usado; E1d recomputa solo N')


def _recompute_Np(b, N):
    """Recomputa SOLO N' (3) desde N (coords internas). Costo: 6 T."""
    a0, a1 = N[0:3], N[3:6]
    Np = b.alloc_qubits(3)
    T2.mulN_init(b, T2.PLAN3, 3, a0, a1, Np)
    T2._lin(b, T2.SQ8, a0, Np)
    T2._lin(b, T2.NUSQ8, a1, Np)
    return Np


def _free_Np(b, N, Np):
    """Libera N' (0 T, MBU). N en coords internas (sus mitades son las entradas del producto)."""
    a0, a1 = N[0:3], N[3:6]
    T2._lin(b, T2.NUSQ8, a1, Np)
    T2._lin(b, T2.SQ8, a0, Np)
    T2.mulN_del(b, T2.PLAN3, 3, a0, a1, Np)
    b.free(Np)


class Inner6E1d(Inner6):
    """Inner6 que libera N' tras computar r, antes de los productos en y."""

    def forward(self):
        b, x, y = self.b, self.x, self.y
        a0, a1 = x[0:3], x[3:6]
        N = b.alloc_qubits(3)
        T2.mulN_init(b, T2.PLAN3, 3, a0, a1, N)
        T2._lin(b, T2.SQ8, a0, N)
        T2._lin(b, T2.NUSQ8, a1, N)
        r = b.alloc_qubits(3)
        T2.inv8_init(b, N, r)
        self.R = {'N': N, 'r': r}
        # --- E1d: liberar N' aqui (no se usa en los productos) ---
        _free_Np(b, x, N)
        self.R = {'r': r}
        _xor_in(b, a1, a0)
        T2.mulN_init(b, T2.PLAN3, 3, r, a0, y[0:3])
        T2.mulN_init(b, T2.PLAN3, 3, r, a1, y[3:6])
        _xor_in(b, a1, a0)


class TowerInv3E1d:
    """w ^= a^-1 ; a en coords de torre. Igual que TowerInv3 salvo liberar N' temprano."""

    def __init__(self, b, a, w):
        self.b, self.a, self.w = b, a, w
        self.R = {}

    def forward(self):
        b, a, w = self.b, self.a, self.w
        a0, a1 = a[0:6], a[6:12]
        N = b.alloc_qubits(6)
        T1.mul6_init(b, a0, a1, N)
        T2._lin(b, T1.SQ, a0, N)
        T2._lin(b, T1.NUSQ, a1, N)
        apply_inplace(b, OPS_P2C, N)
        rc = b.alloc_qubits(6)
        self.inner = Inner6E1d(b, N, rc)
        self.inner.forward()
        apply_inplace(b, OPS_C2P, rc)
        _xor_in(b, a1, a0)
        _mulN_to(b, None, 6, rc, a0, W0, w)
        _mulN_to(b, None, 6, rc, a1, W1, w)
        _xor_in(b, a1, a0)
        self.R = {'N': N, 'rc': rc}

    def undo(self):
        b, a, w, R = self.b, self.a, self.w, self.R
        a0, a1 = a[0:6], a[6:12]
        N, rc = R['N'], R['rc']
        _xor_in(b, a1, a0)
        m = b.alloc_bits(12)
        b.hmr(w, m)
        _phase_terms(b, 6, rc, a0, [(fx, fy, _bits(mk)) for fx, fy, mk in W0], m)
        _phase_terms(b, 6, rc, a1, [(fx, fy, _bits(mk)) for fx, fy, mk in W1], m)
        _xor_in(b, a1, a0)
        apply_inplace(b, OPS_C2P, rc, inverse=True)
        # recomputar SOLO N' (6 T; r sigue vivo) y correr inner.undo() estandar
        Np = _recompute_Np(b, N)
        inner2 = Inner6(b, N, rc)
        inner2.R = {'N': Np, 'r': self.inner.R['r']}
        inner2.undo()
        apply_inplace(b, OPS_P2C, N, inverse=True)
        T2._lin(b, T1.NUSQ, a1, N)
        T2._lin(b, T1.SQ, a0, N)
        T1.mul6_del(b, a0, a1, N)
        b.free(N)
        b.free(rc)
        self.R = {}


class ValueInv3E1d:
    """w ^= a^-1 con a en representacion de valor. Igual que ValueInv3 salvo E1d."""

    def __init__(self, b, a_val, w):
        self.b, self.a, self.w = b, a_val, w

    def forward(self):
        b = self.b
        apply_inplace(b, OPS_V2C, self.a)
        self.T = TowerInv3E1d(b, self.a, self.w)
        self.T.forward()
        apply_inplace(b, OPS_V2C, self.a, inverse=True)
        return self

    def undo(self):
        b = self.b
        apply_inplace(b, OPS_V2C, self.a)
        self.T.undo()
        apply_inplace(b, OPS_V2C, self.a, inverse=True)
