#!/usr/bin/env python3
"""Barrido de n_iters del EEA sincronizado de v10: fallos por peso, T medio y R estimado.
Uso: python3 tools/dqi_sweep_niters.py 222 200 180 --shots 10240 --seed 7
Salida: una linea JSON por n_iters.
"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "src"))
import dqi_harness as H  # noqa: E402
import kickmix as km  # noqa: E402
import verify_submission_dqi as v  # noqa: E402
from dqi_optimized_v10 import ProosAndZalkaDecoderV10  # noqa: E402


def construye(n_iters: int, m=4095, n=70, degree=12) -> km.Circuit:
    b = km.CircuitBuilder()
    S = [b.create_quantum_register(degree, name=f"S{i}") for i in range(n)]
    E = [b.create_classical_register(degree, name=f"E{j}") for j in range(m)]
    ProosAndZalkaDecoderV10(n, km.GF2Field(degree)).build_syndrome_decoding_mbuc(b, syndromes=S, error_mbuc=E, n_iters=n_iters)
    return b.finish_circuit()


def mide(c: km.Circuit, shots: int, seed: int) -> dict:
    wp = v.optimal_dqi_weights(4095, 35, 12, v.default_num_accepted_values(12)) ** 2
    fall = np.zeros(len(wp), dtype=np.int64); tot = np.zeros(len(wp), dtype=np.int64); tof = 0; done = 0
    for b0, bad, tof, pesos in H.corre(c, shots, seed):
        done += len(bad)
        np.add.at(tot, pesos, 1); np.add.at(fall, pesos, bad.astype(np.int64))
    k = int(fall.sum()); eps = v.clopper_pearson_upper_bound(k, done, log2_delta=v.DEFAULT_LOG2_DELTA) if k < done else 1.0
    return {"fallos": k, "shots": done, "eps_plus": eps, "R": v.repetition_overhead(eps) if eps < 1 / 16 else None,
            "T": tof / done, "Q": c.num_qubits, "fallos_por_peso": {int(i): int(f) for i, f in enumerate(fall) if f}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("n_iters", type=int, nargs="+"); ap.add_argument("--shots", type=int, default=10240)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    for ni in a.n_iters:
        t0 = time.time(); c = construye(ni); r = mide(c, a.shots, a.seed)
        r.update(n_iters=ni, segundos=round(time.time() - t0))
        if r["R"]: r["score_rel"] = r["R"] * r["Q"] ** 2 * r["T"]
        print(json.dumps(r), flush=True)
