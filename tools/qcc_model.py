#!/usr/bin/env python3
"""CLI for the QCC surrogate model (tools/qcc_model.json).

Every output is an ESTIMATE from real measured logs — never a verifier
result. The model is tiny (coefficients in a ~10 KB JSON) and runs
without loading any circuit, so it works on this 7 GB box and on a
laptop where the full dqi verifier cannot run.

Usage:
  python tools/qcc_model.py predict --benchmark invsqrt \\
      --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1
  python tools/qcc_model.py predict --benchmark dfthcsos \\
      --rho 1e-4 --eps 0.017 --epochs 100 [--brot 12 --J 8]
  python tools/qcc_model.py predict --benchmark dqi \\
      --T 784172 --Q 2016 --shots 102400 --failures 0
  python tools/qcc_model.py validate   # stored validation + dqi formula re-check
  python tools/qcc_model.py info       # model card

dfthcsos notes: the trajectory model covers LBFGS fine-tuning only.
Adam inputs are refused: Adam lr=1e-4 destroys the seed (measured,
diag_20ep.log). The encode offsets (continuous -> verified) were
measured once (n=1) on the lbfgs_ep100 candidate.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "tools" / "qcc_model.json"


def load_model():
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _predict(model_dict, features):
    coef = np.array(model_dict["coef"])
    mu = np.array(model_dict["mu"])
    sd = np.array(model_dict["sd"])
    x = np.array(features, dtype=float)
    xs = np.concatenate([[1.0], (x - mu) / sd])
    return float(xs @ coef)


def clopper_pearson_upper_bound(k: int, n: int, log2_delta: float = -128.0) -> float:
    """Same math as verifiers/dqi/verify_submission_dqi.py (numpy only)."""
    if n <= 0 or not (0 <= k <= n):
        raise ValueError("bad k/n")
    log_delta = log2_delta * math.log(2.0)
    if k == 0:
        return -math.expm1(log_delta / n)
    if k == n:
        return 1.0
    j = np.arange(k + 1, dtype=np.float64)
    log_comb = np.r_[0.0, np.cumsum(np.log(n - j[1:] + 1.0) - np.log(j[1:]))]

    def log_tail(p: float) -> float:
        terms = log_comb + j * math.log(p) + (n - j) * math.log1p(-p)
        m = float(terms.max())
        return m + math.log(float(np.exp(terms - m).sum()))

    lo = k / n if log_tail(k / n) >= log_delta else 0.0
    hi = 1.0
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        if mid == lo or mid == hi:
            break
        if log_tail(mid) > log_delta:
            lo = mid
        else:
            hi = mid
    return hi


def repetition_overhead(eps: float) -> float:
    if not 0.0 <= eps < 1 / 16:
        raise ValueError(f"eps must be in [0, 1/16), got {eps}")
    if eps == 0.0:
        return 1.0
    return math.log(2.0) / -math.log(0.5 + 2.0 * math.sqrt(eps))


def predict_invsqrt(m, a):
    feats = [a.j, a.wc, a.dd, a.sesgo]
    out = {}
    for target in ("Q", "T", "max_err"):
        out[target] = _predict(m["invsqrt"]["models"][target], feats)
    ratio = m["invsqrt"]["score_ratio_toffoli_equiv_over_T"]
    out["score_estimate"] = out["Q"] * out["T"] * ratio
    out["pass_estimate"] = bool(out["max_err"] < 1.0)
    val = m["invsqrt"]["validation"]
    print(f"ESTIMATE invsqrt (deg={a.deg} j={a.j} wc={a.wc} dd={a.dd} sesgo={a.sesgo})")
    print(f"  Q ≈ {out['Q']:.1f}   T ≈ {out['T']:.0f}   "
          f"max_err/tol ≈ {out['max_err']:.3f}   "
          f"score ≈ {out['score_estimate']:,.0f}")
    print(f"  PASS estimate: {'yes' if out['pass_estimate'] else 'no'} "
          f"(max_err < 1.0)")
    print(f"  Basis: n={m['invsqrt']['n']} measured sweep rows; "
          f"validation MAE Q={val['Q']['mae']:.2f} (group-out "
          f"{val['Q']['group_out_mae']:.2f}), T={val['T']['mae']:.0f} "
          f"(group-out {val['T']['group_out_mae']:.0f}), max_err="
          f"{val['max_err']['mae']:.3f}. Score uses the mean measured "
          f"toffoli_equiv/T = {ratio:.4f} (3 verified circuits).")
    return out


def predict_dfthcsos(m, a):
    if a.solver == "adam":
        print("REFUSED: the trajectory model covers LBFGS fine-tuning only.",
              file=sys.stderr)
        print("Adam lr=1e-4 destroys the converged seed (measured: eps "
              "16.13 -> 172 mHa in 20 epochs, lambda_eff 49.3 -> 107; see "
              "dfthcsos-refit/diag_20ep.log). No prediction is offered for "
              "Adam inputs.", file=sys.stderr)
        raise SystemExit(2)
    feats = [math.log10(a.rho), a.eps, a.epochs / 100.0, 0.0]
    d = m["dfthcsos"]
    lam_eff = _predict(d["models"]["lambda_eff"], feats)
    eps_fro = math.exp(_predict(d["models"]["eps_fro"], feats))
    gap = _predict(d["models"]["E_gap"], feats)
    off = d["encode_offsets"]
    lam_eff_enc = lam_eff + off["lambda_eff"]
    err2_enc = eps_fro + off["error_2_mHa"]
    gap_enc = gap + off["E_gap"]
    print(f"ESTIMATE dfthcsos (LBFGS rho={a.rho} eps={a.eps} "
          f"epochs={a.epochs} shape=65,60,60)")
    print(f"  continuous (trainer): lambda_eff ≈ {lam_eff:.3f}, "
          f"eps_fro ≈ {eps_fro:.2f} mHa, E_gap ≈ {gap:.4f}")
    print(f"  encoded (verifier scale, offsets measured n=1): "
          f"lambda_eff ≈ {lam_eff_enc:.3f}, error_2 ≈ {err2_enc:.2f} mHa, "
          f"E_gap ≈ {gap_enc:.4f}")
    print(f"  gates estimate: error_2 <= 20 mHa: "
          f"{'yes' if err2_enc <= 20 else 'NO'}, E_gap > 3.914898: "
          f"{'yes' if gap_enc > 3.914898 else 'NO'}, "
          f"Lambda > 49: {'yes' if lam_eff_enc > 49 else 'NO'}")
    out = {"lambda_eff": lam_eff, "eps_fro_mHa": eps_fro, "E_gap": gap,
           "lambda_eff_enc": lam_eff_enc, "error_2_enc_mHa": err2_enc,
           "E_gap_enc": gap_enc}
    if a.brot is not None and a.J is not None:
        key = f"{a.brot},{a.J}"
        table = d["brot_J_table"]
        if key in table:
            t, q = table[key]["T"], table[key]["Q"]
            score = lam_eff_enc * t * q
            out["score_estimate"] = score
            print(f"  score ≈ {score:,.0f} (brot={a.brot} J={a.J}: "
                  f"T={t:,.0f} Q={q}, lambda_eff_enc × T × Q)")
        else:
            print(f"  score: no PASS data for brot={a.brot} J={a.J} "
                  f"(only {sorted(table)} measured PASS)")
    val = d["validation"]
    print(f"  Basis: n={d['n_traj']} LBFGS trajectory points, 3 runs; "
          f"leave-one-run-out MAE lambda_eff={val['lambda_eff']['leave_one_run_out_mae']:.2f}, "
          f"eps={val['eps_fro']['leave_one_run_out_mae']:.2f} mHa, "
          f"gap={val['E_gap']['leave_one_run_out_mae']:.3f}.")
    return out


def predict_dqi(m, a):
    eps_plus = clopper_pearson_upper_bound(a.failures, a.shots)
    rep = repetition_overhead(eps_plus)
    score = rep * (a.Q ** 2) * a.T
    print(f"ESTIMATE dqi (T={a.T:,} Q={a.Q} shots={a.shots} "
          f"failures={a.failures})")
    print(f"  eps_plus (Clopper-Pearson 1-2^-128) = {eps_plus:.3g}, "
          f"R = {rep:.4f}, score ≈ {score:.4g}")
    print("  Basis: the verifier's own score formula "
          "(verifiers/dqi/verify_submission_dqi.py), checked against the "
          "recorded v10 score (relative error 3e-8; the residual is the "
          "rounded mean-toffoli anchor). This converts (T, Q, shots, "
          "failures) into a score; it cannot predict T/Q for a new "
          "decoder (only 2 decoder points exist).")
    return {"eps_plus": eps_plus, "R": rep, "score_estimate": score}


def cmd_validate(m):
    print("Stored validation (from tools/qcc_model_train.py):")
    print(json.dumps({"invsqrt": m["invsqrt"]["validation"],
                      "dfthcsos": m["dfthcsos"]["validation"]},
                     indent=2))
    print("dqi formula re-check (recomputed here, compared to anchors):")
    for anchor in m["dqi"]["anchors"]:
        got = predict_dqi(m, argparse.Namespace(
            T=anchor["T"], Q=anchor["Q"], shots=anchor["shots"],
            failures=anchor["failures"]))
        rec = anchor.get("recorded_score")
        if rec:
            print(f"  {anchor['label']}: rel error vs recorded = "
                  f"{(got['score_estimate'] - rec) / rec:.3g}")
        else:
            print(f"  {anchor['label']}: no recorded score; formula gives "
                  f"{got['score_estimate']:.4g} (R={got['R']:.4f})")


def cmd_info(m):
    print(f"QCC surrogate model v{m['version']} ({m['kind']}), "
          f"trained {m['trained']}")
    print(m["note"])
    print(f"invsqrt: n={m['invsqrt']['n']} sweep rows")
    print(f"dfthcsos: n={m['dfthcsos']['n_traj']} LBFGS trajectory points "
          f"(+ {m['dfthcsos']['n_traj_all_runs'] - m['dfthcsos']['n_traj']} "
          f"Adam rows kept in the dataset but excluded from the fit); "
          f"{m['dfthcsos']['regime']}")
    print(f"dqi: {m['dqi']['note']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--benchmark", choices=["invsqrt", "dfthcsos", "dqi"],
                   required=True)
    p.add_argument("--deg", type=int, default=2)
    p.add_argument("--j", type=int, default=8)
    p.add_argument("--wc", type=int, default=28)
    p.add_argument("--dd", type=int, default=13)
    p.add_argument("--sesgo", type=int, default=1)
    p.add_argument("--rho", type=float, default=1e-4)
    p.add_argument("--eps", type=float, default=0.017)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--solver", choices=["lbfgs", "adam"], default="lbfgs")
    p.add_argument("--brot", type=int, default=12)
    p.add_argument("--J", type=int, default=8)
    p.add_argument("--T", type=float, default=784172)
    p.add_argument("--Q", type=int, default=2016)
    p.add_argument("--shots", type=int, default=102400)
    p.add_argument("--failures", type=int, default=0)
    sub.add_parser("validate")
    sub.add_parser("info")
    a = ap.parse_args()
    m = load_model()
    if a.cmd == "predict":
        if a.benchmark == "invsqrt":
            predict_invsqrt(m, a)
        elif a.benchmark == "dfthcsos":
            predict_dfthcsos(m, a)
        else:
            predict_dqi(m, a)
    elif a.cmd == "validate":
        cmd_validate(m)
    else:
        cmd_info(m)


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
