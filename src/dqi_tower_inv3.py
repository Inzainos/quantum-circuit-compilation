#!/usr/bin/env python3
"""Inversion GF(2^12) por torre (75 Toffoli, igual que dqi_tower_inv2) con MUCHOS menos qubits vivos.

Arquitectura "sin copias": cada capa se escribe directo en su destino y se cierra en cuanto deja de hacer falta.
  * N se calcula directo (producto + terminos lineales), sin registro Pn intermedio.
  * Los cambios de base (P2C, C2P) se hacen EN EL SITIO con redes de CX (0 Toffoli), sin registros Nc ni r.
  * s = a0 ^ a1 se forma temporalmente sobre a0 (a0 ^= a1 ... a0 ^= a1), sin registro s.
  * Los productos o0 = r*s y o1 = r*a1 se acumulan directo en la salida w (via WCOLS); no existen o0/o1.
    La salida se limpia con UNA medicion X de w y fase corregida (0 Toffoli).
Condicion: w (y rc interno) deben estar en 0 al llamar a forward() (todos los usos del decodificador asignan registros frescos).

Qubits vivos de la torre: 18 (N 6, N' 3, r' 3, rc 6) frente a 81 en dqi_tower_inv2.   Logs: logging 'dqi_tower3'.
"""
from __future__ import annotations
import sys, logging
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import kickmix as km
import dqi_bm_model as G
import dqi_tower_inv as T1
import dqi_tower_inv2 as T2

log = logging.getLogger("dqi_tower3")


# ---------- transformaciones lineales en el sitio (solo CX) ----------
def inplace_ops(cols, n):
    """Lista de pares (control, objetivo) tal que aplicarlos EN ORDEN deja reg <- M reg, con M[o][i] = (cols[i]>>o)&1."""
    A = [[(cols[i] >> o) & 1 for i in range(n)] for o in range(n)]   # filas = bits de salida
    ops = []                                                         # operaciones de fila (t ^= c) que reducen A a I

    def row_xor(t, c):
        A[t] = [x ^ y for x, y in zip(A[t], A[c])]
        ops.append((c, t))

    for col in range(n):
        piv = next((r for r in range(col, n) if A[r][col]), None)
        assert piv is not None, "matriz singular"
        if piv != col:
            row_xor(col, piv)            # A[col] ^= A[piv] ; garantiza A[col][col] = 1
        for r in range(n):
            if r != col and A[r][col]:
                row_xor(r, col)
    assert all(A[o][i] == (1 if o == i else 0) for o in range(n) for i in range(n))
    return list(reversed(ops))           # A = E1 E2 ... Ek  ->  se aplican Ek primero


def apply_inplace(b, ops, reg, inverse=False):
    seq = reversed(ops) if inverse else ops
    for c, t in seq:
        b.cx(reg[c], reg[t])


OPS_P2C = inplace_ops(T2.P2C, 6)
OPS_C2P = inplace_ops(T2.C2P, 6)


def _xor_in(b, src, dst):
    for i in range(len(src)):
        b.cx(src[i], dst[i])


def _mulN_to(b, plan, n, x, y, target_masks, target):
    """target ^= producto segun plan, con mascaras de salida ya mapeadas (lista de (fx, fy, mask_bits_de_target))."""
    tx, ty, t = b.alloc_qubits(1)[0], b.alloc_qubits(1)[0], b.alloc_qubits(1)[0]
    for fx, fy, tm in target_masks:
        qx, ux = T2._form(b, fx, x, n, tx); qy, uy = T2._form(b, fy, y, n, ty)
        b.init_and(qx, qy, t)
        for j in range(len(target)):
            if (tm >> j) & 1: b.cx(t, target[j])
        b.del_and(qx, qy, t)
        if ux: T2._unform(b, fx, x, n, tx)
        if uy: T2._unform(b, fy, y, n, ty)
    b.free(tx); b.free(ty); b.free(t)


def _phase_terms(b, n, x, y, terms_with_bits, m):
    """Para cada termino (fx, fy, bits) aplica CZ(fx(x), fy(y)) condicionado a cada bit medido m[j], j en bits."""
    tx, ty = b.alloc_qubits(1)[0], b.alloc_qubits(1)[0]
    for fx, fy, bits in terms_with_bits:
        qx, ux = T2._form(b, fx, x, n, tx); qy, uy = T2._form(b, fy, y, n, ty)
        for j in bits:
            b.push_condition(m[j]); b.cz(qx, qy); b.pop_condition()
        if ux: T2._unform(b, fx, x, n, tx)
        if uy: T2._unform(b, fy, y, n, ty)
    b.free(tx); b.free(ty)


def _bits(mask):
    return [j for j in range(mask.bit_length()) if (mask >> j) & 1]


class Inner6:
    """y ^= x^-1, x en GF(64) (coords internas: a0 = x[0:3], a1 = x[3:6]); y 6 qubits en 0. Vivos: N(3) + r(3)."""

    def __init__(self, b, x, y):
        self.b, self.x, self.y, self.R = b, x, y, {}

    def forward(self):
        b, x, y = self.b, self.x, self.y
        a0, a1 = x[0:3], x[3:6]
        N = b.alloc_qubits(3)
        T2.mulN_init(b, T2.PLAN3, 3, a0, a1, N)
        T2._lin(b, T2.SQ8, a0, N); T2._lin(b, T2.NUSQ8, a1, N)
        r = b.alloc_qubits(3); T2.inv8_init(b, N, r)
        _xor_in(b, a1, a0)                                    # a0 = s
        T2.mulN_init(b, T2.PLAN3, 3, r, a0, y[0:3])
        T2.mulN_init(b, T2.PLAN3, 3, r, a1, y[3:6])
        _xor_in(b, a1, a0)                                    # a0 restaurado
        self.R = {'N': N, 'r': r}

    def undo(self):
        b, x, y, R = self.b, self.x, self.y, self.R
        a0, a1 = x[0:3], x[3:6]
        N, r = R['N'], R['r']
        _xor_in(b, a1, a0)
        T2.mulN_del(b, T2.PLAN3, 3, r, a1, y[3:6])
        T2.mulN_del(b, T2.PLAN3, 3, r, a0, y[0:3])
        _xor_in(b, a1, a0)
        T2.inv8_del(b, N, r)
        T2._lin(b, T2.NUSQ8, a1, N); T2._lin(b, T2.SQ8, a0, N)
        T2.mulN_del(b, T2.PLAN3, 3, a0, a1, N)
        b.free(N); b.free(r)
        self.R = {}


def _w_terms():
    """Terminos (fx, fy, mascara de 12 bits en w) de r*s -> o0 y r*a1 -> o1 mapeados por WCOLS."""
    out0, out1 = [], []
    for fx, fy, tm in T1.PLAN6:
        m0 = m1 = 0
        for j in range(6):
            if (tm >> j) & 1:
                m0 ^= T1.WCOLS[j]; m1 ^= T1.WCOLS[6 + j]
        if m0: out0.append((fx, fy, m0))
        if m1: out1.append((fx, fy, m1))
    return out0, out1


W0, W1 = _w_terms()


class TowerInv3:
    """w ^= a^-1 ; a en coords de torre (a0 = a[0:6], a1 = a[6:12]); w (12) debe estar en 0."""

    def __init__(self, b, a, w):
        self.b, self.a, self.w, self.R = b, a, w, {}

    def forward(self):
        b, a, w = self.b, self.a, self.w
        a0, a1 = a[0:6], a[6:12]
        N = b.alloc_qubits(6)
        T1.mul6_init(b, a0, a1, N)
        T2._lin(b, T1.SQ, a0, N); T2._lin(b, T1.NUSQ, a1, N)
        apply_inplace(b, OPS_P2C, N)                          # N en coords internas
        rc = b.alloc_qubits(6)
        self.inner = Inner6(b, N, rc); self.inner.forward()
        apply_inplace(b, OPS_C2P, rc)                         # rc = N^-1 en base g (ya es 'r')
        _xor_in(b, a1, a0)                                    # a0 = s
        _mulN_to(b, None, 6, rc, a0, W0, w)
        _mulN_to(b, None, 6, rc, a1, W1, w)
        _xor_in(b, a1, a0)
        self.R = {'N': N, 'rc': rc}

    def undo(self):
        b, a, w, R = self.b, self.a, self.w, self.R
        a0, a1 = a[0:6], a[6:12]
        N, rc = R['N'], R['rc']
        _xor_in(b, a1, a0)
        m = b.alloc_bits(12)
        b.hmr(w, m)
        _phase_terms(b, 6, rc, a0, [(fx, fy, _bits(mk)) for fx, fy, mk in W0], m)
        _phase_terms(b, 6, rc, a1, [(fx, fy, _bits(mk)) for fx, fy, mk in W1], m)
        _xor_in(b, a1, a0)
        apply_inplace(b, OPS_C2P, rc, inverse=True)
        self.inner.undo()
        apply_inplace(b, OPS_P2C, N, inverse=True)
        T2._lin(b, T1.NUSQ, a1, N); T2._lin(b, T1.SQ, a0, N)
        T1.mul6_del(b, a0, a1, N)
        b.free(N); b.free(rc)
        self.R = {}


OPS_V2C = inplace_ops(T1.CCOLS, 12)        # valor de 12 bits -> coordenadas de torre, EN EL SITIO


class ValueInv3:
    """w ^= a^-1 con a en representacion de valor (12 qubits). Sin registro auxiliar: cambia a coords EN EL SITIO
    mientras corre la torre y lo devuelve a valor entre forward() y undo() (solo CX, 0 Toffoli)."""

    def __init__(self, b, a_val, w):
        self.b, self.a, self.w = b, a_val, w

    def forward(self):
        b = self.b
        apply_inplace(b, OPS_V2C, self.a)
        self.T = TowerInv3(b, self.a, self.w); self.T.forward()
        apply_inplace(b, OPS_V2C, self.a, inverse=True)      # a vuelve a valor: el llamador lo puede usar
        return self

    def undo(self):
        b = self.b
        apply_inplace(b, OPS_V2C, self.a)
        self.T.undo()
        apply_inplace(b, OPS_V2C, self.a, inverse=True)


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
    Bn = 4096
    vals = np.arange(Bn)

    def bits(v): return ((v[None, :] >> np.arange(12)[:, None]) & 1) == 1

    b = km.CircuitBuilder()
    a = b.create_quantum_register(12, name='a'); w = b.create_quantum_register(12, name='w')
    keep = b.create_quantum_register(12, name='keep')
    ac = b.alloc_qubits(12)
    for k in range(12):
        for o in range(12):
            if (T1.CCOLS[k] >> o) & 1: b.cx(a[k], ac[o])
    TI = TowerInv3(b, ac, w); TI.forward()
    for k in range(12): b.cx(w[k], keep[k])
    TI.undo()
    for k in range(12):
        for o in range(12):
            if (T1.CCOLS[k] >> o) & 1: b.cx(a[k], ac[o])
    c = b.finish_circuit()
    sim = km.Simulator(batch_size=Bn, debug_print=False, counting_operations=True, seed=1); sim.use_same_registers_as(c)
    sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(vals)); sim.do(c)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
    kept = np.zeros(Bn, dtype=np.int64)
    for k in range(12): kept |= out[24 + k].astype(np.int64) << k
    exp = np.array([0 if v == 0 else G.inv(int(v)) for v in vals])
    sucio = out[12:24].any(axis=0) | out[36:].any(axis=0)
    log.info("inverso correcto %d/%d ; basura en %d tiros ; fase volteada=%d ; toffoli(fwd+undo)=%d (esperado 75) qubits=%d (aux: %d)",
             int((kept == exp).sum()), Bn, int(sucio.sum()), int(sim.read_phase_flipped_across_shots().sum()),
             c.operation_statistics().num_toffoli_like, c.num_qubits, c.num_qubits - 48)
