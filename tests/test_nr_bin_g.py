"""NR dbhexa con s binario + redondeo de guarda (src/invsqrt_nr_bin_g.py).

No corre el verificador oficial (eso es `verify_submission_invsqrt.py`
sobre el .kmb). El PASS oficial esta en
~/workspace/qcc-data/invsqrt-sweep/nr_bin_g_verify.json:
score 2,040,366.64, Q=255, T=7,761, peor error 0.6004 de tolerancia.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifiers" / "invsqrt"))

from invsqrt_nr_bin_g import DBHEXA_PRECISION, build_nr_bin_g_circuit  # noqa: E402


def test_nr_bin_g_qubits_toffolis():
    circ = build_nr_bin_g_circuit(10, prec=DBHEXA_PRECISION)
    assert circ.num_qubits == 255
    assert int(circ.operation_statistics().num_toffoli_like) == 7761
