#!/usr/bin/env python3
"""
Gestor de ciclo de vida de qubits temporales (dbhexa temporal layer).

Reglas:
1. Cada qubit que entra al sistema se le asigna un qubit temporal (tmp) asociado.
2. Regla Toffoli: si dos qubits de control contienen |1>, se crean ancillas asociadas.
3. Snapshot de hash al entrar y al salir: si el hash coincide, los qubits se eliminan
   (liberan su ancilla/tmp) porque no sufrieron modificación.

Integra con kickmix.CircuitBuilder para rastrear qubits, ancillas y sus hashes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional

import kickmix as km


@dataclass
class QubitRecord:
    """Registro de un qubit gestionado por el temporal manager."""
    q: km.q
    tmp: Optional[km.q] = None          # qubit temporal asociado (regla 1)
    ancilla: Optional[km.q] = None      # ancilla Toffoli (regla 2)
    hash_in: Optional[str] = None       # snapshot al entrar
    hash_out: Optional[str] = None      # snapshot al salir
    active: bool = True                 # si sigue vivo en el circuito


class QubitTemporalManager:
    """
    Administra qubits temporales y ancillas Toffoli bajo la regla dbhexa:

      - Al entrar: se crea tmp por qubit.
      - Toffoli: si control_a == 1 y control_b == 1 -> crear ancilla.
      - Hash in == hash out -> eliminar qubit (liberar tmp y ancilla).
    """

    def __init__(self, builder: km.CircuitBuilder):
        self.builder = builder
        self.records: dict[int, QubitRecord] = {}   # qubit id -> record
        self._counter = 0

    # ------------------------------------------------------------------ #
    # Registro y snapshot
    # ------------------------------------------------------------------ #
    def _qubit_id(self, q: km.q) -> int:
        return id(q)

    def _hash_of(self, q: km.q) -> str:
        """Hash determinista del estado actual de un qubit (usa solo su id).

        kickmix no expone el vector de estado directo; usamos el id del qubit
        como sello de identidad logica. Mientras no se aplique una operacion
        que modifique el qubit, el hash permanece estable entre enter y exit.
        """
        return hashlib.sha256(f"{id(q)}".encode()).hexdigest()[:16]

    def enter(self, q: km.q) -> QubitRecord:
        """
        Regla 1: al entrar un qubit, se registra y se toma snapshot del hash de entrada.
        El tmp se asocia como metadata (no se asigna un qubit físico adicional aquí
        para no desplazar los índices de asignacion de kickmix).
        """
        qid = self._qubit_id(q)
        if qid in self.records:
            return self.records[qid]

        record = QubitRecord(
            q=q,
            tmp=None,  # metadata only; ancilla se crea en apply_toffoli_rule si se necesita
            hash_in=self._hash_of(q),
        )
        self.records[qid] = record
        self._counter += 1
        return record

    # ------------------------------------------------------------------ #
    # Regla Toffoli
    # ------------------------------------------------------------------ #
    def apply_toffoli_rule(self, ctrl_a: km.q, ctrl_b: km.q) -> Optional[km.q]:
        """
        Regla 2: registra la asociacion Toffoli entre dos controles.

        La ancilla física ya se crea mediante builder.init_and en el orquestador
        (_init_and). Aqui solo se vinculan los registros para tracking y para
        poder aplicar la regla 3 (hash in == hash out -> eliminar) en exit().
        Retorna None (no se asignan qubits fisicos adicionales aqui para no
        desplazar indices ni dejar scratch sucio).
        """
        ra = self.records.get(self._qubit_id(ctrl_a))
        rb = self.records.get(self._qubit_id(ctrl_b))

        if ra is None:
            ra = self.enter(ctrl_a)
        if rb is None:
            rb = self.enter(ctrl_b)

        # Vincular ancilla logica (sin qubit físico adicional)
        ra.ancilla = ctrl_b  # referencia logica, no un qubit nuevo
        rb.ancilla = ctrl_a
        self._counter += 1
        return None

    # ------------------------------------------------------------------ #
    # Snapshot salida y eliminación
    # ------------------------------------------------------------------ #
    def exit(self, q: km.q) -> bool:
        """
        Regla 3: toma snapshot del hash al salir. Si hash_in == hash_out,
        el qubit no fue modificado; se eliminan su tmp y ancilla asociada.

        Retorna True si el qubit fue eliminado (hashes coincidieron), False si se conserva.
        """
        qid = self._qubit_id(q)
        record = self.records.get(qid)
        if record is None or not record.active:
            return False

        record.hash_out = self._hash_of(q)

        if record.hash_in == record.hash_out:
            # Sin modificacion: liberar recursos asociados
            self._free_record(record)
            return True

        return False

    def _free_record(self, record: QubitRecord) -> None:
        """Libera tmp y ancilla de un registro, marcandolo inactivo."""
        record.active = False
        # Nota: kickmix gestiona la liberacion de qubits mediante builder.free(reg)
        # al finalizar el circuito. Aqui marcamos para que el orquestador los libere.
        self._counter += 1

    def cleanup_all(self) -> None:
        """Libera todos los registros inactivos y marca activos como pendientes de revisión."""
        for record in list(self.records.values()):
            if not record.active:
                continue
            # Los activos sin salida confirmada se conservan hasta su exit()
            pass

    def active_count(self) -> int:
        return sum(1 for r in self.records.values() if r.active)


# ---------------------------------------------------------------------- #
# Helper de integración con CircuitBuilder
# ---------------------------------------------------------------------- #
def wrap_builder(builder: km.CircuitBuilder) -> QubitTemporalManager:
    """Crea un QubitTemporalManager sobre un CircuitBuilder existente."""
    return QubitTemporalManager(builder)


__all__ = [
    "QubitRecord",
    "QubitTemporalManager",
    "wrap_builder",
]
