#!/usr/bin/env python3
"""Modelo offline de T_total y Q_total del score dfthcsos (sin FCIDUMP ni npz).

score = lambda_eff * T_total * Q_total.  Aqui solo se modela T_total*Q_total;
lambda_eff (y las puertas error_1/error_2/Lambda/E_gap) requieren FCIDUMP + npz
y NO se pueden calcular desde este modulo.

MEDIDO/EXACTO: la parte heuristica (SpinFreeData_V1 importado del verificador,
mismas formulas que verify.heuristic_costs) y las formulas de combinacion de
verify.resource_costs.
MODELO (ver --measure para contrastarlo con kickmix): ANGLES = 2*K*(A-2) para
unary iteration (QROM ordinaria del ejemplo), A = N + R*B.
ESTIMADO: variantes QROAM/SELECT-SWAP (no hay circuito construido).

Uso (desde /home/claude/qcc-local, 1 nucleo, sin simulacion):
    python3 tools/dfthcsos_cost_model.py            # tablas completas
    python3 tools/dfthcsos_cost_model.py --measure  # ademas cuenta puertas de QROMs unary reales
"""

from __future__ import annotations

import argparse
import itertools
import math
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "verifiers"))

from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1, QR, QI  # noqa: E402

N = 76
KEEP_BITS = 10          # verify.KEEP_BITS (chi), fijo por el verificador
QUBIT_CAP = 128         # verify.QUBIT_CAP, solo sobre cada ANGLE_k
LOG = []


def out(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


# ---------------------------------------------------------------- heuristica (exacta)
def heuristic(R, B, C, brot, n=N):
    m = SpinFreeData_V1(R=R, B=B, C=C, N=n, chi=KEEP_BITS, beta=brot)
    oq, iq = m.outer_state_prep_qubit_cost(), m.inner_state_prep_qubit_cost()
    return dict(
        outer=m.outer_state_prep(), inner=m.inner_state_prep(), givens=m.givens_rotations(),
        persistent=oq["persistent"] + iq["persistent"],
        temp=max(oq["temporary"], iq["temporary"]),
        outer_temp=oq["temporary"], inner_temp=iq["temporary"],
        outer_pers=oq["persistent"], inner_pers=iq["persistent"],
    )


# ---------------------------------------------------------------- ANGLES
def sel_bits(A):
    return (A - 1).bit_length()


def unary_circuit(A, J, brot):
    """QROM unary iteration del ejemplo: Toffolis por circuito y qubits (modelo)."""
    n = sel_bits(A)
    return dict(tof=A - 2, qubits=n + J * brot + (n - 1), temp=n - 1)


def total(R, B, C, J, brot, n=N, angles=None):
    """T_total, Q_total con ANGLES unary (o 'angles' = dict(tof_per_circuit, temp, qubits))."""
    A = n + R * B
    K = math.ceil((n - 1) / J)
    h = heuristic(R, B, C, brot, n)
    u = angles or unary_circuit(A, J, brot)
    ang_T = 2 * K * u["tof"]
    T = ang_T + h["outer"] + h["inner"] + h["givens"]
    Q = h["persistent"] + J * brot + max(h["temp"], u["temp"])
    return dict(R=R, B=B, C=C, J=J, brot=brot, A=A, K=K, sel=sel_bits(A), ang_T=ang_T,
                outer=h["outer"], inner=h["inner"], givens=h["givens"], T=T,
                pers_heur=h["persistent"], pers_ang=J * brot, temp_heur=h["temp"],
                temp_ang=u["temp"], temp=max(h["temp"], u["temp"]), Q=Q, TQ=T * Q,
                ang_qubits=u["qubits"], ok=u["qubits"] <= QUBIT_CAP)


def maxJ(A, brot):
    """J maximo con sel + J*brot + (sel-1) <= 128 (unary)."""
    n = sel_bits(A)
    return (QUBIT_CAP - n - (n - 1)) // brot


# ---------------------------------------------------------------- QROAM / SELECT-SWAP (estimado)
def qroam_circuit(A, J, brot, k, kp=None, clean_target_alias=False):
    """XOR-oracle con QROAM de bloque 2^k y descomputacion por medicion (ESTIMADO).

    Carga:    unary iteration sobre L = ceil(A/2^k) bloques: max(L-2,0) Toffolis
    Swap:     W*(2^k-1) CSWAP (red de swap sobre los k bits bajos)
    Copia a target: CX (gratis)
    Descomp.: medir registros de datos en X + fixup de fase: modelo QI de Berry
              ceil(A/2^kp)+2^kp-1 (identico a QI() del verificador; kp optimo libre)
    Qubits:   sel + W (target) + W*2^k (registros de datos limpios; optimista
              W*(2^k-1) si el registro 0 se alias con el target, no verificado)
              + (ceil(log2 L) - 1) ancillas del unary.
    k=0 se reduce a la unary del ejemplo (sin datos extra, sin swap, descomp. por del_and).
    """
    n, W = sel_bits(A), J * brot
    if k == 0:
        return unary_circuit(A, J, brot)
    L = math.ceil(A / 2**k)
    nL = max(1, (L - 1).bit_length())
    data = W * (2**k - 1) if clean_target_alias else W * 2**k
    anc_unary = max(0, nL - 1)
    load = max(L - 2, 0) + W * (2**k - 1)
    # descomputacion: elegir kp que quepa (los registros de datos se miden y quedan libres)
    best = None
    for kq in range(0, 12):
        free = data  # qubits liberados tras medir (reusados para el fixup)
        need = 2**kq + max(0, math.ceil(math.log2(max(2, A / 2**kq))))
        if need > free + anc_unary:
            continue
        c = math.ceil(A / 2**kq) + 2**kq - 1
        if best is None or c < best[0]:
            best = (c, kq)
    unc = best[0] if best else A  # peor caso: sin fixup compacto
    tof = load + unc
    temp = data + anc_unary
    return dict(tof=tof, qubits=n + W + temp, temp=temp, k=k, kp=best[1] if best else None,
                load=load, unc=unc)


# ---------------------------------------------------------------- tablas
HDR = ("R", "B", "C", "J", "brot", "A", "K", "sel", "ang_T", "outer", "inner", "givens", "T",
       "pers_heur", "pers_ang", "temp", "Q", "TQ", "ang_qubits")


def row(d):
    return "  ".join(f"{d[h]:>10}" if h == "TQ" else f"{d[h]:>7}" for h in HDR)


def header():
    return "  ".join(f"{h:>10}" if h == "TQ" else f"{h:>7}" for h in HDR)


def measure_unary():
    """Cuenta estatica de puertas de la QROM unary de referencia con deltas aleatorios
    (solo estructura/costo; NO se simula ni se verifica; no es un envio)."""
    import importlib.util
    import numpy as np
    spec = importlib.util.spec_from_file_location(
        "ref", _ROOT / "verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py")
    sys.path.insert(0, str(_ROOT / "verifiers"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rng = np.random.default_rng(0)
    out("\n[MEDIDO con kickmix, conteo estatico, deltas aleatorios]")
    out("   A  J brot  sel  qubits(med) qubits(mod)  tof(med) tof(mod=A-2)")
    for A, J, brot in [(3976, 8, 12), (2026, 9, 12), (3000, 8, 12), (3976, 9, 11), (1500, 4, 12), (3976, 1, 12)]:
        delta = rng.integers(0, 2**brot, size=(A, J), dtype=np.int64)
        c = mod.build_angle_k_circuit(delta, brot)
        m = unary_circuit(A, J, brot)
        out(f"{A:>5} {J:>2} {brot:>4} {sel_bits(A):>4} {c.num_qubits:>11} {m['qubits']:>11} "
            f"{c.operation_statistics().num_toffoli_like:>9} {m['tof']:>12}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--log", default=str(_ROOT / "logs/dfthcsos_cost_model.log"))
    args = ap.parse_args()

    # 1) baseline
    out("== 1. BASELINE (R,B,C)=(65,60,60) J=8 brot=12 ==")
    b = total(65, 60, 60, 8, 12)
    exp = dict(ang_T=79480, outer=846, inner=9461, givens=3450, T=93237, Q=730,
               pers_heur=90, pers_ang=96, temp=544)
    for k, v in exp.items():
        out(f"  {k:<10} modelo={b[k]:<8} esperado={v:<8} {'OK' if b[k] == v else 'DIFIERE'}")
    out(f"  A={b['A']} K={b['K']} sel={b['sel']} ang_qubits={b['ang_qubits']} (ejemplo: 119) "
        f"temp_ang={b['temp_ang']} (11, << 544)  TQ={b['TQ']}")
    out(f"  persistentes totales = {b['pers_heur'] + b['pers_ang']} (esperado 186); "
        f"outer_temp={heuristic(65,60,60,12)['outer_temp']} inner_temp={heuristic(65,60,60,12)['inner_temp']}")
    h16 = heuristic(65, 60, 60, 16)
    out(f"  chequeo brot=16 (README: 846+9461+4650, 90 pers, 1087 temp): "
        f"{h16['outer']}+{h16['inner']}+{h16['givens']}, pers={h16['persistent']}, temp={h16['temp']}")
    out(f"  lambda_eff baseline (README, NO calculable aqui) = 49.30136925057438 -> "
        f"score = {49.30136925057438 * b['T'] * b['Q']:.10g} (README: 3355599588.3155365)")

    # 2) brot x J en baseline
    out("\n== 2. Baseline (65,60,60): brot x J (unary, cap 128 por ANGLE_k) ==")
    out(header())
    for brot in range(6, 17):
        for J in sorted({maxJ(b["A"], brot), 8, 6, 5, 4}):
            if J < 1:
                continue
            try:
                d = total(65, 60, 60, J, brot)
            except ValueError as e:
                out(f"brot={brot} J={J}: {e}")
                continue
            if d["ok"]:
                out(row(d))

    # 3) barrido (R,B,C)
    out("\n== 3. Barrido (R,B,C) con J maximo bajo el cap, brot 8..12; top 25 por T*Q (sin lambda_eff) ==")
    res = []
    for R, B, C, brot in itertools.product((30, 40, 50, 55, 60, 65), (30, 40, 50, 55, 60), (30, 40, 50, 60), range(8, 13)):
        A = N + R * B
        J = maxJ(A, brot)
        if J < 1:
            continue
        try:
            res.append(total(R, B, C, J, brot))
        except ValueError:
            continue
    res.sort(key=lambda d: d["TQ"])
    out(header())
    for d in res[:25]:
        out(row(d))
    out(f"  (baseline TQ = {b['TQ']}; el mejor del barrido = {res[0]['TQ']} -> x{res[0]['TQ']/b['TQ']:.3f})")
    out("  OJO: reducir R,B,C empeora error_1/error_2/Lambda/E_gap (no modelado); el score real incluye lambda_eff.")

    # 4) sensibilidades marginales desde baseline
    out("\n== 4. Sensibilidad marginal desde baseline (cada fila cambia UNA variable) ==")
    out(header())
    for kw in [dict(), dict(R=55), dict(B=50), dict(C=50), dict(R=50, B=50), dict(brot=10, J=10),
               dict(brot=11, J=9), dict(brot=12, J=8), dict(J=5), dict(J=4)]:
        a = dict(R=65, B=60, C=60, J=8, brot=12)
        a.update(kw)
        if "R" in kw or "B" in kw:
            a["J"] = maxJ(N + a["R"] * a["B"], a["brot"]) if "J" not in kw else a["J"]
        d = total(**a)
        out(row(d), "  <-", kw)

    # 5) QROAM
    out("\n== 5. QROAM/SELECT-SWAP vs unary por circuito ANGLE_k (ESTIMADO, no construido) ==")
    out("  modelo: carga=(ceil(A/2^k)-2)+W*(2^k-1); descomp.=ceil(A/2^kp)+2^kp-1; qubits=sel+W+W*2^k+anc_unary")
    out("  A=3976, brot=12; T_ang = 2*K*tof; fila con ok=False excede 128")
    out(f"  {'J':>2} {'W':>4} {'k':>2} {'K':>3} {'tof/circ':>9} {'qubits':>7} {'temp':>5} {'T_ang':>8} {'T':>8} {'Q':>5} {'TQ':>10} ok")
    cands = []
    for brot in (8, 10, 12):
        for J in range(1, 14):
            for k in range(0, 5):
                for alias in (False, True):
                    if k == 0 and alias:
                        continue
                    u = qroam_circuit(3976, J, brot, k, clean_target_alias=alias)
                    d = total(65, 60, 60, J, brot, angles=u)
                    cands.append((brot, J, k, alias, u, d))
    shown = 0
    for brot, J, k, alias, u, d in sorted(cands, key=lambda t: t[5]["TQ"]):
        if not d["ok"]:
            continue
        out(f"  brot={brot} J={J:>2} W={J*brot:>3} k={k} alias={int(alias)} K={d['K']:>2} tof/c={u['tof']:>5} "
            f"qubits={u['qubits']:>3} temp={u['temp']:>3} T_ang={d['ang_T']:>6} T={d['T']:>6} Q={d['Q']:>4} TQ={d['TQ']}")
        shown += 1
        if shown >= 12:
            break
    out("  Mejor unary (k=0) vs mejor QROAM (k>0) a igual brot (T*Q, A=3976):")
    for brot in (8, 10, 12):
        u0 = min((c for c in cands if c[0] == brot and c[2] == 0 and c[5]["ok"]), key=lambda t: t[5]["TQ"])
        u1 = min((c for c in cands if c[0] == brot and c[2] > 0 and c[5]["ok"]), key=lambda t: t[5]["TQ"])
        out(f"    brot={brot}: unary J={u0[1]} TQ={u0[5]['TQ']} | QROAM J={u1[1]} k={u1[2]} alias={int(u1[3])} "
            f"TQ={u1[5]['TQ']} (x{u1[5]['TQ']/u0[5]['TQ']:.3f} vs unary)")
    best_k = [c for c in cands if c[2] > 0 and c[5]["ok"]]
    best_k.sort(key=lambda t: t[5]["TQ"])
    if best_k:
        brot, J, k, alias, u, d = best_k[0]
        out(f"  mejor QROAM (k>0) que cabe: brot={brot} J={J} k={k} alias={int(alias)} tof/c={u['tof']} T_ang={d['ang_T']} "
            f"TQ={d['TQ']} (x{d['TQ']/b['TQ']:.3f} vs baseline)")
    out("  Toffolis por direccion (carga unary, 1 circuito, A=3976): "
        f"{(3976 - 2) / 3976:.4f}/dir (A-2 total); QR del verificador A=3976,W=96: {QR(3976, 96)}, QI(3976): {QI(3976)}")
    cap_free = QUBIT_CAP - sel_bits(3976) - 96 - (sel_bits(3976) - 1)
    out(f"  qubits libres bajo el cap con el baseline (J=8, brot=12): {cap_free}")
    out("  nota: el espacio temporal < 544 es gratis en Q, pero el cap de 128 por ANGLE_k es el limite duro.")

    if args.measure:
        measure_unary()

    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    Path(args.log).write_text("\n".join(LOG) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
