"""NR dbhexa con s binario (src/invsqrt_nr_bin.py): Q/T y error del modelo.

No corre el verificador oficial (eso es `verify_submission_invsqrt.py`
sobre el .kmb); el error aqui es el del modelo de punto fijo, que es exacto
para esta aritmetica.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifiers" / "invsqrt"))

from invsqrt_nr_bin import DBHEXA_PRECISION, build_nr_bin_circuit  # noqa: E402
from nr_reference_circuit import relative_error  # noqa: E402


def test_nr_bin_qubits_toffolis():
    circ = build_nr_bin_circuit(10, prec=DBHEXA_PRECISION)
    assert circ.num_qubits == 248
    assert int(circ.operation_statistics().num_toffoli_like) == 7099


def test_nr_bin_model_error_below_tolerance():
    xs = np.arange(1, 3 * (2**10 - 2) ** 2 + 1, dtype=np.int64)
    err = relative_error(10, DBHEXA_PRECISION, xs)
    assert float(err.max()) < 1.0
