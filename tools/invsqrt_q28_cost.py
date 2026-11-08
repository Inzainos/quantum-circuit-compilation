#!/usr/bin/env python3
"""Costo REAL (kickmix) del cluster q28 de invsqrt compuesto a monomios (rotaciones_q28_en_x.json).

Construye el circuito de fase  exp(i*pi * sum_k a_k * parity_k(x))  donde parity_k es el XOR (ANF) de los monomios de la
rotacion k, con las variables base como qubits de entrada, y mide:
  * Toffoli medios por tiro, T, rotaciones, qubits;
  * correccion de fase contra la formula clasica (todos los x muestreados) y ancillas limpias.

Arquitectura (sin copias, ANDs compartidos):
  Pasada 1: DFS sobre el trie global de monomios (orden de variables elegido); cada nodo de grado>=2 se calcula con un AND
            (1 Toffoli) y se hace CX hacia el qubit de paridad de cada rotacion que lo contiene; al volver del DFS el AND se
            borra por medicion (0 Toffoli).
  Rotaciones: z_pow(paridad_k, a_k) con a_k en medias vueltas (potencias de 2 del archivo).
  Pasada 2: cada paridad se mide en base X (hmr); la fase (-1)^{m_k * parity_k(x)} = prod_monomios (-1)^{m_k * monomio}
            se corrige con CZ(prefijo, ultima variable) condicionados a m_k (DFS por rotacion; los Toffoli del prefijo se
            ejecutan solo si m_k=1, es decir, la mitad de las veces).
Logs: logging 'invsqrt_q28' y eventos qcc_log (qcc_log.auto al inicio del main).
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import kickmix as km  # noqa: E402

log = logging.getLogger("invsqrt_q28")


def cargar(path: Path, orden: str):
    rot = json.loads(Path(path).read_text())
    mons = []
    angs = []
    for r in rot:
        a = Fraction(2) ** round(math.log2(r["angle"]))
        angs.append(a)
        mons.append([tuple(m) for m in r["monomials"]])
    vars_ = sorted({v for ms in mons for m in ms for v in m}, key=lambda s: int(s[1:]))
    freq = {v: sum(1 for ms in mons for m in ms if v in m) for v in vars_}
    if orden == "frecuencia":
        vars_ = sorted(vars_, key=lambda v: -freq[v])
    idx = {v: i for i, v in enumerate(vars_)}
    mons = [[tuple(sorted(idx[v] for v in m)) for m in ms] for ms in mons]
    return vars_, angs, mons


def construir(vars_, angs, mons):
    b = km.CircuitBuilder()
    X = b.create_quantum_register(len(vars_), name="x")
    Pq = b.alloc_qubits(len(mons))
    # trie global: nodo = tupla (prefijo); hijos ordenados
    trie = {}
    own = {}                                    # monomio -> lista de rotaciones que lo contienen
    for k, ms in enumerate(mons):
        for m in ms:
            own.setdefault(m, []).append(k)
            for j in range(1, len(m) + 1):
                trie.setdefault(m[:j - 1], set()).add(m[j - 1])
    consts = own.get((), [])
    for k in consts:
        b.x(Pq[k])

    def dfs1(prefijo, qprefijo):
        for v in sorted(trie.get(prefijo, ())):
            nodo = prefijo + (v,)
            if not prefijo:
                q = X[v]; extra = None
            else:
                extra = b.alloc_qubits(1)[0]
                b.init_and(qprefijo, X[v], extra); q = extra
            for k in own.get(nodo, ()):
                b.cx(q, Pq[k])
            dfs1(nodo, q)
            if extra is not None:
                b.del_and(qprefijo, X[v], extra); b.free(extra)

    dfs1((), None)
    for k, a in enumerate(angs):
        b.z_pow(Pq[k], a)
    m = b.alloc_bits(len(mons))
    b.hmr(Pq, m)
    for k, ms in enumerate(mons):
        b.push_condition(m[k])
        if () in ms:
            b.neg()
        t = {}
        for mm in ms:
            if mm:
                for j in range(1, len(mm) + 1):
                    t.setdefault(mm[:j - 1], set()).add(mm[j - 1])
        S = set(ms)

        def dfs2(prefijo, qprefijo):
            for v in sorted(t.get(prefijo, ())):
                nodo = prefijo + (v,)
                if not prefijo:
                    if nodo in S:
                        b.z(X[v])
                    dfs2(nodo, X[v])
                else:
                    if nodo in S:
                        b.cz(qprefijo, X[v])
                    if nodo in t:                       # solo se calcula el AND si algun monomio mas largo lo usa
                        extra = b.alloc_qubits(1)[0]
                        b.init_and(qprefijo, X[v], extra)
                        dfs2(nodo, extra)
                        b.del_and(qprefijo, X[v], extra); b.free(extra)

        dfs2((), None)
        b.pop_condition()
    for q in Pq:
        b.free(q)
    return b.finish_circuit(), len(vars_)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(ROOT / "data/invsqrt-sweep/rotaciones_q28_en_x.json"))
    ap.add_argument("--orden", choices=["indice", "frecuencia"], default="frecuencia")
    ap.add_argument("--tiros", type=int, default=4096)
    ap.add_argument("--eps", type=float, default=1e-9, help="error de sintesis por rotacion (para el costo en T)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    vars_, angs, mons = cargar(Path(a.json), a.orden)
    log.info("variables=%d rotaciones=%d monomios_distintos=%d", len(vars_), len(mons), len({m for ms in mons for m in ms}))
    c, nv = construir(vars_, angs, mons)
    rng = np.random.default_rng(1)
    xs = rng.integers(0, 1 << nv, size=a.tiros, dtype=np.int64)
    sim = km.Simulator(batch_size=a.tiros, debug_print=False, counting_operations=True, seed=3)
    sim.use_same_registers_as(c)
    bits = ((xs[None, :] >> np.arange(nv)[:, None]) & 1) == 1
    sim.write_across_shots(km.array([km.q(i) for i in range(nv)]), bits)
    sim.do(c)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
    restaurado = bool((out[:nv] == bits).all())
    limpio = not out[nv:].any()
    # fase esperada (medias vueltas, modulo 2)
    idx_bits = {i: bits[i] for i in range(nv)}
    esperado = np.zeros(a.tiros)
    for k, ms in enumerate(mons):
        par = np.zeros(a.tiros, dtype=bool)
        for m in ms:
            t = np.ones(a.tiros, dtype=bool)
            for v in m:
                t &= idx_bits[v]
            par ^= t
        esperado += float(angs[k]) * par
    peor = 0.0
    for i in range(a.tiros):
        ph = float(sim.read_shot_phase(i))
        d = (ph - esperado[i] + 1.0) % 2.0 - 1.0
        peor = max(peor, abs(d))
    st = sim.operation_statistics()
    tof = st.num_toffoli_like / a.tiros
    n_t = st.num_t_like / a.tiros
    n_rot = st.num_z_pow(min_clifford_hierarchy_level=4) / a.tiros
    tcost = n_t + n_rot * (0.56 * math.log2(1 / a.eps) + 5.3)
    log.info("x restaurado=%s ancillas limpias=%s error de fase peor=%.3e medias vueltas", restaurado, limpio, peor)
    log.info("Toffoli medios=%.1f (max estatico=%d) T=%.1f rotaciones=%.1f qubits=%d", tof,
             c.operation_statistics().num_toffoli_like, n_t, n_rot, c.num_qubits)
    log.info("C = Toffoli + T/4 con eps=%.1e -> %.1f ; Q*C = %.0f", a.eps, tof + tcost / 4, c.num_qubits * (tof + tcost / 4))


if __name__ == "__main__":
    try:  # logs estructurados (qcc_log): una linea por script
        import sys as _qs
        from pathlib import Path as _qp
        _qs.path.insert(0, str(_qp(__file__).resolve().parent.parent / "tools"))
        from qcc_log import auto as _qcc_auto
        _qcc_auto(__file__)
    except Exception:  # noqa: BLE001
        pass
    main()
