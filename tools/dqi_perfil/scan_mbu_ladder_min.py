#!/usr/bin/env python3
"""Minimal: escalera f sola, MBU vs Bennett. ¿Cambia la fase?

La escalera calcula f=[s==0] con 11 AND y la deshace. No hay puertas de
fase en este circuito, asi que la fase debe ser 0 en ambas variantes.
Si MBU da fase != 0, el fixup CZ del del_and esta metiendo fase (o el
simulador la cuenta distinto). Si Bennett da != 0, el re-AND mete fase.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import kickmix as km

DEG = 12


def build_ladder(bennett, s_val):
    b = km.CircuitBuilder()
    s = b.alloc_qubits(DEG)
    lad = b.alloc_qubits(DEG - 2)
    f = b.alloc_qubits(1)[0]
    # s se fija con X segun s_val (bit=1 -> X)
    for j in range(DEG):
        if (s_val >> j) & 1:
            b.x(s[j])
    b.x(s)  # invertir (como en el scan)
    b.init_and(s[0], s[1], lad[0])
    for i in range(2, DEG - 1):
        b.init_and(lad[i - 2], s[i], lad[i - 1])
    b.init_and(lad[DEG - 3], s[DEG - 1], f)
    clean = b.init_and if bennett else b.del_and
    clean(lad[DEG - 3], s[DEG - 1], f)
    for i in reversed(range(2, DEG - 1)):
        clean(lad[i - 2], s[i], lad[i - 1])
    clean(s[0], s[1], lad[0])
    b.x(s)
    # deshacer s
    for j in range(DEG):
        if (s_val >> j) & 1:
            b.x(s[j])
    return b.finish_circuit(), s, lad, f


def bits_of(vals_list, deg=DEG, nshots=1):
    out = np.zeros((len(vals_list) * deg, nshots), dtype=bool)
    for idx, v in enumerate(vals_list):
        for j in range(deg):
            out[idx * deg + j, 0] = bool((v >> j) & 1)
    return out


for s_val in (0, 0xABC, 0xFFF):
    for bennett in (False, True):
        circ, s, lad, f = build_ladder(bennett, s_val)
        nq = circ.num_qubits
        sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
        sim.use_same_registers_as(circ)
        # s ya se fija con X en el circuito; no hace falta escribir nada
        sim.do(circ)
        out = sim.read_across_shots(km.array([km.q(i) for i in range(nq)]))
        sucios = int(out[:, 0].sum())
        fase = int(sim.read_phase_flipped_across_shots().sum())
        f_val = int(out[DEG + (DEG - 2), 0])  # f es el ultimo qubit (lad tiene DEG-2, f es 1)
        print(f"s_val=0x{s_val:03X} {'Bennett' if bennett else 'MBU    '} "
              f"T={int(circ.operation_statistics().num_toffoli_like)} sucios={sucios} "
              f"fase={fase} f_final={f_val}")
