"""Tubería ligera/pesada con acarreo como filtro.

El acarreo es el filtro: un peso va a la tubería pesada (conteo exacto)
si y solo si puede acarrear con error significativo; si no, va a la
ligera (XOR, barato). El filtro es el error de acarreo por peso
(2^w * 2 * floor(maxS_w/2)), medido en dos_tuberias.py.

- Pesos -1..-9: max S_w = 1, nunca acarrean, error 0. Ligeros y exactos.
- Pesos < CUTOFF (def. -30): error residual chico, se dejan en XOR.
  Con CUTOFF=-30 el residual max es 2.733e-08 (pasa, margen 2.18x).
- Pesos >= CUTOFF: pesados. Se cuentan los monomios en 1 con un
  contador binario (iadd de 1 bit por monomio), se suma el contador
  al ACC en la posición del peso (iadd), y se limpia el contador
  deshaciendo (recomputar monomio + isub). Sin el deshacer, el
  contador no se puede reusar.

CORRECCIÓN DE SIGNO (2026-11-08): V = B - (S*t)>>18 + (C2*t2)>>36.
El término S*t se RESTA. La versión anterior sumaba todos los
monomios (error 2×S*t ≈ 0.12% en V, fase 3.97e-06). Ahora los
monomios S*t se cuentan y se RESTAN con isub, siempre (la resta no
se puede hacer con XOR porque falta el borrow). B y C2*t2 se suman.

Base: lookup_grupos_fase_valor.py (normalización logshift2, lookups
B/S/C2, t, ACC + barrel shift + fase). Las tres tablas se cargan a la
vez (regB/regS/regC2) para procesar por peso.

Uso:
  python3.13 lookup_grupos_fase_valor_filtro.py [--tiros N] [--corte -30]
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np
import kickmix as km

sys.path.insert(0, "/home/hatch/workspace/qcc-zip-final/src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from invsqrt_logshift2 import _nor

N_X = 22
N_MANT = 18
N_SEG = 8
N_T = N_MANT - N_SEG
N_VAL = 28
N_ACC = 36 + 10
ACC_OFF = 36
N_CNT = 6  # contador binario (max 49 monomios por peso -> 6 bits)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiros", type=int, default=8)
    ap.add_argument("--corte", type=int, default=-30)
    ap.add_argument("--xs", type=str, default=None)
    a = ap.parse_args()
    CUTOFF = a.corte

    base, slope, curv = tablas()
    monos = json.load(open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "monomios_valor_fase.json")))["monomios"]
    if a.xs:
        xs = np.array([int(v) for v in a.xs.split(",")], dtype=np.int64)
    else:
        rng = np.random.default_rng(11)
        xs = rng.integers(1, 1 << N_X, size=a.tiros, dtype=np.int64)
    print("xs:", xs)

    por_peso = defaultdict(list)
    for m in monos:
        por_peso[m["fase_exp"]].append(m)
    pesos = sorted(por_peso)
    n_pesado = sum(len(por_peso[p]) for p in pesos if p >= CUTOFF)
    n_ligero = sum(len(por_peso[p]) for p in pesos if p < CUTOFF)
    print(f"corte={CUTOFF}: pesos pesados={sum(1 for p in pesos if p>=CUTOFF)} "
          f"monomios pesados={n_pesado} ligeros={n_ligero}")

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

    ACC = b.create_quantum_register(N_ACC, name="acc")
    and_q = b.create_quantum_register(1, name="andq")[0]
    tmp2 = b.create_quantum_register(1, name="andtmp2")[0]
    cnt = b.create_quantum_register(N_CNT, name="cnt")

    regB = b.create_quantum_register(N_VAL, name="regB")
    regS = b.create_quantum_register(N_VAL, name="regS")
    regC = b.create_quantum_register(N_VAL, name="regC")
    b.init_lookup(table=base, address=addr, target=regB)
    b.init_lookup(table=slope, address=addr, target=regS)
    b.init_lookup(table=curv, address=addr, target=regC)

    def bit_de(nombre):
        if nombre.startswith("B"):
            return regB[int(nombre[1:])]
        if nombre.startswith("S"):
            return regS[int(nombre[1:])]
        if nombre.startswith("C2_"):
            return regC[int(nombre[3:])]
        if nombre.startswith("t"):
            return t[int(nombre[1:])]
        raise ValueError(nombre)

    def computar_monomio(m):
        """AND del monomio en and_q. Devuelve nada; and_q queda con el valor."""
        bits = m["bits"]
        if len(bits) == 1:
            b.cx(bit_de(bits[0]), and_q)
        elif len(bits) == 2:
            b.init_and(bit_de(bits[0]), bit_de(bits[1]), and_q)
        elif len(bits) == 3:
            b.init_and(bit_de(bits[0]), bit_de(bits[1]), tmp2)
            b.init_and(tmp2, bit_de(bits[2]), and_q)
        else:
            raise ValueError(f"monomio de grado {len(bits)}")

    def limpiar_monomio(m):
        """Inverso de computar_monomio (deja and_q/tmp2 en 0)."""
        bits = m["bits"]
        if len(bits) == 1:
            b.cx(bit_de(bits[0]), and_q)
        elif len(bits) == 2:
            b.del_and(bit_de(bits[0]), bit_de(bits[1]), and_q)
        elif len(bits) == 3:
            b.del_and(tmp2, bit_de(bits[2]), and_q)
            b.del_and(bit_de(bits[0]), bit_de(bits[1]), tmp2)

    def contar_y_aplicar(lista, peso_bit, restar):
        """Cuenta los monomios en cnt, lo suma (o resta si restar) al ACC
        en peso_bit, y deshace el conteo para reusar cnt.
        El target es ACC[peso_bit:] (hasta el final) para que el acarreo
        / borrow se propague a los bits altos; un slice acotado a 6 bits
        pierde el borrow y da fase mala."""
        for m in lista:
            computar_monomio(m)
            b.iadd(km.array([and_q]), target=cnt)
            limpiar_monomio(m)
        if restar:
            b.isub(cnt, target=ACC[peso_bit:])
        else:
            b.iadd(cnt, target=ACC[peso_bit:])
        for m in reversed(lista):
            computar_monomio(m)
            b.isub(km.array([and_q]), target=cnt)
            limpiar_monomio(m)

    # --- Segmentar por grupos (Elán) ---
    # Solo segmentar por grupos: los monomios van en paquetes, un paquete
    # por valor idéntico/semejante (peso). Cada paquete pasa por el Horner
    # (los originales se cuentan al ACC) y su depuración (se limpian los
    # ANDs y el contador de ese paquete), uno tras otro. Después de todos
    # los paquetes: barrel shift, fase, y arranca el mirror (banderas).
    paquetes = [(peso, por_peso[peso]) for peso in pesos]

    def depurar_paquete():
        """Depuración de un paquete: los ANDs ya se limpiaron monomio por
        monomio (limpiar_monomio) y el contador se deshizo en
        contar_y_aplicar; aquí solo se verifica que cnt quedó en 0
        (no hay nada más que limpiar por paquete)."""
        pass

    for peso, lista in paquetes:
        peso_bit = peso + ACC_OFF
        pos = [m for m in lista if m["tipo"] != "S*t"]
        neg = [m for m in lista if m["tipo"] == "S*t"]
        # Horner del paquete: los originales pasan y se cuentan al ACC.
        if pos:
            if peso < CUTOFF:
                for m in pos:
                    computar_monomio(m)
                    b.cx(and_q, ACC[peso_bit])
                    limpiar_monomio(m)
            else:
                contar_y_aplicar(pos, peso_bit, restar=False)
        # Negativos (S*t): SIEMPRE se restan con isub.
        if neg:
            contar_y_aplicar(neg, peso_bit, restar=True)
        # Depuración del paquete (los ANDs y el contador ya quedaron
        # limpios por monomio; el paquete queda cerrado).
        depurar_paquete()

    b.del_lookup(table=base, address=addr, target=regB)
    b.del_lookup(table=slope, address=addr, target=regS)
    b.del_lookup(table=curv, address=addr, target=regC)

    # Barrel shift sobre ACC (controlado por sb).
    for bit, r in ((3, 8), (2, 4), (1, 2), (0, 1)):
        ctrl = sb[bit]
        for j in range(len(ACC) - 1, r - 1, -1):
            b.cswap(ctrl, ACC[j - r], ACC[j])

    acc = b.create_quantum_register(1, name="accphase")[0]
    b.x(acc)
    for p in range(len(ACC)):
        ang = 2.0 ** (p - 45)
        b.z_pow(acc, ang)
        b.cx(ACC[p], acc)
        b.z_pow(acc, -ang)
        b.cx(ACC[p], acc)
    # Resetear el qubit de fase a |0> (la fase ya quedó aplicada como fase
    # global; el X solo cambia el bit, no la fase).
    b.x(acc)

    # --- Una sola línea con BANDERAS (Elán) ---
    # Una sola línea (no dos tuberías): los valores (monomios) van agrupados
    # por valor idéntico/semejante (peso), uno tras otro. Primero pasan todos
    # los ORIGINALES; los ESPEJOS van hasta el final de todo el recorrido.
    # Bandera 1: cuando terminan los originales, se levanta y lanza el
    # depurador (HMR) para limpiar los espejos. Bandera 2: cuando el que
    # manda los resultados termina con los espejos, se levanta y manda al
    # depurador final. La limpieza corre en dos carriles (vectores), como
    # en dos_carriles, pero coordinada por las banderas.
    # Bandera 1: originales terminados (fase ya aplicada, acc reseteado).
    bandera_orig = b.alloc_bits(1)
    b.bit_store(bandera_orig, True)
    # Depurador de espejos, lanzado por la bandera 1.
    b.push_condition(bandera_orig[0])
    # 1) Revertir barrel shift (mismos CSWAP en orden inverso).
    for bit, r in ((0, 1), (1, 2), (2, 4), (3, 8)):
        ctrl = sb[bit]
        for j in range(r, len(ACC)):
            b.cswap(ctrl, ACC[j - r], ACC[j])

    # 2) Carril ORIGINALES: HMR vectorial al ACC entero.
    bits_acc = b.alloc_bits(len(ACC))
    b.hmr(ACC, bits_acc)

    # 3) Revertir mux (limpiar Hm/tm). Inverso de mux_into, en orden inverso.
    def mux_inverso(odd_q, even_q, out_q):
        b.cx(even_q, tmp_d)
        b.cx(odd_q, tmp_d)
        b.init_and(comodin, tmp_d, tmp_a)
        b.cx(tmp_a, out_q)
        b.del_and(comodin, tmp_d, tmp_a)
        b.cx(even_q, out_q)
        b.cx(even_q, tmp_d)
        b.cx(odd_q, tmp_d)

    for i in range(N_T - 1, -1, -1):
        mux_inverso(x[N_X - 2 - N_SEG - i], x[N_X - 3 - N_SEG - i], tm[i])
    for i in range(N_SEG - 1, -1, -1):
        mux_inverso(x[N_X - 2 - i], x[N_X - 3 - i], Hm[i])

    # 4) Revertir normalizar: restaura x Y limpia sb/coef. Por cada bit
    # (0..3, orden inverso al forward): right_rotate (deshace el
    # left_rotate de ese bit) y luego _nor inverso sobre el top, que ahora
    # está en el estado rotado correcto para ese bit.
    w = len(x)
    for bit in (0, 1, 2, 3):
        r = 2 << bit
        b.right_rotate(x, r, control=sb[bit])
        top = x[w - r:w]
        _nor(b, True, top, sb[bit], coef)
    b.pop_condition()
    # Bandera 2: resultados terminados con los espejos. Lanza el depurador final.
    bandera_res = b.alloc_bits(1)
    b.bit_store(bandera_res, True)
    b.push_condition(bandera_res[0])
    # Depurador final: HMR vectorial a sb/coef por si quedó algo (deben estar
    # en 0 por el _nor inverso; el HMR los deja en 0 de todos modos).
    # (Se hace sobre sb, que es el registro que el _nor inverso limpia.)
    bits_sb = b.alloc_bits(len(sb))
    b.hmr(sb, bits_sb)
    b.pop_condition()

    circ = b.finish_circuit()
    print(f"circuito: {circ.num_qubits} qubits")
    st = circ.operation_statistics()
    print("Toffoli-like:", st.num_toffoli_like, "T-like:", st.num_t_like)
    print("reaction_depth:", circ.reaction_depth())
    circ.to_file("/tmp/proto_fase_valor_segmentos.kmx")
    print("escrito en /tmp/proto_fase_valor_segmentos.kmx")

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
    # Ancillas: leer TODOS los qubits al final.
    nq = circ.num_qubits
    allq = sim.read_across_shots(km.array([km.q(i) for i in range(nq)]))
    dirty = [q for q in range(nq) if q >= N_X and bool(allq[q].any())]
    print(f"qubits sucios (no-x con algún 1): {len(dirty)} de {nq - N_X} ancillas")
    if dirty:
        print("  primeros sucios:", dirty[:20])


if __name__ == "__main__":
    main()
