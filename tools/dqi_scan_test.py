#!/usr/bin/env python3
"""Prueba de la etapa A (barrido de fase) contra la fase directa. sigma/omega/psi se calculan con el modelo clasico y se
escriben en los registros del circuito; se compara la fase volteada del simulador con paridad(sum popcount(e&M)),
y se exige que los registros se restauren y que no queden ancillas sucias.
Uso: python3 tools/dqi_scan_test.py --posiciones 256 --tiros 64   Log: logs/dqi_scan_test.log"""
import sys, argparse, logging, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import kickmix as km
import dqi_bm_model as G
import dqi_phase_model as PM
from dqi_bm_forecast import traza_empate_replace
import dqi_scan_stage as SC
log = logging.getLogger("scan_test")
DEG = 12

def bits_of(vals, batch):
    a = np.array(vals, dtype=np.int64)            # (batch,)
    return ((a[None, :] >> np.arange(DEG)[:, None]) & 1) == 1   # (DEG, batch)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--posiciones", type=int, default=256)
    ap.add_argument("--tiros", type=int, default=64); ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--n", type=int, default=70); ap.add_argument("--kmax", type=int, default=35)
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "dqi_scan_test.log", mode="w")])
    LS, LO, LP, m = 36, 35, 35, 4095
    t0 = time.time()
    c = SC.build_stage_a(LS, LO, LP, m, positions=range(a.posiciones))
    st = c.operation_statistics()
    log.info("circuito: %d posiciones, toffoli-like=%d (esperado %d), qubits=%d, build %.1fs", a.posiciones,
             st.num_toffoli_like, 23 * a.posiciones, c.num_qubits, time.time() - t0)
    rng = np.random.default_rng(a.seed)
    B = a.tiros
    sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=a.seed)
    sim.use_same_registers_as(c)
    nreg_q = (LS + LO + LP) * DEG
    qs = [km.q(i) for i in range(nreg_q)]
    sigv = [[0] * B for _ in range(LS)]; omv = [[0] * B for _ in range(LO)]; psv = [[0] * B for _ in range(LP)]
    Mall = np.zeros((m, B), dtype=np.int64); ref = np.zeros(B, dtype=bool)
    for sh in range(B):
        k = int(rng.integers(1, a.kmax + 1))
        pos = [int(x) for x in rng.choice(a.posiciones, size=k, replace=False)]
        vals = [int(x) for x in rng.integers(1, 4096, size=k)]
        Ms = [int(x) for x in rng.integers(0, 4096, size=m)]
        S = []
        for t in range(1, a.n + 1):
            s = 0
            for q_, e in zip(pos, vals):
                s ^= G.mul(e, int(G.EXP[(q_ * t) % 4095]))
            S.append(s)
        sig, L, ev = traza_empate_replace(S); sig = PM.trim(sig)
        omega = PM.trim(PM.pmul(S[:a.n], sig)[:a.n]); dsig = PM.pderiv(sig)
        psi = PM.pinvmod(dsig, sig)
        assert psi is not None and L == k and len(omega) <= LO and len(psi) <= LP and len(sig) <= LS, (k, L, len(omega), len(psi))
        for i, cf in enumerate(sig): sigv[i][sh] = cf
        for i, cf in enumerate(omega): omv[i][sh] = cf
        for i, cf in enumerate(psi): psv[i][sh] = cf
        Mall[:, sh] = Ms
        ref[sh] = PM.fase_directa(pos, vals, Ms)
    init = np.concatenate([bits_of(sigv[i], B) for i in range(LS)] + [bits_of(omv[i], B) for i in range(LO)] +
                          [bits_of(psv[i], B) for i in range(LP)], axis=0)
    sim.write_across_shots(km.array(qs), init)
    cb = [km.b(j * DEG + k) for j in range(m) for k in range(DEG)]
    mbits = np.concatenate([bits_of(Mall[j], B) for j in range(m)], axis=0)
    sim.write_across_shots(km.array(cb), mbits)
    t1 = time.time(); sim.do(c); log.info("simulacion %.1fs", time.time() - t1)
    pf = sim.read_phase_flipped_across_shots()
    rest = sim.read_across_shots(km.array(qs)) ^ init
    anc = [km.q(i) for i in range(nreg_q, c.num_qubits)]
    sucio = sim.read_across_shots(km.array(anc)).any(axis=0) if anc else np.zeros(B, dtype=bool)
    mal_fase = int((pf != ref).sum()); mal_reg = int(rest.any(axis=0).sum()); mal_anc = int(sucio.sum())
    log.info("tiros=%d  fase incorrecta=%d  registros no restaurados=%d  ancillas sucias=%d  (fase=1 en ref: %d)",
             B, mal_fase, mal_reg, mal_anc, int(ref.sum()))
    log.info("Toffolis por tiro (medio, simulador)=%s", sim.operation_statistics().num_toffoli_like / B if hasattr(sim.operation_statistics(), 'num_toffoli_like') else '?')
    log.info("RESULTADO: %s", "PASA" if (mal_fase == 0 and mal_reg == 0 and mal_anc == 0) else "FALLA")

if __name__ == "__main__":
    main()
