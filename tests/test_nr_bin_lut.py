"""NR dbhexa con s binario y semilla por tabla lineal (src/invsqrt_nr_bin_lut.py).

No corre el verificador oficial (eso es `verify_submission_invsqrt.py`
sobre el .kmb). El PASS oficial esta en
~/workspace/qcc-data/invsqrt-sweep/nr_bin_lut_verify.json:
score 1,426,020.28, Q=216, T=6,356, peor error 0.5295 de tolerancia.
A 27/27/27 el circuito FALLA (peor error 1.1711 en x=1040463); la precision
verificada es 28/28/28.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifiers" / "invsqrt"))

from invsqrt_nr_bin_lut import DBHEXA_PRECISION, build_nr_bin_lut_circuit, lut_seed_error  # noqa: E402


def test_nr_bin_lut_qubits_toffolis():
    circ = build_nr_bin_lut_circuit(10, prec=DBHEXA_PRECISION)
    assert circ.num_qubits == 216
    assert int(circ.operation_statistics().num_toffoli_like) == 6356


def test_nr_bin_lut_seed_error_below_tolerance():
    assert lut_seed_error() < 1.0
