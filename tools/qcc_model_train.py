#!/usr/bin/env python3
"""Train the first QCC surrogate model from the logs that already exist.

Real measurements only — no synthetic data. Reads the log inventory
(see docs/LOGS_MODELO_2026-11-06.md), assembles a dataset, fits small
ridge/least-squares regressors, validates honestly, and writes
tools/qcc_model.json (coefficients + validation errors + anchors,
kilobytes) plus ~/workspace/qcc-data/logs/qcc_dataset.csv.

Sub-models:
  invsqrt   (deg, j, wc, dd, sesgo) -> Q, T, max_err_over_tol.
            23 unique sweep rows. Score = Q * T * RATIO with RATIO the
            mean measured toffoli_equivalent/T of 3 verified circuits.
  dfthcsos  (log10 rho, eps, epoch, solver) -> lambda_eff, eps_fro, gap.
            ~25 epoch checkpoints from 4 refit runs + seed + truncations.
            Score = lambda_eff_enc * T(brot,J) * Q(brot,J) with the
            deterministic (brot,J) table from the official sweep and the
            measured encode offsets (n=1).
  dqi       No fitted regressor (only 2 decoder points exist). The model
            IS the verifier's own score formula
            score = R(failures, shots) * Q^2 * mean_toffoli, with R from
            the Clopper-Pearson upper bound + repetition_overhead, plus
            the measured anchors (v10, BM v1, n_iters sweep table).
            tools/qcc_model.py implements the same formulas.

Validation: invsqrt 80/20 split + leave-one-(j,wc,dd)-group-out;
dfthcsos leave-one-run-out; dqi formula check against the recorded v10
score (BM v1 has no recorded score; its stored score is the formula's
own output from the measured T/Q/shots/failures).

Usage:
  python tools/qcc_model_train.py [--out tools/qcc_model.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
QCC_DATA = Path.home() / "workspace" / "qcc-data"
REFIT = QCC_DATA / "dfthcsos-refit"

# ---------------------------------------------------------------- invsqrt
# Verified circuits used only to calibrate score = Q * T * RATIO.
# (score, Q, T, toffoli_equivalent) — all measured with the official verifier.
INVSQRT_SCORE_ANCHORS = [
    {"label": "halfsplit", "score": 570323.0, "Q": 183, "T": 2867,
     "toffoli_equiv": 3116.52},
    {"label": "logshift2", "score": 497462.32, "Q": 177, "T": 2561,
     "toffoli_equiv": 497462.32 / 177},
    {"label": "logshift2_sesgo1", "score": 390005.06, "Q": 139, "T": 2561,
     "toffoli_equiv": 2805.7917668892883},
]

# ---------------------------------------------------------------- dfthcsos
# Truncation points (measured with the verifier's math, REFIT.md section 2.3).
# Seed point (verifier math, REFIT.md section 0).
DFTHCSOS_SHAPE_POINTS = [
    {"shape": [65, 60, 60], "error_2_mHa": 16.1332, "Lambda": 308.448,
     "lambda_eff": 49.2547, "E_gap": 3.958, "source": "REFIT.md sec 0"},
    {"shape": [50, 50, 50], "error_2_mHa": 1743.6, "Lambda": 383.56,
     "lambda_eff": 318.57, "E_gap": 169.95, "source": "REFIT.md sec 2.3"},
    {"shape": [40, 40, 40], "error_2_mHa": 8175.4, "Lambda": 600.01,
     "lambda_eff": 599.44, "E_gap": 626.16, "source": "REFIT.md sec 2.3"},
]

# Encode offsets (continuous trainer values -> verified encoded values),
# measured once, on the lbfgs_ep100_rho1e-4 candidate.
DFTHCSOS_ENCODE_OFFSETS = {
    "lambda_eff": 49.015771929305174 - 48.987327575683594,  # +0.0284
    "error_2_mHa": 19.37060272200423 - 16.985,              # +2.386
    "E_gap": 3.920492788653064 - 3.916015625,                # +0.00448
    "n": 1,
}

# Deterministic (brot, J) -> (T, Q) from the official sweep (PASS rows).
DFTHCSOS_BROT_J = {"12,4": {"T": 164769.0, "Q": 682},
                   "12,8": {"T": 93237.0, "Q": 730}}

# ---------------------------------------------------------------- dqi
# (T, Q, shots, failures, recorded_score) — all measured.
DQI_ANCHORS = [
    {"label": "v10", "T": 5708480, "Q": 1888, "shots": 2560, "failures": 0,
     "score": 100553499141099.0},
    {"label": "bm_v1_0fail", "T": 784172, "Q": 2016, "shots": 102400,
     "failures": 0, "score": None},  # score computed from the formula below
    {"label": "bm_v1_2fail", "T": 784172, "Q": 2016, "shots": 102400,
     "failures": 2, "score": None},
]
# n_iters sweep on v10 (10,240 shots; 222-row is 0/2,560). Measured, DQI doc.
DQI_NITERS = [
    {"n_iters": 222, "failures": 0, "shots": 2560, "T": 5708480},
    {"n_iters": 218, "failures": 2, "shots": 10240, "T": 5631100},
    {"n_iters": 216, "failures": 5, "shots": 10240, "T": 5592408},
    {"n_iters": 214, "failures": 5073, "shots": 10240, "T": None},
]


def clopper_pearson_upper_bound(k: int, n: int, log2_delta: float = -128.0) -> float:
    """Same math as verifiers/dqi/verify_submission_dqi.py (reimplemented
    here so the model CLI needs only numpy)."""
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
    """R(eps) = ln(2) / -ln(1/2 + 2*sqrt(eps)); R(0) = 1."""
    if not 0.0 <= eps < 1 / 16:
        raise ValueError(f"eps must be in [0, 1/16), got {eps}")
    if eps == 0.0:
        return 1.0
    return math.log(2.0) / -math.log(0.5 + 2.0 * math.sqrt(eps))


def dqi_score(T: float, Q: int, shots: int, failures: int) -> dict:
    eps_plus = clopper_pearson_upper_bound(failures, shots)
    rep = repetition_overhead(eps_plus)
    return {"eps_plus": eps_plus, "R": rep,
            "score": rep * (Q ** 2) * T}


# ---------------------------------------------------------------- parsing
_CKPT = re.compile(
    r"epoch (\d+): ε_fro=([\d.]+)mHa, λ_eff=([\d.]+)Ha, Λ=([\d.]+)Ha "
    r"\(Λ_1=[\d.]+, Λ_2=[\d.]+\)[^\n]*?E_SOS: (-?[\d.]+)Ha, gap: ([\d.]+)Ha")
_START = re.compile(
    r"start: eps=([\d.]+) mHa Lambda=([\d.]+) lambda_eff=([\d.]+) E_gap=([\d.]+)")
_DONE = re.compile(
    r"  Lambda = ([\d.]+)\n  lambda_eff = ([\d.]+)\n  epsilon_fro = ([\d.]+)\n"
    r"  sos_gap = ([\d.]+)\n  E_SOS = (-?[\d.]+)")
_TAG_A = re.compile(
    r"tag=(\S+) solver=(\S+) lr=([\d.e-]+) epochs=(\d+) "
    r"shape=\((\d+),\s*(\d+),\s*(\d+)\) rho=([\d.e-]+) eps=([\d.]+)")
_TAG_B = re.compile(
    r"tag=(\S+) epochs=(\d+) shape=\((\d+),\s*(\d+),\s*(\d+)\) "
    r"rho=([\d.e-]+) epsilon=([\d.]+) lr=([\d.e-]+)")
# _TAG_B is the diag/pilot format (no solver field; both were Adam runs,
# REFIT.md section 1). _TAG_A is the refit.py format.


def parse_refit_logs():
    """Parse every refit run log into trajectory rows."""
    rows = []
    for path in sorted(REFIT.glob("*.log")):
        text = path.read_text(encoding="utf-8", errors="replace")
        m = _TAG_A.search(text)
        if m:
            tag, solver, lr, epochs, R, B, C, rho, eps = m.groups()
        else:
            m = _TAG_B.search(text)
            if not m:
                continue
            tag, epochs, R, B, C, rho, eps, lr = m.groups()
            solver = "adam"
        base = {"run": tag, "solver": solver, "lr": float(lr),
                "epochs": int(epochs), "R": int(R), "B": int(B), "C": int(C),
                "rho": float(rho), "eps_target": float(eps),
                "source": path.name}
        s = _START.search(text)
        if s:
            e, lam, le, gap = map(float, s.groups())
            rows.append({**base, "epoch": 0, "eps_fro": e, "Lambda": lam,
                         "lambda_eff": le, "E_gap": gap})
        for em, ef, le, lam, esos, gap in _CKPT.findall(text):
            rows.append({**base, "epoch": int(em), "eps_fro": float(ef),
                         "Lambda": float(lam), "lambda_eff": float(le),
                         "E_gap": float(gap), "E_SOS": float(esos)})
        d = _DONE.search(text)
        if d:
            lam, le, ef, gap, esos = map(float, d.groups())
            rows.append({**base, "epoch": int(epochs), "eps_fro": ef * 1000,
                         "Lambda": lam, "lambda_eff": le, "E_gap": gap,
                         "E_SOS": esos})
    return rows


# ---------------------------------------------------------------- fitting
def _design_invsqrt(rows):
    X = np.array([[1.0, r["j"], r["wc"], r["dd"], r["sesgo"]] for r in rows])
    return X


def _design_dfthcsos(rows):
    X = np.array([[1.0, math.log10(r["rho"]), r["eps_target"],
                   r["epoch"] / 100.0, 1.0 if r["solver"] == "adam" else 0.0]
                  for r in rows])
    return X


def ridge_fit(X, y, lam=1.0):
    """Ridge with feature standardization (intercept unpenalized)."""
    mu = X[:, 1:].mean(axis=0)
    sd = X[:, 1:].std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X[:, 1:] - mu) / sd
    Xs = np.column_stack([np.ones(len(X)), Xs])
    A = Xs.T @ Xs + lam * np.diag([0.0] + [1.0] * (Xs.shape[1] - 1))
    w = np.linalg.solve(A, Xs.T @ y)
    return {"coef": w.tolist(), "mu": mu.tolist(), "sd": sd.tolist(),
            "lam": lam}


def ridge_predict(model, X):
    Xs = (X[:, 1:] - np.array(model["mu"])) / np.array(model["sd"])
    Xs = np.column_stack([np.ones(len(X)), Xs])
    return Xs @ np.array(model["coef"])


def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "tools" / "qcc_model.json")
    a = ap.parse_args()

    dataset_rows = []

    # ---- invsqrt ----
    inv = {}
    for csv_path in (ROOT / "logs" / "invsqrt_sweep_0.csv",
                     ROOT / "logs" / "invsqrt_sweep_1.csv"):
        with csv_path.open(newline="") as f:
            for r in csv.DictReader(f):
                key = (int(r["deg"]), int(r["j"]), int(r["wc"]),
                       int(r["dd"]), int(r["sesgo"]))
                inv[key] = {"deg": key[0], "j": key[1], "wc": key[2],
                            "dd": key[3], "sesgo": key[4],
                            "max_err": float(r["max_err_over_tol"]),
                            "Q": int(r["Q"]), "T": int(r["T"]),
                            "source": csv_path.name}
    inv_rows = sorted(inv.values(), key=lambda r: (r["j"], r["wc"], r["dd"], r["sesgo"]))
    for r in inv_rows:
        dataset_rows.append({"benchmark": "invsqrt", **r})
    X = _design_invsqrt(inv_rows)
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(inv_rows))
    test_idx = set(idx[: max(1, len(inv_rows) // 5)].tolist())
    tr = [i for i in range(len(inv_rows)) if i not in test_idx]
    te = sorted(test_idx)
    inv_models, inv_val = {}, {}
    for target in ("Q", "T", "max_err"):
        y = np.array([r[target] for r in inv_rows], dtype=float)
        model = ridge_fit(X[tr], y[tr], lam=1.0)
        pred = ridge_predict(model, X[te])
        inv_models[target] = model
        inv_val[target] = {"test_n": len(te),
                           "mae": mae(pred, y[te]),
                           "max_abs_err": float(np.max(np.abs(pred - y[te]))),
                           "target_mean": float(np.mean(y))}
    # leave-one-(j,wc,dd)-group-out
    groups = sorted({(r["j"], r["wc"], r["dd"]) for r in inv_rows})
    glo_err = {t: [] for t in ("Q", "T", "max_err")}
    for g in groups:
        tr = [i for i, r in enumerate(inv_rows)
              if (r["j"], r["wc"], r["dd"]) != g]
        te = [i for i, r in enumerate(inv_rows)
              if (r["j"], r["wc"], r["dd"]) == g]
        for target in glo_err:
            y = np.array([r[target] for r in inv_rows], dtype=float)
            model = ridge_fit(X[tr], y[tr], lam=1.0)
            glo_err[target].extend(np.abs(ridge_predict(model, X[te]) - y[te]).tolist())
    for target in glo_err:
        inv_val[target]["group_out_mae"] = float(np.mean(glo_err[target]))
        inv_val[target]["group_out_max"] = float(np.max(glo_err[target]))
    ratio = float(np.mean([p["toffoli_equiv"] / p["T"]
                           for p in INVSQRT_SCORE_ANCHORS]))

    # ---- dfthcsos ----
    traj = parse_refit_logs()
    for r in traj:
        dataset_rows.append({"benchmark": "dfthcsos_traj", **r})
    for p in DFTHCSOS_SHAPE_POINTS:
        dataset_rows.append({"benchmark": "dfthcsos_shape", **p})
    Xt = _design_dfthcsos(traj)
    # The Adam diagnostic (diag_20ep) is a different regime: Adam lr=1e-4
    # destroys the seed (eps 16 -> 172 mHa, lambda_eff 49 -> 107). A single
    # linear model cannot extrapolate across that regime change (leave-one-
    # run-out MAE on lambda_eff was 13.7 when the Adam run was held out).
    # The trajectory model is therefore fit on LBFGS runs only; Adam inputs
    # are refused by the CLI with a pointer to diag_20ep.log. The Adam rows
    # stay in the dataset CSV as real measurements.
    traj_lbfgs = [r for r in traj if r["solver"] == "lbfgs"]
    Xt = _design_dfthcsos(traj_lbfgs)
    runs = sorted({r["run"] for r in traj_lbfgs})
    dft_models, dft_val = {}, {}
    for target, log_it in (("lambda_eff", False), ("eps_fro", True),
                           ("E_gap", False)):
        y = np.array([math.log(r[target]) if log_it else r[target]
                      for r in traj_lbfgs], dtype=float)
        errs = []
        for run in runs:
            tr = [i for i, r in enumerate(traj_lbfgs) if r["run"] != run]
            te = [i for i, r in enumerate(traj_lbfgs) if r["run"] == run]
            if not te:
                continue
            model = ridge_fit(Xt[tr], y[tr], lam=1.0)
            pred = ridge_predict(model, Xt[te])
            if log_it:
                pred, yy = np.exp(pred), np.exp(y[te])
            else:
                yy = y[te]
            errs.extend(np.abs(pred - yy).tolist())
        model = ridge_fit(Xt, y, lam=1.0)
        dft_models[target] = {**model, "log_target": log_it}
        dft_val[target] = {"leave_one_run_out_mae": float(np.mean(errs)),
                           "leave_one_run_out_max": float(np.max(errs)),
                           "runs": runs, "n": len(traj_lbfgs),
                           "target_mean": float(np.mean(
                               np.exp(y) if log_it else y)),
                           "excluded_runs": ["diag_20ep"],
                           "excluded_reason": "Adam lr=1e-4 destroys the "
                           "seed (measured); different regime, see "
                           "diag_20ep.log"}
    # shape model: log(error_2) and log(Lambda) vs R (R=B=C in all 3 points).
    shape_models = {}
    for target in ("error_2_mHa", "Lambda"):
        xs = np.array([[1.0, float(p["shape"][0])]
                       for p in DFTHCSOS_SHAPE_POINTS])
        y = np.array([math.log(p[target]) for p in DFTHCSOS_SHAPE_POINTS])
        w, *_ = np.linalg.lstsq(xs, y, rcond=None)
        shape_models[target] = {"coef": w.tolist(), "log_target": True,
                                "n": 3,
                                "note": "3 points, R=B=C collinear: "
                                        "rough ordering only"}

    # ---- dqi: formula check against the recorded scores ----
    dqi_checks = []
    for anchor in DQI_ANCHORS:
        got = dqi_score(anchor["T"], anchor["Q"], anchor["shots"],
                        anchor["failures"])
        recorded = anchor["score"]  # None when no recorded score exists
        anchor = {**anchor, **got}
        anchor["recorded_score"] = recorded
        if recorded is not None:
            anchor["rel_error_vs_recorded"] = (
                got["score"] - recorded) / recorded
        dqi_checks.append(anchor)
    for r in DQI_NITERS:
        dataset_rows.append({"benchmark": "dqi_niters", **r})

    # ---- write dataset + model ----
    ds_path = QCC_DATA / "logs" / "qcc_dataset.csv"
    ds_path.parent.mkdir(parents=True, exist_ok=True)
    with ds_path.open("w", newline="") as f:
        keys = sorted({k for r in dataset_rows for k in r})
        w = csv.DictWriter(f, fieldnames=["benchmark"] +
                           [k for k in keys if k != "benchmark"])
        w.writeheader()
        for r in dataset_rows:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})

    model = {
        "version": 1,
        "kind": "qcc-surrogate-v1",
        "trained": "2026-11-06",
        "note": "ESTIMATES ONLY. Every prediction is an estimate from "
                "real measured logs; nothing here is a verifier result.",
        "invsqrt": {"features": ["1", "j", "wc", "dd", "sesgo"],
                    "models": inv_models, "validation": inv_val,
                    "score_ratio_toffoli_equiv_over_T": ratio,
                    "score_anchors": INVSQRT_SCORE_ANCHORS, "n": len(inv_rows)},
        "dfthcsos": {"features": ["1", "log10(rho)", "eps_target",
                                  "epoch/100", "solver_is_adam"],
                     "models": dft_models, "validation": dft_val,
                     "shape_models": shape_models,
                     "shape_points": DFTHCSOS_SHAPE_POINTS,
                     "encode_offsets": DFTHCSOS_ENCODE_OFFSETS,
                     "brot_J_table": DFTHCSOS_BROT_J, "n_traj": len(traj_lbfgs),
                     "n_traj_all_runs": len(traj),
                     "regime": "LBFGS fine-tuning only; Adam inputs refused "
                               "(measured seed destruction, diag_20ep.log)"},
        "dqi": {"formula": "score = R(failures, shots) * Q^2 * mean_toffoli; "
                           "R from Clopper-Pearson upper bound (1-2^-128) + "
                           "repetition_overhead, same math as "
                           "verifiers/dqi/verify_submission_dqi.py",
                "anchors": dqi_checks, "n_iters_table": DQI_NITERS,
                "note": "No fitted regressor: only 2 decoder points exist. "
                        "The model converts (T, Q, shots, failures) into a "
                        "score estimate; it cannot predict T/Q for a new decoder."},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(model, indent=2), encoding="utf-8")

    print(f"dataset: {ds_path} ({len(dataset_rows)} rows)")
    print(f"model: {a.out}")
    print(f"invsqrt n={len(inv_rows)} validation: " +
          json.dumps(inv_val, indent=2))
    print(f"dfthcsos traj n={len(traj)} runs={runs} validation: " +
          json.dumps(dft_val, indent=2))
    print("dqi formula checks:")
    for c in dqi_checks:
        print(f"  {c['label']}: R={c['R']:.4f} score={c['score']:.4g} "
              f"rel_error_vs_recorded={c.get('rel_error_vs_recorded')}")


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
