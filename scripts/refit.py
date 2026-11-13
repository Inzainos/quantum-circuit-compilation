#!/usr/bin/env python3
"""Refit driver v2: calls Train directly so the solver can be chosen.

Usage:
  python refit.py --epochs 30 --solver lbfgs --lr 1.0 --rho 0.0001 --epsilon 0.01 \
      --rank 65 --bases 60 --copies 60 --tag lbfgs_65_60_60_ep30
  python refit.py --epochs 1000 --solver adam --lr 1e-6 --rho 0.0001 --epsilon 0.01 \
      --rank 40 --bases 40 --copies 40 --tag adam1e-6_40_40_40_ep1000
"""
import argparse
import os
import sys
import time

KIT = os.path.expanduser("~/workspace/qcc-data/starter-kit/starter_kit")
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.expanduser("~/workspace/qcc/kickmix"))

import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402
from dfthc import df_thc_sga  # noqa: E402
from dfthc.train_df_thc_sga import Initialize, Train  # noqa: E402
from starter.task1_factorization import train_df_thc_qaggle as T  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--solver", choices=["adam", "lbfgs"], default="lbfgs")
    ap.add_argument("--lr", type=float, default=1.0)
    ap.add_argument("--rho", type=float, default=0.0001)
    ap.add_argument("--epsilon", type=float, default=0.01)
    ap.add_argument("--rank", type=int, default=65)
    ap.add_argument("--bases", type=int, default=60)
    ap.add_argument("--copies", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-file", default=None)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--print-interval", type=int, default=10)
    ap.add_argument("--freeze-U", action="store_true",
                    help="freeze U; train only W and H2_I")
    a = ap.parse_args()

    out = os.path.expanduser(f"~/workspace/qcc-data/dfthcsos-refit/{a.tag}.npz")
    seed_file = a.seed_file or os.path.join(
        KIT, "starter/task1_factorization/FeMoco76_65_60_60.npz")
    print(f"tag={a.tag} solver={a.solver} lr={a.lr} epochs={a.epochs} "
          f"shape=({a.rank},{a.bases},{a.copies}) rho={a.rho} eps={a.epsilon} "
          f"freeze_U={a.freeze_U}", flush=True)
    print(f"seed={seed_file}\nout={out}", flush=True)

    ref = Initialize(os.path.join(KIT, "data/integrals/FeMoCo76o113e.fcidump"),
                     -22140.27335)
    params, _ = T.load_seed_params(seed_file, rank=a.rank, bases=a.bases,
                                   copies=a.copies, orbitals=ref["orbitals"],
                                   seed=a.seed)
    frozen = T.frozen_symmetry_params(ref)
    if a.freeze_U:
        frozen = {**frozen, "U": params["U"]}
    params = {**params, **frozen}
    o0 = df_thc_sga.Compute_qaggle_df_thc_cost_function(
        params, ref, a.rho, "DF-THC-SOS", epsilon_dfthc=a.epsilon,
        **T.FEMOCO_FLOORS)
    print(f"start: eps={1000*float(o0['epsilon_fro']):.4f} mHa "
          f"Lambda={float(o0['Lambda']):.4f} lambda_eff={float(o0['lambda_eff']):.4f} "
          f"E_gap={float(o0['sos_gap']):.4f}", flush=True)

    t0 = time.time()
    sol = Train(
        generating_set="Qaggle", method="DF-THC-SOS", epochs=a.epochs,
        learning_rate=a.lr, rho=a.rho, params=params, ref=ref,
        print_interval=a.print_interval, solver=a.solver,
        frozen_params=frozen, epsilon_dfthc=a.epsilon, **T.FEMOCO_FLOORS,
    )
    dt = time.time() - t0
    print(f"\nDONE tag={a.tag} wall={dt:.1f}s ({dt/max(a.epochs,1):.3f}s/epoch)",
          flush=True)
    vals = sol["values"]
    for k in ("Lambda", "lambda_eff", "epsilon_fro", "sos_gap", "E_SOS",
              "lambda_H1", "lambda_H2", "cost"):
        if k in vals:
            print(f"  {k} = {vals[k]}")
    T.save_solution(output_file=out, params_best=sol["params_best"],
                    values=sol["values"], ref=ref,
                    metadata={"tag": a.tag, "solver": a.solver, "lr": a.lr,
                              "epochs": a.epochs, "rho": a.rho,
                              "epsilon_dfthc": a.epsilon, "seed": a.seed,
                              "seed_solution_file": seed_file,
                              "freeze_U": a.freeze_U})
    print(f"  saved -> {out}")


if __name__ == "__main__":
    main()
