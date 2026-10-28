#!/usr/bin/env python3
"""
Optimizador de circuito dfthcsos (Benchmark III — Quantum Chemistry).

Optimiza los parametros de los circuitos ANGLE_k probando diferentes combinaciones
de brot (bits por palabra) y batch_size J contra el verifier oficial.

Metrica: score = lambda_eff * T_total * Q_total (menor es mejor)

Usa el sample submission como punto de partida y el verifier dfthcsos para evaluar.
"""

from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from qubit_temporal_manager import QubitTemporalManager, QubitRecord

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIER_DIR = PROJECT_ROOT / "verifiers"
# El sample submission de la competencia NO esta versionado; pasar --sample-dir.
SAMPLE_DFTHCSOS = PROJECT_ROOT / "sample_submission" / "dfthcsos"


def run_verifier(run_dir: Path, salt: str = "", timeout: int = 120) -> dict | None:
    """Ejecuta el verifier dfthcsos y devuelve el JSON parseado."""
    cmd = [
        sys.executable,
        str(VERIFIER_DIR / "dfthcsos" / "verify.py"),
        str(run_dir),
    ]
    if salt:
        cmd += ["--salt", salt]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(VERIFIER_DIR),
        )
        if result.returncode != 0:
            return {"status": "FAIL", "error": result.stderr.strip() or result.stdout.strip()}
        return json.loads(result.stdout)
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def evaluate_params(brot: int, batch_size: int, output_dir: Path,
                    sample_dir: Path = SAMPLE_DFTHCSOS) -> dict:
    """Genera circuitos angle_k con los parametros dados y los verifica."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generar circuitos angle_k usando el script de referencia del example
    ref_script = VERIFIER_DIR / "dfthcsos" / "example_submission" / "angle_k_reference_circuit.py"
    npz_path = sample_dir / "submission.npz"
    if not npz_path.is_file():
        return {"status": "ERROR", "error": f"No existe {npz_path}; usa --sample-dir"}

    cmd = [
        sys.executable,
        str(ref_script),
        str(npz_path),
        str(output_dir),
        "--brot", str(brot),
        "--batch-size", str(batch_size),
        "--format", "kmx",
        "--overwrite",
    ]

    try:
        gen = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(VERIFIER_DIR))
    except Exception as e:
        return {"status": "ERROR", "error": f"Generacion de circuitos: {e}"}
    if gen.returncode != 0:
        return {"status": "ERROR",
                "error": f"Generacion de circuitos fallo (rc={gen.returncode}): "
                         f"{(gen.stderr or gen.stdout).strip()[-500:]}"}

    # Copiar submission.npz al directorio de salida (el verifier lo necesita)
    import shutil
    shutil.copy2(npz_path, output_dir / "submission.npz")

    # Verificar
    return run_verifier(output_dir)


def optimize_dfthcsos(brot_values: list[int], batch_values: list[int], output_root: Path,
                      sample_dir: Path = SAMPLE_DFTHCSOS) -> None:
    """Busqueda de parametros optimos para dfthcsos."""
    results = []

    for brot, batch_size in itertools.product(brot_values, batch_values):
        run_dir = output_root / f"brot{brot}_J{batch_size}"
        print(f"\n=== Probando brot={brot}, J={batch_size} ===")

        result = evaluate_params(brot, batch_size, run_dir, sample_dir)
        status = result.get("status", "ERROR")

        entry = {"brot": brot, "batch_size": batch_size, "status": status, "dir": str(run_dir)}

        if status == "PASS":
            entry.update({
                "score": result.get("score"),
                "lambda_eff": result.get("lambda_eff"),
                "T_total": result.get("toffoli_count"),
                "num_qubits": result.get("num_qubits"),
                "Lambda": result.get("Lambda"),
                "E_gap": result.get("E_gap"),
            })
            print(f"  PASS: score={entry['score']:.0f}, Q={entry['num_qubits']}, T={entry['T_total']}")
        else:
            entry["error"] = result.get("error", "UNKNOWN")
            print(f"  {status}: {entry['error'][:100]}")

        results.append(entry)

    # Ordenar por score (mejor primero)
    passing = [r for r in results if r["status"] == "PASS"]
    passing.sort(key=lambda r: r.get("score", float("inf")))

    print("\n" + "=" * 60)
    print("RESUMEN DE OPTIMIZACION DFTHCSOS")
    print("=" * 60)
    if passing:
        best = passing[0]
        print(f"Mejor configuracion: brot={best['brot']}, J={best['batch_size']}")
        print(f"  Score: {best['score']:.0f}")
        print(f"  Qubits: {best['num_qubits']}")
        print(f"  Toffolis: {best['T_total']}")
        print(f"  lambda_eff: {best['lambda_eff']}")
        print(f"  Directorio: {best['dir']}")
    else:
        print("Ninguna configuracion paso el verificador.")

    # Guardar resultados
    results_file = output_root / "optimization_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResultados guardados en: {results_file}")


def main():
    parser = argparse.ArgumentParser(description="Optimizador dfthcsos")
    parser.add_argument("--brot", type=int, nargs="+", default=[8, 10, 12, 14, 16],
                        help="Valores de brot a probar")
    parser.add_argument("--batch", type=int, nargs="+", default=[4, 8, 12, 16],
                        help="Valores de batch_size J a probar")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "dfthcsos_optimization",
                        help="Directorio de salida")
    parser.add_argument("--sample-dir", type=Path, default=SAMPLE_DFTHCSOS,
                        help="Directorio con el submission.npz de ejemplo de la competencia")
    args = parser.parse_args()

    optimize_dfthcsos(args.brot, args.batch, args.output, args.sample_dir)


if __name__ == "__main__":
    main()
