#!/usr/bin/env python3
"""Prueba de la etapa D (BM reversible): sigma del circuito proporcional a sigma del modelo clasico (variante paper),
y ida+vuelta restaura S y deja todas las ancillas en 0.  Log: logs/dqi_bm_test_v1.log"""
import sys, argparse, logging, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import kickmix as km
import dqi_bm_model as G
import dqi_phase_model as PM
from dqi_bm_forecast import traza_empate_replace
import dqi_bm_stage_v1 as BM
log = logging.getLogger("bm_test"); DEG = 12

def bits(vals): return ((np.array(vals, dtype=np.int64)[None, :] >> np.arange(DEG)[:, None]) & 1) == 1
def word(out, base, B):
    v = np.zeros(B, dtype=np.int64)
    for bit in range(DEG): v |= out[base + bit].astype(np.int64) << bit
    return v

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tiros", type=int, default=64)
    ap.add_argument("--seed", type=int, default=21); ap.add_argument("--n", type=int, default=70)
    ap.add_argument("--kmax", type=int, default=35)
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "dqi_bm_test_v1.log", mode="w")])
    n, B, LS = a.n, a.tiros, 36
    rng = np.random.default_rng(a.seed)
    Ss, sigs = [], []
    for sh in range(B):
        k = int(rng.integers(1, a.kmax + 1))
        pos = rng.choice(4095, size=k, replace=False); vals = [int(x) for x in rng.integers(1, 4096, size=k)]
        S = []
        for t in range(1, n + 1):
            s = 0
            for q_, e in zip(pos, vals): s ^= G.mul(e, int(G.EXP[(int(q_) * t) % 4095]))
            S.append(s)
        sg, L, ev = traza_empate_replace(S); sg = PM.trim(sg)
        assert L == k and len(sg) <= LS
        Ss.append(S); sigs.append(sg + [0] * (LS - len(sg)))
    init = np.concatenate([bits([Ss[sh][i] for sh in range(B)]) for i in range(n)], axis=0)
    nq_in = n * DEG
    # ---- ida: leer sigma del circuito ----
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    Sreg = [b.create_quantum_register(DEG, name=f'S{i}') for i in range(n)]
    bm = BM.BMStageV1(b, gf, Sreg, LS, n)
    t0 = time.time(); bm.forward(); c = b.finish_circuit()
    log.info("IDA: build %.1fs toffoli-like=%d qubits=%d", time.time() - t0, c.operation_statistics().num_toffoli_like, c.num_qubits)
    sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=a.seed); sim.use_same_registers_as(c)
    qin = km.array([km.q(i) for i in range(nq_in)])
    sim.write_across_shots(qin, init); sim.do(c)
    qall = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
    # sigma qubits: ids de bm.sigma
    malos = 0; cero0 = 0
    for sh in range(B):
        got = []
        for i in range(LS):
            reg = bm.sigma[i]; v = 0
            for bit in range(DEG): v |= int(qall[int(reg[bit].id) if hasattr(reg[bit], 'id') else int(reg[bit])][sh]) << bit
            got.append(v)
        lam = got[0]
        if lam == 0: cero0 += 1; malos += 1; continue
        if any(got[i] != G.mul(lam, sigs[sh][i]) for i in range(LS)): malos += 1
    log.info("IDA: sigma no proporcional al modelo en %d/%d tiros (sigma_0=0 en %d)  fase volteada=%d", malos, B, cero0,
             int(sim.read_phase_flipped_across_shots().sum()))
    # ---- ida+vuelta ----
    b2 = km.CircuitBuilder()
    Sreg2 = [b2.create_quantum_register(DEG, name=f'S{i}') for i in range(n)]
    bm2 = BM.BMStageV1(b2, gf, Sreg2, LS, n); bm2.forward(); bm2.reverse()  # v1
    # sigma/tau/d iniciales tienen X: la vuelta debe devolverlos a su valor inicial; los liberamos deshaciendo las X
    b2.x(bm2.sigma[0][0]); b2.x(bm2.tau[1][0]); b2.x(bm2.d[0])
    c2 = b2.finish_circuit()
    sim2 = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=a.seed); sim2.use_same_registers_as(c2)
    sim2.write_across_shots(km.array([km.q(i) for i in range(nq_in)]), init); sim2.do(c2)
    out2 = sim2.read_across_shots(km.array([km.q(i) for i in range(c2.num_qubits)]))
    rest = int((out2[:nq_in] != init).any(axis=0).sum()); sucio = int(out2[nq_in:].any(axis=0).sum())
    log.info("IDA+VUELTA: toffoli-like=%d qubits=%d  S no restaurado=%d  ancillas sucias=%d  fase volteada=%d",
             c2.operation_statistics().num_toffoli_like, c2.num_qubits, rest, sucio, int(sim2.read_phase_flipped_across_shots().sum()))
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
