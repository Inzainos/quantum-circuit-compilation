#!/usr/bin/env python3
"""
Barrido de bits de segmento / bits fraccionarios del plan "meseta MAC" contra la
tolerancia REAL del verificador (relativa, 2^-24).

Usa SIN CAMBIOS las funciones del script original adjunto
(invsqrt_mac_bench_original.py): compute_chebyshev_piecewise_coeffs y
fixed_point_truncated_mul. Solo mide error numerico; NO mide Q ni Toffoli
(el script original no los mide: los calcula con constantes).

Uso:
    python3 -I sweep_seg_bits.py [--samples 20000] [--log ruta.log]
"""
import argparse
import logging
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import invsqrt_mac_bench_original as m  # noqa: E402

TOL = 2.0 ** -24


def build_logger(path):
    log = logging.getLogger("sweep_seg_bits")
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(path, mode="w")):
        h.setFormatter(fmt)
        log.addHandler(h)
    return log


def max_rel_err(seg_bits, frac_bits, p_cut, n):
    prev = logging.root.manager.disable
    logging.disable(logging.CRITICAL)  # silencia el logger del script original
    try:
        coeffs = m.compute_chebyshev_piecewise_coeffs(seg_bits, frac_bits)
    finally:
        logging.disable(prev)
    scale = 1 << frac_bits
    dx_bits = frac_bits - seg_bits
    rng = np.random.default_rng(1)
    xs = np.concatenate([np.linspace(1.0, 2.0 - 1e-9, n), rng.uniform(1.0, 2.0, n)])
    worst = 0.0
    worst_x = 1.0
    for x in xs:
        xf = int(x * scale)
        mant = xf - scale
        s = (mant >> dx_bits) & ((1 << seg_bits) - 1)
        dx = mant & ((1 << dx_bits) - 1)
        c0, c1, c2 = coeffs[s]
        t1 = m.fixed_point_truncated_mul(c2, dx, frac_bits, p_cut, seg_bits)
        a1 = c1 + t1
        t2 = -m.fixed_point_truncated_mul(abs(a1), dx, frac_bits, p_cut, seg_bits)
        y = (c0 + t2) / scale
        ye = 1.0 / math.sqrt(x)
        e = abs(y - ye) / ye
        if e > worst:
            worst, worst_x = e, x
    return worst, worst_x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=20000)
    ap.add_argument("--log", default=os.path.join(HERE, "..", "logs", "sweep_seg_bits.log"))
    a = ap.parse_args()
    log = build_logger(a.log)
    log.info("tolerancia relativa del verificador 2^-24 = %.6e", TOL)
    log.info("dominio medido: x en [1,2) (el plan original NO cubre [2,4) en su script)")
    log.info("%8s %9s %6s  %-12s %-10s %s", "seg_bits", "frac_bits", "p_cut", "max_rel_err", "x(2^-24)", "peor_x")
    for sb in (4, 5, 6, 7, 8, 9):
        for fb in (28, 30, 34):
            t = time.perf_counter()
            e, wx = max_rel_err(sb, fb, fb, a.samples)
            log.info("%8d %9d %6d  %.3e    %8.3f   %.8f (%.1fs)", sb, fb, fb, e, e / TOL, wx, time.perf_counter() - t)


if __name__ == "__main__":
    main()
