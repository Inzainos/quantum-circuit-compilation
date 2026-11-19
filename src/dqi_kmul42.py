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


def _form_to(b, form, reg, tmp):
    """Si la forma es un solo bit devuelve ese qubit; si no la calcula en tmp con CNOT."""
    bits = [i for i in range(DEG) if (form >> i) & 1]
    if len(bits) == 1:
        return reg[bits[0]], False
    for i in bits:
        b.cx(reg[i], tmp)
    return tmp, True


def ixor_kmul42(b: km.CircuitBuilder, x: km.array, y: km.array, target: km.array) -> None:
    tx = b.alloc_qubits(1)[0]; ty = b.alloc_qubits(1)[0]; t = b.alloc_qubits(1)[0]
    for fx, fy, tm in PLAN42:
        qx, ux = _form_to(b, fx, x, tx)
        qy, uy = _form_to(b, fy, y, ty)
        b.init_and(qx, qy, t)
        for j in range(DEG):
            if (tm >> j) & 1:
                b.cx(t, target[j])
        b.del_and(qx, qy, t)
        if ux:
            for i in range(DEG):
                if (fx >> i) & 1:
                    b.cx(x[i], tx)
        if uy:
            for i in range(DEG):
                if (fy >> i) & 1:
                    b.cx(y[i], ty)
    b.free(tx); b.free(ty); b.free(t)


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
