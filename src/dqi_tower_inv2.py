#!/usr/bin/env python3
"""Inversion GF(2^12) por torre de dos niveles GF(2^12)/GF(2^6)/GF(2^3): 75 Toffoli (vs 108 de un nivel).

 Nivel 12->6: a = a0 + a1 y,  N = a0^2 + a0 a1 + nu a1^2 (GF(2^6)),  a^-1 = N^-1 ((a0+a1) + a1 y)     [18 + inv6 + 36 AND]
 Nivel 6->3 : igual sobre GF(2^3) con nu' ;  inv3 es una funcion cuadratica de 3 bits (3 AND, sin mult.)   [6 + 3 + 12 = 21 AND]
Todo uncomputo libre (HMR + correccion de fase condicionada).  Logs: logging 'dqi_tower2'.
"""
from __future__ import annotations
import sys, logging
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import kickmix as km
import dqi_bm_model as G
import dqi_tower_inv as T1
from dqi_kmul import _kar

log = logging.getLogger("dqi_tower2")
mul = G.mul
pw = T1._pow

# ---------- nivel interno: GF(8) dentro de GF(64) ----------
g8 = pw(T1.g, 9)
C8 = [1, g8, mul(g8, g8)]
SUB64 = [v for v in range(1, 4096) if pw(v, 64) == v]           # elementos no nulos de GF(64) (valores de 12 bits)
assert len(SUB64) == 63
Y8 = next(y for y in SUB64 if pw(y, 8) == (y ^ 1))             # y^8 = y+1 -> y en GF(64) \ GF(8), y^2+y en GF(8)
NU8 = mul(Y8, Y8) ^ Y8
assert pw(NU8, 8) == NU8
B2 = C8 + [mul(c, Y8) for c in C8]                              # nueva base de GF(64) sobre GF(2)
VAL2COORD = {}
for cmb in range(64):
    v = 0
    for i in range(6):
        if (cmb >> i) & 1: v ^= B2[i]
    VAL2COORD[v] = cmb
assert len(VAL2COORD) == 64 and all(v in VAL2COORD for v in SUB64)


def val2(c):
    v = 0
    for i in range(6):
        if (c >> i) & 1: v ^= B2[i]
    return v


def c8(v):      # coords (3 bits) de un elemento de GF(8) (valor de 12 bits)
    return VAL2COORD[v] & 7


# conversion de coords g-base (T1.B) a coords de la base interna y viceversa (6x6, columnas)
P2C = [VAL2COORD[T1.B[i]] for i in range(6)]
C2P = [0] * 6
for i in range(6):
    v = B2[i]; cc = 0
    for k in range(6):
        pass
# C2P columna i = coords en base g de B2[i]: se resuelve por busqueda
GCOORD = {}
for cmb in range(64):
    v = 0
    for i in range(6):
        if (cmb >> i) & 1: v ^= T1.B[i]
    GCOORD[v] = cmb
C2P = [GCOORD[B2[i]] for i in range(6)]

SQ8 = [c8(mul(C8[i], C8[i])) for i in range(3)]
NUSQ8 = [c8(mul(NU8, mul(C8[i], C8[i]))) for i in range(3)]
RED8 = [c8(pw(g8, k)) for k in range(5)]


def _plan3():
    from dqi_kmul import _kar3
    terms = _kar3([1, 2, 4], [1, 2, 4])
    plan = []
    for fx, fy, m in terms:
        tm = 0
        for k in range(5):
            if (m >> k) & 1: tm ^= RED8[k]
        if tm: plan.append((fx, fy, tm))
    return plan


PLAN3 = _plan3()
assert len(PLAN3) == 6

# inv en GF(8): ANF de cada bit de salida en coords
INV8 = {}
for x in range(8):
    val = 0
    for i in range(3):
        if (x >> i) & 1: val ^= C8[i]
    INV8[x] = 0 if x == 0 else c8(pw(val, 6))


def _anf(o):
    f = [(INV8[x] >> o) & 1 for x in range(8)]
    a = f[:]
    for i in range(3):
        for x in range(8):
            if (x >> i) & 1: a[x] ^= a[x ^ (1 << i)]
    return a                    # a[mask] = coeficiente del monomio prod_{i in mask} x_i


ANF = [_anf(o) for o in range(3)]
assert all(ANF[o][0] == 0 and ANF[o][7] == 0 for o in range(3))


def _form(b, form, reg, n, tmp):
    bits = [i for i in range(n) if (form >> i) & 1]
    if len(bits) == 1: return reg[bits[0]], False
    for i in bits: b.cx(reg[i], tmp)
    return tmp, True


def _unform(b, form, reg, n, tmp):
    for i in range(n):
        if (form >> i) & 1: b.cx(reg[i], tmp)


def mulN_init(b, plan, n, x, y, target):
    tx, ty, t = b.alloc_qubits(1)[0], b.alloc_qubits(1)[0], b.alloc_qubits(1)[0]
    for fx, fy, tm in plan:
        qx, ux = _form(b, fx, x, n, tx); qy, uy = _form(b, fy, y, n, ty)
        b.init_and(qx, qy, t)
        for j in range(n):
            if (tm >> j) & 1: b.cx(t, target[j])
        b.del_and(qx, qy, t)
        if ux: _unform(b, fx, x, n, tx)
        if uy: _unform(b, fy, y, n, ty)
    b.free(tx); b.free(ty); b.free(t)


def mulN_del(b, plan, n, x, y, target):
    m = b.alloc_bits(n)
    b.hmr(target, m)
    tx, ty = b.alloc_qubits(1)[0], b.alloc_qubits(1)[0]
    for fx, fy, tm in plan:
        qx, ux = _form(b, fx, x, n, tx); qy, uy = _form(b, fy, y, n, ty)
        for j in range(n):
            if (tm >> j) & 1:
                b.push_condition(m[j]); b.cz(qx, qy); b.pop_condition()
        if ux: _unform(b, fx, x, n, tx)
        if uy: _unform(b, fy, y, n, ty)
    b.free(tx); b.free(ty)


def inv8_init(b, x, target):
    """target ^= x^-1 en GF(8) (coords); 3 AND."""
    for o in range(3):
        for i in range(3):
            if ANF[o][1 << i]: b.cx(x[i], target[o])
    for (i, j) in ((0, 1), (0, 2), (1, 2)):
        mk = (1 << i) | (1 << j)
        outs = [o for o in range(3) if ANF[o][mk]]
        if outs:
            t = b.alloc_qubits(1)[0]
            b.init_and(x[i], x[j], t)
            for o in outs: b.cx(t, target[o])
            b.del_and(x[i], x[j], t); b.free(t)


def inv8_del(b, x, target):
    m = b.alloc_bits(3)
    b.hmr(target, m)
    for o in range(3):
        for i in range(3):
            if ANF[o][1 << i]:
                b.push_condition(m[o]); b.z(x[i]); b.pop_condition()
    for (i, j) in ((0, 1), (0, 2), (1, 2)):
        mk = (1 << i) | (1 << j)
        for o in range(3):
            if ANF[o][mk]:
                b.push_condition(m[o]); b.cz(x[i], x[j]); b.pop_condition()


def _lin(b, cols, src, dst):
    for i in range(len(src)):
        for o in range(len(dst)):
            if (cols[i] >> o) & 1: b.cx(src[i], dst[o])


ID3 = [1, 2, 4]


class Inv6:
    """y ^= x^-1 para x en GF(64) dado en coords internas (x[0:3] + x[3:6] y')."""

    def __init__(self, b, x, y):
        self.b, self.x, self.y, self.R = b, x, y, {}

    def forward(self):
        b, x = self.b, self.x
        a0, a1 = x[0:3], x[3:6]
        R = self.R
        R['Pn'] = b.alloc_qubits(3); mulN_init(b, PLAN3, 3, a0, a1, R['Pn'])
        R['N'] = b.alloc_qubits(3)
        _lin(b, ID3, R['Pn'], R['N']); _lin(b, SQ8, a0, R['N']); _lin(b, NUSQ8, a1, R['N'])
        R['r'] = b.alloc_qubits(3); inv8_init(b, R['N'], R['r'])
        R['s'] = b.alloc_qubits(3); _lin(b, ID3, a0, R['s']); _lin(b, ID3, a1, R['s'])
        R['o0'] = b.alloc_qubits(3); R['o1'] = b.alloc_qubits(3)
        mulN_init(b, PLAN3, 3, R['r'], R['s'], R['o0']); mulN_init(b, PLAN3, 3, R['r'], a1, R['o1'])
        for i in range(3):
            b.cx(R['o0'][i], self.y[i]); b.cx(R['o1'][i], self.y[3 + i])

    def undo(self):
        b, x, R = self.b, self.x, self.R
        a0, a1 = x[0:3], x[3:6]
        for i in range(3):
            b.cx(R['o0'][i], self.y[i]); b.cx(R['o1'][i], self.y[3 + i])
        mulN_del(b, PLAN3, 3, R['r'], a1, R['o1']); mulN_del(b, PLAN3, 3, R['r'], R['s'], R['o0'])
        _lin(b, ID3, a1, R['s']); _lin(b, ID3, a0, R['s'])
        inv8_del(b, R['N'], R['r'])
        _lin(b, NUSQ8, a1, R['N']); _lin(b, SQ8, a0, R['N']); _lin(b, ID3, R['Pn'], R['N'])
        mulN_del(b, PLAN3, 3, a0, a1, R['Pn'])
        for v in R.values(): b.free(v)
        self.R = {}


class TowerInv2:
    """w ^= a^-1 ; a en coords de torre nivel 1 (a0=a[0:6], a1=a[6:12]) como en dqi_tower_inv.TowerInv."""

    def __init__(self, b, a, w):
        self.b, self.a, self.w, self.R = b, a, w, {}

    def forward(self):
        b, a, R = self.b, self.a, self.R
        a0, a1 = a[0:6], a[6:12]
        ID6 = [1 << i for i in range(6)]
        P6 = T1.PLAN6
        R['Pn'] = b.alloc_qubits(6); T1.mul6_init(b, a0, a1, R['Pn'])
        R['N'] = b.alloc_qubits(6)
        _lin(b, ID6, R['Pn'], R['N']); _lin(b, T1.SQ, a0, R['N']); _lin(b, T1.NUSQ, a1, R['N'])
        R['Nc'] = b.alloc_qubits(6); _lin(b, P2C, R['N'], R['Nc'])           # N en coords internas
        R['rc'] = b.alloc_qubits(6); self.inner = Inv6(b, R['Nc'], R['rc']); self.inner.forward()
        R['r'] = b.alloc_qubits(6); _lin(b, C2P, R['rc'], R['r'])            # N^-1 en base g
        R['s'] = b.alloc_qubits(6); _lin(b, ID6, a0, R['s']); _lin(b, ID6, a1, R['s'])
        R['o0'] = b.alloc_qubits(6); R['o1'] = b.alloc_qubits(6)
        T1.mul6_init(b, R['r'], R['s'], R['o0']); T1.mul6_init(b, R['r'], a1, R['o1'])
        for i in range(6):
            for o in range(12):
                if (T1.WCOLS[i] >> o) & 1: b.cx(R['o0'][i], self.w[o])
                if (T1.WCOLS[6 + i] >> o) & 1: b.cx(R['o1'][i], self.w[o])

    def undo(self):
        b, a, R = self.b, self.a, self.R
        a0, a1 = a[0:6], a[6:12]
        ID6 = [1 << i for i in range(6)]
        for i in range(6):
            for o in range(12):
                if (T1.WCOLS[i] >> o) & 1: b.cx(R['o0'][i], self.w[o])
                if (T1.WCOLS[6 + i] >> o) & 1: b.cx(R['o1'][i], self.w[o])
        T1.mul6_del(b, R['r'], a1, R['o1']); T1.mul6_del(b, R['r'], R['s'], R['o0'])
        _lin(b, ID6, a1, R['s']); _lin(b, ID6, a0, R['s'])
        _lin(b, C2P, R['rc'], R['r'])
        self.inner.undo()
        _lin(b, P2C, R['N'], R['Nc'])
        _lin(b, T1.NUSQ, a1, R['N']); _lin(b, T1.SQ, a0, R['N']); _lin(b, ID6, R['Pn'], R['N'])
        T1.mul6_del(b, a0, a1, R['Pn'])
        for v in R.values(): b.free(v)
        self.R = {}


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
    a = b.create_quantum_register(12, name='a'); w = b.create_quantum_register(12, name='w'); keep = b.create_quantum_register(12, name='keep')
    ac = b.alloc_qubits(12)
    for k in range(12):
        for o in range(12):
            if (T1.CCOLS[k] >> o) & 1: b.cx(a[k], ac[o])
    TI = TowerInv2(b, ac, w); TI.forward()
    n_fwd = b.finish_circuit().operation_statistics().num_toffoli_like if False else None
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
    log.info("inverso correcto %d/%d ; basura en %d tiros ; fase volteada=%d ; toffoli(fwd+undo)=%d (esperado 75) qubits=%d",
             int((kept == exp).sum()), Bn, int(sucio.sum()), int(sim.read_phase_flipped_across_shots().sum()),
             c.operation_statistics().num_toffoli_like, c.num_qubits)


class ValueInv:
    """w ^= a^-1 con a en representacion original (12 qubits de valor). Calcula coords en un registro auxiliar."""

    def __init__(self, b, a_val, w):
        self.b, self.a, self.w = b, a_val, w

    def forward(self):
        b = self.b
        self.ac = b.alloc_qubits(12)
        for k in range(12):
            for o in range(12):
                if (T1.CCOLS[k] >> o) & 1: b.cx(self.a[k], self.ac[o])
        self.T = TowerInv2(b, self.ac, self.w); self.T.forward()
        return self

    def undo(self):
        b = self.b
        self.T.undo()
        for k in range(12):
            for o in range(12):
                if (T1.CCOLS[k] >> o) & 1: b.cx(self.a[k], self.ac[o])
        b.free(self.ac)
