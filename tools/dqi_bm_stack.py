#!/usr/bin/env python3
"""Distribucion de rondas RETAIN (profundidad de pila de discrepancias) del BM variante-paper (empate->replace),
muestreando k ~ w_k^2 como el verificador y sindromes S_t=sum v_j X_j^t, t=1..n (igual que verify_submission_dqi).
Tambien verifica correctitud: L==k y sigma(X_j^-1)=0. Log: logs/dqi_bm_stack.log"""
import sys, logging, argparse, collections
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import dqi_bm_model as M
from dqi_bm_forecast import traza_empate_replace
v = M.v
log = logging.getLogger("bm_stack")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n-muestras", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=11); ap.add_argument("--n", type=int, default=70)
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "dqi_bm_stack.log", mode="w")])
    rng = np.random.default_rng(a.seed)
    p = v.optimal_dqi_weights(4095, a.n // 2, 12, v.default_num_accepted_values(12)) ** 2; p /= p.sum()
    prof = collections.Counter(); malas = 0; roots_mal = 0; ret_en_k = collections.defaultdict(int)
    for it in range(a.n_muestras):
        k = int(rng.choice(len(p), p=p))
        pos = rng.choice(4095, size=k, replace=False); vals = rng.integers(1, 4096, size=k)
        S = []
        for t in range(1, a.n + 1):
            s = 0
            for q, e in zip(pos, vals):
                s ^= M.mul(int(e), int(M.EXP[(int(q) * t) % 4095]))
            S.append(s)
        sig, L, ev = traza_empate_replace(S)
        nr = ev.count("t"); prof[nr] += 1
        if nr: ret_en_k[k] += 1
        if L != k: malas += 1
        else:
            for q in pos:
                xi = int(M.EXP[(-int(q)) % 4095]); acc = 0
                for i, c in enumerate(sig):
                    acc ^= M.mul(c, int(M.EXP[(int(M.LOG[xi]) * i) % 4095])) if xi else 0
                if acc: roots_mal += 1; break
    N = a.n_muestras
    log.info("muestras=%d  L!=k: %d  raices incorrectas: %d", N, malas, roots_mal)
    for nr in sorted(prof): log.info("rondas retain=%d : %d  (%.3e)", nr, prof[nr], prof[nr] / N)
    log.info(">=1 retain: %.3e   >=2 retain: %.3e", sum(c for r_, c in prof.items() if r_ >= 1) / N, sum(c for r_, c in prof.items() if r_ >= 2) / N)
main()
