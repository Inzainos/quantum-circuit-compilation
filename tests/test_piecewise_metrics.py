"""Consistencia de las metricas de la arquitectura por tramos (no requiere kickmix)."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PW = ROOT / "benchmarks" / "fusion_energy" / "piecewise" / "metrics.json"
BASE = ROOT / "benchmarks" / "fusion_energy" / "baseline" / "metrics.json"
PREV = ROOT / "benchmarks" / "fusion_energy" / "optimized" / "metrics.json"


def test_score_es_q_por_toffoli_equivalent():
    m = json.loads(PW.read_text())["metrics"]
    assert math.isclose(m["score_q_times_c"], m["num_qubits"] * m["toffoli_equivalent"], rel_tol=1e-12)


def test_porcentajes_coinciden_con_los_scores():
    d = json.loads(PW.read_text())
    s = d["metrics"]["score_q_times_c"]
    base = json.loads(BASE.read_text())["metrics"]["score_q_times_c"]
    prev = json.loads(PREV.read_text())["metrics"]["score_q_times_c"]
    assert math.isclose(d["comparison"]["baseline_score"], base, rel_tol=1e-12)
    assert math.isclose(d["comparison"]["previous_best_score"], prev, rel_tol=1e-12)
    assert math.isclose(d["comparison"]["score_reduction_vs_baseline_percent"], (base - s) / base * 100, abs_tol=0.01)
    assert math.isclose(d["comparison"]["score_reduction_vs_previous_best_percent"], (prev - s) / prev * 100, abs_tol=0.01)


def test_la_verificacion_completa_no_se_declara_sin_correrla():
    d = json.loads(PW.read_text())
    pendiente = [v for v in d["verification"] if v["status"] == "PENDIENTE"]
    assert "PENDIENTE" in d["status"] or not pendiente
