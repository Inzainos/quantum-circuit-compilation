"""Pruebas de validacion de submission/build_submission.py (requiere numpy)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "submission"))

import build_submission as bs  # noqa: E402

KEYS = ("U", "W", "H2_I", "H1_I", "Hsym_lower", "tree_edges")


def _touch(path: Path, data: bytes = b"x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_gap_in_angle_numbering_is_rejected(tmp_path):
    for k in (0, 1, 3):
        _touch(tmp_path / f"angle_k_{k}.kmb")
    with pytest.raises(SystemExit, match="Gap"):
        bs._validate_angle_files(tmp_path)


def test_sequential_angle_files_are_accepted_in_numeric_order(tmp_path):
    for k in range(11):
        _touch(tmp_path / f"angle_k_{k}.kmb")
    files = bs._validate_angle_files(tmp_path)
    assert [int(f.stem.split("_")[-1]) for f in files] == list(range(11))


def test_npz_missing_key_is_rejected(tmp_path):
    npz = tmp_path / "submission.npz"
    np.savez(npz, **{k: np.zeros(1) for k in KEYS[:-1]})
    with pytest.raises(SystemExit, match="tree_edges"):
        bs._validate_npz(npz)


def test_build_creates_expected_layout(tmp_path):
    inv = _touch(tmp_path / "a.kmb")
    dqi = _touch(tmp_path / "b.kmb")
    d = tmp_path / "dfthcsos"
    for k in range(3):
        _touch(d / f"angle_k_{k}.kmb")
    npz = tmp_path / "submission.npz"
    np.savez(npz, **{k: np.zeros(1) for k in KEYS})
    out = tmp_path / "out" / "s.zip"
    bs.build_submission(inv, dqi, d, npz, out)
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert names == {
        "invsqrt.kmb", "dqi.kmb",
        "dfthcsos/angle_k_0.kmb", "dfthcsos/angle_k_1.kmb", "dfthcsos/angle_k_2.kmb",
        "dfthcsos/submission.npz",
    }
