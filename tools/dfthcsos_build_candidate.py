#!/usr/bin/env python3
"""Build one dfthcsos candidate from a trained factorization .npz, with
structured JSON-lines logging per phase (tools/qcc_log.py).

Reemplazo con logs de build_candidate.sh (~/workspace/qcc-data/
dfthcsos-refit/build_candidate.sh). Las 4 fases son las mismas, con
los mismos comandos del Starter Kit y el mismo verificador oficial:

  1) check_factorization  (factorización continua)
  2) encode               (barrido de brot, 12 por defecto)
  3) build_circuits       (circuitos ANGLE, J=8 por defecto)
  4) verify               (verificador oficial de la competición)

Cada fase emite un evento qcc_log con duración, código de salida y,
cuando aplica, los números parseados (score, lambda_eff, error_2,
E_gap, sha256). La salida de cada fase también queda en
<candidate_dir>/<fase>.log, como antes.

Usage:
  python tools/dfthcsos_build_candidate.py <factorization.npz> <name> [brot] [J]

No mueve ni borra los .kmx/.npz del candidato; solo los genera.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from qcc_log import emit as _qcc_emit  # noqa: E402

KIT = Path.home() / "workspace" / "qcc-data" / "starter-kit" / "starter_kit"
REFIT = Path.home() / "workspace" / "qcc-data" / "dfthcsos-refit"
PY = Path.home() / "workspace" / "py313-venv" / "bin" / "python"
ENV = {**os.environ,
       "PYTHONPATH": f"{Path.home() / 'workspace' / 'qcc' / 'kickmix'}:"
                     f"{Path.home() / 'workspace' / 'qcc' / 'src'}:"
                     f"{Path.home() / 'workspace' / 'qcc' / 'verifiers'}"}


def _run(cmd, cwd, log_file: Path, phase: str, inputs, parse_json=False):
    """Run one phase, tee stdout+stderr to its .log, emit qcc events."""
    t0 = time.time()
    _qcc_emit("dfthcsos_build_candidate", phase, "start", inputs=inputs)
    with log_file.open("w", encoding="utf-8") as f:
        proc = subprocess.run(cmd, cwd=cwd, env=ENV, stdout=f,
                              stderr=subprocess.STDOUT, text=True)
    dt = time.time() - t0
    outputs = {"rc": proc.returncode, "log": str(log_file)}
    if parse_json and proc.returncode == 0:
        try:
            text = log_file.read_text(encoding="utf-8")
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])
            for k in ("status", "score", "lambda_eff", "error_1", "error_2",
                      "Lambda", "E_gap", "toffoli_count", "num_qubits",
                      "submission_sha256", "verified_shots"):
                if k in data:
                    outputs[k] = data[k]
            if "metrics" in data:
                outputs.update({k: data["metrics"][k] for k in
                                ("error_1", "error_2", "Lambda", "E_gap",
                                 "lambda_eff") if k in data["metrics"]})
        except (ValueError, KeyError) as exc:
            outputs["parse_error"] = str(exc)
    status = "ok" if proc.returncode == 0 else "error"
    _qcc_emit("dfthcsos_build_candidate", phase, status, inputs=inputs,
              outputs=outputs, duration_s=dt)
    if proc.returncode != 0:
        raise SystemExit(f"fase {phase} falló (rc={proc.returncode}); "
                         f"ver {log_file}")
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("npz", type=Path)
    ap.add_argument("name")
    ap.add_argument("brot", type=int, nargs="?", default=12)
    ap.add_argument("J", type=int, nargs="?", default=8)
    a = ap.parse_args()
    d = REFIT / "candidates" / a.name
    d.mkdir(parents=True, exist_ok=True)
    _qcc_emit("dfthcsos_build_candidate", "start", "ok",
              inputs={"npz": str(a.npz), "name": a.name, "brot": a.brot,
                      "J": a.J, "dir": str(d)})
    _run([str(PY), "starter/task1_factorization/check_factorization.py",
          "FeMoCo76o113e", str(a.npz)], cwd=KIT, log_file=d / "check_factorization.log",
         phase="check_factorization", inputs={"npz": str(a.npz)})
    _run([str(PY), "starter/task2_angles/encode.py", "FeMoCo76o113e",
          str(a.npz), "--tree", "log_depth", "--rounding", "nearest",
          "--brots", str(a.brot)], cwd=KIT, log_file=d / "encode.log",
         phase="encode", inputs={"brot": a.brot})
    _run([str(PY), "starter/task3_circuits/build_circuits.py",
          "FeMoCo76o113e", str(a.npz), "--tree", "log_depth",
          "--brot", str(a.brot), "--batch-size", str(a.J),
          "--rounding", "nearest", "--output", str(d)], cwd=KIT,
         log_file=d / "build_circuits.log", phase="build_circuits",
         inputs={"brot": a.brot, "J": a.J})
    out = _run([str(PY), "verifiers/dfthcsos/verify.py", str(d)],
               cwd=Path.home() / "workspace" / "qcc",
               log_file=d / "verify_official.log", phase="verify",
               inputs={"dir": str(d)}, parse_json=True)
    print(f"=== {a.name} done: status={out.get('status')} "
          f"score={out.get('score')} ===")


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
