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
    """target ^= inv8[addr] usando QROM tipo angle_k con árbol de 7 init_and y MBU.
    addr: lista 3 qubits [MSB..LSB], target: lista 3 qubits.
    Coste: 7 init_and + 24 CX, descomputación 0 Toffoli (del_and = HMR+CZ).
    """
    table = [INV8[i] for i in range(8)]
    # QROM estilo angle_k: bits MSB primero
    bits = [addr[0], addr[1], addr[2]]  # MSB first
    ancillas = b.alloc_qubits(2)  # 2 ancillas para niveles 1 y 2
    
    def load(row: int, control: Any) -> None:
        """Aplica tabla[row] a target si control=1."""
        for k in range(3):
            if (table[row] >> k) & 1:
                b.cx(control, target[k])
    
    def node(control: Any, level: int, lo: int, hi: int) -> None:
        if hi - lo == 1:
            load(lo, control)
            return
        mid = (lo + hi) // 2
        bit = bits[level]
        ancilla = ancillas[level - 1]
        
        # control AND ~bit -> lower half
        b.x(bit)
        b.init_and(control, bit, ancilla)
        b.x(bit)
        node(ancilla, level + 1, lo, mid)
        
        # control AND bit -> upper half
        b.cx(control, ancilla)
        node(ancilla, level + 1, mid, hi)
        
        # Uncompute con MBU
        b.del_and(control, bit, ancilla)
    
    # Raíz: bit 0 (MSB)
    # Lower half: ~bit0
    b.x(bits[0])
    node(bits[0], 1, 0, 4)
    b.x(bits[0])
    # Upper half: bit0
    node(bits[0], 1, 4, 8)
    
    b.free(ancillas)

def inv64_qrom(b: km.CircuitBuilder, addr, target):
    """QROM para inversa GF(64). 6 bits -> 6 bits, 64 entradas.
    Coste estimado: 6*64 CNOTs, 0 Toffoli.
    """
    # TODO
    pass

if __name__ == "__main__":
    b = km.CircuitBuilder()
    addr = b.create_quantum_register(3, name='addr')
    tgt = b.create_quantum_register(3, name='tgt')
    inv8_qrom(b, addr, tgt)
    c = b.finish_circuit()
    print("QROM inv8 qubits", c.num_qubits, "toffoli", c.operation_statistics().num_toffoli_like)
