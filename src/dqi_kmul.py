#!/usr/bin/env python3
"""Multiplicador GF(2^12) Karatsuba de 54 AND (vs 63 del constructor): target ^= x*y.

Cada AND (formas lineales fx, fy) se materializa con init_and, se reparte con CNOT a los bits de target segun la matriz
simbolica (Karatsuba + reduccion modulo el polinomio del campo) y se libera por MBU de inmediato: 3 qubits transitorios.
Log: logging 'dqi_kmul'.
"""
from __future__ import annotations
import logging
import kickmix as km

log = logging.getLogger("dqi_kmul")
DEG = 12
POLY = 0x1053


def _kar3(a, b):
    """a,b: listas de 3 formas (mascaras). Devuelve lista (fx,fy,mask_posiciones 0..4)."""
    t = [(a[0], b[0], 0b00001 | 0b00010 | 0b00100),
         (a[1], b[1], 0b00010 | 0b00100 | 0b01000),
         (a[2], b[2], 0b00100 | 0b01000 | 0b10000),
         (a[0] ^ a[1], b[0] ^ b[1], 0b00010),
         (a[0] ^ a[2], b[0] ^ b[2], 0b00100),
         (a[1] ^ a[2], b[1] ^ b[2], 0b01000)]
    return t


def _kar(a, b):
    n = len(a)
    if n == 3:
        return _kar3(a, b)
    h = n // 2
    a0, a1, b0, b1 = a[:h], a[h:], b[:h], b[h:]
    p0 = _kar(a0, b0); p1 = _kar(a1, b1)
    pm = _kar([x ^ y for x, y in zip(a0, a1)], [x ^ y for x, y in zip(b0, b1)])
    out = []
    for fx, fy, m in p0:
        out.append((fx, fy, m | (m << h)))          # P0Q0 aparece en x^0 y en x^h (termino medio)
    for fx, fy, m in p1:
        out.append((fx, fy, (m << h) | (m << (2 * h))))
    for fx, fy, m in pm:
        out.append((fx, fy, m << h))
    return out


def _plan():
    forms = [1 << i for i in range(DEG)]
    terms = _kar(forms, forms)
    merged = {}
    for fx, fy, m in terms:
        merged[(fx, fy)] = merged.get((fx, fy), 0) ^ m
    # reduccion: posicion k (0..22) -> mascara de bits de salida
    red = []
    for k in range(2 * DEG - 1):
        v = 1 << k
        for s in range(2 * DEG - 2, DEG - 1, -1):
            if (v >> s) & 1:
                v ^= POLY << (s - DEG)
        red.append(v)
    plan = []
    for (fx, fy), m in merged.items():
        tm = 0
        for k in range(2 * DEG - 1):
            if (m >> k) & 1:
                tm ^= red[k]
        if tm:
            plan.append((fx, fy, tm))
    return plan


PLAN = _plan()


def _form_to(b, form, reg, tmp):
    """Si la forma es un solo bit devuelve ese qubit; si no la calcula en tmp con CNOT."""
    bits = [i for i in range(DEG) if (form >> i) & 1]
    if len(bits) == 1:
        return reg[bits[0]], False
    for i in bits:
        b.cx(reg[i], tmp)
    return tmp, True


def ixor_kmul(b: km.CircuitBuilder, x: km.array, y: km.array, target: km.array) -> None:
    tx = b.alloc_qubits(1)[0]; ty = b.alloc_qubits(1)[0]; t = b.alloc_qubits(1)[0]
    for fx, fy, tm in PLAN:
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
    try:  # logs estructurados (qcc_log): una linea por script
        import sys as _qs
        from pathlib import Path as _qp
        _qs.path.insert(0, str(_qp(__file__).resolve().parent.parent / "tools"))
        from qcc_log import auto as _qcc_auto
        _qcc_auto(__file__)
    except Exception:  # noqa: BLE001
        pass
    import numpy as np
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log.info("ANDs del plan: %d", len(PLAN))
    B = 256
    rng = np.random.default_rng(1)
    gf = km.GF2Field(DEG)
    xs = rng.integers(0, 4096, B); ys = rng.integers(0, 4096, B); ts = rng.integers(0, 4096, B)

    def bits(v): return ((v[None, :] >> np.arange(DEG)[:, None]) & 1) == 1
    def build(use_k):
        b = km.CircuitBuilder()
        x = b.create_quantum_register(DEG, name='x'); y = b.create_quantum_register(DEG, name='y'); t = b.create_quantum_register(DEG, name='t')
        if use_k: ixor_kmul(b, x, y, t)
        else: b.ixor_gf2_mul(x, y, target=t, field=gf)
        return b.finish_circuit()
    outs = []
    for use_k in (False, True):
        c = build(use_k)
        sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=1); sim.use_same_registers_as(c)
        sim.write_across_shots(km.array([km.q(i) for i in range(36)]), np.concatenate([bits(xs), bits(ys), bits(ts)]))
        sim.do(c)
        outs.append(sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)])))
        log.info("kmul=%s toffoli=%d qubits=%d fase=%d", use_k, c.operation_statistics().num_toffoli_like, c.num_qubits,
                 int(sim.read_phase_flipped_across_shots().sum()))
    log.info("igual al constructor: %s ; ancillas limpias: %s", bool((outs[0][:36] == outs[1][:36]).all()), not outs[1][36:].any())
