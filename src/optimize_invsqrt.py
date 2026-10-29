#!/usr/bin/env python3
"""
Búsqueda de precisión óptima para invsqrt usando el reference de kickmix.

Prueba diferentes configuraciones de DbHexaPrecision, ejecuta el modelo de punto
fijo para validar el error, y genera el circuito para verificar con el verificador
oficial.

La filosofía dbhexa se mantiene:
- Lookup uniforme: tabla de coeficientes indexada por bits de intervalo
- Banderas: selectores de intervalo como interruptores Clifford/Toffoli
- Qubits fijos dentro del presupuesto
"""

from __future__ import annotations

import itertools
import math
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import kickmix as km
import numpy as np

# Importar el reference para usar su build_nr_circuit y modelos
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifiers" / "invsqrt"))
from nr_reference_circuit import build_nr_circuit, Precision, relative_error, POLY_A, POLY_B

# Coeficientes para la tabla de coeficientes (mismo que el reference)
COEFF_TABLE_FUNC = None  # Se define abajo


def coefficient_table(prec: Precision) -> list[list[int]]:
    """Tabla de coeficientes por intervalo."""
    cases = [
        POLY_A,
        POLY_B,
        [a / (2**j * math.sqrt(2)) for j, a in enumerate(POLY_A)],
        [b / (2**j * math.sqrt(2)) for j, b in enumerate(POLY_B)],
    ]
    return [[round(c * 2**prec.coef_bits) for c in case] for case in cases]


@dataclass
class SearchResult:
    prec: Precision
    max_rel_error_log2: float
    toffoli_count: int
    num_qubits: int
    score: float
    status: str  # "PASS", "FAIL_MODEL", "FAIL_VERIFY", "ERROR"


BATCH_SIZE = 256  # Verifier default; num_shots must be a multiple of this.


def test_precision(prec: Precision, n_p: int = 10,
                   max_x_subset: int = 256, shots_per_x: int = 64) -> SearchResult:
    """Prueba una configuración de precisión completa.

    `max_x_subset` es el subconjunto de valores x [1..max_x_subset] a verificar
    (rápido para optimización). `shots_per_x` disparos por x. El producto
    `max_x_subset * shots_per_x` se redondea a múltiplo de BATCH_SIZE para el
    verificador oficial.
    """
    max_x_full = 3 * (2**n_p - 2)**2
    xs = np.arange(1, max_x_full + 1, dtype=np.int64)

    # 1. Verificar modelo de punto fijo sobre el dominio completo
    try:
        error = relative_error(n_p, prec, xs)
        max_err_log2 = math.log2(error.max())
        worst_x = int(error.argmax() + 1)
    except OverflowError as e:
        return SearchResult(
            prec=prec, max_rel_error_log2=float('inf'),
            toffoli_count=0, num_qubits=0, score=0.0,
            status="FAIL_MODEL"
        )

    if max_err_log2 > -24:
        # Error demasiado grande, no cumple tolerancia 2^-24
        return SearchResult(
            prec=prec, max_rel_error_log2=max_err_log2,
            toffoli_count=0, num_qubits=0, score=0.0,
            status="FAIL_MODEL"
        )

    # 2. Generar circuito y verificar con el verificador oficial (subconjunto rápido)
    max_x_verify = min(max_x_subset, max_x_full)
    # Redondear hacia abajo a múltiplo de BATCH_SIZE / shots_per_x para que
    # num_shots = max_x_verify * shots_per_x sea múltiplo de BATCH_SIZE.
    divisor = BATCH_SIZE // __import__('math').gcd(BATCH_SIZE, shots_per_x)
    max_x_verify = (max_x_verify // divisor) * divisor
    if max_x_verify < 1:
        max_x_verify = 1

    with tempfile.NamedTemporaryFile(suffix='.kmb', delete=False) as f:
        tmp_path = f.name

    try:
        circuit = build_nr_circuit(n_p, prec=prec)
        stats = circuit.operation_statistics()
        circuit.to_file(tmp_path, format='kmb')

        # Verificar con subconjunto rápido
        num_shots = max_x_verify * shots_per_x
        result = subprocess.run(
            [sys.executable, "verifiers/invsqrt/verify_submission_invsqrt.py", tmp_path,
             "--n-p", str(n_p), "--max-x", str(max_x_verify),
             "--shots-per-x", str(shots_per_x)],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            return SearchResult(
                prec=prec, max_rel_error_log2=max_err_log2,
                toffoli_count=int(stats.num_toffoli_like),
                num_qubits=int(circuit.num_qubits),
                score=float(circuit.num_qubits * stats.num_toffoli_like),
                status="FAIL_VERIFY"
            )

        # Calcular score aproximado (Q × C donde C ≈ Toffolis)
        score = float(circuit.num_qubits * stats.num_toffoli_like)
        return SearchResult(
            prec=prec, max_rel_error_log2=max_err_log2,
            toffoli_count=int(stats.num_toffoli_like),
            num_qubits=int(circuit.num_qubits),
            score=score,
            status="PASS"
        )
    except Exception as e:
        return SearchResult(
            prec=prec, max_rel_error_log2=float('nan'),
            toffoli_count=0, num_qubits=0, score=0.0,
            status="ERROR"
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def main():
    n_p = 10

    # Espacio de búsqueda: reducir bits gradualmente desde el baseline
    baseline = Precision(delta_bits=14, coef_bits=17, square_bits=28, product_bits=28, result_bits=29)

    print(f"Baseline: delta={baseline.delta_bits}, coef={baseline.coef_bits}, "
          f"square={baseline.square_bits}, product={baseline.product_bits}, result={baseline.result_bits}")

    # Primero verificar el baseline
    print("\n=== Verificando baseline ===")
    r = test_precision(baseline, n_p=n_p)
    print(f"  Status: {r.status}, Score: {r.score:.0f}, Q: {r.num_qubits}, T: {r.toffoli_count}, "
          f"Error: 2^{r.max_rel_error_log2:.2f}")

    # Búsqueda en espacio reducido
    print("\n=== Búsqueda de precisión reducida ===")
    results = []

    # Probar reducciones individuales y combinadas
    delta_range = range(10, 15)
    coef_range = range(13, 18)
    square_range = range(20, 29)
    product_range = range(20, 29)
    result_range = range(24, 30)

    # Para no explodir el combinatorio, probar primero reducciones individuales
    print("\n--- Reducciones individuales ---")
    for delta in delta_range:
        prec = Precision(delta_bits=delta, coef_bits=baseline.coef_bits,
                         square_bits=baseline.square_bits, product_bits=baseline.product_bits,
                         result_bits=baseline.result_bits)
        r = test_precision(prec, n_p=n_p)
        results.append(r)
        print(f"  delta={delta:2d}: {r.status:10s} score={r.score:>12.0f} Q={r.num_qubits:3d} "
              f"T={r.toffoli_count:5d} err=2^{r.max_rel_error_log2:7.2f}")

    for coef in coef_range:
        prec = Precision(delta_bits=baseline.delta_bits, coef_bits=coef,
                         square_bits=baseline.square_bits, product_bits=baseline.product_bits,
                         result_bits=baseline.result_bits)
        r = test_precision(prec, n_p=n_p)
        results.append(r)
        print(f"  coef={coef:2d}:  {r.status:10s} score={r.score:>12.0f} Q={r.num_qubits:3d} "
              f"T={r.toffoli_count:5d} err=2^{r.max_rel_error_log2:7.2f}")

    for square in square_range:
        prec = Precision(delta_bits=baseline.delta_bits, coef_bits=baseline.coef_bits,
                         square_bits=square, product_bits=baseline.product_bits,
                         result_bits=baseline.result_bits)
        r = test_precision(prec, n_p=n_p)
        results.append(r)
        print(f"  square={square:2d}: {r.status:10s} score={r.score:>12.0f} Q={r.num_qubits:3d} "
              f"T={r.toffoli_count:5d} err=2^{r.max_rel_error_log2:7.2f}")

    for product in product_range:
        prec = Precision(delta_bits=baseline.delta_bits, coef_bits=baseline.coef_bits,
                         square_bits=baseline.square_bits, product_bits=product,
                         result_bits=baseline.result_bits)
        r = test_precision(prec, n_p=n_p)
        results.append(r)
        print(f"  product={product:2d}: {r.status:10s} score={r.score:>12.0f} Q={r.num_qubits:3d} "
              f"T={r.toffoli_count:5d} err=2^{r.max_rel_error_log2:7.2f}")

    for result in result_range:
        prec = Precision(delta_bits=baseline.delta_bits, coef_bits=baseline.coef_bits,
                         square_bits=baseline.square_bits, product_bits=baseline.product_bits,
                         result_bits=result)
        r = test_precision(prec, n_p=n_p)
        results.append(r)
        print(f"  result={result:2d}: {r.status:10s} score={r.score:>12.0f} Q={r.num_qubits:3d} "
              f"T={r.toffoli_count:5d} err=2^{r.max_rel_error_log2:7.2f}")

    # Mejor resultado
    passing = [r for r in results if r.status == "PASS"]
    if passing:
        best = min(passing, key=lambda r: r.score)
        print(f"\n=== Mejor configuración ===")
        print(f"  delta={best.prec.delta_bits}, coef={best.prec.coef_bits}, "
              f"square={best.prec.square_bits}, product={best.prec.product_bits}, "
              f"result={best.prec.result_bits}")
        print(f"  Score: {best.score:.0f}, Q: {best.num_qubits}, T: {best.toffoli_count}, "
              f"Error: 2^{best.max_rel_error_log2:.2f}")

        # Generar circuito final con la mejor configuración
        best_prec = best.prec
        circuit = build_nr_circuit(n_p, prec=best_prec)
        stats = circuit.operation_statistics()
        output = f"benchmarks/fusion_energy/optimized/invsqrt_dbhexa_opt.kmb"
        circuit.to_file(output, format='kmb')
        print(f"\nCircuito guardado: {output}")
        print(f"  Qubits: {circuit.num_qubits}")
        print(f"  Toffolis: {stats.num_toffoli_like:,}")
    else:
        print("\n=== Ninguna configuración pasó la verificación ===")


if __name__ == "__main__":
    main()
