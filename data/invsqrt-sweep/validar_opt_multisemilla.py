"""Validación multi-semilla del HMR vectorial del ACC (tubería de monomios).

El informe de investigación flaggeó que el HMR vectorial del ACC solo se
validó con 8 shots y una semilla (seed=3) — el mismo mecanismo de falso
positivo que tumbó sin_ruido/todo_en_uno/patada_final podría afectarla.
Elán: ya teníamos las semillas.

Corre la tubería de monomios (segmentos) con varias semillas y muchos
shots por semilla, verificando en TODOS: fase dentro de tolerancia, x
restaurada, ancillas limpias.
"""
import sys
import os

sys.path.insert(0, "/home/hatch/workspace/qcc-zip-final/src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import kickmix as km

# Reusar el constructor de la tubería de segmentos importando el módulo
# (su main() corre al importar, así que mejor reconstruir el circuito aquí
# ejecutando el script como subprocess no es práctico; en su lugar cargamos
# el .kmx ya construido).
CIRCUIT = "/tmp/proto_fase_valor_opt.kmx"
N_X = 22
TOL = 5.96e-08
SEEDS = [3, 7, 11, 13, 42]
SHOTS_PER_SEED = 64


def main():
    circ = km.Circuit.from_file(CIRCUIT)
    print(f"circuito: {circ.num_qubits} qubits, {CIRCUIT}")
    st = circ.operation_statistics()
    print(f"Toffoli-like: {st.num_toffoli_like} T-like: {st.num_t_like}")
    total_fail = 0
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        xs = rng.integers(1, 1 << N_X, size=SHOTS_PER_SEED, dtype=np.int64)
        # Incluir casos borde en cada semilla.
        xs[0] = 1
        xs[1] = 2
        xs[2] = 3
        xs[3] = (1 << 21) - 1
        sim = km.Simulator(batch_size=len(xs), debug_print=False,
                           counting_operations=True, seed=seed)
        sim.use_same_registers_as(circ)
        bits_in = ((xs[None, :] >> np.arange(N_X)[:, None]) & 1) == 1
        sim.write_across_shots(km.array([km.q(i) for i in range(N_X)]), bits_in)
        sim.do(circ)
        outx = sim.read_across_shots(km.array([km.q(i) for i in range(N_X)]))
        x_ok = bool((outx == bits_in).all())
        errs = []
        for t_idx in range(len(xs)):
            ph = sim.read_shot_phase(t_idx)
            xv = int(xs[t_idx])
            exact = 2.0 / np.sqrt(xv)
            d = abs((ph - exact) % 1.0)
            d = min(d, 1.0 - d)
            errs.append(d)
        errs = np.array(errs)
        nq = circ.num_qubits
        allq = sim.read_across_shots(km.array([km.q(i) for i in range(nq)]))
        dirty = [qq for qq in range(nq) if qq >= N_X and bool(allq[qq].any())]
        pasa = bool(errs.max() < TOL and x_ok and len(dirty) == 0)
        if not pasa:
            total_fail += 1
        print(f"seed={seed}: fase max={errs.max():.3e} ¿Pasa? {errs.max() < TOL} | "
              f"x restaurada: {x_ok} | sucios: {len(dirty)} | TOTAL: {'PASA' if pasa else 'FALLA'}")
        if errs.max() >= TOL:
            worst = int(np.argmax(errs))
            print(f"  peor x={int(xs[worst])} err={errs[worst]:.3e}")
    print(f"\nSemillas que FALLAN: {total_fail}/{len(SEEDS)}")
    if total_fail == 0:
        print("El HMR vectorial del ACC pasa en todas las semillas y shots.")
    else:
        print("El HMR vectorial del ACC es FALSO POSITIVO en al menos una semilla.")


if __name__ == "__main__":
    main()
