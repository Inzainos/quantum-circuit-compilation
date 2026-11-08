#!/usr/bin/env python3
"""
invsqrt NR (dbhexa) con `s` binario y semilla por tabla lineal (panal).

El panal de Elan: 96 celdas de ancho 1/32 sobre M en [1,4). Cada celda tiene
su semilla precomputada (a_k, c_k) y el dato cae en su celda: la direccion
son los 7 bits altos de x_norm (valores 32..127) y t son los 15 bits bajos.
Sin restas ni copias: direccion y t son rebanadas de x_norm.

La semilla es y0 = a_k - c_k*t (la pendiente de 1/sqrt siempre es negativa),
con a_k, c_k en 17 bits (minimax por celda: la cuerda desplazada la mitad de
su desviacion maxima) y t truncada a 11 bits (la multiplicacion de
interpolacion usa 11 bits de t). Modelo (lut_seed_error): error tras 1 Newton
exacto 0.0642 de tolerancia, mejor que la semilla cubica (0.1289).

Precision verificada: 28/28/28 (Q=216, T=6,356, score 1,426,020.28, PASS).
A 27/27/27 el circuito FALLA el verificador (peor error 1.1711 en
x=1040463): la semilla LUT cambia los bits de y0 y el patron de truncacion
de Newton se reordena; el modelo fiel (lut_full_model.py) lo reproduce al
entero (1.1711 en el mismo x). Ensanchar solo square/producto a 28 no basta
(1.0336); hace falta el resultado a 28 (0.5295).

La tabla se carga con un QROM por grupos: los 5 bits altos de la direccion
forman 24 grupos de 4 celdas; el prefijo se calcula una vez por grupo (4 T)
y cada celda suma su sufijo de 2 bits (2 T). ~288 T por direccion, contra
1,071 T del Horner cubico que reemplaza. La interpolacion son 11 _add_row
(una por bit de t). Todo lo demas es el reference verificado (nr_bin):
mismo paso de Newton, misma fase por bits.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(_ROOT / "tools"))
try:
    from qcc_log import emit as _qcc_emit
    _HAS_QCC_LOG = True
except Exception:  # noqa: BLE001 - logging opcional; el circuito no depende de el
    _HAS_QCC_LOG = False

import kickmix as km  # noqa: E402
import numpy as np  # noqa: E402
from invsqrt_nr_bin import _denormalize_bin, _normalize_bin  # noqa: E402
from nr_reference_circuit import (  # noqa: E402
    Precision,
    _add_row,
    _correct,
    _multiply_m,
    _multiply_y0,
    _phase_by_bits,
    _square,
)

log = logging.getLogger("nr_bin_lut")

DBHEXA_PRECISION = Precision(
    delta_bits=14,
    coef_bits=17,
    square_bits=28,
    product_bits=28,
    result_bits=28,
)
NSEG = 96
T_BITS = 11  # bits de t usados en la interpolacion


def lut_table() -> list[tuple[int, int]]:
    """(a_k, c_k) en enteros de 17 bits, k = 0..95.

    Celda k: M en [1 + k/32, 1 + (k+1)/32). a_k = 1/sqrt(inicio) desplazado
    la mitad de la desviacion maxima de la cuerda (minimax); c_k =
    |1/sqrt(fin) - 1/sqrt(inicio)|. Ambos en piso a 2^-17.
    """
    table = []
    for k in range(NSEG):
        start = 1.0 + k / 32.0
        fa = 1.0 / math.sqrt(start)
        fb = 1.0 / math.sqrt(start + 1.0 / 32.0)
        # Desviacion maxima de la cuerda en la celda (muestreo denso).
        tt = np.linspace(0.0, 1.0, 4097)
        mm = start + tt / 32.0
        chord = fa + (fb - fa) * tt
        dev = float(np.max(chord - 1.0 / np.sqrt(mm)))
        a_k = fa - 0.5 * dev
        c_k = fa - fb
        table.append((math.floor(a_k * 2.0**17), math.floor(c_k * 2.0**17)))
    return table


LUT = lut_table()


def lut_seed_error() -> float:
    """Error maximo tras 1 Newton exacto con la tabla (a,b 17 bits, t 11 bits),
    en unidades de tolerancia, sobre todo el dominio."""
    xs = np.arange(1, 3 * (2**10 - 2) ** 2 + 1, dtype=np.float64)
    exact = 1.0 / np.sqrt(xs)
    # M y t de cada x (como en el circuito: M de x_norm, t de los bits bajos).
    s = (22 - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
    x_norm = (xs.astype(np.int64) << (2 * s)).astype(np.float64)
    M = x_norm / 2.0**20
    k = np.clip(((M - 1.0) * 32.0).astype(np.int64), 0, NSEG - 1)
    t = (M - 1.0) * 32.0 - k
    t11 = np.floor(t * 2.0**T_BITS) / 2.0**T_BITS
    a = np.array([LUT[int(kk)][0] for kk in k], dtype=np.float64) / 2.0**17
    c = np.array([LUT[int(kk)][1] for kk in k], dtype=np.float64) / 2.0**17
    y0 = a - c * t11
    p = y0 * (3.0 - M * y0 * y0)
    true = 2.0 / np.sqrt(M)
    err = np.abs(p - true) / true / 2.0**-24
    return float(err.max())


def _and_on(builder: km.CircuitBuilder, literals, target: km.q,
            temps: km.array) -> None:
    """target := AND(literales). target y temps en 0; los intermedios de la
    cadena quedan VIVOS (los deshace _and_off sin recomputar)."""
    qs = [q for q, _ in literals]
    neg = [q for q, w in literals if not w]
    if neg:
        builder.x(km.array(neg))
    n = len(literals)
    if n == 1:
        builder.cx(qs[0], target)
    elif n == 2:
        builder.init_and(qs[0], qs[1], target)
    else:
        chain = [(qs[0], qs[1], temps[0])]
        for i in range(2, n - 1):
            chain.append((temps[i - 2], qs[i], temps[i - 1]))
        last = (temps[n - 3], qs[n - 1], target)
        for c in chain:
            builder.init_and(*c)
        builder.init_and(*last)
    if neg:
        builder.x(km.array(neg))


def _and_off(builder: km.CircuitBuilder, literals, target: km.q,
             temps: km.array) -> None:
    """Deshace un _and_on previo (target vuelve a 0, intermedios a 0)."""
    qs = [q for q, _ in literals]
    neg = [q for q, w in literals if not w]
    if neg:
        builder.x(km.array(neg))
    n = len(literals)
    if n == 1:
        builder.cx(qs[0], target)
    elif n == 2:
        builder.del_and(qs[0], qs[1], target)
    else:
        chain = [(qs[0], qs[1], temps[0])]
        for i in range(2, n - 1):
            chain.append((temps[i - 2], qs[i], temps[i - 1]))
        last = (temps[n - 3], qs[n - 1], target)
        builder.del_and(*last)
        for c in reversed(chain):
            builder.del_and(*c)
    if neg:
        builder.x(km.array(neg))


def _lut_load(builder: km.CircuitBuilder, address: km.array, a_reg: km.array,
              c_reg: km.array, scratch: km.array) -> None:
    """Carga (a_k, c_k) por la direccion de 7 bits. Su propio inverso.

    Grupos por los 5 bits altos (24 grupos de 4 celdas); el prefijo se
    calcula una vez por grupo y cada celda suma su sufijo de 2 bits.
    scratch[0] prefijo, scratch[1] sufijo, scratch[2] match,
    scratch[3:6] cadena del prefijo.
    """
    prefix_q, suffix_q, match_q = scratch[0], scratch[1], scratch[2]
    temps = scratch[3:6]
    for pv in range(8, 32):  # prefijos usados: 8..31
        plits = [(address[2 + i], bool((pv >> i) & 1)) for i in range(5)]
        _and_on(builder, plits, prefix_q, temps)
        for ev in range(4):
            slits = [(address[i], bool((ev >> i) & 1)) for i in range(2)]
            _and_on(builder, slits, suffix_q, temps)
            builder.init_and(suffix_q, prefix_q, match_q)
            a_val, c_val = LUT[(pv * 4 + ev) - 32]
            for j in range(17):
                if (a_val >> j) & 1:
                    builder.cx(match_q, a_reg[j])
                if (c_val >> j) & 1:
                    builder.cx(match_q, c_reg[j])
            builder.del_and(suffix_q, prefix_q, match_q)
            _and_off(builder, slits, suffix_q, temps)
        _and_off(builder, plits, prefix_q, temps)


def _interpolate(builder: km.CircuitBuilder, inverse: bool, x: km.array,
                 a_reg: km.array, c_reg: km.array, scratch: km.array) -> None:
    """`a_reg -= c_reg * t`, con t = los 11 bits altos de x[0:15].

    El bit j de t (peso 2^-(j+1)) es x[14-j]; el termino (c[i], i-(j+1))
    existe si i >= j+1. Es su propio inverso via _add_row (inverse=True).
    """
    for j in range(T_BITS):
        ctl = x[14 - j]
        _add_row(builder, inverse, ctl,
                 [(c_reg[i], i - (j + 1)) for i in range(j + 1, 17)],
                 a_reg, scratch, subtract=True)


def _compute_y1_bin_lut(builder: km.CircuitBuilder, inverse: bool, prec: Precision,
                        x: km.array, sb: km.array, a_reg: km.array, c_reg: km.array,
                        square: km.array, z: km.array, y1: km.array,
                        scratch: km.array) -> None:
    """Como `_compute_y1_bin`, con semilla por tabla lineal en vez de Horner."""
    y0, p = a_reg, y1[:prec.result_bits + 1]  # p ocupa los bits bajos de y1
    temps = a_reg  # en 0 durante normalizar (ida y vuelta)
    address = x[15:22]  # 7 bits: floor(M*32), valores 32..127
    with builder.mark("uncompute_y1" if inverse else "compute_y1"):
        if inverse:
            with builder.mark("denormalize"):
                _denormalize_bin(builder, inverse, sb, y1, len(p))
            with builder.mark("multiply_y0"):
                _multiply_y0(builder, inverse, y0, z, p, scratch)
            with builder.mark("correct"):
                _correct(builder, inverse, z)
            with builder.mark("multiply_m"):
                _multiply_m(builder, inverse, x, square, z, scratch)
            with builder.mark("square"):
                _square(builder, inverse, y0, square, scratch)
            with builder.mark("interpolate"):
                _interpolate(builder, inverse, x, a_reg, c_reg, scratch)
            with builder.mark("lut_load"):
                _lut_load(builder, address, a_reg, c_reg, scratch)
            with builder.mark("normalize"):
                _normalize_bin(builder, inverse, x, sb, temps)
        else:
            with builder.mark("normalize"):
                _normalize_bin(builder, inverse, x, sb, temps)
            with builder.mark("lut_load"):
                _lut_load(builder, address, a_reg, c_reg, scratch)
            with builder.mark("interpolate"):
                _interpolate(builder, inverse, x, a_reg, c_reg, scratch)
            with builder.mark("square"):
                _square(builder, inverse, y0, square, scratch)
            with builder.mark("multiply_m"):
                _multiply_m(builder, inverse, x, square, z, scratch)
            with builder.mark("correct"):
                _correct(builder, inverse, z)
            with builder.mark("multiply_y0"):
                _multiply_y0(builder, inverse, y0, z, p, scratch)
            with builder.mark("denormalize"):
                _denormalize_bin(builder, inverse, sb, y1, len(p))


def build_nr_bin_lut_circuit(n_p: int, *, prec: Precision = DBHEXA_PRECISION,
                             compute_only: bool = False) -> km.Circuit:
    """El circuito NR/dbhexa con `s` binario y semilla por tabla lineal."""
    if n_p < 1:
        raise ValueError(f"n_p must be positive, got {n_p}.")
    if n_p != 10:
        raise ValueError("s binario de 4 bits supone n_p == 10 (s <= 10).")
    width = 2 * n_p + 2
    out_bits = prec.output_bits(n_p)
    builder = km.CircuitBuilder()

    def alloc(length: int, name: str) -> km.array:
        if compute_only:
            return builder.create_quantum_register(length, name=name)
        return builder.alloc_qubits(length)

    x = builder.create_quantum_register(width, name="x")
    y1, sb = alloc(out_bits, "y1"), alloc(4, "sb")
    a_reg, c_reg = alloc(prec.coef_bits, "a"), alloc(prec.coef_bits, "c")
    square, z = alloc(prec.square_bits, "square"), alloc(prec.product_bits + 2, "z")
    scratch = alloc(max(prec.square_bits, prec.product_bits + 2,
                        prec.result_bits + 1), "scratch")
    registers = (x, sb, a_reg, c_reg, square, z, y1, scratch)
    _compute_y1_bin_lut(builder, False, prec, *registers)
    if not compute_only:
        _phase_by_bits(builder, y1)
        _compute_y1_bin_lut(builder, True, prec, *registers)
        for reg in (y1, sb, a_reg, c_reg, square, z, scratch):
            builder.free(reg)
    return builder.finish_circuit()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output", help="Ruta del archivo .kmb de salida.")
    ap.add_argument("--n-p", type=int, default=10)
    ap.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    a = ap.parse_args()

    prec = DBHEXA_PRECISION
    t0 = time.time()
    log.info("Modelo semilla LUT (tabla + Newton exacto): max error %.4f de tolerancia.",
             lut_seed_error())
    circ = build_nr_bin_lut_circuit(a.n_p, prec=prec)
    q = int(circ.num_qubits)
    t_toff = int(circ.operation_statistics().num_toffoli_like)
    log.info("circuito: Q=%d T=%d", q, t_toff)
    if _HAS_QCC_LOG:
        _qcc_emit("invsqrt_nr_bin_lut", "build", "ok",
                  inputs={"n_p": a.n_p, "prec": "dbhexa-lut-96"},
                  outputs={"Q": q, "T": t_toff},
                  duration_s=time.time() - t0)
    if a.output:
        t0 = time.time()
        circ.to_file(a.output, format=a.format)
        digest = hashlib.sha256(Path(a.output).read_bytes()).hexdigest()
        log.info("sha256 %s", digest)
        if _HAS_QCC_LOG:
            _qcc_emit("invsqrt_nr_bin_lut", "write", "ok",
                      inputs={"out": a.output},
                      outputs={"sha256": digest},
                      duration_s=time.time() - t0)


if __name__ == "__main__":
    try:  # logs estructurados (qcc_log): una linea por script
        import sys as _qs
        from pathlib import Path as _qp
        _qs.path.insert(0, str(_qp(__file__).resolve().parent.parent / "tools"))
        from qcc_log import auto as _qcc_auto
        _qcc_auto(__file__)
    except Exception:  # noqa: BLE001
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
