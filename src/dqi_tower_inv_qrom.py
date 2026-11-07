#!/usr/bin/env python3
"""
QROM para inversas en GF(8) y GF(64) usadas en TowerInv2.
Objetivo: reemplazar inv8_init/inv8_del por lookup tabla precomputada.
Coste: 0 Toffoli, solo CNOTs.

Tabla GF(8) con primitivo g.
inv8[x] = x^-1 para x != 0, inv8[0]=0

Se implementa con QROM diferencial usando builder.cx con control clásico.
"""

from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import kickmix as km

# Tabla de inversas GF(8) con primitivo 2
INV8 = {0:0,1:1,2:6,3:5,4:7,5:3,6:2,7:4}

def inv8_qrom(b: km.CircuitBuilder, addr, target):
    """target ^= inv8[addr] usando QROM con 3 bits de addr -> 3 bits target.
    addr y target son listas de 3 qubits.
    Coste: 3*8 CNOTs, 0 Toffoli.
    """
    # Implementación simplificada: para cada entrada i, si addr == i,
    # copiar tabla[i] a target con XOR condicional.
    # En kickmix se puede hacer con CX controlados clásicos tras computar
    # comparación de addr; simplificado aquí a placeholder.
    # TODO: implementar comparación eficiente con QROM diferencial.
    for i in range(8):
        # placeholder: en práctica usar QROM diferencial con 2^3 líneas
        pass

def inv64_qrom(b: km.CircuitBuilder, addr, target):
    """QROM para inversa GF(64). 6 bits -> 6 bits, 64 entradas.
    Coste estimado: 6*64 CNOTs, 0 Toffoli.
    """
    # TODO
    pass

if __name__ == "__main__":
    b = km.CircuitBuilder()
    addr = b.create_quantum_register(3)
    tgt = b.create_quantum_register(3)
    inv8_qrom(b, addr, tgt)
    c = b.finish_circuit()
    print("QROM inv8 qubits", c.num_qubits, "toffoli", c.operation_statistics().num_toffoli_like)
