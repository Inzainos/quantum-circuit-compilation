#!/usr/bin/env python3
"""Pico vivo del scan (build_scan_inv) sobre una base realista de 1864 qubits vivos.

Replica la base del decoder (S 70x12 + sigma 36x12 + tau 36x12 + d 8 + H 12 + flags 138 = 1862,
mas 2 de redondeo del reporte = 1864) y corre el scan real 16 posiciones.
Mide Q del circuito (high-water del pool) y el vivo maximo durante el scan.
Si el pico del scan (sobre la base) es <= 66 (= 1930-1864, el pico BM sobre la base),
el pico BM es el que manda y el scan no limita.
Uso: python3 -u scripts/medir_scan_pico.py  (desde la raiz del repo)
"""
import sys, time
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import kickmix as km
import dqi_decoder_v1 as D
import dqi_bm_model as G

DEG = 12
t0 = time.time()
b = km.CircuitBuilder()
gf = km.GF2Field(DEG)
# base realista: S (70x12) + sigma (36x12) + tau (36x12) + d (8) + H (12) + flags (69x2=138)
S = [b.create_quantum_register(DEG, name=f'S{i}') for i in range(70)]
sig = [b.create_quantum_register(DEG, name=f'sig{i}') for i in range(36)]
tau = [b.create_quantum_register(DEG, name=f'tau{i}') for i in range(36)]
d = b.alloc_qubits(8)
H = b.alloc_qubits(12)
flags = b.alloc_qubits(138)
base = int(b.num_allocated_qubits)
print(f"base viva = {base} (esperado 1862-1864)", flush=True)
E = [b.create_classical_register(DEG, name=f'E{j}') for j in range(4095)]
# scan real, 16 posiciones (suficiente para el pico en regimen; el pico por posicion es el mismo)
D.build_scan_inv(b, gf, sig, S[:35], E, range(16))
live_despues = int(b.num_allocated_qubits)
c = b.finish_circuit()
q = int(c.num_qubits)
t = int(c.operation_statistics().num_toffoli_like)
print(f"scan 16 pos: Q={q} (pico sobre base={q - base}) vivo_despues={live_despues} "
      f"(scan regs reutilizados={live_despues - base}) T={t} ({time.time()-t0:.1f}s)", flush=True)
print(f"  pico BM sobre base (reporte fusion): 1930-1864 = 66", flush=True)
print(f"  pico scan sobre base (medido): {q - base}", flush=True)
