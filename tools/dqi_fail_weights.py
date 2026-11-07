#!/usr/bin/env python3
"""Reporta el peso de error (k) de los tiros fallidos del decodificador. Uso: python3 tools/dqi_fail_weights.py circuito.kmb --shots 102400 --seed 7"""
import sys, argparse, logging
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "src"))
import kickmix as km
import dqi_harness as H
logging.basicConfig(level=logging.INFO, format="%(message)s")
ap = argparse.ArgumentParser(); ap.add_argument("circuit"); ap.add_argument("--shots", type=int, default=102400); ap.add_argument("--seed", type=int, default=7)
a = ap.parse_args()
c = km.Circuit.from_file(a.circuit)
for b0, bad, tof, pesos in H.corre(c, a.shots, a.seed):
    if bad.any():
        logging.info("lote %d: fallos en tiros %s con peso k=%s", b0, np.nonzero(bad)[0].tolist(), pesos[bad].tolist())
logging.info("fin")
