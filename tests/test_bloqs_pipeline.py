"""Fases-clase: mismo circuito que invsqrt_piecewise, captura de ErrorAncho e insercion de fases pesadas."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import invsqrt_bloqs as bq  # noqa: E402
import invsqrt_piecewise as pw  # noqa: E402

SPEC = pw.PWSpec(deg=2, j=7, wc=28, dd=13)


def test_mismo_circuito_que_piecewise():
    a = bq.Pipeline(SPEC).construye()
    b = pw.construye(SPEC)
    assert (a.num_qubits, int(a.operation_statistics().num_toffoli_like)) == (185, 2993)
    assert (a.num_qubits, a.operation_statistics().num_toffoli_like) == (b.num_qubits, b.operation_statistics().num_toffoli_like)


def test_error_ancho_capturado_y_reajustado():
    p = bq.Pipeline(SPEC)
    bits = p.anchos()
    bits["scratch"] = 3
    with pytest.raises(bq.ErrorAncho):
        p.adapta(bits)
    p.anchos = lambda: {**bits}  # el orquestador reajusta el registro pedido
    assert p.adapta_o_reajusta()["scratch"] == max(p.w)


def test_insercion_de_fase_pesada_se_ejecuta_en_ambos_sentidos():
    p = bq.Pipeline(SPEC)
    visto = []
    p.inserta(bq.Pesada("nada", lambda b, R, inv: visto.append(inv)), despues_de="horner")
    p.construye()
    assert visto == [False, True]
