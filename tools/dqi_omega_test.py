#!/usr/bin/env python3
"""Prueba de la etapa C: ida (omega in place) contra la formula clasica y ida+vuelta restaura todo. Entradas: sigma con
sigma_0 != 0 aleatorio (y delta = sigma_0^-1) y S aleatorios + un bloque con tiros reales del modelo.
Log: logs/dqi_omega_test.log"""
import sys, argparse, logging
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import kickmix as km
import dqi_bm_model as G
import dqi_omega_stage as OM
log = logging.getLogger("omega_test"); DEG = 12

def bits(vals): return ((np.array(vals, dtype=np.int64)[None, :] >> np.arange(DEG)[:, None]) & 1) == 1

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tiros", type=int, default=128); ap.add_argument("--seed", type=int, default=4)
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "dqi_omega_test.log", mode="w")])
    LS, LO, n, B = 36, 35, 70, a.tiros
    rng = np.random.default_rng(a.seed)
    sig = [[int(x) for x in rng.integers(0, 4096, size=B)] for _ in range(LS)]
    sig[0] = [int(x) for x in rng.integers(1, 4096, size=B)]
    delta = [G.inv(x) for x in sig[0]]
    S = [[int(x) for x in rng.integers(0, 4096, size=B)] for _ in range(n)]
    esperado = []
    for i in range(LO):
        row = []
        for sh in range(B):
            acc = 0
            for j in range(0, i + 1):
                acc ^= G.mul(sig[j][sh], S[i - j][sh])
            row.append(acc)
        esperado.append(row)
    nq = (LS + 1 + n) * DEG
    init = np.concatenate([bits(sig[i]) for i in range(LS)] + [bits(delta)] + [bits(S[i]) for i in range(n)], axis=0)
    for iv in (False, True):
        c = OM.build_stage_c(LS, LO, n, DEG, ida_y_vuelta=iv)
        sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=a.seed)
        sim.use_same_registers_as(c)
        qs = km.array([km.q(i) for i in range(nq)])
        sim.write_across_shots(qs, init); sim.do(c)
        out = sim.read_across_shots(qs)
        anc = km.array([km.q(i) for i in range(nq, c.num_qubits)])
        sucio = int(sim.read_across_shots(anc).any(axis=0).sum()) if c.num_qubits > nq else 0
        pf = int(sim.read_phase_flipped_across_shots().sum())
        if not iv:
            base = (LS + 1) * DEG
            malos = 0
            for i in range(LO):
                got = np.zeros(B, dtype=np.int64)
                for bit in range(DEG): got |= out[base + i * DEG + bit].astype(np.int64) << bit
                malos += int((got != np.array(esperado[i])).sum())
            # entradas intactas: sigma, delta y S_i con i>=LO
            intactas = bool((out[:base] == init[:base]).all() and (out[base + LO * DEG:] == init[base + LO * DEG:]).all())
            log.info("IDA: palabras omega incorrectas=%d  entradas intactas=%s  ancillas sucias=%d  fase volteada=%d  toffoli/tiro=%.0f",
                     malos, intactas, sucio, pf, sim.operation_statistics().num_toffoli_like / B)
        else:
            rest = int((out != init).any(axis=0).sum())
            log.info("IDA+VUELTA: tiros no restaurados=%d  ancillas sucias=%d  fase volteada=%d  toffoli/tiro=%.0f",
                     rest, sucio, pf, sim.operation_statistics().num_toffoli_like / B)
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
