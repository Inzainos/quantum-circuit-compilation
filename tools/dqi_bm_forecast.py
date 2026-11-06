#!/usr/bin/env python3
"""Pronostico clasico (forecast) del BM sobre GF(2^12) para el decodificador DQI.

Para cada peso de error k se corre BM sobre sindromes reales y se registra, por ronda:
  - cero   : discrepancia d == 0 (no hay actualizacion)
  - replace: d != 0 y 2L <= r (cambio de longitud; la rama se puede recuperar del estado, invariante sigma0*delta=1)
  - retain : d != 0 y 2L >  r (hay que guardar delta en historial)
Resultado: distribucion (ponderada por w_k^2 como el verificador) del numero de rondas retain,
rondas con cambio de longitud y la longitud final L. Sirve para dimensionar el historial y el
presupuesto de fallo ANTES de construir el circuito.
Logs: logs/dqi_bm_forecast.log
"""
from __future__ import annotations
import sys, logging, argparse, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import dqi_bm_model as M
v = M.v

log = logging.getLogger("bm_forecast")


def traza(S):
    """BM con traza por ronda. Devuelve (sig, L, lista de eventos 'z','p','t')."""
    n = len(S)
    sig = [1] + [0] * n; B = [1] + [0] * n
    L, m, b = 0, 1, 1
    ev = []
    for r in range(n):
        d = 0
        for i in range(0, min(L, r) + 1):
            d ^= M.mul(sig[i], S[r - i])
        if d == 0:
            ev.append("z"); m += 1; continue
        c = M.mul(d, M.inv(b))
        T = sig[:]
        for i in range(0, n + 1 - m):
            sig[i + m] ^= M.mul(c, B[i])
        if 2 * L <= r:
            L = r + 1 - L; B = T; b = d; m = 1; ev.append("p")  # replace
        else:
            m += 1; ev.append("t")                              # retain
    return sig[:L + 1], L, ev


def traza_empate_replace(S):
    """BM variante del paper (SI eq. 33): en empate de longitudes se hace REPLACE (retain solo si Ltau~ < Lsigma).
    Estado: sigma, tau, delta, s (desplazamiento: tau~ = x^s tau), Lsigma, Ltau. Eventos: z (delta=0), p (replace), t (retain)."""
    n = len(S)
    sig = [1] + [0] * (n + 1); tau = [1] + [0] * (n + 1)
    dl, s, Ls, Lt = 1, 1, 0, 0
    ev = []
    for r in range(n):
        D = 0
        for i in range(0, min(Ls, r) + 1):
            D ^= M.mul(sig[i], S[r - i])
        if D == 0:
            ev.append("z"); s += 1; continue
        c = M.mul(D, M.inv(dl))
        viejo = sig[:]
        for i in range(0, n + 1 - s):
            sig[i + s] ^= M.mul(c, tau[i])
        if Lt + s >= Ls:            # replace (incluye empate)
            Ln = max(Ls, Lt + s)
            tau = viejo; dl = D; Lt = Ls; s = 1; Ls = Ln; ev.append("p")
        else:                       # retain (guarda D)
            s += 1; ev.append("t")
    return sig[:Ls + 1], Ls, ev


def sindromes(rng, k, n=70, m_pos=4095):
    pos = rng.choice(m_pos, size=k, replace=False)
    vals = rng.integers(1, M.Q, size=k)
    S = []
    for t in range(n):
        s = 0
        for p_, e in zip(pos, vals):
            s ^= M.mul(int(e), int(M.EXP[(int(p_) * t) % (M.Q - 1)]))
        S.append(s)
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--por-k", type=int, default=12, help="ensayos por peso k")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n", type=int, default=70)
    ap.add_argument("--l", type=int, default=35)
    ap.add_argument("--variante", choices=["massey", "paper"], default="massey")
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "dqi_bm_forecast.log", mode="w")])
    rng = np.random.default_rng(a.seed)
    r = v.default_num_accepted_values(12)
    p = v.optimal_dqi_weights(4095, a.l, 12, r) ** 2
    p = p / p.sum()
    log.info("pesos w_k^2: k<=23: %.3e  k=35: %.3f  media k=%.2f", p[:24].sum(), p[35], float(np.arange(len(p)) @ p))
    filas = []
    for k in range(a.l + 1):
        if p[k] < 1e-9:
            continue
        ret, rep, ceros, falla = [], [], [], 0
        for _ in range(a.por_k):
            S = sindromes(rng, k, a.n)
            sig, L, ev = (traza(S) if a.variante == "massey" else traza_empate_replace(S))
            falla += (L != k)
            ret.append(ev.count("t")); rep.append(ev.count("p")); ceros.append(ev.count("z"))
        filas.append((k, p[k], np.mean(ret), max(ret), np.mean(rep), np.mean(ceros), falla))
        log.info("k=%2d p=%.3e  retain media=%.1f max=%d | replace media=%.1f | ceros media=%.1f | L!=k: %d/%d",
                 k, p[k], np.mean(ret), max(ret), np.mean(rep), np.mean(ceros), falla, a.por_k)
    pm = lambda idx: sum(f[1] * f[idx] for f in filas)
    log.info("PONDERADO: retain=%.2f replace=%.2f ceros=%.2f  (rondas totales n=%d)", pm(2), pm(4), pm(5), a.n)
    json.dump([list(map(float, f)) for f in filas], open(ROOT / "logs" / "dqi_bm_forecast.json", "w"))


if __name__ == "__main__":
    main()
