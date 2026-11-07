#!/usr/bin/env python3
"""Barrido de n_iters para dqi_optimized_v10: construye, verifica con el verificador oficial y reporta R*Q^2*T.

Uso: python3 src/dqi_niters_sweep.py --niters 222 150 100 --shots 2560 [--salt X]
No modifica el verificador; solo evita reaction_depth() (std::bad_alloc en 7 GB, no entra al score).
"""
from __future__ import annotations
import argparse, json, logging, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "verifiers" / "invsqrt")); sys.path.insert(0, str(ROOT / "verifiers" / "dqi"))
import kickmix as km  # noqa: E402
km.Circuit.reaction_depth = lambda self: -1
import verify_submission_dqi as v  # noqa: E402
from dqi_optimized_v10 import ProosAndZalkaDecoderV10  # noqa: E402

log = logging.getLogger("niters")


def build(n_iters: int, m=4095, n=70, degree=12) -> km.Circuit:
    b = km.CircuitBuilder()
    S = [b.create_quantum_register(degree, name=f"S{i}") for i in range(n)]
    E = [b.create_classical_register(degree, name=f"E{j}") for j in range(m)]
    ProosAndZalkaDecoderV10(n, km.GF2Field(degree)).build_syndrome_decoding_mbuc(b, syndromes=S, error_mbuc=E, n_iters=n_iters)
    return b.finish_circuit()


def run(circ, shots, salt, workers):
    spec = v.ProblemSpecDQI(m=4095, n=70, degree=12, r=v.default_num_accepted_values(12), num_shots=shots)
    try:
        s = v.verify(circ, spec, seed=None, salt=salt, batch_size=v.DEFAULT_BATCH_SIZE, log2_delta=v.DEFAULT_LOG2_DELTA, max_workers=workers)
        return {k: s[k] for k in ("status", "score", "num_qubits", "toffoli_count", "value_errors", "phase_errors", "verified_shots", "effective_error_rate", "repetition_factor")}
    except AssertionError as e:
        return {"status": "FAIL", "detail": str(e)}


if __name__ == "__main__":
    try:  # logs estructurados (qcc_log): una linea por script
        import sys as _qs
        from pathlib import Path as _qp
        _qs.path.insert(0, str(_qp(__file__).resolve().parent.parent / "tools"))
        from qcc_log import auto as _qcc_auto
        _qcc_auto(__file__)
    except Exception:  # noqa: BLE001
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--niters", type=int, nargs="+", required=True)
    ap.add_argument("--shots", type=int, default=2560)
    ap.add_argument("--salt", default="")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    for ni in a.niters:
        t0 = time.time()
        c = build(ni)
        res = run(c, a.shots, a.salt, a.workers)
        res["n_iters"] = ni; res["seg"] = round(time.time() - t0, 1)
        log.info(json.dumps(res, default=str))
