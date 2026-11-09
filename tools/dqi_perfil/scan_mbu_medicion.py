#!/usr/bin/env python3
"""Medicion del scan MBU del DQI: ¿el -23 Toffoli/posicion teorico se sostiene?

Pregunta: el doc docs/OPTIMIZACION_DQI_SCAN.md propone ahorrar 23 T/posicion
(11 del test-cero + 12 de fase) reemplazando del_and por HMR. Pero del_and
EN kickmix YA ES HMR + CZ (0 Toffoli). Este script mide:
  A. Descomposicion del 98 T/posicion por componente (medido).
  B. Variante Bennett (del_and -> re-init_and) para probar que el MBU ya
     ahorra esos 23 T/posicion (si Bennett da 121, el MBU ya esta realizado).
  C. Correctitud a escala chica en el simulador kickmix (fase correcta y
     todos los ancillas en |0⟩) para el scan MBU (actual) y el Bennett.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/tools")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_scan_stage import _linear_sources, _emit_linear, _alpha_pow_bits
from dqi_decoder_v1 import build_scan_inv
from dqi_tower_inv3 import TowerInv3
from dqi_tower_inv3 import TowerInv3 as TowerInv
from dqi_tower_inv import CCOLS

DEG = 12


def _to_coords(srcs):
    out = []
    for o in range(DEG):
        par = {}
        for k in range(DEG):
            if (CCOLS[k] >> o) & 1:
                for q in srcs[k]:
                    par[q] = par.get(q, 0) ^ 1
        out.append([q for q, v in par.items() if v])
    return out


def count_toff(circ):
    return int(circ.operation_statistics().num_toffoli_like)


# ---------------- A. Descomposicion por componente ----------------
print("=== A. Descomposicion del costo por posicion (medido) ===")
# A1. TowerInv3 forward solo y forward+undo
b = km.CircuitBuilder()
dd = b.alloc_qubits(DEG); w = b.alloc_qubits(DEG)
TI = TowerInv3(b, dd, w); TI.forward()
print("TowerInv3 forward solo:      T =", count_toff(b.finish_circuit()))
b = km.CircuitBuilder()
dd = b.alloc_qubits(DEG); w = b.alloc_qubits(DEG)
TI = TowerInv3(b, dd, w); TI.forward(); TI.undo()
print("TowerInv3 forward+undo:      T =", count_toff(b.finish_circuit()))

# A2. Escalera f = [s==0]: 11 init_and + 11 del_and (MBU) vs 11+11 Bennett
def build_f_ladder(bennett=False):
    b = km.CircuitBuilder()
    s = b.alloc_qubits(DEG); lad = b.alloc_qubits(DEG - 2); f = b.alloc_qubits(1)[0]
    b.x(s)
    b.init_and(s[0], s[1], lad[0])
    for i in range(2, DEG - 1):
        b.init_and(lad[i - 2], s[i], lad[i - 1])
    b.init_and(lad[DEG - 3], s[DEG - 1], f)
    # limpieza
    clean = b.init_and if bennett else b.del_and
    clean(lad[DEG - 3], s[DEG - 1], f)
    for i in reversed(range(2, DEG - 1)):
        clean(lad[i - 2], s[i], lad[i - 1])
    clean(s[0], s[1], lad[0])
    b.x(s)
    return b.finish_circuit()

print("Escalera f MBU (del_and):     T =", count_toff(build_f_ladder(False)), "(esperado 11)")
print("Escalera f Bennett (re-and): T =", count_toff(build_f_ladder(True)), "(esperado 22)")

# A3. Fase g de un solo 'a': init_and + CZ + del_and vs Bennett
def build_g_one(bennett=False):
    b = km.CircuitBuilder()
    f = b.alloc_qubits(1)[0]; tmp = b.alloc_qubits(1)[0]; g = b.alloc_qubits(1)[0]
    w = b.alloc_qubits(DEG)
    b.init_and(f, tmp, g)
    b.cz(g, w[0])
    if bennett:
        b.init_and(f, tmp, g)
    else:
        b.del_and(f, tmp, g)
    return b.finish_circuit()

print("Fase g (1 a) MBU:            T =", count_toff(build_g_one(False)), "(esperado 1; x12 = 12)")
print("Fase g (1 a) Bennett:        T =", count_toff(build_g_one(True)), "(esperado 2; x12 = 24)")

# A4. Scan completo (build_scan_inv real) para N posiciones
def build_scan_n(npos, LS=36, LO=35):
    b = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    sig = [b.create_quantum_register(DEG, name=f"sig{i}") for i in range(LS)]
    om = [b.create_quantum_register(DEG, name=f"om{i}") for i in range(LO)]
    E = [b.create_classical_register(DEG, name=f"E{j}") for j in range(npos)]
    build_scan_inv(b, gf, sig, om, E, positions=range(npos))
    return b.finish_circuit()

for npos in (1, 4, 8):
    c = build_scan_n(npos)
    t = count_toff(c)
    print(f"Scan real {npos} pos: T = {t}  -> {t / npos:.1f} T/posicion (esperado 98.0)")

# A5. Variante Bennett del scan completo.
# OJO: el descomputo Bennett correcto usa Toffoli PROPIO (multi_controlled_x),
# NO re-init_and: init_and es un AND de fase relativa (tipo Margolus), NO es
# autoinverso (medido: init_and x2 deja t=1). Re-init_and NO deshace el AND
# (deja sucios los temporales y corrompe la fase). El Toffoli propio si deshace
# (medido: init_and + Toffoli -> t=0, fase 0) y cuesta 1 T.
# Se reemplazan los 11 del_and de f y 12 de g por Toffolis (TI.undo se deja MBU).
def build_scan_inv_bennett(b, field, sig, om, E, positions=None, tower=True):
    n_pos = len(E)
    positions = range(min(n_pos, G.Q - 1)) if positions is None else positions
    apow = [_alpha_pow_bits(s) for s in range(2 * DEG - 1)]
    s = b.alloc_qubits(DEG); dd = b.alloc_qubits(DEG); w = b.alloc_qubits(DEG)
    tmp = b.alloc_qubits(1)[0]; f = b.alloc_qubits(1)[0]; lad = b.alloc_qubits(DEG - 2); g = b.alloc_qubits(1)[0]

    def toff(a, c, t):
        b.multi_controlled_x(km.array([a, c]), t)

    for p in positions:
        r = _alpha_pow_bits(-p)
        with b.mark("scan_pos"):
            pw = [1]
            for i in range(1, max(len(sig), len(om))):
                pw.append(G.mul(pw[-1], r))
            src_s = _linear_sources(pw[:len(sig)], sig)
            src_u = _linear_sources(pw[:len(om)], om)
            dco = [pw[i - 1] if i % 2 == 1 else 0 for i in range(len(sig))]
            src_d = _linear_sources(dco, sig)
            if tower:
                src_d = _to_coords(src_d)
            _emit_linear(b, src_s, s)
            b.x(s)
            b.init_and(s[0], s[1], lad[0])
            for i in range(2, DEG - 1):
                b.init_and(lad[i - 2], s[i], lad[i - 1])
            b.init_and(lad[DEG - 3], s[DEG - 1], f)
            _emit_linear(b, src_d, dd)
            if tower:
                TI = TowerInv(b, dd, w); TI.forward()
            for a in range(DEG):
                for q in src_u[a]:
                    b.cx(q, tmp)
                b.init_and(f, tmp, g)
                for k in range(DEG):
                    srcs = [w[bb] for bb in range(DEG) if (apow[a + bb] >> k) & 1]
                    if srcs:
                        b.push_condition(E[p][k])
                        b.cz(km.array(srcs), km.array([g] * len(srcs)))
                        b.pop_condition()
                toff(f, tmp, g)  # Bennett con Toffoli propio
                for q in src_u[a]:
                    b.cx(q, tmp)
            if tower:
                TI.undo()
            _emit_linear(b, src_d, dd)
            # Bennett para la escalera f (Toffolis propios, orden inverso)
            toff(lad[DEG - 3], s[DEG - 1], f)
            for i in reversed(range(2, DEG - 1)):
                toff(lad[i - 2], s[i], lad[i - 1])
            toff(s[0], s[1], lad[0])
            b.x(s)
            _emit_linear(b, src_s, s)
    for q in (s, dd, w, lad):
        b.free(q)
    b.free(tmp); b.free(f); b.free(g)


def build_scan_bennett_n(npos, LS=36, LO=35):
    b = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    sig = [b.create_quantum_register(DEG, name=f"sig{i}") for i in range(LS)]
    om = [b.create_quantum_register(DEG, name=f"om{i}") for i in range(LO)]
    E = [b.create_classical_register(DEG, name=f"E{j}") for j in range(npos)]
    build_scan_inv_bennett(b, gf, sig, om, E, positions=range(npos))
    return b.finish_circuit()


for npos in (1, 4, 8):
    c = build_scan_bennett_n(npos)
    t = count_toff(c)
    print(f"Scan Bennett {npos} pos: T = {t}  -> {t / npos:.1f} T/posicion (esperado 121.0)")

print()
print("Resumen A: MBU ya presente = Bennett - real =", 121 - 98, "T/posicion")
print("  Si Bennett da 121 y real da 98, el ahorro de 23 ya esta realizado.")
