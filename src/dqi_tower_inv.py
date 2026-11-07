#!/usr/bin/env python3
"""Inversion en GF(2^12) por torre GF(2^6)[y]/(y^2+y+nu): 108 Toffoli (6 mult. Karatsuba de 18 AND), desc. libre por MBU.

 a = a0 + a1*y   (a0,a1 en GF(2^6));  N = a0^2 + a0*a1 + nu*a1^2;  a^-1 = N^-1 * ((a0+a1) + a1*y)
 N^-1 = N^62 (cadena 1,2,3,5: 3 mult.) ; resto lineal (cuadrados, constantes, cambio de base: solo CNOT).
Uncomputo: cada producto Karatsuba se borra midiendo el registro (HMR, base X) y corrigiendo la fase con CZ condicionados
(0 Toffoli).  API: tower_inverse(b, srcs12, w12) calcula w12 ^= a^-1 dejando basura (regs) y devuelve un objeto con .undo().
Logs: logging 'dqi_tower'.
"""
from __future__ import annotations
import sys, logging
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import kickmix as km
import dqi_bm_model as G
from dqi_kmul import _kar

log = logging.getLogger("dqi_tower")
D12, D6 = 12, 6

# ---------- algebra clasica de la torre ----------
mul, EXP = G.mul, G.EXP
g = int(EXP[65]); assert g != 1
B = [1]
for _ in range(5): B.append(mul(B[-1], g))
Y = next(y for y in range(2, 4096) if G.mul(y, y) ^ y in set()) if False else None


def _pow(x, e):
    r = 1
    while e:
        if e & 1: r = mul(r, x)
        x = mul(x, x); e >>= 1
    return r


Y = next(y for y in range(2, 4096) if _pow(y, 64) == (y ^ 1))          # y^64 = y+1  =>  y no esta en GF(2^6), y^2+y en GF(2^6)
NU = mul(Y, Y) ^ Y
assert _pow(NU, 64) == NU


def _gauss_inv(cols):
    """cols: lista de n enteros (columnas) de una matriz GF(2) n x n -> columnas de la inversa."""
    n = len(cols)
    rows = [[(cols[c] >> r) & 1 for c in range(n)] + [1 if i == r else 0 for i in range(n)] for r in range(n)]
    for c in range(n):
        p = next(r for r in range(c, n) if rows[r][c])
        rows[c], rows[p] = rows[p], rows[c]
        for r in range(n):
            if r != c and rows[r][c]:
                rows[r] = [x ^ y for x, y in zip(rows[r], rows[c])]
    inv_cols = []
    for c in range(n):
        v = 0
        for r in range(n):
            if rows[r][n + c]: v |= 1 << r
        inv_cols.append(v)
    return inv_cols


WCOLS = B + [mul(b_, Y) for b_ in B]          # coordenadas (a0[0..5], a1[0..5]) -> valor de 12 bits
CCOLS = _gauss_inv(WCOLS)                     # valor de 12 bits -> coordenadas (columna k = coords de 1<<k)


def coords(v):
    out = 0
    for k in range(D12):
        if (v >> k) & 1: out ^= CCOLS[k]
    return out


def value(c):
    out = 0
    for k in range(D12):
        if (c >> k) & 1: out ^= WCOLS[k]
    return out


def _mat6(f):
    """columnas (6 coords) de la aplicacion lineal f sobre GF(2^6) dada sobre valores de 12 bits."""
    return [coords(f(B[i])) & 63 for i in range(6)]


SQ = _mat6(lambda v: mul(v, v))
SQ2 = _mat6(lambda v: _pow(v, 4))
NUSQ = _mat6(lambda v: mul(NU, mul(v, v)))
RED = [coords(_pow(g, k)) & 63 for k in range(11)]       # g^k en coordenadas


def _plan6():
    terms = _kar([1 << i for i in range(6)], [1 << i for i in range(6)])
    merged = {}
    for fx, fy, m in terms:
        merged[(fx, fy)] = merged.get((fx, fy), 0) ^ m
    plan = []
    for (fx, fy), m in merged.items():
        tm = 0
        for k in range(11):
            if (m >> k) & 1: tm ^= RED[k]
        if tm: plan.append((fx, fy, tm))
    return plan


PLAN6 = _plan6()
assert len(PLAN6) == 18, len(PLAN6)


# ---------- primitivas de circuito ----------
def _lin(b, cols, src, dst):
    """dst ^= M * src, con M dada por columnas (src indexa columnas)."""
    for i in range(len(src)):
        for o in range(len(dst)):
            if (cols[i] >> o) & 1:
                b.cx(src[i], dst[o])


def _form(b, form, reg, tmp):
    bits = [i for i in range(6) if (form >> i) & 1]
    if len(bits) == 1:
        return reg[bits[0]], False
    for i in bits: b.cx(reg[i], tmp)
    return tmp, True


def _unform(b, form, reg, tmp):
    for i in range(6):
        if (form >> i) & 1: b.cx(reg[i], tmp)


def mul6_init(b, x, y, target):
    tx = b.alloc_qubits(1)[0]; ty = b.alloc_qubits(1)[0]; t = b.alloc_qubits(1)[0]
    for fx, fy, tm in PLAN6:
        qx, ux = _form(b, fx, x, tx); qy, uy = _form(b, fy, y, ty)
        b.init_and(qx, qy, t)
        for j in range(6):
            if (tm >> j) & 1: b.cx(t, target[j])
        b.del_and(qx, qy, t)
        if ux: _unform(b, fx, x, tx)
        if uy: _unform(b, fy, y, ty)
    b.free(tx); b.free(ty); b.free(t)


def mul6_del(b, x, y, target):
    """target == x*y  ->  0, con medicion X y fase corregida (0 Toffoli)."""
    m = b.alloc_bits(6)
    b.hmr(target, m)
    tx = b.alloc_qubits(1)[0]; ty = b.alloc_qubits(1)[0]
    for fx, fy, tm in PLAN6:
        qx, ux = _form(b, fx, x, tx); qy, uy = _form(b, fy, y, ty)
        for j in range(6):
            if (tm >> j) & 1:
                b.push_condition(m[j]); b.cz(qx, qy); b.pop_condition()
        if ux: _unform(b, fx, x, tx)
        if uy: _unform(b, fy, y, ty)
    b.free(tx); b.free(ty)


class TowerInv:
    """Calcula w (12 bits, valor original) = a^-1 donde a se da como 12 qubits 'ya en coordenadas de torre' (a0=a[0:6], a1=a[6:12])."""

    def __init__(self, b, a, w):
        self.b, self.a, self.w = b, a, w
        self.regs = {}

    def _alloc(self, name, n=6):
        self.regs[name] = self.b.alloc_qubits(n)
        return self.regs[name]

    def forward(self):
        b, a = self.b, self.a
        a0, a1 = a[0:6], a[6:12]
        Pn = self._alloc('Pn'); mul6_init(b, a0, a1, Pn)
        N = self._alloc('N')
        _lin(b, [1 << i for i in range(6)], Pn, N)
        _lin(b, SQ, a0, N); _lin(b, NUSQ, a1, N)
        q = self._alloc('q'); b2 = self._alloc('b2')
        _lin(b, SQ, N, q); mul6_init(b, q, N, b2); _lin(b, SQ, N, q)
        b3 = self._alloc('b3'); _lin(b, SQ, b2, q); mul6_init(b, q, N, b3); _lin(b, SQ, b2, q)
        b5 = self._alloc('b5'); _lin(b, SQ2, b3, q); mul6_init(b, q, b2, b5); _lin(b, SQ2, b3, q)
        r = self._alloc('r'); s = self._alloc('s')
        _lin(b, SQ, b5, r)                                          # r = N^-1
        _lin(b, [1 << i for i in range(6)], a0, s); _lin(b, [1 << i for i in range(6)], a1, s)
        o0 = self._alloc('o0'); o1 = self._alloc('o1')
        mul6_init(b, r, s, o0); mul6_init(b, r, a1, o1)
        # w = Phi^-1 (o0,o1): valor = sum coords * WCOLS
        for i in range(6):
            for o in range(D12):
                if (WCOLS[i] >> o) & 1: b.cx(o0[i], self.w[o])
                if (WCOLS[6 + i] >> o) & 1: b.cx(o1[i], self.w[o])

    def undo(self):
        b, a, R = self.b, self.a, self.regs
        a0, a1 = a[0:6], a[6:12]
        for i in range(6):
            for o in range(D12):
                if (WCOLS[i] >> o) & 1: b.cx(R['o0'][i], self.w[o])
                if (WCOLS[6 + i] >> o) & 1: b.cx(R['o1'][i], self.w[o])
        mul6_del(b, R['r'], a1, R['o1']); mul6_del(b, R['r'], R['s'], R['o0'])
        _lin(b, [1 << i for i in range(6)], a1, R['s']); _lin(b, [1 << i for i in range(6)], a0, R['s'])
        _lin(b, SQ, R['b5'], R['r'])
        q = R['q']
        _lin(b, SQ2, R['b3'], q); mul6_del(b, q, R['b2'], R['b5']); _lin(b, SQ2, R['b3'], q)
        _lin(b, SQ, R['b2'], q); mul6_del(b, q, R['N'], R['b3']); _lin(b, SQ, R['b2'], q)
        _lin(b, SQ, R['N'], q); mul6_del(b, q, R['N'], R['b2']); _lin(b, SQ, R['N'], q)
        _lin(b, NUSQ, a1, R['N']); _lin(b, SQ, a0, R['N']); _lin(b, [1 << i for i in range(6)], R['Pn'], R['N'])
        mul6_del(b, a0, a1, R['Pn'])
        for v in R.values(): b.free(v)
        self.regs = {}


def coords_cols_from_value_sources():
    """Matriz 12x12 valor->coordenadas (columna k = coords de 1<<k) para cargar a en coordenadas desde bits de valor."""
    return CCOLS


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
    log.info("g=%d Y=%d NU=%d  ANDs mult6=%d", g, Y, NU, len(PLAN6))
    # comprobacion algebraica clasica de la formula
    import random
    for v in [0, 1, 2, 77, 4095] + [random.randrange(1, 4096) for _ in range(200)]:
        c = coords(v); a0, a1 = c & 63, c >> 6
        assert value(c) == v
    # prueba del circuito completo sobre todos los valores de 12 bits
    Bn = 4096
    b = km.CircuitBuilder()
    a = b.create_quantum_register(12, name='a')       # valor original
    w = b.create_quantum_register(12, name='w')
    ac = b.alloc_qubits(12)
    for k in range(12):
        for o in range(12):
            if (CCOLS[k] >> o) & 1: b.cx(a[k], ac[o])
    T = TowerInv(b, ac, w); T.forward()
    st1 = b.finish_circuit().operation_statistics().num_toffoli_like if False else None
    c1 = None
    # (se vuelve a construir con undo para medir limpieza)
    b2 = km.CircuitBuilder()
    a_ = b2.create_quantum_register(12, name='a'); w_ = b2.create_quantum_register(12, name='w')
    ac2 = b2.alloc_qubits(12)
    for k in range(12):
        for o in range(12):
            if (CCOLS[k] >> o) & 1: b2.cx(a_[k], ac2[o])
    T2 = TowerInv(b2, ac2, w_); T2.forward()
    cf = b2.finish_circuit()
    log.info("forward: toffoli=%d qubits=%d", cf.operation_statistics().num_toffoli_like, cf.num_qubits)
    # forward: w debe ser a^-1
    vals = np.arange(Bn)
    def bits(v): return ((v[None, :] >> np.arange(12)[:, None]) & 1) == 1
    def run(circ, nb=Bn):
        sim = km.Simulator(batch_size=nb, debug_print=False, counting_operations=True, seed=1); sim.use_same_registers_as(circ)
        sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(vals))
        sim.do(circ)
        return sim, sim.read_across_shots(km.array([km.q(i) for i in range(circ.num_qubits)]))
    sim, out = run(cf)
    got = np.zeros(Bn, dtype=np.int64)
    for k in range(12): got |= out[12 + k].astype(np.int64) << k
    exp = np.array([0 if v == 0 else G.inv(int(v)) for v in vals])
    log.info("inverso correcto en %d/%d valores", int((got == exp).sum()), Bn)
    # forward + undo
    b3 = km.CircuitBuilder()
    a3 = b3.create_quantum_register(12, name='a'); w3 = b3.create_quantum_register(12, name='w'); keep = b3.create_quantum_register(12, name='keep')
    ac3 = b3.alloc_qubits(12)
    for k in range(12):
        for o in range(12):
            if (CCOLS[k] >> o) & 1: b3.cx(a3[k], ac3[o])
    T3 = TowerInv(b3, ac3, w3); T3.forward()
    # copiar w a un registro de salida, luego undo
    for k in range(12): b3.cx(w3[k], keep[k])
    T3.undo()
    for k in range(12):
        for o in range(12):
            if (CCOLS[k] >> o) & 1: b3.cx(a3[k], ac3[o])
    c3 = b3.finish_circuit()
    sim3, out3 = run(c3)
    nq = c3.num_qubits
    # keep son los ultimos 12 qubits asignados; todo lo demas (salvo a y keep) debe ser 0
    ids = list(range(nq))
    kept = np.zeros(Bn, dtype=np.int64)
    for k in range(12): kept |= out3[24 + k].astype(np.int64) << k
    sucio = out3[12:24].any(axis=0) | out3[36:].any(axis=0)
    log.info("forward+undo: keep correcto=%d/%d  basura (w,ancillas) en %d tiros  fase volteada=%d  toffoli=%d",
             int((kept == exp).sum()), Bn, int(sucio.sum()), int(sim3.read_phase_flipped_across_shots().sum()),
             c3.operation_statistics().num_toffoli_like)
