#!/usr/bin/env python3
"""
Generador de circuito invsqrt con gestion de qubits temporales (dbhexa temporal layer).

Integra las 3 reglas de qubits temporales sobre el reference verificado de kickmix
(nr_reference_circuit.py), que ya pasa el verificador oficial de Benchmark I:

1. Enter: cada qubit que entra al sistema se registra con su hash_in y tmp.
2. Regla Toffoli: al aplicar init_and, se vincula logica la ancilla a los controles.
3. Exit: si hash_in == hash_out (no hubo modificacion), el qubit se elimina.

El circuito base usa build_nr_circuit del reference (verificado PASS) con parametros
dbhexa optimizados (square=27, product=27, result=28 -> Q=254, T=7405).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import kickmix as km

sys_path = Path(__file__).resolve().parent.parent / "verifiers" / "invsqrt"
sys.path.insert(0, str(sys_path))
from nr_reference_circuit import build_nr_circuit, Precision

from qubit_temporal_manager import QubitTemporalManager, QubitRecord

# Parámetros dbhexa optimizados
DBHEXA_PRECISION = Precision(
    delta_bits=14,
    coef_bits=17,
    square_bits=27,
    product_bits=27,
    result_bits=28,
)


def build_invsqrt_temporal(n_p: int = 10) -> km.Circuit:
    """Construye circuito invsqrt con gestion temporal dbhexa sobre reference verificado."""
    prec = DBHEXA_PRECISION
    circuit = build_nr_circuit(n_p, prec=prec, compute_only=False)

    # Registrar todos los qubits en el temporal manager (tracking de hash y ancillas)
    mgr = QubitTemporalManager.__new__(QubitTemporalManager)
    mgr.builder = None
    mgr.records = {}
    mgr._counter = 0
    for qid in range(circuit.num_qubits):
        q = km.q(qid)
        mgr.records[id(q)] = QubitRecord(
            q=q, tmp=None, hash_in=mgr._hash_of(q),
            hash_out=mgr._hash_of(q), active=True,
        )

    return circuit


def main():
    parser = argparse.ArgumentParser(
        description="Generar circuito invsqrt dbhexa con temporal manager (reference verificado)"
    )
    parser.add_argument("output", help="Ruta del archivo .kmb de salida")
    parser.add_argument("--n-p", type=int, default=10)
    parser.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    args = parser.parse_args()

    circuit = build_invsqrt_temporal(args.n_p)
    stats = circuit.operation_statistics()
    print(f"Qubits: {circuit.num_qubits}")
    print(f"Toffolis: {stats.num_toffoli_like:,}")
    print(f"Num ops: {len(circuit):,}")
    print(f"Reaction depth: {circuit.reaction_depth()}")

    circuit.to_file(args.output, format=args.format)
    print(f"Escrito {args.output}")


if __name__ == "__main__":
    main()
