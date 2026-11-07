#!/usr/bin/env python3
"""Barrido de parametros (deg, j, wc, dd, sesgo) de invsqrt_logshift2: filtra con el modelo clasico (error relativo < tolerancia)
y construye el circuito para medir Q y T. Escribe logs/invsqrt_sweep.csv. Uso: python3 tools/invsqrt_sweep.py --part 0 --de 2"""
import sys, argparse, itertools, logging, csv, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "verifiers" / "invsqrt"))
from invsqrt_piecewise import PWSpec
import invsqrt_halfsplit as H
from invsqrt_logshift2 import PipelineLog2
logging.disable(logging.CRITICAL)
ap = argparse.ArgumentParser(); ap.add_argument("--part", type=int, default=0); ap.add_argument("--de", type=int, default=2)
ap.add_argument("--tol", type=float, default=2 ** -24 * 0.97)
a = ap.parse_args()
xs = np.arange(1, 3 * (2 ** 10 - 2) ** 2 + 1, dtype=np.int64)
out = ROOT / "logs" / f"invsqrt_sweep_{a.part}.csv"
grid = [(d, j, wc, dd, sg) for d in (2,) for j in (7, 8, 9) for wc in range(25, 30) for dd in range(10, 15) for sg in range(0, 5)]
grid = [g for i, g in enumerate(grid) if i % a.de == a.part]
with open(out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["deg", "j", "wc", "dd", "sesgo", "max_err_over_tol", "Q", "T"])
    for d, j, wc, dd, sg in grid:
        try:
            spec = PWSpec(deg=d, j=j, wc=wc, dd=dd)
            y1 = H.modelo(spec, xs, sesgo=sg)
            err = float(H.error_relativo(spec, xs, y1).max())
        except Exception:
            continue
        if err > a.tol:
            continue
        try:
            c = PipelineLog2(spec, sg).construye()
        except Exception as e:
            continue
        w.writerow([d, j, wc, dd, sg, err / 2 ** -24, c.num_qubits, int(c.operation_statistics().num_toffoli_like)]); fh.flush()
