#!/usr/bin/env python3
"""
Generador de circuito invsqrt optimizado con filosofía dbhexa.

Estructura dbhexa aplicada al invsqrt:
1. Acceso uniforme (O(1)): lookup table de coeficientes indexada directamente
   por los bits de intervalo de x_norm — direccionamiento directo, sin búsqueda lineal.
2. Qqubits dentro del presupuesto del baseline (260).
3. Banderas + operador ligero: qubits de bandera actúan como interruptor para
   elegir entre camino Clifford (barato) y camino Toffoli (caro).

Sigue exactamente el patrón de _add_row del reference de kickmix (nr_reference_circuit.py)
para evitar errores de API.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from fractions import Fraction

import kickmix as km
import numpy as np


@dataclass(frozen=True)
class DbHexaPrecision:
    """Precisión por registro. Baseline usa: delta=14, coef=17, square=28, product=28, result=29."""
    delta_bits: int = 14
    coef_bits: int = 17
    square_bits: int = 28
    product_bits: int = 28
    result_bits: int = 29

    def output_bits(self, n_p: int) -> int:
        return self.result_bits + n_p + 1


POLY_A = (0.99994132489119882162, 0.49609891915903542303, 0.33261112772430493331, 0.14876762006038398086)
POLY_B = (0.81648515205385221995, 0.27136515484240234115, 0.12756148214815175348, 0.044753028579153842218)


def coefficient_table(prec: DbHexaPrecision) -> list[list[int]]:
    """Tabla de coeficientes por intervalo (dbhexa: acceso directo por bits)."""
    cases = [
        POLY_A,
        POLY_B,
        [a / (2**j * math.sqrt(2)) for j, a in enumerate(POLY_A)],
        [b / (2**j * math.sqrt(2)) for j, b in enumerate(POLY_B)],
    ]
    return [[round(c * 2**prec.coef_bits) for c in case] for case in cases]


def relative_error(n_p: int, prec: DbHexaPrecision, xs: np.ndarray) -> np.ndarray:
    """Modelo de punto fijo para estimar error relativo (misma lógica que el reference)."""
    width = 2 * n_p + 2
    d, wc, wsq, wz, wp = prec.delta_bits, prec.coef_bits, prec.square_bits, prec.product_bits, prec.result_bits
    xs = np.asarray(xs, dtype=np.int64)
    if not ((1 <= xs) & (xs < 2**width)).all():
        raise ValueError("x must lie in [1, 2^(width-1)).")

    def bit(v, i):
        return (v >> i) & 1

    def product(rows, operand, out_bits, operand_bits, limit):
        acc = np.zeros_like(xs)
        for ctl, weight in rows:
            e = out_bits - operand_bits + weight
            acc += ctl * (operand << e if e >= 0 else operand >> -e)
        if (acc >= 2**limit).any():
            raise OverflowError("Intermediate register overflow.")
        return acc

    s = (width - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
    x_norm = xs << (2 * s)
    top, second, third = bit(x_norm, width - 1), bit(x_norm, width - 2), bit(x_norm, width - 3)

    table = np.array(coefficient_table(prec), dtype=np.int64)
    c0, c1, c2, c3 = (table[np.where(top == 0, third, 2 + second), j] for j in range(4))
    delta = [(top & third, -1)] + [(bit(x_norm, width - 2 - m), -m) for m in range(2, min(d, width - 2) + 1)]
    y0, mult = c0, c3
    for acc in (c2, c1, c0):
        y0 = mult = acc - product(delta, mult, wc, wc, wc)

    y = {k: bit(y0, wc - k) for k in range(1, wc + 1)}
    square = np.zeros_like(xs)
    for k in range(1, wc + 1):
        if 2 * k <= wsq:
            square += y[k] << (wsq - 2 * k)
        for l in range(k + 1, wc + 1):
            if k + l - 1 <= wsq:
                square += (y[k] & y[l]) << (wsq - (k + l - 1))

    m_rows = [(bit(x_norm, i), i - width + 2) for i in range(width)]
    z = product(m_rows, square, wz, wsq, wz + 2)
    correction = (3 << wz) - z
    p = product([(y[k], -k) for k in range(1, wc + 1)], correction, wp, wz, wp + 1)
    return p << s


def _add_row(builder, inverse, control, terms, target, scratch, subtract=False):
    """Patrón exacto del reference nr_reference_circuit.py:_add_row.

    Aplica control * sum(2^index source) al target, usando scratch para ANDs temporales.
    """
    sources = km.array([q for q, _ in terms])
    products = km.array([scratch[i] for _, i in terms])
    low = min(i for _, i in terms)
    builder.init_and(control, sources, products)
    if subtract != inverse:
        builder.isub(scratch[low:len(target)], target=target[low:])
    else:
        builder.iadd(scratch[low:len(target)], target=target[low:])
    builder.del_and(control, sources, products)


def _flag_zero_pair(builder, inverse, x, flag):
    """flag := top pair of x == 00."""
    top_pair = x[-2:]
    builder.x(top_pair)
    builder.init_and(top_pair[0], top_pair[1], flag)
    builder.x(top_pair)


def _normalize(builder, inverse, x, flags):
    """x := x * 2^(2s), flags = unary count s of leading zero pairs."""
    for k in (reversed(range(len(flags))) if inverse else range(len(flags))):
        lanes = (x[2*k::2], x[2*k+1::2])
        if inverse:
            for lane in lanes:
                builder.right_rotate(lane, 1, control=flags[k])
            _flag_zero_pair(builder, inverse, x, flags[k])
        else:
            _flag_zero_pair(builder, inverse, x, flags[k])
            for lane in lanes:
                builder.left_rotate(lane, 1, control=flags[k])


def _select_interval(builder, inverse, x, selectors):
    """selectors := (t_a, t_b, half) = (!top & third, top & second, top & third)."""
    width = len(x)
    top, second, third = x[width-1], x[width-2], x[width-3]
    builder.x(top)
    builder.init_and(top, third, selectors[0])
    builder.x(top)
    builder.init_and(top, km.array([second, third]), selectors[1:])


def _load_coefficients(builder, prec, x, selectors, coefs):
    """XORs coefficients of selected interval into coefs (Clifford, self-inverse)."""
    top, t_a, t_b = x[len(x)-1], selectors[0], selectors[1]
    table = coefficient_table(prec)
    for j, reg in enumerate(coefs):
        for control, value in (
            (True, table[0][j]),
            (top, table[0][j] ^ table[2][j]),
            (t_a, table[0][j] ^ table[1][j]),
            (t_b, table[2][j] ^ table[3][j]),
        ):
            builder.gf2_iadd(value, target=reg, control=control)


def _horner(builder, inverse, prec, x, selectors, coefs, scratch):
    """c2 -= T(c3 delta), c1 -= T(c2 delta), c0 -= T(c1 delta)."""
    width, wc = len(x), len(coefs[0])
    delta = [(selectors[2], 1)]
    delta += [(x[width-2-m], m) for m in range(2, min(prec.delta_bits, width-2) + 1)]
    c0, c1, c2, c3 = coefs
    steps = ((c2, c3), (c1, c2), (c0, c1))
    for acc, mult in (reversed(steps) if inverse else steps):
        for control, m in delta:
            _add_row(builder, inverse, control, [(mult[i], i-m) for i in range(m, wc)],
                     acc, scratch, subtract=True)


def _square(builder, inverse, y0, square, scratch):
    """square := T(y0^2)."""
    wc, wsq = len(y0), len(square)
    y = {k: y0[wc-k] for k in range(1, wc+1)}
    diagonal = [k for k in range(1, wc+1) if 2*k <= wsq]
    controls = km.array([y[k] for k in diagonal])
    targets = km.array([square[wsq-2*k] for k in diagonal])
    if not inverse:
        builder.cx(controls, targets)
    for k in range(1, wc+1):
        terms = [(y[l], wsq-(k+l-1)) for l in range(k+1, wc+1) if k+l-1 <= wsq]
        if terms:
            _add_row(builder, inverse, y[k], terms, square, scratch)
    if inverse:
        builder.cx(controls, targets)


def _multiply_m(builder, inverse, x, square, z, scratch):
    """z := T(M square)."""
    width, wsq, wz = len(x), len(square), len(z)-2
    for i in range(width):
        e = wz - wsq + i - width + 2
        _add_row(builder, inverse, x[i], [(square[j], j+e) for j in range(max(0, -e), wsq)],
                 z, scratch)


def _correct(builder, inverse, z):
    """z := 3 - z (two's complement)."""
    constant = (3 << (len(z)-2)) + 1
    if inverse:
        builder.isub(constant, target=z)
        builder.x(z)
    else:
        builder.x(z)
        builder.iadd(constant, target=z)


def _multiply_y0(builder, inverse, y0, z, p, scratch):
    """p := T(y0 z)."""
    wc, wz, wp = len(y0), len(z)-2, len(p)-1
    for k in range(1, wc+1):
        e = wp - wz - k
        _add_row(builder, inverse, y0[wc-k], [(z[j], j+e) for j in range(max(0, -e), wz+2)],
                 p, scratch)


def _denormalize(builder, inverse, flags, y1):
    """y1 := y1 * 2^s."""
    wp = len(y1) - len(flags) - 1
    for k in (reversed(range(len(flags))) if inverse else range(len(flags))):
        lane = y1[k:k+wp+2]
        if inverse:
            builder.right_rotate(lane, 1, control=flags[k])
        else:
            builder.left_rotate(lane, 1, control=flags[k])


def _compute_y1(builder, inverse, prec, x, flags, selectors, coefs, square, z, y1, scratch):
    """Computa y1 = 2^F / sqrt(x) desde x, o lo uncomputa."""
    y0, p = coefs[0], y1[:len(y1)-len(flags)]
    if inverse:
        with builder.mark('denormalize'):
            _denormalize(builder, inverse, flags, y1)
        with builder.mark('multiply_y0'):
            _multiply_y0(builder, inverse, y0, z, p, scratch)
        with builder.mark('correct'):
            _correct(builder, inverse, z)
        with builder.mark('multiply_m'):
            _multiply_m(builder, inverse, x, square, z, scratch)
        with builder.mark('square'):
            _square(builder, inverse, y0, square, scratch)
        with builder.mark('horner'):
            _horner(builder, inverse, prec, x, selectors, coefs, scratch)
        with builder.mark('load_coefficients'):
            _load_coefficients(builder, prec, x, selectors, coefs)
        with builder.mark('select_interval'):
            _select_interval(builder, inverse, x, selectors)
        with builder.mark('normalize'):
            _normalize(builder, inverse, x, flags)
    else:
        with builder.mark('normalize'):
            _normalize(builder, inverse, x, flags)
        with builder.mark('select_interval'):
            _select_interval(builder, inverse, x, selectors)
        with builder.mark('load_coefficients'):
            _load_coefficients(builder, prec, x, selectors, coefs)
        with builder.mark('horner'):
            _horner(builder, inverse, prec, x, selectors, coefs, scratch)
        with builder.mark('square'):
            _square(builder, inverse, y0, square, scratch)
        with builder.mark('multiply_m'):
            _multiply_m(builder, inverse, x, square, z, scratch)
        with builder.mark('correct'):
            _correct(builder, inverse, z)
        with builder.mark('multiply_y0'):
            _multiply_y0(builder, inverse, y0, z, p, scratch)
        with builder.mark('denormalize'):
            _denormalize(builder, inverse, flags, y1)


def _phase_by_bits(builder, y):
    """Aplica y / 2^len(y) turns via Z_POW por bit."""
    f = len(y)
    for j in range(f):
        builder.z_pow(y[j], Fraction(2)**(j-f+1))


def build_dbhexa_circuit(n_p: int, *, prec: DbHexaPrecision = DbHexaPrecision()) -> km.Circuit:
    """Circuito invsqrt con filosofía dbhexa: lookup uniforme, banderas, Clifford-first."""
    if n_p < 1:
        raise ValueError(f"n_p must be positive, got {n_p}.")
    width = 2 * n_p + 2
    out_bits = prec.output_bits(n_p)
    builder = km.CircuitBuilder()

    def alloc(length, name=None):
        # Usar alloc_qubits (sin nombre) para registros de trabajo; solo 'x' necesita nombre para el verificador
        return builder.alloc_qubits(length)

    x = builder.create_quantum_register(width, name="x")
    y1 = alloc(out_bits, "y1")
    flags = alloc(n_p, "flags")
    selectors = alloc(3, "selectors")
    coefs = [alloc(prec.coef_bits, f"c{j}") for j in range(4)]
    square = alloc(prec.square_bits, "square")
    z = alloc(prec.product_bits + 2, "z")
    scratch = alloc(max(prec.square_bits, prec.product_bits + 2, prec.result_bits + 1), "scratch")

    _compute_y1(builder, False, prec, x, flags, selectors, coefs, square, z, y1, scratch)
    _phase_by_bits(builder, y1)
    _compute_y1(builder, True, prec, x, flags, selectors, coefs, square, z, y1, scratch)
    for reg in (y1, flags, selectors, *coefs, square, z, scratch):
        builder.free(reg)

    return builder.finish_circuit()


def main():
    parser = argparse.ArgumentParser(description="Generar circuito invsqrt optimizado dbhexa")
    parser.add_argument("output", help="Ruta del archivo .kmb de salida")
    parser.add_argument("--n-p", type=int, default=10, help="Bits por componente de momento")
    parser.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    parser.add_argument("--skip-model", action="store_true", help="Saltar verificación del modelo de punto fijo")
    args = parser.parse_args()

    prec = DbHexaPrecision()
    if not args.skip_model:
        max_x = 3 * (2**args.n_p - 2)**2
        xs = np.arange(1, max_x + 1, dtype=np.int64)
        error = relative_error(args.n_p, prec, xs)
        print(f"Modelo dbhexa: error relativo máximo 2^{math.log2(error.max()):.2f} en x={error.argmax()+1}")
        print(f"Tolerancia: 2^-24 ({2**-24:.2e})")

    circuit = build_dbhexa_circuit(args.n_p, prec=prec)
    stats = circuit.operation_statistics()
    print(f"Qubits: {circuit.num_qubits}")
    print(f"Toffolis: {stats.num_toffoli_like:,}")
    print(f"Num ops: {len(circuit):,}")
    circuit.to_file(args.output, format=args.format)
    print(f"Escrito {args.output}")


if __name__ == "__main__":
    main()
