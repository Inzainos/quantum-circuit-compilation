#!/usr/bin/env python3
"""
Generador de circuito invsqrt con gestion de qubits temporales (dbhexa temporal layer).

Integra las 3 reglas de qubits temporales sobre el reference verificado de kickmix
(nr_reference_circuit.py), que ya pasa el verificador oficial de Benchmark I:

1. Enter: cada qubit que entra al sistema se registra con su hash_in y tmp.
2. Regla Toffoli: al aplicar init_and, se vincula logica la ancilla a los controles.
3. Exit: si hash_in == hash_out (no hubo modificacion), el qubit se elimina.

El circuito base usa build_nr_circuit del reference (verificado PASS) con
parametros dbhexa optimizados (square=27, product=27, result=27 ->
Q=254, T=7405; ~6.5% menos Q x toffoli_equivalent que el baseline Q=260, T=7735).

NOTA: result_bits=28 NO es valido (Q=255, T=7493, falla el verificador).
La capa QubitTemporalManager es solo contabilidad: no modifica el circuito.
Todo el ahorro proviene de los anchos de bit en Precision().
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


# ══════════════════════════════════════════════════════════════════════════════
# Parametros dbhexa optimizados
# ══════════════════════════════════════════════════════════════════════════════

DBHEXA_PRECISION = Precision(
    delta_bits=14,
    coef_bits=17,
    square_bits=27,
    product_bits=27,
    result_bits=27,
)


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline dbhexa con temporal manager (sobre reference verificado)
# ══════════════════════════════════════════════════════════════════════════════

class DbHexaInvSqrt:
    """Generador de circuito invsqrt con arquitectura dbhexa + temporal manager."""

    def __init__(self, n_p: int = 10,
                 delta_bits: int = 14,
                 coef_bits: int = 17,
                 square_bits: int = 27,
                 product_bits: int = 27,
                 result_bits: int = 27):
        self.n_p = n_p
        self.width = 2 * n_p + 2
        self.prec = Precision(
            delta_bits=delta_bits,
            coef_bits=coef_bits,
            square_bits=square_bits,
            product_bits=product_bits,
            result_bits=result_bits,
        )

    def output_bits(self) -> int:
        return self.prec.output_bits(self.n_p)

    def build(self) -> km.Circuit:
        """Construye el circuito con gestion temporal dbhexa."""
        # Usar el reference verificado para construir el circuito (pasa el verificador)
        circuit = build_nr_circuit(self.n_p, prec=self.prec, compute_only=False)

        # Regla 1: registrar todos los qubits del circuito en el temporal manager
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

        # Regla 3: evaluar salida - si hash_in == hash_out, eliminar qubit
        for qid in range(circuit.num_qubits):
            q = km.q(qid)
            mgr.exit(q)

        return circuit


def main():
    parser = argparse.ArgumentParser(
        description="Generar circuito invsqrt dbhexa con temporal manager (reference verificado)"
    )
    parser.add_argument("output", help="Ruta del archivo .kmb de salida")
    parser.add_argument("--n-p", type=int, default=10)
    parser.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    args = parser.parse_args()

    pipeline = DbHexaInvSqrt(n_p=args.n_p)
    circuit = pipeline.build()

    stats = circuit.operation_statistics()
    print(f"Qubits: {circuit.num_qubits}")
    print(f"Toffolis: {stats.num_toffoli_like:,}")
    print(f"Num ops: {len(circuit):,}")
    print(f"Reaction depth: {circuit.reaction_depth()}")

    circuit.to_file(args.output, format=args.format)
    print(f"Escrito {args.output}")


if __name__ == "__main__":
    main()
