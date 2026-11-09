#!/usr/bin/env python3
"""Prototipo cuantico a escala chica: reciproco de serie GF(2^12), n=6.
Usa ixor_kmul (54 AND) e init_kinv/del_kinv (270 T) del DQI.
h[0] = inv(g[0]);  h[k] = inv0 * sum_{i=1..k} g[i]*h[k-i].
Mide Q, T (Toffoli-like), profundidad; verifica h correcto, g intacto,
ancillas limpios (inv0, acc), fase 0.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_kmul import ixor_kmul
from dqi_kinv import init_kinv, del_kinv

DEG = 12
N = 6  # coeficientes de la serie

def gf_reciprocal_classical(g):
    if g[0] == 0:
        return None
    inv0 = G.inv(g[0])
    h = [0]*N
    h[0] = inv0
    for k in range(1, N):
        acc = 0
        for i in range(1, k+1):
            acc ^= G.mul(g[i], h[k-i])
        h[k] = G.mul(inv0, acc)
    return h

def bits_of(vals_list, deg=DEG, nshots=1):
    out = np.zeros((len(vals_list) * deg, nshots), dtype=bool)
    for idx, v in enumerate(vals_list):
        for j in range(deg):
            out[idx * deg + j, 0] = bool((v >> j) & 1)
    return out

def build_reciprocal_circuit():
    b = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    g_regs = [b.alloc_qubits(DEG) for _ in range(N)]
    inv0 = b.alloc_qubits(DEG)
    h_regs = [b.alloc_qubits(DEG) for _ in range(N)]
    acc = b.alloc_qubits(DEG)
    scaf = init_kinv(b, gf, g_regs[0], inv0)
    for j in range(DEG):
        b.cx(inv0[j], h_regs[0][j])
    for k in range(1, N):
        for i in range(1, k+1):
            ixor_kmul(b, g_regs[i], h_regs[k-i], acc)
        ixor_kmul(b, inv0, acc, h_regs[k])
        # Limpia acc reaplicando los productos (XOR es su propio inverso;
        # ixor_kmul libera sus transitorios con MBU internamente)
        for i in range(k, 0, -1):
            ixor_kmul(b, g_regs[i], h_regs[k-i], acc)
    del_kinv(b, gf, g_regs[0], inv0, scaf)
    circ = b.finish_circuit()
    return circ, (g_regs, inv0, h_regs, acc)

def read_reg(sim, reg):
    bits = sim.read_across_shots(km.array(list(reg)))
    return sum(int(bits[j, 0]) << j for j in range(len(reg)))

def main():
    rng = np.random.default_rng(42)
    g_vals = [int(rng.integers(1, 4096)) if i == 0 else int(rng.integers(0, 4096)) for i in range(N)]
    h_exp = gf_reciprocal_classical(g_vals)
    print(f"g = {g_vals}")
    print(f"h esperado = {h_exp}")
    prod = [0]*(2*N-1)
    for i in range(N):
        for j in range(N):
            prod[i+j] ^= G.mul(g_vals[i], h_exp[j])
    print(f"g*h mod x^{N} = {prod[:N]} (debe ser [1,0,0,0,0,0])")
    circ, (g_regs, inv0, h_regs, acc) = build_reciprocal_circuit()
    nq = circ.num_qubits
    toff = int(circ.operation_statistics().num_toffoli_like)
    print(f"\nCircuito reciproco n={N}: Q={nq} T={toff} "
          f"reaction_depth={circ.reaction_depth()}")
    # Simulacion
    sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(circ)
    g_qubits = []
    for reg in g_regs:
        g_qubits.extend(list(reg))
    sim.write_across_shots(km.array(g_qubits), bits_of(g_vals))
    sim.do(circ)
    g_out = [read_reg(sim, g_regs[i]) for i in range(N)]
    h_out = [read_reg(sim, h_regs[i]) for i in range(N)]
    inv0_out = read_reg(sim, inv0)
    acc_out = read_reg(sim, acc)
    fase = int(sim.read_phase_flipped_across_shots().sum())
    print(f"g intacto: {g_out == g_vals}  {g_out}")
    print(f"h correcto: {h_out == h_exp}  {h_out}")
    print(f"inv0 limpio (0): {inv0_out == 0}  valor={inv0_out}")
    print(f"acc limpio (0): {acc_out == 0}  valor={acc_out}")
    print(f"fase (0 esperado): {fase}")
    # Costo teorico: 1 inversion (270) + productos.
    # Productos: por k, k productos para acc + 1 para h[k] + k para limpiar acc = 2k+1.
    # Total productos = sum_{k=1}^{5} (2k+1) = 3+5+7+9+11 = 35. A 54 ANDs = 1890.
    # Mas inversion 270 = 2160 esperado (si del_kinv es 0 T y los ANDs de limpieza
    # se cuentan igual que los de ida).
    nprod = sum(2*k+1 for k in range(1, N))
    print(f"\nProductos GF(2^12): {nprod} x 54 AND = {nprod*54} + inversion 270 = {nprod*54+270} T esperado")
    print(f"T medido = {toff}")
    print(f"Q esperado: g {N*DEG} + inv0 {DEG} + h {N*DEG} + acc {DEG} = {2*N*DEG+2*DEG} + transitorios")

if __name__ == "__main__":
    main()
