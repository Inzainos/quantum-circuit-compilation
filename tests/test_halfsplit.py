"""invsqrt mitad-dividida: error del modelo < tolerancia y costos del circuito (dominio completo)."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "verifiers" / "invsqrt"))

import invsqrt_halfsplit as hs  # noqa: E402
from invsqrt_piecewise import PWSpec  # noqa: E402

SPEC = PWSpec(deg=2, j=8, wc=28, dd=13)


def test_error_bajo_tolerancia_en_dominio_completo():
    xs = np.arange(1, 3 * (2 ** 10 - 2) ** 2 + 1, dtype=np.int64)
    err = hs.error_relativo(SPEC, xs, hs.modelo(SPEC, xs)).max() / 2.0 ** -24
    assert err < 1.0


def test_costos_del_circuito():
    c = hs.PipelineMitad(SPEC).construye()
    assert (c.num_qubits, int(c.operation_statistics().num_toffoli_like)) == (183, 2867)


def test_tabla_tiene_potencia_de_dos_entradas():
    assert len(hs.TablaLookupMitad(SPEC).table) == 1 << (SPEC.j + 1)
