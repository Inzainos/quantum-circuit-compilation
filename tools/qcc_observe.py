#!/usr/bin/env python3
"""Outside observer: verify a submission ZIP from the outside and log
every input/output as JSON lines (tools/qcc_log.py).

Runs, on the exact files extracted from the ZIP:
  - invsqrt: official verifier, full domain, 1 shot/x.
  - dfthcsos: official verifier on the extracted dfthcsos/ dir.
  - dqi: sampling with the official verifier's own functions
    (tools/dqi_harness.py), with circuit.reaction_depth() patched to
    -1 exactly like the harness does — the full dqi verifier cannot
    run on this 7 GB box (reaction_depth -> std::bad_alloc), so the
    dqi score reported here is R * Q^2 * mean_toffoli with R from the
    verifier's own Clopper-Pearson + repetition_overhead formulas.
    It is an ESTIMATE, labelled as such, not a verifier PASS.

Nothing here loads a circuit through reaction_depth. Scratch goes to
~/workspace/qcc-data/observe/<zip-stem>/, never /tmp (512 MB tmpfs).

Usage:
  PYTHONPATH=$HOME/workspace/qcc/kickmix:$PWD/src python tools/qcc_observe.py \\
      ~/workspace/qcc-data/integracion/submission.zip [--shots 2560] [--seed 1]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from qcc_log import emit as _qcc_emit  # noqa: E402

# kickmix lives outside the repo tree in this sandbox (only LICENSE.txt
# is versioned under kickmix/).
_KICKMIX_DIR = None
for _cand in (ROOT / "kickmix", Path.home() / "workspace" / "qcc" / "kickmix"):
    if (_cand / "kickmix.so").exists():
        _KICKMIX_DIR = _cand
        if str(_cand) not in sys.path:
            sys.path.insert(0, str(_cand))
        break
if _KICKMIX_DIR is None:
    _KICKMIX_DIR = ROOT / "kickmix"  # fall through; import will fail loudly

PY = Path.home() / "workspace" / "py313-venv" / "bin" / "python"
OBSERVE_ROOT = Path.home() / "workspace" / "qcc-data" / "observe"


def _resolve_verifiers() -> Path:
    """Verifier root: the copy that actually has the FeMoCo data.
    The repo tree's verifiers/ lacks the 128 MB .fcidump (gitignored);
    the competition-data copy under qcc-data has it (verified SHAs).
    Env QCC_VERIFIERS overrides."""
    candidates = []
    if os.environ.get("QCC_VERIFIERS"):
        candidates.append(Path(os.environ["QCC_VERIFIERS"]))
    candidates.append(Path.home() / "workspace" / "qcc-data" / "verifiers")
    candidates.append(ROOT / "verifiers")
    for cand in candidates:
        if (cand / "dfthcsos" / "FeMoCo76o113e.fcidump").exists():
            return cand
    for cand in candidates:
        if (cand / "dfthcsos" / "verify.py").exists():
            return cand
    return candidates[-1]


VERIFIERS_DIR = _resolve_verifiers()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_verifier(cmd, cwd, phase, inputs, env):
    """Run an official verifier subprocess, parse its JSON, emit events."""
    t0 = time.time()
    _qcc_emit("qcc_observe", phase, "start", inputs=inputs)
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    dt = time.time() - t0
    if proc.returncode != 0:
        _qcc_emit("qcc_observe", phase, "error", inputs=inputs,
                   outputs={"rc": proc.returncode,
                            "stdout_tail": proc.stdout[-2000:],
                            "stderr_tail": proc.stderr[-2000:]},
                   duration_s=dt)
        raise SystemExit(f"{phase}: verificador falló (rc={proc.returncode})\n"
                         f"{proc.stderr[-2000:]}")
    text = proc.stdout
    data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    keep = {k: data[k] for k in
            ("status", "score", "toffoli_equivalent", "toffoli_count",
             "max_toffoli_count", "num_qubits", "reaction_depth",
             "verified_shots", "worst_error_over_tolerance",
             "lambda_eff", "error_1", "error_2", "Lambda", "E_gap",
             "submission_sha256", "circuit_sha256", "num_circuits",
             "num_ops")
            if k in data}
    if "metrics" in data:  # dfthcsos nests its gates under "metrics"
        keep.update({k: data["metrics"][k] for k in
                     ("error_1", "error_2", "Lambda", "E_gap", "lambda_eff")
                     if k in data["metrics"]})
    _qcc_emit("qcc_observe", phase, "ok", inputs=inputs, outputs=keep,
              duration_s=dt)
    return keep


def _observe_dqi(kmb: Path, shots: int, seed: int):
    """Sampling with the official verifier's functions (harness)."""
    import kickmix as km  # noqa: E402
    km.Circuit.reaction_depth = lambda self: -1  # evita std::bad_alloc; no afecta el score
    sys.path.insert(0, str(VERIFIERS_DIR / "dqi"))
    sys.path.insert(0, str(ROOT / "src"))
    import dqi_harness as h  # noqa: E402
    import verify_submission_dqi as v  # noqa: E402

    t0 = time.time()
    inputs = {"circuit": str(kmb), "sha256": _sha256(kmb),
              "shots": shots, "seed": seed}
    _qcc_emit("qcc_observe", "dqi_sample", "start", inputs=inputs)
    c = km.Circuit.from_file(str(kmb), format="kmb")
    total_bad = 0
    done = 0
    tof = 0
    for _b0, bad, tof, _w in h.corre(c, shots, seed):
        total_bad += int(bad.sum())
        done += len(bad)
    mean_toff = tof / done
    eps_plus = v.clopper_pearson_upper_bound(total_bad, done)
    rep = v.repetition_overhead(eps_plus)
    score = rep * (c.num_qubits ** 2) * mean_toff
    outputs = {"shots": done, "failures": total_bad,
               "mean_toffoli": mean_toff, "qubits": int(c.num_qubits),
               "eps_plus": eps_plus, "repetition_factor": rep,
               "score_estimate": score,
               "note": "ESTIMATE: full dqi verifier cannot run on this box "
                       "(reaction_depth bad_alloc); score from the verifier's "
                       "own R formula on sampled failures."}
    _qcc_emit("qcc_observe", "dqi_sample", "ok", inputs=inputs,
              outputs=outputs, duration_s=time.time() - t0)
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip", type=Path)
    ap.add_argument("--shots", type=int, default=2560,
                    help="dqi sampling shots (default 2560)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-dqi", action="store_true")
    a = ap.parse_args()

    work = OBSERVE_ROOT / a.zip.stem
    work.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.zip) as z:
        z.extractall(work)
    zip_sha = _sha256(a.zip)
    _qcc_emit("qcc_observe", "start", "ok",
              inputs={"zip": str(a.zip), "shots": a.shots, "seed": a.seed},
              outputs={"zip_sha256": zip_sha, "extract_dir": str(work),
                       "files": [i.filename for i in
                                 zipfile.ZipFile(a.zip).infolist()]})

    env = {**os.environ,
           "PYTHONPATH": f"{_KICKMIX_DIR}:{ROOT / 'src'}:{ROOT / 'verifiers'}"}
    results = {}
    results["invsqrt"] = _run_verifier(
        [str(PY), str(VERIFIERS_DIR / "invsqrt" / "verify_submission_invsqrt.py"),
         str(work / "invsqrt.kmb"), "--shots-per-x", "1",
         "--batch-size", "1022"],
        cwd=ROOT, phase="invsqrt_verify", env=env,
        inputs={"circuit": str(work / "invsqrt.kmb"),
                "sha256": _sha256(work / "invsqrt.kmb"),
                "shots_per_x": 1,
                "verifier": str(VERIFIERS_DIR)})
    results["dfthcsos"] = _run_verifier(
        [str(PY), str(VERIFIERS_DIR / "dfthcsos" / "verify.py"),
         str(work / "dfthcsos")],
        cwd=ROOT, phase="dfthcsos_verify", env=env,
        inputs={"dir": str(work / "dfthcsos"),
                "verifier": str(VERIFIERS_DIR)})
    if not a.no_dqi:
        results["dqi"] = _observe_dqi(work / "dqi.kmb", a.shots, a.seed)

    print(json.dumps({"zip_sha256": zip_sha, "results": results},
                     indent=2, ensure_ascii=False))
    _qcc_emit("qcc_observe", "done", "ok",
              inputs={"zip": str(a.zip)},
              outputs={"zip_sha256": zip_sha,
                       "invsqrt_score": results["invsqrt"].get("score"),
                       "dfthcsos_score": results["dfthcsos"].get("score"),
                       "dqi_score_estimate":
                           results.get("dqi", {}).get("score_estimate")})


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
