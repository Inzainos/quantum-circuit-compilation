"""Regresion de la arquitectura por tramos (requiere kickmix y numpy)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

pw = pytest.importorskip("invsqrt_piecewise")

SPEC = pw.PWSpec(deg=2, j=7, wc=28, dd=13)
TOL = 2.0 ** -24


def _xs_subconjunto() -> np.ndarray:
    max_x = 3 * (2**10 - 2) ** 2
    return np.unique(np.concatenate([
        np.arange(1, 4097), np.arange(max_x - 4096, max_x + 1), np.arange(1, max_x + 1, 997)]))


def test_coeficientes_alternan_signo_y_widths_decrecen():
    b, w = pw.tabla_coeficientes(SPEC)
    assert len(b) == SPEC.deg + 1
    assert w[0] > w[1] > w[2]
    assert all(v == 0 for v in (b[0][A] for A in range(1 << SPEC.j)))  # tramos inalcanzables


def test_modelo_dentro_de_tolerancia_en_subconjunto():
    xs = _xs_subconjunto()
    y1 = pw.modelo(SPEC, xs)
    assert (pw.error_relativo(SPEC, xs, y1) / TOL).max() < 1.0


def test_dd_excesivo_es_rechazado():
    with pytest.raises(ValueError):
        pw.modelo(pw.PWSpec(deg=2, j=7, wc=28, dd=99), np.arange(1, 10))


def test_circuito_tiene_el_costo_medido():
    q, t = pw.metricas_circuito(pw.construye(SPEC))
    assert (q, t) == (185, 2993)
