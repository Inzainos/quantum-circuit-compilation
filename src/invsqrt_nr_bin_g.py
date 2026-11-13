#!/usr/bin/env python3
"""
invsqrt NR (dbhexa) con `s` binario + redondeo con bit de guarda (fracciones).

La idea de Elan: en vez de redondear cada termino durante el calculo, llevar
la fraccion y decidir UNA vez al final de cada etapa: si pasa de la mitad
sube al numero de arriba, si no se queda. El modelo (error_slack.py,
stage_all) da 0.2983 de tolerancia contra 0.9529 en piso, y con UN solo bit
de guarda da exactamente lo mismo que con la fraccion exacta (el bit de
arriba de la fraccion ES la decision).

Implementacion por etapa (por todo igual, como pidio Elan):
- Cada etapa calcula su total con un bit de guarda: un qubit aparte que hace
  de LSB extra del objetivo (el objetivo se pasa concatenado [guarda]+registro
  y la lista de terminos se extiende un termino, el de peso 2^-(out+1)).
  Las funciones del reference no cambian: derivan todo de len(), asi que al
  pasarles el objetivo concatenado incluyen solas los terminos de guarda.
- Al final de la etapa, el incremento controlado `target += guarda` redondea
  (la fraccion mayor gana). La inversa es el decremento controlado, en orden
  espejo, asi cada guarda vuelve a 0.
- Horner: un guarda por paso (3); square, multiply_m y multiply_y0: uno cada
  uno. Total 6 guardas + scratch de 30 bits (el objetivo mas ancho es z con
  guarda: 30). _correct, select, load, normalizar y desnormalizar no cambian
  (son exactos); la fase usa y1 tal cual (el guarda de p es aparte).
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import math
import os
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
    _load_coefficients,
    _multiply_m,
    _multiply_y0,
    _phase_by_bits,
    _select_interval,
    _square,
)

log = logging.getLogger("nr_bin_g")

DBHEXA_PRECISION = Precision(
    delta_bits=14,
    coef_bits=17,
    square_bits=27,
    product_bits=27,
    result_bits=27,
)


def _round(builder: km.CircuitBuilder, inverse: bool, guard: km.q,
           target: km.array) -> None:
    """`target += guarda` (ida) o `target -= guarda` (vuelta): la fraccion
    mayor gana. El guarda queda como estaba; lo restaura la vuelta."""
    if inverse:
        builder.isub(1, target=target, control=guard)
    else:
        builder.iadd(1, target=target, control=guard)


def _horner_g(builder: km.CircuitBuilder, inverse: bool, prec: Precision,
              x: km.array, selectors: km.array, coefs: list[km.array],
              scratch: km.array, guards: km.array) -> None:
    """Como `_horner`, pero cada paso lleva su bit de guarda y redondea al final.

    El objetivo de cada paso se pasa concatenado [guarda]+acc y la lista de
    terminos se extiende un termino (el de peso 2^-(wc+1), la guarda). En la
    vuelta, primero se deshace el redondeo y luego las sumas, en espejo.
    """
    width, wc = len(x), len(coefs[0])
    delta = [(selectors[2], 1)]  # (qubit, m) con peso 2^-m: el bit mitad, luego bits de M.
    delta += [(x[width - 2 - m], m) for m in range(2, min(prec.delta_bits, width - 2) + 1)]
    c0, c1, c2, c3 = coefs
    steps = ((c2, c3), (c1, c2), (c0, c1))
    horner_step = builder.mark('horner_step')
    order = list(reversed(range(3))) if inverse else list(range(3))
    for si in order:
        acc, mult = steps[si]
        guard = guards[si]
        target = km.array([guard]) + acc
        with horner_step:
            if inverse:
                _round(builder, True, guard, acc)
            for control, m in delta:
                _add_row(builder, inverse, control,
                         [(mult[i], i - m + 1) for i in range(m - 1, wc)],
                         target, scratch, subtract=True)
            if not inverse:
                _round(builder, False, guard, acc)


def _compute_y1_bin_g(builder: km.CircuitBuilder, inverse: bool, prec: Precision,
                      x: km.array, sb: km.array, selectors: km.array,
                      coefs: list[km.array], square: km.array, z: km.array,
                      y1: km.array, scratch: km.array, guards: km.array) -> None:
    """Como `_compute_y1_bin`, con redondeo de guarda en cada etapa.

    Guardas: 0-2 Horner, 3 square, 4 multiply_m, 5 multiply_y0.
    """
    y0, p = coefs[0], y1[:prec.result_bits + 1]  # p ocupa los bits bajos de y1
    temps = coefs[0]  # en 0 durante normalizar (ida y vuelta)
    g_h, g_sq, g_m, g_y0 = guards[:3], guards[3], guards[4], guards[5]
    with builder.mark("uncompute_y1" if inverse else "compute_y1"):
        if inverse:
            with builder.mark("denormalize"):
                _denormalize_bin(builder, inverse, sb, y1, len(p))
            _round(builder, True, g_y0, p)
            with builder.mark("multiply_y0"):
                _multiply_y0(builder, inverse, y0, z, km.array([g_y0]) + p, scratch)
            with builder.mark("correct"):
                _correct(builder, inverse, z)
            _round(builder, True, g_m, z)
            with builder.mark("multiply_m"):
                _multiply_m(builder, inverse, x, square, km.array([g_m]) + z, scratch)
            _round(builder, True, g_sq, square)
            with builder.mark("square"):
                _square(builder, inverse, y0, km.array([g_sq]) + square, scratch)
            with builder.mark("horner"):
                _horner_g(builder, inverse, prec, x, selectors, coefs, scratch, g_h)
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
                _horner_g(builder, inverse, prec, x, selectors, coefs, scratch, g_h)
            with builder.mark("square"):
                _square(builder, inverse, y0, km.array([g_sq]) + square, scratch)
            _round(builder, False, g_sq, square)
            with builder.mark("multiply_m"):
                _multiply_m(builder, inverse, x, square, km.array([g_m]) + z, scratch)
            _round(builder, False, g_m, z)
            with builder.mark("correct"):
                _correct(builder, inverse, z)
            with builder.mark("multiply_y0"):
                _multiply_y0(builder, inverse, y0, z, km.array([g_y0]) + p, scratch)
            _round(builder, False, g_y0, p)
            with builder.mark("denormalize"):
                _denormalize_bin(builder, inverse, sb, y1, len(p))


def build_nr_bin_g_circuit(n_p: int, *, prec: Precision = DBHEXA_PRECISION,
                           compute_only: bool = False) -> km.Circuit:
    """El circuito NR/dbhexa con `s` binario y redondeo de guarda por etapa."""
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
    # Scratch de 30: el objetivo mas ancho es z con guarda (29+1).
    scratch = alloc(max(prec.square_bits + 1, prec.product_bits + 3,
                        prec.result_bits + 2), "scratch")
    guards = alloc(6, "guards")
    registers = (x, sb, selectors, coefs, square, z, y1, scratch, guards)
    _compute_y1_bin_g(builder, False, prec, *registers)
    if not compute_only:
        _phase_by_bits(builder, y1)
        _compute_y1_bin_g(builder, True, prec, *registers)
        for reg in (y1, sb, selectors, *coefs, square, z, scratch, guards):
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
    try:
        sys.path.insert(0, os.path.expanduser(os.environ.get("QCC_INVSQRT_SWEEP", "~/workspace/qcc-data/invsqrt-sweep")))
        from error_slack import model as _slack_model
        err = _slack_model(np.arange(1, max_x + 1), rounding="stage_all")
        exact = 1.0 / np.sqrt(np.arange(1, max_x + 1, dtype=np.float64))
        rel = np.abs(err - exact) / exact / 2.0**-24
        log.info("Modelo stage_all: max error %.4f de tolerancia en x=%d.",
                 rel.max(), rel.argmax() + 1)
    except Exception as exc:  # noqa: BLE001 - el modelo es informativo
        log.warning("No se pudo correr el modelo stage_all: %s", exc)
    circ = build_nr_bin_g_circuit(a.n_p, prec=prec)
    q = int(circ.num_qubits)
    t_toff = int(circ.operation_statistics().num_toffoli_like)
    log.info("circuito: Q=%d T=%d", q, t_toff)
    if _HAS_QCC_LOG:
        _qcc_emit("invsqrt_nr_bin_g", "build", "ok",
                  inputs={"n_p": a.n_p, "prec": "dbhexa-27/27/27-guard"},
                  outputs={"Q": q, "T": t_toff},
                  duration_s=time.time() - t0)
    if a.output:
        t0 = time.time()
        circ.to_file(a.output, format=a.format)
        digest = hashlib.sha256(Path(a.output).read_bytes()).hexdigest()
        log.info("sha256 %s", digest)
        if _HAS_QCC_LOG:
            _qcc_emit("invsqrt_nr_bin_g", "write", "ok",
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
