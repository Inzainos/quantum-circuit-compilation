"""Consistencia de las metricas versionadas (no requiere kickmix)."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "benchmarks" / "fusion_energy" / "baseline" / "metrics.json"
OPTIMIZED = ROOT / "benchmarks" / "fusion_energy" / "optimized" / "metrics.json"


def _score(path: Path) -> tuple[float, dict]:
    d = json.loads(path.read_text())
    m = d["metrics"]
    return m["num_qubits"] * m["toffoli_equivalent"], d


def test_baseline_score_is_q_times_c():
    expected, d = _score(BASELINE)
    assert math.isclose(d["metrics"]["score_q_times_c"], expected, rel_tol=1e-9)


def test_optimized_score_uses_same_definition_as_baseline():
    expected, d = _score(OPTIMIZED)
    assert math.isclose(d["metrics"]["score_q_times_c"], expected, rel_tol=1e-9)
    assert math.isclose(d["baseline_comparison"]["dbhexa_score"], expected, rel_tol=1e-9)


def test_reduction_percent_matches_scores():
    base, _ = _score(BASELINE)
    opt, d = _score(OPTIMIZED)
    reported = d["baseline_comparison"]["score_reduction_percent"]
    assert reported > 0, "una reduccion de score es una mejora (signo positivo)"
    assert math.isclose(reported, (base - opt) / base * 100, abs_tol=0.01)


def test_optimized_is_below_tolerance_on_full_domain():
    d = json.loads(OPTIMIZED.read_text())
    full = d["full_domain_verification"]
    assert full["status"] == "PASS"
    assert full["worst_error_over_tolerance"] < 1.0


def test_precision_matches_documented_circuit():
    d = json.loads(OPTIMIZED.read_text())
    p = d["dbhexa_precision"]
    assert (p["square_bits"], p["product_bits"], p["result_bits"]) == (27, 27, 27)
    assert d["metrics"]["num_qubits"] == 254
    assert d["metrics"]["toffoli_count"] == 7405
