#!/usr/bin/env python3
"""
build_submission.py — Empaqueta el ZIP de envío para la competición.

Genera un archivo ZIP con la estructura requerida:
  invsqrt.kmb/.kmx
  dqi.kmb/.kmx
  dfthcsos/
    angle_k_0...angle_k_<n-1>.kmb/.kmx
    submission.npz
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


def _validate_angle_files(dfthcsos_dir: Path) -> list[Path]:
    """Valida que los archivos angle_k_* estén numerados desde 0 sin gaps."""
    angle_files = sorted(
        dfthcsos_dir.glob("angle_k_*"),
        key=lambda p: int(p.stem.split("_")[-1]),
    )
    if not angle_files:
        raise SystemExit("No se encontraron archivos angle_k_* en dfthcsos/")

    expected = 0
    for f in angle_files:
        k = int(f.stem.split("_")[-1])
        if k != expected:
            raise SystemExit(
                f"Gap en numeración angle_k: se esperaba angle_k_{expected}, "
                f"encontró angle_k_{k}"
            )
        expected += 1

    return angle_files


def _validate_npz(npz_path: Path) -> None:
    """Valida que submission.npz contenga las claves requeridas."""
    try:
        import numpy as np
    except ImportError:
        raise SystemExit("numpy no instalado; no se puede validar .npz")

    required = {"U", "W", "H2_I", "H1_I", "Hsym_lower", "tree_edges"}
    with np.load(npz_path) as data:
        missing = required - set(data.keys())
        if missing:
            raise SystemExit(
                f"submission.npz le faltan claves: {sorted(missing)}"
            )


def build_submission(
    invsqrt: Path,
    dqi: Path,
    dfthcsos_dir: Path,
    npz: Path,
    output: Path,
) -> None:
    """Construye el ZIP de envío."""
    # Validar entradas
    for p in (invsqrt, dqi, npz):
        if not p.is_file():
            raise SystemExit(f"Archivo no encontrado: {p}")
    if not dfthcsos_dir.is_dir():
        raise SystemExit(f"Directorio no encontrado: {dfthcsos_dir}")

    angle_files = _validate_angle_files(dfthcsos_dir)
    _validate_npz(npz)

    # Crear ZIP
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(invsqrt, arcname="invsqrt.kmb" if invsqrt.suffix == ".kmb" else "invsqrt.kmx")
        zf.write(dqi, arcname="dqi.kmb" if dqi.suffix == ".kmb" else "dqi.kmx")

        for af in angle_files:
            zf.write(af, arcname=f"dfthcsos/{af.name}")
        zf.write(npz, arcname="dfthcsos/submission.npz")

    print(f"ZIP de envío creado: {output}")
    print(f"  invsqrt: {invsqrt.name}")
    print(f"  dqi: {dqi.name}")
    print(f"  dfthcsos: {len(angle_files)} archivos angle_k_* + submission.npz")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construye el ZIP de envío para la competición de circuitos cuánticos."
    )
    parser.add_argument("--invsqrt", required=True, type=Path, help="Ruta a invsqrt.kmb/.kmx")
    parser.add_argument("--dqi", required=True, type=Path, help="Ruta a dqi.kmb/.kmx")
    parser.add_argument(
        "--dfthcsos-dir", required=True, type=Path,
        help="Directorio dfthcsos/ con archivos angle_k_* y submission.npz",
    )
    parser.add_argument("--npz", required=True, type=Path, help="Ruta a submission.npz")
    parser.add_argument("--output", required=True, type=Path, help="Ruta del ZIP de salida")
    args = parser.parse_args()

    build_submission(
        args.invsqrt, args.dqi, args.dfthcsos_dir, args.npz, args.output
    )


if __name__ == "__main__":
    main()
