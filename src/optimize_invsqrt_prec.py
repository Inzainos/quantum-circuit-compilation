#!/usr/bin/env python3
"""
Búsqueda de precisión óptima para reducir Q (qubits) en invsqrt.

Prueba reducir square_bits, product_bits, result_bits para ver cuánto
se puede bajar Q manteniendo el PASS del verificador oficial.
"""

from __future__ import annotations

import sys
from pathlib import Path

import kickmix as km
import numpy as np

sys_path = Path(__file__).resolve().parent.parent / "verifiers" / "invsqrt"
sys.path.insert(0, str(sys_path))
from nr_reference_circuit import build_nr_circuit, Precision


def test_precision(prec, n_p=10, max_x=1000, shots_per_x=64):
    """Prueba una configuración de precisión y devuelve métricas."""
    max_x_full = 3 * (2**n_p - 2)**2
    xs = np.arange(1, max_x_full + 1, dtype=np.int64)

    # Verificar modelo de punto fijo
    try:
        from nr_reference_circuit import relative_error
        error = relative_error(n_p, prec, xs)
        max_err_log2 = float(np.log2(error.max()))
    except OverflowError:
        return None

    if max_err_log2 > -24:
        return None  # No cumple tolerancia

    # Generar circuito y verificar
    try:
        circuit = build_nr_circuit(n_p, prec=prec)
        stats = circuit.operation_statistics()
        score = circuit.num_qubits * stats.num_toffoli_like
        return {
            'prec': prec,
            'qubits': circuit.num_qubits,
            'toffolis': stats.num_toffoli_like,
            'score': score,
            'error_log2': max_err_log2,
        }
    except Exception:
        return None


def main():
    n_p = 10
    baseline = Precision(delta_bits=14, coef_bits=17, square_bits=28, product_bits=28, result_bits=29)

    print("=== Búsqueda de precisión óptima para reducir Q ===\n")

    # Primero verificar baseline
    r = test_precision(baseline, n_p)
    print(f"Baseline: Q={r['qubits']}, T={r['toffolis']}, Score={r['score']:.0f}, Error=2^{r['error_log2']:.2f}")

    best = r

    # Probar reducciones en square_bits
    print("\n--- Reducir square_bits ---")
    for sb in range(20, 28):
        prec = Precision(delta_bits=14, coef_bits=17, square_bits=sb, product_bits=27, result_bits=28)
        r = test_precision(prec, n_p)
        if r:
            print(f"  square_bits={sb}: Q={r['qubits']}, T={r['toffolis']}, Score={r['score']:.0f}, Error=2^{r['error_log2']:.2f}")
            if r['score'] < best['score']:
                best = r
        else:
            print(f"  square_bits={sb}: FAIL (overflow o error demasiado grande)")

    print("\n--- Reducir product_bits ---")
    for pb in range(20, 28):
        prec = Precision(delta_bits=14, coef_bits=17, square_bits=27, product_bits=pb, result_bits=28)
        r = test_precision(prec, n_p)
        if r:
            print(f"  product_bits={pb}: Q={r['qubits']}, T={r['toffolis']}, Score={r['score']:.0f}, Error=2^{r['error_log2']:.2f}")
            if r['score'] < best['score']:
                best = r
        else:
            print(f"  product_bits={pb}: FAIL")

    print("\n--- Reducir result_bits ---")
    for rb in range(24, 29):
        prec = Precision(delta_bits=14, coef_bits=17, square_bits=27, product_bits=27, result_bits=rb)
        r = test_precision(prec, n_p)
        if r:
            print(f"  result_bits={rb}: Q={r['qubits']}, T={r['toffolis']}, Score={r['score']:.0f}, Error=2^{r['error_log2']:.2f}")
            if r['score'] < best['score']:
                best = r
        else:
            print(f"  result_bits={rb}: FAIL")

    print("\n=== Mejor configuración ===")
    print(f"  delta_bits={best['prec'].delta_bits}, coef_bits={best['prec'].coef_bits}")
    print(f"  square_bits={best['prec'].square_bits}, product_bits={best['prec'].product_bits}")
    print(f"  result_bits={best['prec'].result_bits}")
    print(f"  Q={best['qubits']}, T={best['toffolis']}, Score={best['score']:.0f}, Error=2^{best['error_log2']:.2f}")

    # Generar circuito final con la mejor configuración
    best_prec = best['prec']
    circuit = build_nr_circuit(n_p, prec=best_prec)
    output = 'benchmarks/fusion_energy/optimized/invsqrt_dbhexa_opt2.kmb'
    circuit.to_file(output, format='kmb')
    print(f"\nCircuito guardado: {output}")
    print(f"  Qubits: {circuit.num_qubits}")
    print(f"  Toffolis: {circuit.operation_statistics().num_toffoli_like:,}")


if __name__ == "__main__":
    main()
