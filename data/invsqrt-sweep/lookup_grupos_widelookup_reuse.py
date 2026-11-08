"""Prototipo WideLookup dividido (split): dos lookups ordenados.

Tubería 1: C2 (28 bits). Tubería 2: B|S (56 bits). V REUSA los 28 qubits limpios de regC2 (tras del_lookup) + 10 nuevos. Se libera C2
tras el MAC 1 (bandera: del_lookup), bajando el Q pico durante
el MAC 2. Basado en WideLookup b=6.

Basado en full15 (Horner, Q=211, ~716k). En vez de tres lookups
de 28 bits (B, S, C2) con la misma dirección de 9 bits (~510 T
cada uno, ~1,530 total), se hace UN solo lookup de 84 bits de
salida con la misma dirección (~510 T). Ahorro ~1,020 Toffolis,
costo +56 qubits (registro de 84 bits en vez de reusar uno de 28).

Empaquetado: entrada = (B << 56) | (S << 28) | C2.
  regW[0:28]  = C2, regW[28:56] = S, regW[56:84] = B.

Estimado (sin medir): Q~267, C~2,372, Q·C ~633k.

Uso:
  python lookup_grupos_widelookup.py [--tiros N] [--xs 1,2,3]
"""
import argparse
import os
import sys

import numpy as np
import kickmix as km

sys.path.insert(0, "/home/hatch/workspace/qcc-zip-final/src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from invsqrt_logshift2 import _nor

N_X = 22
N_MANT = 18
N_SEG = int(os.environ.get("BSEG", "8"))
N_T = N_MANT - N_SEG
N_VAL = 28
N_SHIFT = 10
N_WIDE = 3 * N_VAL  # 84 bits: B|S|C2


def tablas():
    nseg = 1 << N_SEG
    inv = 1.0 / np.sqrt(2.0)

    def a_u(v):
        return min(int(round(v * (1 << N_VAL))), (1 << N_VAL) - 1)
    if os.environ.get("MINIMAX", "") == "1":
        # Minimax/Chebyshev grado 2 por segmento (ver minimax_tablas.py).
        from numpy.polynomial import chebyshev as _C
        base, slope, curv = [], [], []
        for seg in range(nseg):
            e = 1.0 + seg / nseg
            w = 1.0 / nseg
            xs = np.linspace(0.0, w, 400)
            ys = (e + xs) ** (-0.5)
            ch = _C.Chebyshev.fit(xs, ys, 2, domain=[0.0, w])
            p = ch.convert(kind=np.polynomial.Polynomial)
            c0, c1, c2 = float(p.coef[0]), float(p.coef[1]), float(p.coef[2])
            for mult in (1.0, inv):
                base.append(a_u(c0 * mult)); slope.append(a_u(-c1 * mult)); curv.append(a_u(c2 * mult))
        return base, slope, curv
    edges = 1.0 + np.arange(nseg) / nseg
    base_f = edges ** (-0.5)
    slope_f = 0.5 * edges ** (-1.5)
    curv_f = 0.375 * edges ** (-2.5)
    base_e = [a_u(v) for v in base_f]
    slope_e = [a_u(v) for v in slope_f]
    curv_e = [a_u(v) for v in curv_f]
    base_o = [a_u(v * inv) for v in base_f]
    slope_o = [a_u(v * inv) for v in slope_f]
    curv_o = [a_u(v * inv) for v in curv_f]
    base, slope, curv = [], [], []
    for seg in range(nseg):
        base.append(base_e[seg]); slope.append(slope_e[seg]); curv.append(curv_e[seg])
        base.append(base_o[seg]); slope.append(slope_o[seg]); curv.append(curv_o[seg])
    return base, slope, curv


def tabla_c2(base, slope, curv):
    return list(curv)


def tabla_bs(base, slope, curv):
    """Tabla de 56 bits: (B << 28) | S."""
    return [(b << N_VAL) | s for b, s in zip(base, slope)]


def normalizar(b, x, sb, coef):
    w = len(x)
    for bit in (3, 2, 1, 0):
        r = 2 << bit
        top = x[w - r:w]
        _nor(b, False, top, sb[bit], coef)
        b.left_rotate(x, r, control=sb[bit])


def desnormalizar(b, x, sb):
    for bit in (0, 1, 2, 3):
        r = 2 << bit
        b.right_rotate(x, r, control=sb[bit])


def czpow(b, ctrl, tgt, ang):
    b.z_pow(tgt, ang)
    b.cx(ctrl, tgt)
    b.z_pow(tgt, -ang)
    b.cx(ctrl, tgt)


def mac_sub_trunc(b, A, tbits, V, scratch, shift):
    """MAC fusionado: V -= (A*t) >> shift, sin materializar el producto."""
    nA = len(A)
    nV = 28
    for i, tb in enumerate(tbits):
        j0 = max(0, shift - i)
        if j0 >= nA:
            continue
        m = nA - j0
        dst0 = i + j0 - shift
        w = nV - dst0
        for j in range(j0, nA):
            b.init_and(tb, A[j], scratch[j - j0])
        b.isub(km.array(list(scratch[:w])), target=V[dst0:nV])
        for j in range(j0, nA):
            b.del_and(tb, A[j], scratch[j - j0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiros", type=int, default=8)
    ap.add_argument("--xs", type=str, default=None,
                    help="lista de x separados por coma para probar")
    a = ap.parse_args()

    base, slope, curv = tablas()
    tab_c2 = tabla_c2(base, slope, curv)
    tab_bs = tabla_bs(base, slope, curv)
    if a.xs:
        xs = np.array([int(v) for v in a.xs.split(",")], dtype=np.int64)
    else:
        rng = np.random.default_rng(11)
        xs = rng.integers(1, 1 << N_X, size=a.tiros, dtype=np.int64)
    print("xs:", xs)
    print("leads:", [int(v).bit_length() - 1 for v in xs])

    b = km.CircuitBuilder()
    x = b.create_quantum_register(N_X, name="x")
    sb = b.create_quantum_register(4, name="sb")
    coef = b.create_quantum_register(14, name="coef")
    scratch = b.create_quantum_register(N_VAL, name="scratch")

    normalizar(b, x, sb, coef)

    comodin = x[N_X - 1]
    tmp_d = b.create_quantum_register(1, name="tmp_d")[0]
    tmp_a = b.create_quantum_register(1, name="tmp_a")[0]
    Hm = b.create_quantum_register(N_SEG, name="Hm")
    tm = b.create_quantum_register(N_T, name="tm")

    def mux_into(odd_q, even_q, out_q):
        b.cx(odd_q, tmp_d)
        b.cx(even_q, tmp_d)
        b.cx(even_q, out_q)
        b.init_and(comodin, tmp_d, tmp_a)
        b.cx(tmp_a, out_q)
        b.del_and(comodin, tmp_d, tmp_a)
        b.cx(odd_q, tmp_d)
        b.cx(even_q, tmp_d)

    for i in range(N_SEG):
        mux_into(x[N_X - 2 - i], x[N_X - 3 - i], Hm[i])
    for i in range(N_T):
        mux_into(x[N_X - 2 - N_SEG - i], x[N_X - 3 - N_SEG - i], tm[i])

    H = list(Hm[::-1])
    t = list(tm[::-1])
    addr = km.array([comodin] + list(H))

    # Tubería 1: lookup C2 (28 bits).
    regC2 = b.create_quantum_register(N_VAL, name="regC2")
    b.init_lookup(table=tab_c2, address=addr, target=regC2)
    C2 = list(regC2)
    # Tubería 2: lookup B|S (56 bits).
    regBS = b.create_quantum_register(2 * N_VAL, name="regBS")
    b.init_lookup(table=tab_bs, address=addr, target=regBS)
    # Slices: S = regBS[0:28], B = regBS[28:56].
    S = list(regBS[0:N_VAL])
    B = list(regBS[N_VAL:2 * N_VAL])

    # Horner: h = S - (C2*t)>>18 (positivo); V = B - (t*h)>>18.
    h = b.create_quantum_register(N_VAL, name="h")
    for i in range(N_VAL):
        b.cx(S[i], h[i])
    # Paso 2: h -= (C2*t)>>18.
    mac_sub_trunc(b, C2, t, h, scratch, N_MANT)
    # Bandera: C2 ya no se necesita, liberar su tubería.
    b.del_lookup(table=tab_c2, address=addr, target=regC2)
    # V = B, REUSANDO los 28 qubits limpios de regC2 + 10 nuevos.
    # (del_lookup ya los dejó en |0⟩; el builder no los reusa solo.)
    Vextra = b.create_quantum_register(N_SHIFT, name="Vextra")
    V = km.array(list(regC2) + list(Vextra))
    for i in range(N_VAL):
        b.cx(B[i], V[i])
    # Paso 3: V -= (t*h)>>18.
    mac_sub_trunc(b, h, t, V, scratch, N_MANT)

    # Ya no se necesitan B/S: limpiar la tubería 2.
    b.del_lookup(table=tab_bs, address=addr, target=regBS)

    # Barrel shift in-place sobre V (38 bits). Los 10 bits altos eran 0.
    for bit, r in ((3, 8), (2, 4), (1, 2), (0, 1)):
        ctrl = sb[bit]
        for j in range(len(V) - 1, r - 1, -1):
            b.cswap(ctrl, V[j - r], V[j])

    acc = b.create_quantum_register(1, name="acc")[0]
    b.x(acc)
    for i in range(len(V)):
        ang = 2.0 ** (i - N_VAL - 9)
        czpow(b, V[i], acc, ang)

    desnormalizar(b, x, sb)

    circ = b.finish_circuit()
    print(f"circuito: {circ.num_qubits} qubits")
    st = circ.operation_statistics()
    print("Toffoli-like:", st.num_toffoli_like, "T-like:", st.num_t_like)
    circ.to_file("/tmp/proto_widelookup_reuse_b%d.kmx" % N_SEG)
    print("escrito en /tmp/proto_widelookup_b%d.kmx" % N_SEG)
    import subprocess
    tot = 0
    for op in ["CCX", "CCZ", "CSWAP"]:
        r = subprocess.run(["grep", "-c", f"^{op}", "/tmp/proto_widelookup_reuse_b%d.kmx" % N_SEG],
                           capture_output=True, text=True)
        n = int(r.stdout.strip()); tot += n
        print(f"  {op}: {n}")
    print(f"  Toffoli-like total (grep .kmx): {tot}")

    sim = km.Simulator(batch_size=len(xs), debug_print=False,
                       counting_operations=True, seed=3)
    sim.use_same_registers_as(circ)
    bits_in = ((xs[None, :] >> np.arange(N_X)[:, None]) & 1) == 1
    sim.write_across_shots(km.array([km.q(i) for i in range(N_X)]), bits_in)
    sim.do(circ)
    outx = sim.read_across_shots(km.array([km.q(i) for i in range(N_X)]))
    x_ok = bool((outx == bits_in).all())
    print(f"\nx restaurada: {x_ok}")
    errs = []
    for t_idx in range(len(xs)):
        ph = sim.read_shot_phase(t_idx)
        xv = int(xs[t_idx])
        exact = 2.0 / np.sqrt(xv)
        d = abs((ph - exact) % 1.0)
        d = min(d, 1.0 - d)
        errs.append(d)
        print(f"  x={xv} lead={xv.bit_length()-1} ph={ph:.6e} exact={exact:.6e} err={d:.3e}")
    errs = np.array(errs)
    print(f"error de fase (vueltas): max={errs.max():.3e} media={errs.mean():.3e}")
    print(f"tol ~5.96e-08. ¿Pasa? {errs.max() < 5.96e-08}")


if __name__ == "__main__":
    main()
