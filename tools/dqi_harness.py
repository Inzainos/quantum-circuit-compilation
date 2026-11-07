#!/usr/bin/env python3
"""Arnes de medicion DQI: simula lotes de tiros sobre un circuito y reporta fallos por peso de error.

Usa las mismas funciones de muestreo del verificador oficial (verify_submission_dqi). No sustituye al
verificador: sirve para explorar (n_iters, poda) antes de la verificacion oficial.
Uso: python3 tools/dqi_harness.py circuito.kmb --shots 2560 [--seed 1]
"""
from __future__ import annotations
import argparse, json, logging, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "verifiers" / "dqi")); sys.path.insert(0, str(ROOT / "verifiers" / "invsqrt"))
sys.path.insert(0, str(ROOT / "src"))
import kickmix as km  # noqa: E402
km.Circuit.reaction_depth = lambda self: -1  # evita std::bad_alloc; no afecta el score
import verify_submission_dqi as v  # noqa: E402

log = logging.getLogger("harness")


def corre(circuit: km.Circuit, shots: int, seed: int, batch: int = 256, m=4095, n=70, degree=12):
    spec = v.ProblemSpecDQI(m=m, n=n, degree=degree, r=v.default_num_accepted_values(degree), num_shots=shots)
    syn_q, mbuc_b, anc_q = v.validate_registers(circuit, spec)
    syn, mb = km.array(syn_q), km.array(mbuc_b)
    wp = v.optimal_dqi_weights(m, spec.max_errors, degree, spec.r) ** 2
    tables = v.FieldTables(km.GF2Field(degree))
    fallos = np.zeros(len(wp), dtype=np.int64); cuenta = np.zeros(len(wp), dtype=np.int64)
    tof = 0
    for b0 in range(0, shots, batch):
        rng = np.random.default_rng([seed, b0])
        # sample_shots no devuelve el peso; lo recuperamos del numero de sindromes != 0 no es fiable, asi que
        # muestreamos el peso con el mismo rng antes y reutilizamos funciones del verificador.
        pesos = np.random.default_rng([seed, b0]).choice(len(wp), size=batch, p=wp)  # misma 1a extraccion que sample_shots
        syndromes, mbuc, phases = v.sample_shots(spec, tables, rng, batch, wp)
        sim = km.Simulator(batch_size=batch, debug_print=False, counting_operations=True, seed=seed * 1000003 + b0)
        sim.use_same_registers_as(circuit)
        ins = v.to_bits(syndromes, degree)
        sim.write_across_shots(syn, ins); sim.write_across_shots(mb, v.to_bits(mbuc, degree))
        sim.do(circuit)
        pf = sim.read_phase_flipped_across_shots()
        diff = sim.read_across_shots(syn) ^ ins
        junk = sim.read_across_shots(anc_q) if len(anc_q) else np.zeros((0, batch), dtype=bool)
        val = diff.any(axis=0) | junk.any(axis=0)
        ph = (pf ^ phases) & ~val
        bad = val | ph
        tof += int(sim.operation_statistics().num_toffoli_like)
        yield b0, bad, tof, pesos


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("circuit"); ap.add_argument("--shots", type=int, default=2560)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--format", default="kmb")
    a = ap.parse_args()
    c = km.Circuit.from_file(a.circuit, format=a.format)
    t0 = time.time(); total_bad = 0; done = 0; tof = 0
    for b0, bad, tof, _w in corre(c, a.shots, a.seed):
        total_bad += int(bad.sum()); done += len(bad)
        log.info("lote %d: acumulado fallos %d / %d (%.0fs)", b0 // 256, total_bad, done, time.time() - t0)
    print(json.dumps({"shots": done, "fallos": total_bad, "toffoli_medio": tof / done,
                      "qubits": c.num_qubits, "segundos": time.time() - t0}))
