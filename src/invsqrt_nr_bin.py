#!/usr/bin/env python3
"""
invsqrt NR (dbhexa) con `s` binario de 4 bits, sin banderas unarias.

Transplante de logshift2 a la arquitectura NR/dbhexa:

- Normalizacion: contador de pares de ceros iniciales por etapas 8,4,2,1 (pares),
  como `NormalizarLog` de invsqrt_logshift2. `sb[b] := los 2*2^b bits superiores
  de x son 0` (cadena de ANDs, `_nor`); los temporales son qubits de `coef`,
  que valen 0 en esta fase (ida y vuelta). Luego `x := x << 2*2^b` controlado
  por sb[b]. Registro `flags` (10, unario) eliminado: Q baja 6.
- Desnormalizacion: `y1 := p << s` con 4 etapas controladas (1,2,4,8 bits),
  como `DesnormLog` de invsqrt_logshift. El carril de cada etapa crece con el
  desplazamiento acumulado, asi los bits que darian la vuelta son 0.
  La desnormalizacion unaria (10 rotaciones) costaba ~560 Toffolis; la
  logaritmica ~260.

Todo lo demas es el reference verificado (`nr_reference_circuit.py`):
mismo Horner cubico, mismo paso de Newton, misma fase por bits. La aritmetica
no cambia, asi que `fixed_point_model` sigue siendo el modelo exacto del
error y el verificador oficial es el arbitro.

Precision dbhexa: square=27, product=27, result=27 -> Q=254, T=7405 en la
version unaria. result_bits=28 NO es valido (falla el verificador).
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
from nr_reference_circuit import (  # noqa: E402
    Precision,
    _correct,
    _horner,
    _load_coefficients,
    _multiply_m,
    _multiply_y0,
    _phase_by_bits,
    _select_interval,
    _square,
    relative_error,
)

log = logging.getLogger("nr_bin")

DBHEXA_PRECISION = Precision(
    delta_bits=14,
    coef_bits=17,
    square_bits=27,
    product_bits=27,
    result_bits=27,
)


def _nor(b: km.CircuitBuilder, inverse: bool, bits, target, temps) -> None:
    """target ^= (todos los `bits` son 0). Cadena de ANDs; `temps` debe estar en 0 y queda en 0."""
    n = len(bits)
    b.x(bits)
    if n == 2:
        (b.del_and if inverse else b.init_and)(bits[0], bits[1], target)
    else:
        chain = [(bits[0], bits[1], temps[0])]
        for i in range(2, n - 1):
            chain.append((temps[i - 2], bits[i], temps[i - 1]))
        last = (temps[n - 3], bits[n - 1], target)
        for c in chain:
            b.init_and(*c)
        (b.del_and if inverse else b.init_and)(*last)
        for c in reversed(chain):
            b.del_and(*c)
    b.x(bits)


def _normalize_bin(builder: km.CircuitBuilder, inverse: bool, x: km.array,
                   sb: km.array, temps: km.array) -> None:
    """`x := x 2^(2s)`, con `s` binario de 4 bits en `sb` (etapas 8,4,2,1 pares).

    `temps` (qubits de `coef`, en 0 en esta fase) alimenta las cadenas de ANDs.
    """
    w = len(x)
    with builder.mark("normalize_log"):
        for bit in (range(4) if inverse else (3, 2, 1, 0)):
            r = 2 << bit
            top = x[w - r:w]
            if inverse:
                builder.right_rotate(x, r, control=sb[bit])
                _nor(builder, True, top, sb[bit], temps)
            else:
                _nor(builder, False, top, sb[bit], temps)
                builder.left_rotate(x, r, control=sb[bit])


def _denormalize_bin(builder: km.CircuitBuilder, inverse: bool, sb: km.array,
                     y1: km.array, p_bits: int) -> None:
    """`y1 := p << s`, con `s` binario: 4 etapas controladas (1,2,4,8 bits).

    El carril de cada etapa cubre `p_bits + desplazamiento acumulado`, asi los
    bits que darian la vuelta al rotar son 0.
    """
    out = len(y1)
    cum, largos = 0, []
    for bit in range(4):
        cum = min(cum + (1 << bit), 10)
        largos.append(min(p_bits + cum, out))
    with builder.mark("denormalize_log"):
        for bit in (reversed(range(4)) if inverse else range(4)):
            lane = y1[:largos[bit]]
            (builder.right_rotate if inverse else builder.left_rotate)(
                lane, 1 << bit, control=sb[bit])


def _compute_y1_bin(builder: km.CircuitBuilder, inverse: bool, prec: Precision,
                    x: km.array, sb: km.array, selectors: km.array,
                    coefs: list[km.array], square: km.array, z: km.array,
                    y1: km.array, scratch: km.array) -> None:
    """Como `_compute_y1` del reference, pero con `s` binario (sin `flags`)."""
    y0, p = coefs[0], y1[:prec.result_bits + 1]  # p ocupa los bits bajos de y1
    temps = coefs[0]  # en 0 durante normalizar (ida y vuelta)
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
            with builder.mark("horner"):
                _horner(builder, inverse, prec, x, selectors, coefs, scratch)
            with builder.mark("load_coefficients"):
                _load_coefficients(builder, prec, x, selectors, coefs)
            with builder.mark("select_interval"):
                _select_interval(builder, inverse, x, selectors)
            with builder.mark("normalize"):
                _normalize_bin(builder, inverse, x, sb, temps)
        else:
            with builder.mark("normalize"):
                _normalize_bin(builder, inverse, x, sb, temps)
            with builder.mark("select_interval"):
                _select_interval(builder, inverse, x, selectors)
            with builder.mark("load_coefficients"):
                _load_coefficients(builder, prec, x, selectors, coefs)
            with builder.mark("horner"):
                _horner(builder, inverse, prec, x, selectors, coefs, scratch)
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


def build_nr_bin_circuit(n_p: int, *, prec: Precision = DBHEXA_PRECISION,
                         compute_only: bool = False) -> km.Circuit:
    """El circuito NR/dbhexa con `s` binario. `compute_only` para tests."""
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
    y1, sb, selectors = alloc(out_bits, "y1"), alloc(4, "sb"), alloc(3, "selectors")
    coefs = [alloc(prec.coef_bits, f"c{j}") for j in range(4)]
    square, z = alloc(prec.square_bits, "square"), alloc(prec.product_bits + 2, "z")
    scratch = alloc(max(prec.square_bits, prec.product_bits + 2, prec.result_bits + 1), "scratch")
    registers = (x, sb, selectors, coefs, square, z, y1, scratch)
    _compute_y1_bin(builder, False, prec, *registers)
    if not compute_only:
        _phase_by_bits(builder, y1)
        _compute_y1_bin(builder, True, prec, *registers)
        for reg in (y1, sb, selectors, *coefs, square, z, scratch):
            builder.free(reg)
    return builder.finish_circuit()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output", help="Ruta del archivo .kmb de salida.")
    ap.add_argument("--n-p", type=int, default=10)
    ap.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    a = ap.parse_args()

    max_x = 3 * (2**a.n_p - 2) ** 2
    prec = DBHEXA_PRECISION
    t0 = time.time()
    error = relative_error(a.n_p, prec, np.arange(1, max_x + 1))
    log.info("Modelo: max error relativo 2^%.2f en x=%d (tolerancia 2^-24).",
             math.log2(error.max()), error.argmax() + 1)
    circ = build_nr_bin_circuit(a.n_p, prec=prec)
    q = int(circ.num_qubits)
    t_toff = int(circ.operation_statistics().num_toffoli_like)
    log.info("circuito: Q=%d T=%d", q, t_toff)
    if _HAS_QCC_LOG:
        _qcc_emit("invsqrt_nr_bin", "build", "ok",
                  inputs={"n_p": a.n_p, "prec": "dbhexa-27/27/27"},
                  outputs={"Q": q, "T": t_toff},
                  duration_s=time.time() - t0)
    if a.output:
        t0 = time.time()
        circ.to_file(a.output, format=a.format)
        digest = hashlib.sha256(Path(a.output).read_bytes()).hexdigest()
        log.info("sha256 %s", digest)
        if _HAS_QCC_LOG:
            _qcc_emit("invsqrt_nr_bin", "write", "ok",
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
