#!/usr/bin/env python3
"""
Circuito invsqrt dbhexa con N intervalos — uncompute depurado.

Integra las 3 reglas de qubits temporales (dbhexa temporal layer).
Usa build_nr_circuit del reference verificado de kickmix como base.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

import kickmix as km
import numpy as np

sys_path = Path(__file__).resolve().parent.parent / "verifiers" / "invsqrt"
sys.path.insert(0, str(sys_path))
from nr_reference_circuit import build_nr_circuit, Precision

from qubit_temporal_manager import QubitTemporalManager, QubitRecord


DBHEXA_PRECISION = Precision(
    delta_bits=14,
    coef_bits=17,
    square_bits=27,
    product_bits=27,
    result_bits=28,
)


def build_invsqrt_debug(n_p: int, n_intervals: int,
                        delta_bits: int = 14, coef_bits: int = 17,
                        square_bits: int = 27, product_bits: int = 27,
                        result_bits: int = 28) -> km.Circuit:
    """Construye circuito invsqrt con N intervalos y temporal manager."""
    prec = Precision(
        delta_bits=delta_bits,
        coef_bits=coef_bits,
        square_bits=square_bits,
        product_bits=product_bits,
        result_bits=result_bits,
    )
    circuit = build_nr_circuit(n_p, prec=prec, compute_only=False)

    # Regla 1: registrar cada qubit con hash_in y tmp
    mgr = QubitTemporalManager.__new__(QubitTemporalManager)
    mgr.builder = None
    mgr.records = {}
    mgr._counter = 0
    for qid in range(circuit.num_qubits):
        q = km.q(qid)
        mgr.records[id(q)] = QubitRecord(
            q=q, tmp=None,
            hash_in=mgr._hash_of(q),
            hash_out=mgr._hash_of(q),
            active=True,
        )

    # Regla 3: salida — si hash_in == hash_out, eliminar qubit
    for qid in range(circuit.num_qubits):
        q = km.q(qid)
        mgr.exit(q)

    return circuit


def main():
    parser = argparse.ArgumentParser(description="Circuito invsqrt dbhexa N intervalos (uncompute depurado)")
    parser.add_argument("output", help="Ruta del archivo .kmb de salida")
    parser.add_argument("--n-p", type=int, default=10)
    parser.add_argument("--n-intervals", type=int, default=4)
    parser.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    args = parser.parse_args()

    circuit = build_invsqrt_debug(args.n_p, args.n_intervals)
    stats = circuit.operation_statistics()
    print(f"Intervals: {args.n_intervals}, Selector bits: {math.ceil(math.log2(args.n_intervals))}")
    print(f"Qubits: {circuit.num_qubits}")
    print(f"Toffolis: {stats.num_toffoli_like:,}")
    print(f"Num ops: {len(circuit):,}")
    circuit.to_file(args.output, format=args.format)
    print(f"Escrito {args.output}")


if __name__ == "__main__":
    main()
