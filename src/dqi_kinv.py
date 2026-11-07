#!/usr/bin/env python3
"""Inversion GF(2^12) por Itoh-Tsujii con multiplicador Karatsuba (54 AND): 5 productos = 270 Toffoli (vs 315 del constructor).
Cadena de adicion 1,2,4,5,10,11:  b1=x, b2=b1^2*b1, b4=b2^4*b2, b5=b4^2*b1, b10=b5^32*b5, b11=b10^2*b1, x^-1 = b11^2.
Las potencias de Frobenius son lineales (CNOT sobre un registro temporal).  La descomputacion usa del_gf2_mul del constructor
(MBU, 0 Toffoli) porque cada producto vale exactamente lhs*rhs.  API: init_kinv(b, field, x, target) -> andamiaje;
del_kinv(b, field, x, target, andamiaje).  Log: logger 'dqi_kinv'.
"""
from __future__ import annotations
import logging
import kickmix as km
import dqi_bm_model as G
from dqi_kmul import ixor_kmul

log = logging.getLogger("dqi_kinv")
DEG = 12
_STEPS = [("b2", "b1", 1, "b1"), ("b4", "b2", 2, "b2"), ("b5", "b4", 1, "b1"), ("b10", "b5", 5, "b5"), ("b11", "b10", 1, "b1")]


def _frob_cols(k: int):
    cols = []
    for j in range(DEG):
        v = 1 << j
        for _ in range(k):
            v = G.mul(v, v)
        cols.append(v)
    return cols


def _frob(b, src, dst, k):
    """dst ^= src^(2^k)  (lineal)."""
    cols = _frob_cols(k)
    for o in range(DEG):
        s = [src[j] for j in range(DEG) if (cols[j] >> o) & 1]
        if s:
            b.cx(km.array(s), km.array([dst[o]] * len(s)))


def init_kinv(b, field, x, target):
    reg = {"b1": x}
    scaf = []
    for name, a, k, c in _STEPS:
        A = reg[a]; C = reg[c]
        P = b.alloc_qubits(DEG)
        if k:
            T = b.alloc_qubits(DEG); _frob(b, A, T, k); ixor_kmul(b, T, C, P); _frob(b, A, T, k); b.free(T)
        else:
            ixor_kmul(b, A, C, P)
        reg[name] = P; scaf.append((name, a, k, c, P))
    _frob(b, reg["b11"], target, 1)
    return scaf


def del_kinv(b, field, x, target, scaf):
    reg = {"b1": x}
    for name, a, k, c, P in scaf:
        reg[name] = P
    _frob(b, reg["b11"], target, 1)
    for name, a, k, c, P in reversed(scaf):
        A = reg[a]; C = reg[c]
        if k:
            T = b.alloc_qubits(DEG); _frob(b, A, T, k)
            b.del_gf2_mul(T, C, target=P, field=field)
            _frob(b, A, T, k); b.free(T)
        else:
            b.del_gf2_mul(A, C, target=P, field=field)
        b.free(P)


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
    B = 512; rng = np.random.default_rng(3); gf = km.GF2Field(DEG)
    xs = rng.integers(0, 4096, B); xs[:4] = [0, 1, 2, 4095]
    def bits(v): return ((v[None, :] >> np.arange(DEG)[:, None]) & 1) == 1
    for modo in ("construido", "kinv"):
        b = km.CircuitBuilder(); x = b.create_quantum_register(DEG, name='x'); t = b.create_quantum_register(DEG, name='t')
        if modo == "kinv":
            sc = init_kinv(b, gf, x, t); mid = b.finish_circuit.__self__ if False else None
        else:
            _, sc = b.init_gf2_inverse_with_scaffold(x, target=t, field=gf)
        c1 = b.finish_circuit()
        sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=1); sim.use_same_registers_as(c1)
        sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(xs)); sim.do(c1)
        out = sim.read_across_shots(km.array([km.q(i) for i in range(12, 24)]))
        got = sum(out[i].astype(np.int64) << i for i in range(DEG))
        exp = np.array([G.inv(int(v)) if v else 0 for v in xs])
        log.info("%s: toffoli=%d qubits=%d inverso correcto=%s", modo, c1.operation_statistics().num_toffoli_like, c1.num_qubits, bool((got == exp).all()))
    # ida y borrado
    b = km.CircuitBuilder(); x = b.create_quantum_register(DEG, name='x'); t = b.create_quantum_register(DEG, name='t')
    sc = init_kinv(b, gf, x, t); del_kinv(b, gf, x, t, sc); c2 = b.finish_circuit()
    sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=1); sim.use_same_registers_as(c2)
    sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(xs)); sim.do(c2)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(c2.num_qubits)]))
    log.info("init+del: toffoli=%d qubits=%d  x restaurado=%s resto limpio=%s fase=%d", c2.operation_statistics().num_toffoli_like, c2.num_qubits,
             bool((out[:12] == bits(xs)).all()), not out[12:].any(), int(sim.read_phase_flipped_across_shots().sum()))
