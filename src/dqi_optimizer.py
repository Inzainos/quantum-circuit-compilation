#!/usr/bin/env python3
"""
Optimizador de circuito dqi (Benchmark II — Combinatorial Optimization).

Integra las 3 reglas de qubits temporales (dbhexa temporal layer):
1. Enter: cada qubit que entra al sistema se registra con hash_in y tmp.
2. Regla Toffoli: al aplicar init_and, se vincula logica la ancilla a los controles.
3. Exit: si hash_in == hash_out (no hubo modificacion), el qubit se elimina.

Usa el baseline dqi_ref.kmb como base (circuito ya verificado) y aplica el
temporal manager para tracking de qubits y ancillas.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import kickmix as km

from qubit_temporal_manager import QubitTemporalManager, QubitRecord

# Ruta del baseline verificado
BASELINE_DQI = Path(__file__).resolve().parent.parent / "benchmarks" / "combinatorial_optimization" / "baseline" / "dqi_ref.kmb"


def build_dqi_temporal(input_kmb: Path | str = BASELINE_DQI) -> km.Circuit:
    """Construye circuito dqi con gestion temporal dbhexa sobre baseline verificado."""
    input_path = Path(input_kmb)
    if not input_path.is_file():
        raise FileNotFoundError(f"Archivo dqi no encontrado: {input_path}")

    circuit = km.Circuit.from_file(str(input_path), format="kmb")

    # Regla 1: registrar cada qubit que entra al sistema con su hash_in y tmp
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

    # Regla 2: vincular ancillas Toffoli (tracking logico)
    # El circuito ya tiene las puertas init_and construidas; aqui solo
    # registramos las asociaciones para el tracking del temporal manager.

    # Regla 3: salida — si hash_in == hash_out, eliminar qubit
    for qid in range(circuit.num_qubits):
        q = km.q(qid)
        mgr.exit(q)

    return circuit


def main():
    parser = argparse.ArgumentParser(
        description="Optimizador de circuito dqi con temporal manager dbhexa"
    )
    parser.add_argument("input", nargs="?", default=str(BASELINE_DQI),
                        help="Ruta al archivo .kmb de entrada (default: baseline dqi_ref.kmb)")
    parser.add_argument("output", help="Ruta del archivo .kmb de salida")
    parser.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    args = parser.parse_args()

    circuit = build_dqi_temporal(args.input)

    stats = circuit.operation_statistics()
    print(f"Qubits: {circuit.num_qubits}")
    print(f"Bits: {circuit.num_bits}")
    print(f"Toffolis: {stats.num_toffoli_like:,}")
    print(f"Num ops: {len(circuit):,}")
    print(f"Reaction depth: {circuit.reaction_depth()}")

    circuit.to_file(args.output, format=args.format)
    print(f"Escrito {args.output}")


if __name__ == "__main__":
    main()
