"""Tests for the structured JSON-lines logger (tools/qcc_log.py).

Stdlib only — no kickmix, no circuits. Run with:
  pytest tests/test_qcc_log.py -q
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import qcc_log  # noqa: E402


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    path = tmp_path / "qcc.jsonl"
    monkeypatch.setenv("QCC_LOG_PATH", str(path))
    monkeypatch.delenv("QCC_LOG_OFF", raising=False)
    return path


def test_emit_writes_one_valid_json_line(log_path):
    qcc_log.emit("test_script", "build", "ok",
                 inputs={"deg": 2}, outputs={"Q": 139, "T": 2561})
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    ev = json.loads(lines[0])
    assert ev["script"] == "test_script"
    assert ev["phase"] == "build"
    assert ev["status"] == "ok"
    assert ev["inputs"] == {"deg": 2}
    assert ev["outputs"] == {"Q": 139, "T": 2561}
    assert ev["ts"] and ev["run_id"]
    assert "duration_s" not in ev  # only set when provided


def test_phase_context_manager_emits_start_and_ok(log_path):
    with qcc_log.phase("test_script", "verify", inputs={"shots": 1}):
        pass
    events = [json.loads(line) for line in
              log_path.read_text(encoding="utf-8").strip().splitlines()]
    assert [e["status"] for e in events] == ["start", "ok"]
    assert events[1]["duration_s"] >= 0.0
    assert events[0]["run_id"] == events[1]["run_id"]


def test_phase_context_manager_emits_error_and_reraises(log_path):
    with pytest.raises(ValueError, match="boom"):
        with qcc_log.phase("test_script", "build"):
            raise ValueError("boom")
    events = [json.loads(line) for line in
              log_path.read_text(encoding="utf-8").strip().splitlines()]
    assert [e["status"] for e in events] == ["start", "error"]
    assert events[1]["error"] == "boom"


def test_log_off_disables_file_logging(tmp_path, monkeypatch):
    path = tmp_path / "qcc.jsonl"
    monkeypatch.setenv("QCC_LOG_PATH", str(path))
    monkeypatch.setenv("QCC_LOG_OFF", "1")
    qcc_log.emit("test_script", "build", "ok")
    assert not path.exists()


def test_emit_never_breaks_on_unwritable_path(monkeypatch):
    monkeypatch.setenv("QCC_LOG_PATH", "/nonexistent-dir-xyz/qcc.jsonl")
    # Must not raise: logging must never break the pipeline.
    qcc_log.emit("test_script", "build", "ok", outputs={"Q": 1})
