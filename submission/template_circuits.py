#!/usr/bin/env python3
"""
template_circuits.py — Genera circuitos placeholder (template) para cada benchmark.

Útil para crear la estructura inicial de archivos antes de optimizar.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path


def write_kmb_placeholder(path: Path, qubits: int, gates: list[str]) -> None:
    """Escribe un archivo .kmb placeholder (formato simplificado para ilustración)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# kickmix circuit placeholder\n"
        f"qubits: {qubits}\n"
        f"gates: {len(gates)}\n"
        + "\n".join(gates)
        + "\n",
        encoding="utf-8",
    )


def write_submission_npz(path: Path) -> None:
    """Escribe un submission.npz de ejemplo con claves requeridas."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        U=np.eye(4),
        W=np.eye(4),
        H2_I=np.zeros((4, 4)),
        H1_I=np.zeros((4, 4)),
        Hsym_lower=np.zeros((4, 4)),
        tree_edges=np.array([[0, 1], [1, 2], [2, 3]], dtype=np.int64),
    )


def generate_templates() -> None:
    """Genera archivos template para los tres benchmarks."""
    base = Path("submission/templates")

    # invsqrt template
    write_kmb_placeholder(
        base / "invsqrt_template.kmb",
        qubits=8,
        gates=["H 0", "T 1", "CNOT 0 1", "measure 1"],
    )

    # dqi template
    write_kmb_placeholder(
        base / "dqi_template.kmb",
        qubits=16,
        gates=["H 0", "T 2", "CNOT 0 2", "measure 2", "T 3"],
    )

    # dfthcsos templates (3 angle circuits)
    dfthcsos_dir = base / "dfthcsos"
    for k in range(3):
        write_kmb_placeholder(
            dfthcsos_dir / f"angle_k_{k}_template.kmb",
            qubits=64,
            gates=["H 0", "T 1", "CNOT 0 1", "measure 1"],
        )
    write_submission_npz(dfthcsos_dir / "submission_template.npz")

    print("Templates generados en submission/templates/")


if __name__ == "__main__":
    generate_templates()
