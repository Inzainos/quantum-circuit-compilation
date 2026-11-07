#!/usr/bin/env python3
"""Prueba del decodificador v1 completo: fase del simulador vs fase directa; S restaurado; ancillas limpias.
Uso: python3 tools/dqi_decoder_test.py --posiciones 256 --tiros 64   Log: logs/dqi_decoder_test.log"""
import sys, argparse, logging, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import kickmix as km
import dqi_bm_model as G
import dqi_phase_model as PM
import dqi_decoder_v1 as DEC
log = logging.getLogger("decoder_test"); DEG = 12

def bits_of(vals):
    a = np.array(vals, dtype=np.int64)
    return ((a[None, :] >> np.arange(DEG)[:, None]) & 1) == 1

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--posiciones", type=int, default=256)
    ap.add_argument("--tiros", type=int, default=64); ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--n", type=int, default=70); ap.add_argument("--kmax", type=int, default=35)
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "dqi_decoder_test.log", mode="w")])
    n, m, B = a.n, 4095, a.tiros
    t0 = time.time(); c, bm = DEC.build_decoder(n=n, positions=range(a.posiciones))
    log.info("circuito: %d posiciones toffoli-like=%d qubits=%d build %.1fs", a.posiciones, c.operation_statistics().num_toffoli_like, c.num_qubits, time.time() - t0)
    rng = np.random.default_rng(a.seed)
    Sv = [[0] * B for _ in range(n)]; Mall = np.zeros((m, B), dtype=np.int64); ref = np.zeros(B, dtype=bool)
    for sh in range(B):
        k = int(rng.integers(1, a.kmax + 1))
        pos = [int(x) for x in rng.choice(a.posiciones, size=k, replace=False)]
        vals = [int(x) for x in rng.integers(1, 4096, size=k)]
        Ms = [int(x) for x in rng.integers(0, 4096, size=m)]
        for t in range(1, n + 1):
            s = 0
            for q_, e in zip(pos, vals): s ^= G.mul(e, int(G.EXP[(q_ * t) % 4095]))
            Sv[t - 1][sh] = s
        Mall[:, sh] = Ms; ref[sh] = PM.fase_directa(pos, vals, Ms)
    init = np.concatenate([bits_of(Sv[i]) for i in range(n)], axis=0)
    sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=a.seed); sim.use_same_registers_as(c)
    nq = n * DEG
    sim.write_across_shots(km.array([km.q(i) for i in range(nq)]), init)
    cb = [km.b(j * DEG + k) for j in range(m) for k in range(DEG)]
    sim.write_across_shots(km.array(cb), np.concatenate([bits_of(Mall[j]) for j in range(m)], axis=0))
    t1 = time.time(); sim.do(c); log.info("simulacion %.1fs", time.time() - t1)
    pf = sim.read_phase_flipped_across_shots()
    rest = sim.read_across_shots(km.array([km.q(i) for i in range(nq)])) ^ init
    anc = [km.q(i) for i in range(nq, c.num_qubits)]
    sucio = sim.read_across_shots(km.array(anc)).any(axis=0)
    log.info("tiros=%d fase incorrecta=%d S no restaurado=%d ancillas sucias=%d (fase=1 en ref: %d)", B, int((pf != ref).sum()),
             int(rest.any(axis=0).sum()), int(sucio.sum()), int(ref.sum()))
    log.info("RESULTADO: %s", "PASA" if ((pf == ref).all() and not rest.any() and not sucio.any()) else "FALLA")
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
