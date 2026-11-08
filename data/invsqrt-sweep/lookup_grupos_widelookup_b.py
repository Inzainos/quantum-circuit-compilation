"""Prototipo WideLookup: un solo lookup ancho de 84 bits (B|S|C2).

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
    edges = 1.0 + np.arange(nseg) / nseg
    base_f = edges ** (-0.5)
    slope_f = 0.5 * edges ** (-1.5)
    curv_f = 0.375 * edges ** (-2.5)
    inv = 1.0 / np.sqrt(2.0)

    def a_u(v):
        return min(int(round(v * (1 << N_VAL))), (1 << N_VAL) - 1)
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


def tabla_ancha(base, slope, curv):
    """Una sola tabla de 84 bits: (B << 56) | (S << 28) | C2."""
    wide = []
    for b, s, c in zip(base, slope, curv):
        wide.append((b << (2 * N_VAL)) | (s << N_VAL) | c)
    return wide


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
    wide = tabla_ancha(base, slope, curv)
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

    # UN solo lookup ancho (84 bits): B|S|C2.
    regW = b.create_quantum_register(N_WIDE, name="regW")
    b.init_lookup(table=wide, address=addr, target=regW)
    # Slices: C2 = regW[0:28], S = regW[28:56], B = regW[56:84].
    C2 = list(regW[0:N_VAL])
    S = list(regW[N_VAL:2 * N_VAL])
    B = list(regW[2 * N_VAL:3 * N_VAL])

    # V = B.
    V = b.create_quantum_register(N_VAL + N_SHIFT, name="V")
    for i in range(N_VAL):
        b.cx(B[i], V[i])

    # Horner: V = B - (t*h)>>18, con h = S - (C2*t)>>18 (positivo).
    h = b.create_quantum_register(N_VAL, name="h")
    for i in range(N_VAL):
        b.cx(S[i], h[i])
    # Paso 2: h -= (C2*t)>>18.
    mac_sub_trunc(b, C2, t, h, scratch, N_MANT)
    # Paso 3: V -= (t*h)>>18.
    mac_sub_trunc(b, h, t, V, scratch, N_MANT)

    # Ya no se necesitan B/S/C2: limpiar el registro ancho.
    b.del_lookup(table=wide, address=addr, target=regW)

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
    circ.to_file("/tmp/proto_widelookup_b%d.kmx" % N_SEG)
    print("escrito en /tmp/proto_widelookup_b%d.kmx" % N_SEG)
    import subprocess
    tot = 0
    for op in ["CCX", "CCZ", "CSWAP"]:
        r = subprocess.run(["grep", "-c", f"^{op}", "/tmp/proto_widelookup_b%d.kmx" % N_SEG],
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
