#!/usr/bin/env python3
"""ValueInv3 con recompute de andamios (variantes E1/E2) — scratch redisenio_inversor.

Idea: N, N' y r solo se necesitan para DESHACER rc (en el undo). Durante los
productos finales (w ^= rc*s, w ^= rc*a1) no hacen falta. Se liberan (0 T, MBU)
tras inner.forward() y se recomputan en el undo antes de inner.undo().

Modos:
  'none' : identico a ValueInv3 (18 andamios, 75 T).
  'N'    : (E1) libera N (6) tras inner.forward(); lo recomputa en el undo.
           Andamios en productos: rc(6)+N'(3)+r(3) = 12. Extra T: mul6_init = 18/inv.
  'all'  : (E2) libera N, N' y r tras inner.forward(); los recomputa en el undo.
           Andamios en productos: rc(6) = 6. Extra T: mul6_init(18)+mulN_init(6)+inv8_init(3) = 27/inv.
"""
from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import kickmix as km
import dqi_tower_inv as T1
import dqi_tower_inv2 as T2
from dqi_tower_inv3 import Inner6, OPS_P2C, OPS_C2P, OPS_V2C, apply_inplace, _xor_in, _mulN_to, _phase_terms, W0, W1, _bits


def _free_inner_scaffolds(b, N, Np, r):
    """Libera r y N' (0 T, MBU). N en coords internas. Orden: r, luego N'."""
    a0, a1 = N[0:3], N[3:6]
    T2.inv8_del(b, Np, r)
    b.free(r)
    T2._lin(b, T2.NUSQ8, a1, Np)
    T2._lin(b, T2.SQ8, a0, Np)
    T2.mulN_del(b, T2.PLAN3, 3, a0, a1, Np)
    b.free(Np)


def _recompute_inner_scaffolds(b, N):
    """Recomputa N' (3) y r (3) desde N (coords internas). Devuelve (Np, r). Costo: 6+3=9 T."""
    a0, a1 = N[0:3], N[3:6]
    Np = b.alloc_qubits(3)
    T2.mulN_init(b, T2.PLAN3, 3, a0, a1, Np)
    T2._lin(b, T2.SQ8, a0, Np)
    T2._lin(b, T2.NUSQ8, a1, Np)
    r = b.alloc_qubits(3)
    T2.inv8_init(b, Np, r)
    return Np, r


def _free_N(b, a, N):
    """Libera N (0 T). a en coords de torre; N en coords internas."""
    a0, a1 = a[0:6], a[6:12]
    apply_inplace(b, OPS_P2C, N, inverse=True)
    T2._lin(b, T1.NUSQ, a1, N)
    T2._lin(b, T1.SQ, a0, N)
    T1.mul6_del(b, a0, a1, N)
    b.free(N)


def _recompute_N(b, a):
    """Recomputa N (6) desde a (coords de torre). Devuelve N en coords internas. Costo: 18 T."""
    a0, a1 = a[0:6], a[6:12]
    N = b.alloc_qubits(6)
    T1.mul6_init(b, a0, a1, N)
    T2._lin(b, T1.SQ, a0, N)
    T2._lin(b, T1.NUSQ, a1, N)
    apply_inplace(b, OPS_P2C, N)
    return N


class TowerInv3R:
    """w ^= a^-1 ; a en coords de torre. Igual que TowerInv3 salvo el recompute de andamios."""

    def __init__(self, b, a, w, recompute='none'):
        assert recompute in ('none', 'N', 'all')
        self.b, self.a, self.w, self.recompute = b, a, w, recompute
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
        self.inner = Inner6(b, N, rc)
        self.inner.forward()
        # --- liberar andamios que solo hacen falta en el undo ---
        if self.recompute == 'all':
            _free_inner_scaffolds(b, N, self.inner.R['N'], self.inner.R['r'])
            _free_N(b, a, N)
            self.R = {'rc': rc}
            self._N_freed = True
            self._inner_freed = True
        elif self.recompute == 'N':
            _free_N(b, a, N)
            self.R = {'rc': rc}
            self._N_freed = True
            self._inner_freed = False
        else:
            self.R = {'N': N, 'rc': rc}
            self._N_freed = False
            self._inner_freed = False
        apply_inplace(b, OPS_C2P, rc)
        _xor_in(b, a1, a0)
        _mulN_to(b, None, 6, rc, a0, W0, w)
        _mulN_to(b, None, 6, rc, a1, W1, w)
        _xor_in(b, a1, a0)

    def undo(self):
        b, a, w, R = self.b, self.a, self.w, self.R
        a0, a1 = a[0:6], a[6:12]
        rc = R['rc']
        _xor_in(b, a1, a0)
        m = b.alloc_bits(12)
        b.hmr(w, m)
        _phase_terms(b, 6, rc, a0, [(fx, fy, _bits(mk)) for fx, fy, mk in W0], m)
        _phase_terms(b, 6, rc, a1, [(fx, fy, _bits(mk)) for fx, fy, mk in W1], m)
        _xor_in(b, a1, a0)
        apply_inplace(b, OPS_C2P, rc, inverse=True)
        # --- recomputar lo liberado antes de inner.undo() ---
        if self.recompute == 'all':
            N = _recompute_N(b, a)
            Np, r = _recompute_inner_scaffolds(b, N)
            inner2 = Inner6(b, N, rc)
            inner2.R = {'N': Np, 'r': r}
            inner2.undo()
            # inner.undo() libera Np y r; queda liberar N
            apply_inplace(b, OPS_P2C, N, inverse=True)
            T2._lin(b, T1.NUSQ, a1, N)
            T2._lin(b, T1.SQ, a0, N)
            T1.mul6_del(b, a0, a1, N)
            b.free(N)
        elif self.recompute == 'N':
            N = _recompute_N(b, a)
            inner2 = Inner6(b, N, rc)
            inner2.R = self.inner.R  # N', r intactos
            inner2.undo()
            apply_inplace(b, OPS_P2C, N, inverse=True)
            T2._lin(b, T1.NUSQ, a1, N)
            T2._lin(b, T1.SQ, a0, N)
            T1.mul6_del(b, a0, a1, N)
            b.free(N)
        else:
            N = R['N']
            self.inner.undo()
            apply_inplace(b, OPS_P2C, N, inverse=True)
            T2._lin(b, T1.NUSQ, a1, N)
            T2._lin(b, T1.SQ, a0, N)
            T1.mul6_del(b, a0, a1, N)
            b.free(N)
        b.free(rc)
        self.R = {}


class ValueInv3R:
    """w ^= a^-1 con a en representacion de valor. Igual que ValueInv3 salvo recompute."""

    def __init__(self, b, a_val, w, recompute='none'):
        self.b, self.a, self.w, self.recompute = b, a_val, w, recompute

    def forward(self):
        b = self.b
        apply_inplace(b, OPS_V2C, self.a)
        self.T = TowerInv3R(b, self.a, self.w, recompute=self.recompute)
        self.T.forward()
        apply_inplace(b, OPS_V2C, self.a, inverse=True)
        return self

    def undo(self):
        b = self.b
        apply_inplace(b, OPS_V2C, self.a)
        self.T.undo()
        apply_inplace(b, OPS_V2C, self.a, inverse=True)
