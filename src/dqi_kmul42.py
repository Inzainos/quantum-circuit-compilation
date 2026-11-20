#!/usr/bin/env python3
"""Multiplicador GF(2^12) Toom-4 sobre GF(8) de 42 AND (vs 54 Karatsuba): target ^= x*y.

Construccion: isomorfismo explicito Phi entre GF(2)[t]/(0x1053) y GF(8)[y]/(y^4+y+1),
evaluacion-interpolacion en 7 puntos de GF(8), 7 productos en GF(8) x 6 ANDs = 42 ANDs,
reduccion mod p(y) y Phi^-1 (todo lineal, 0 ANDs). Cada AND es un par de formas
lineales (fx, fy) con mascara de salida, mismo formato PLAN que dqi_kmul.py: 3 qubits
transitorios (tx, ty, t), liberados por MBU de inmediato. Verificacion clasica:
144/144 pares de base + 20000/20000 aleatorios contra la multiplicacion de referencia.
Log: logging 'dqi_kmul42'.
"""
from __future__ import annotations
import logging
import kickmix as km

log = logging.getLogger("dqi_kmul42")
DEG = 12
POLY = 0x1053

# PLAN42: lista de (fx, fy, mascara_salida), 42 ANDs. Generado por diseno_toom4.py.
PLAN42 = [
    (173, 173, 3958),
    (199, 199, 354),
    (320, 320, 183),
    (420, 420, 1510),
    (493, 493, 4033),
    (518, 518, 2122),
    (692, 692, 2389),
    (717, 717, 396),
    (791, 791, 2446),
    (805, 805, 1345),
    (822, 822, 2302),
    (857, 857, 1571),
    (873, 873, 611),
    (936, 936, 1343),
    (976, 976, 3735),
    (1012, 1012, 1684),
    (1297, 1297, 3189),
    (1396, 1396, 234),
    (1421, 1421, 3826),
    (1444, 1444, 3870),
    (1575, 1575, 3767),
    (1665, 1665, 2655),
    (1756, 1756, 2306),
    (1931, 1931, 1720),
    (2220, 2220, 2620),
    (2370, 2370, 1557),
    (2884, 2884, 173),
    (2944, 2944, 2648),
    (2970, 2970, 1609),
    (2989, 2989, 3287),
    (3094, 3094, 1817),
    (3281, 3281, 4085),
    (3329, 3329, 3865),
    (3441, 3441, 1493),
    (3467, 3467, 1130),
    (3620, 3620, 7),
    (3723, 3723, 1163),
    (3785, 3785, 2279),
    (3801, 3801, 2536),
    (3810, 3810, 1545),
    (3910, 3910, 1925),
    (4038, 4038, 1659),
]

# P1 (prototipo espiral, Fase 2, 2026-11-19): matriz 6x7 EXPLICITA.
# PLAN42 esta agrupado por punto de evaluacion (generador diseno_toom4.py,
# build_plan: bucle externo sobre los 7 PTS, interno sobre los 6 ANDs
# Karatsuba de kar3_plan(); 0 fusiones, 0 nulos -> el orden plano es
# punto-mayor). Fila = indice AND Karatsuba dentro del producto GF(8)
# (0..5); columna = punto de evaluacion (0..6).
# PLAN42[6*col + row] == PLAN42_MATRIX[row][col].
N_ROWS = 6
N_COLS = 7
# OJO: el paso (stride) es N_ROWS (6 ANDs por punto), no N_COLS.
PLAN42_MATRIX = [[PLAN42[N_ROWS * col + row] for col in range(N_COLS)]
                 for row in range(N_ROWS)]
# Verificacion estructural: aplanar por columnas reproduce PLAN42 exacto.
assert [PLAN42_MATRIX[r][c] for c in range(N_COLS) for r in range(N_ROWS)] == PLAN42
assert len(PLAN42_MATRIX) == N_ROWS
assert all(len(fila) == N_COLS for fila in PLAN42_MATRIX)

# Orden de emision de la matriz. "col" = columna-mayor = el orden plano de
# hoy (cada columna = un producto GF(8) completo) -> secuencia de puertas
# IDENTICA a swap42, .kmb byte-identico. "row" = fila-mayor (sonda de
# medicion para la confirmacion #3 de FASE 2: si el orden cambia
# reaction_depth o Q pico). Solo "col" es el entregable P1.
EMIT_ORDER = "col"


def _iter_plan():
    """Itera los 42 terminos en el orden de emision de la matriz."""
    if EMIT_ORDER == "row":
        for row in range(N_ROWS):
            for col in range(N_COLS):
                yield PLAN42_MATRIX[row][col]
    else:  # "col": mismo orden que PLAN42 plano
        for col in range(N_COLS):
            for row in range(N_ROWS):
                yield PLAN42_MATRIX[row][col]


def _form_to(b, form, reg, tmp):
    """Si la forma es un solo bit devuelve ese qubit; si no la calcula en tmp con CNOT."""
    bits = [i for i in range(DEG) if (form >> i) & 1]
    if len(bits) == 1:
        return reg[bits[0]], False
    for i in bits:
        b.cx(reg[i], tmp)
    return tmp, True


def ixor_kmul42(b: km.CircuitBuilder, x: km.array, y: km.array, target: km.array) -> None:
    """Toom-4 42 AND sin ancillas (QF): formas lineales en el sitio + Toffoli con fan-out. Mismo T (42).
    P1+P2+P3 sobre QF: el plan se emite como la matriz 6x7 EXPLICITA (P1) y se
    pasa a qf.mul_terms_init como list(_iter_plan()); con EMIT_ORDER="col" eso
    es exactamente PLAN42 en orden, asi que la secuencia de puertas es
    IDENTICA a la del QF (el bucle sobre el plan vive dentro de
    qf.mul_terms_init, no aqui)."""
    import qf
    qf.mul_terms_init(b, list(_iter_plan()), DEG, DEG, x, y, target, DEG)


if __name__ == "__main__":
    import numpy as np
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log.info("ANDs del plan: %d", len(PLAN42))
    B = 256
    rng = np.random.default_rng(1)
    gf = km.GF2Field(DEG)
    xs = rng.integers(0, 4096, B); ys = rng.integers(0, 4096, B); ts = rng.integers(0, 4096, B)

    def bits(v): return ((v[None, :] >> np.arange(DEG)[:, None]) & 1) == 1
    def build(kind):
        b = km.CircuitBuilder()
        x = b.create_quantum_register(DEG, name='x'); y = b.create_quantum_register(DEG, name='y'); t = b.create_quantum_register(DEG, name='t')
        if kind == 'ctor': b.ixor_gf2_mul(x, y, target=t, field=gf)
        elif kind == 'kar54':
            import dqi_kmul; dqi_kmul.ixor_kmul(b, x, y, t)
        else: ixor_kmul42(b, x, y, t)
        return b.finish_circuit()
    outs = {}
    for kind in ('ctor', 'kar54', 'toom42'):
        c = build(kind)
        sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=1); sim.use_same_registers_as(c)
        sim.write_across_shots(km.array([km.q(i) for i in range(36)]), np.concatenate([bits(xs), bits(ys), bits(ts)]))
        sim.do(c)
        outs[kind] = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
        log.info("%s toffoli=%d qubits=%d fase=%d", kind, c.operation_statistics().num_toffoli_like, c.num_qubits,
                 int(sim.read_phase_flipped_across_shots().sum()))
    log.info("toom42 igual al constructor: %s ; igual a kar54: %s ; ancillas limpias: %s",
             bool((outs['ctor'][:36] == outs['toom42'][:36]).all()),
             bool((outs['kar54'][:36] == outs['toom42'][:36]).all()),
             not outs['toom42'][36:].any())
