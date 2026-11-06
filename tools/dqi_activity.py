#!/usr/bin/env python3
"""Actividad de registros del EEA de v10: para cada iteracion k, que posiciones de reg_a/reg_b valen != 0.

Construye prefijos del EEA directo (k iteraciones), los simula con tiros del verificador y guarda, por k,
el conteo de tiros con reg_a[i] != 0 y reg_b[i] != 0. Uso: python3 tools/dqi_activity.py --ks 0 4 8 ... --shots 2560
Salida: .npz con arrays act_a[k,i], act_b[k,i] (numero de tiros activos).
"""
import argparse, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "verifiers" / "dqi"))
import kickmix as km  # noqa: E402
km.Circuit.reaction_depth = lambda self: -1
import verify_submission_dqi as v  # noqa: E402
from dqi_optimized_v10 import ProosAndZalkaDecoderV10  # noqa: E402

N_ITERS, M_POS, N_SYN, DEG = 222, 4095, 70, 12


def prefijo(k: int):
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG); dec = ProosAndZalkaDecoderV10(N_SYN, gf)
    S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(N_SYN)]
    E = [b.create_classical_register(DEG, name=f"E{j}") for j in range(M_POS)]
    m = N_SYN + 3
    reg_a = [b.alloc_qubits(DEG) if i < 3 else S[i - 3] for i in range(m)]
    reg_b = [b.alloc_qubits(DEG) for _ in range(m)]
    n_A, n_B, n_a, n_b = (b.alloc_qubits(7) for _ in range(4))
    n_q = b.alloc_qubits(m.bit_length()); flag = b.alloc_qubits(1)[0]; counter = b.alloc_qubits(2)
    halting = b.alloc_qubits(N_ITERS.bit_length())
    init_ones = km.array([reg_a[0][0], reg_b[m - 1][0], n_a[0], flag]); b.x(init_ones)
    b.gf2_iadd(N_SYN, target=n_A); b.gf2_iadd(N_SYN + 1, target=n_B)
    dec._initial_shift_loop(b, reg_a, n_A, N_SYN, m, is_adjoint=False)
    dec._synchronized_eea(b, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag, counter, halting, k, m, m, m, is_adjoint=False)
    return b.finish_circuit(), reg_a, reg_b, S


def actividad(k: int, shots: int, seed: int, batch=256):
    c, reg_a, reg_b, S = prefijo(k)
    spec = v.ProblemSpecDQI(m=M_POS, n=N_SYN, degree=DEG, r=v.default_num_accepted_values(DEG), num_shots=shots)
    wp = v.optimal_dqi_weights(M_POS, spec.max_errors, DEG, spec.r) ** 2
    tables = v.FieldTables(km.GF2Field(DEG))
    syn_arr = km.array([q for s in S for q in s])
    ra = [km.array(list(r)) for r in reg_a]; rb = [km.array(list(r)) for r in reg_b]
    act_a = np.zeros(len(ra), dtype=np.int64); act_b = np.zeros(len(rb), dtype=np.int64)
    for b0 in range(0, shots, batch):
        rng = np.random.default_rng([seed, b0])
        syndromes, mbuc, _ = v.sample_shots(spec, tables, rng, batch, wp)
        sim = km.Simulator(batch_size=batch, debug_print=False, counting_operations=False, seed=b0 + 1)
        sim.use_same_registers_as(c)
        sim.write_across_shots(syn_arr, v.to_bits(syndromes, DEG))
        sim.do(c)
        for i in range(len(ra)):
            act_a[i] += int(sim.read_across_shots(ra[i]).any(axis=0).sum())
            act_b[i] += int(sim.read_across_shots(rb[i]).any(axis=0).sum())
    return act_a, act_b


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ks", type=int, nargs="+", required=True); ap.add_argument("--shots", type=int, default=2560)
    ap.add_argument("--seed", type=int, default=3); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {}
    for k in a.ks:
        t0 = time.time(); aa, ab = actividad(k, a.shots, a.seed); res[k] = (aa, ab)
        print(f"k={k} {time.time()-t0:.0f}s  activos a:{int((aa>0).sum())} b:{int((ab>0).sum())}", flush=True)
    np.savez(a.out, ks=np.array(list(res)), act_a=np.array([res[k][0] for k in res]), act_b=np.array([res[k][1] for k in res]), shots=a.shots)
