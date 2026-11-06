"""Tests for the surrogate model CLI (tools/qcc_model.py + qcc_model.json).

No circuits, no verifier runs: predictions are checked against the
measured anchors stored in the model file. Run with:
  pytest tests/test_qcc_model.py -q
"""
import argparse
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import qcc_model  # noqa: E402


@pytest.fixture(scope="module")
def model():
    return qcc_model.load_model()


def test_model_file_structure(model):
    assert model["version"] == 1
    assert set(model) >= {"invsqrt", "dfthcsos", "dqi"}
    assert "ESTIMATES ONLY" in model["note"]


def test_invsqrt_predict_at_verified_point(model, capsys):
    a = argparse.Namespace(deg=2, j=8, wc=28, dd=13, sesgo=1)
    out = qcc_model.predict_invsqrt(model, a)
    assert abs(out["Q"] - 139) <= 2
    assert abs(out["T"] - 2561) <= 200
    assert out["pass_estimate"] is True
    # Score estimate within 10% of the measured 390,005.
    assert abs(out["score_estimate"] - 390005.06) / 390005.06 < 0.10
    assert "ESTIMATE" in capsys.readouterr().out


def test_dfthcsos_predict_at_candidate_point(model):
    a = argparse.Namespace(rho=1e-4, eps=0.017, epochs=100, solver="lbfgs",
                           brot=12, J=8)
    out = qcc_model.predict_dfthcsos(model, a)
    # Measured (verified, encoded): lambda_eff 49.016, error_2 19.37 mHa,
    # E_gap 3.92049, score 3,336,160,975.
    assert abs(out["lambda_eff_enc"] - 49.016) < 1.0
    assert abs(out["error_2_enc_mHa"] - 19.37) < 1.0
    assert abs(out["E_gap_enc"] - 3.92049) < 0.1
    assert abs(out["score_estimate"] - 3336160975) / 3336160975 < 0.02


def test_dfthcsos_adam_is_refused(model):
    a = argparse.Namespace(rho=1e-4, eps=0.01, epochs=20, solver="adam",
                           brot=12, J=8)
    with pytest.raises(SystemExit) as exc:
        qcc_model.predict_dfthcsos(model, a)
    assert exc.value.code == 2


def test_dqi_formula_reproduces_recorded_scores(model):
    # The verifier's own formula must reproduce the recorded v10 score
    # (2,560 shots). BM v1 anchors have no recorded score: their stored
    # score IS the formula output, so only v10 is a real check.
    checked = 0
    for anchor in model["dqi"]["anchors"]:
        if anchor.get("recorded_score") is None:
            continue
        out = qcc_model.predict_dqi(
            model, argparse.Namespace(T=anchor["T"], Q=anchor["Q"],
                                      shots=anchor["shots"],
                                      failures=anchor["failures"]))
        assert abs(out["score_estimate"] - anchor["recorded_score"]) / anchor["recorded_score"] < 1e-6
        checked += 1
    assert checked == 1  # exactly one anchor carries a recorded score


def test_dqi_bm_v1_score_estimate(model):
    out = qcc_model.predict_dqi(
        model, argparse.Namespace(T=784172, Q=2016, shots=102400, failures=0))
    # Measured estimate: R~1.19 -> ~3.80e12.
    assert abs(out["score_estimate"] - 3.797e12) / 3.797e12 < 0.01
    assert abs(out["R"] - 1.1913) < 0.005
