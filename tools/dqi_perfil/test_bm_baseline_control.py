#!/usr/bin/env python3
"""Control: ¿el BM v1 forward+reverse (baseline, banderas guardadas) es correcto?

Simula el BM a escala chica (n=6, LS=6) con un sindrome valido y verifica:
  - S sin cambios
  - sigma/tau/d/H restaurados a sus valores iniciales
    (sigma[0][0]=1, tau[1][0]=1, d[0]=1, resto 0)
Si el baseline es correcto, _dclear (que usa p/t) reconstruye la D verdadera,
y la comparacion D1 vs D2 del test anterior es valida.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_bm_stage_v1 import BMStageV1

DEG = 12
N, LS, K = 6, 6, 2

rng = np.random.default_rng(7)
pos = rng.choice(4095, size=K, replace=False)
vals = rng.integers(1, 4096, size=K)
X = [int(G.EXP[p % 4095]) for p in pos]
Svals = []
for t in range(N):
    s = 0
    for xj, e in zip(X, vals):
        s ^= G.mul(int(e), int(G.EXP[(G.LOG[xj] * t) % 4095]))
    Svals.append(s)

def bits_of(vals_list, deg=DEG):
    out = np.zeros((len(vals_list) * deg, 1), dtype=bool)
    for idx, v in enumerate(vals_list):
        for j in range(deg):
            out[idx * deg + j, 0] = bool((v >> j) & 1)
    return out

bld = km.CircuitBuilder()
gf = km.GF2Field(DEG)
S = [bld.create_quantum_register(DEG, name=f"S{i}") for i in range(N)]
bm = BMStageV1(bld, gf, S, LS, N)
bm.forward()
bm.reverse()
circ = bld.finish_circuit()
print(f"circuito: Q={circ.num_qubits} T={circ.operation_statistics().num_toffoli_like}")

sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
sim.use_same_registers_as(circ)
s_qubits = []
for reg in S:
    s_qubits.extend(list(reg))
sim.write_across_shots(km.array(s_qubits), bits_of(Svals))
sim.do(circ)

def read_reg(reg):
    bits = sim.read_across_shots(km.array(list(reg)))
    return sum(int(bits[j, 0]) << j for j in range(len(reg)))

# S sin cambios
s_out = [read_reg(S[i]) for i in range(N)]
print("S restaurado:", s_out == Svals, s_out)
# sigma: solo sigma[0][0]=1
sig_vals = [read_reg(bm.sigma[i]) for i in range(LS)]
print("sigma:", sig_vals, "-> OK" if sig_vals[0] == 1 and all(v == 0 for v in sig_vals[1:]) else "-> MAL")
tau_vals = [read_reg(bm.tau[i]) for i in range(LS)]
print("tau:", tau_vals, "-> OK" if tau_vals[1] == 1 and all(v == 0 for i, v in enumerate(tau_vals) if i != 1) else "-> MAL")
d_val = read_reg(bm.d)
print("d:", d_val, "-> OK" if d_val == 1 else "-> MAL")
h_val = read_reg(bm.H)
print("H:", h_val, "-> OK" if h_val == 0 else "-> MAL (sucio)")
print("fase volteada:", int(sim.read_phase_flipped_across_shots().sum()))
