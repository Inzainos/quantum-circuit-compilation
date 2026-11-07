#!/usr/bin/env python3
"""Grados reales de sigma y de la plantilla desplazada por ronda (variante paper), muestreando k ~ w_k^2 como el
verificador. Sirve para fijar cotas de bucle (disc: i<=Ls ; update/swap: i<=max(Ls, Lt+s)) y medir la probabilidad de
que una cota candidata se viole (eso es fallo del circuito, presupuesto ~1e-4).  Log: logs/dqi_bm_bounds.log"""
import sys, logging, argparse, collections
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import dqi_bm_model as M
v = M.v; mul, inv = M.mul, M.inv
log = logging.getLogger("bm_bounds")

def trayectoria(S):
    n = len(S); sig = [1] + [0]*(n+1); tau = [1] + [0]*(n+1)
    dl, s, Ls, Lt = 1, 1, 0, 0; tray = []
    for r in range(n):
        D = 0
        for i in range(0, min(Ls, r) + 1): D ^= mul(sig[i], S[r-i])
        tray.append((Ls, max(Ls, Lt + s), D != 0))   # (grado sigma, grado update, ronda activa)
        if D == 0: s += 1; continue
        c = mul(D, inv(dl)); viejo = sig[:]
        for i in range(0, n+1-s): sig[i+s] ^= mul(c, tau[i])
        if Lt + s >= Ls: Ln = max(Ls, Lt+s); tau = viejo; dl = D; Lt = Ls; s = 1; Ls = Ln
        else: s += 1
    return tray

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n-muestras", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=17); a = ap.parse_args()
    (ROOT/"logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT/"logs"/"dqi_bm_bounds.log", mode="w")])
    rng = np.random.default_rng(a.seed); n = 70
    p = v.optimal_dqi_weights(4095, 35, 12, v.default_num_accepted_values(12))**2; p /= p.sum()
    N = a.n_muestras; maxA = [0]*n; maxC = [0]*n
    cand = {m: [0, 0] for m in range(0, 4)}          # viola cota r//2+1+m  (disc, update)
    for it in range(N):
        k = int(rng.choice(len(p), p=p))
        pos = rng.choice(4095, size=k, replace=False); vals = rng.integers(1, 4096, size=k)
        S = []
        for t in range(1, n+1):
            s = 0
            for q, e in zip(pos, vals): s ^= mul(int(e), int(M.EXP[(int(q)*t) % 4095]))
            S.append(s)
        tr = trayectoria(S)
        for r, (A, C, act) in enumerate(tr):
            maxA[r] = max(maxA[r], A)
            if act: maxC[r] = max(maxC[r], C)
        for m in cand:
            if any(A > r//2 + 1 + m for r, (A, C, act) in enumerate(tr)): cand[m][0] += 1
            if any(act and C > r//2 + 1 + m for r, (A, C, act) in enumerate(tr)): cand[m][1] += 1
    log.info("max grado sigma por ronda: %s", maxA)
    log.info("max grado update  por ronda: %s", maxC)
    for m, (a1, a2) in cand.items():
        log.info("cota r//2+1+%d : viola disc en %d/%d, viola update en %d/%d", m, a1, N, a2, N)
main()
