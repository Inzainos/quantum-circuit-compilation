#!/usr/bin/env python3
"""Prototipo cuantico del paso in-place EEA/Schur (un paso de division).

Un paso de division polinomial con grados FIJOS (para evitar control
dependiente de datos): A de grado 5, B de grado 3, sobre GF(2^12).
  q = A[5] / B[3]            (1 inversion torre + 1 multiplicacion)
  A[i] ^= q * B[i-2]  i=2..5 (4 multiplicaciones-acumulacion, EN EL SITIO)
Tras el paso, A[5] = 0 (termino lider eliminado). La vuelta lo deshace
y restaura A. El cociente q es salida legitima del paso (en el EEA
completo se usa para actualizar t); aqui se conserva y se libera en
la vuelta tras restaurar A.

Esto valida el MECANISMO in-place: el estado vive en el arreglo de
entrada (A se sobrescribe), la vuelta lo restaura, y el costo por paso
es medible. Es el nucleo del decodificador in-place (Schur/EEA) donde
el estado vive en S en vez de en registros sigma/tau separados.

Compara contra BM v1 a la misma escala chica (n=6, LS=6): Q=333, T=7680.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_kmul import ixor_kmul
from dqi_tower_inv3 import ValueInv3

DEG = 12
DA, DB = 5, 3  # grados fijos de A y B

def bits_of(vals_list, deg=DEG):
    out = np.zeros((len(vals_list) * deg, 1), dtype=bool)
    for idx, v in enumerate(vals_list):
        for j in range(deg):
            out[idx * deg + j, 0] = bool((v >> j) & 1)
    return out

def build_paso(ida_y_vuelta=True):
    b = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    # A (6 coefs) y B (4 coefs) = el "arreglo S" en sitio
    A = [b.create_quantum_register(DEG, name=f"A{i}") for i in range(DA + 1)]
    B = [b.create_quantum_register(DEG, name=f"B{i}") for i in range(DB + 1)]
    q = b.alloc_qubits(DEG)
    invB = b.alloc_qubits(DEG)
    # --- forward: q = A[5]/B[3] ---
    vi = ValueInv3(b, B[DB], invB).forward()
    ixor_kmul(b, A[DA], invB, q)
    vi.undo()
    b.free(invB)
    # --- forward: A[i] ^= q*B[i-2], i=2..5 (en el sitio) ---
    for i in range(2, DA + 1):
        ixor_kmul(b, q, B[i - 2], A[i])
    if ida_y_vuelta:
        # --- reverse: A[i] ^= q*B[i-2] (restaura A) ---
        for i in reversed(range(2, DA + 1)):
            ixor_kmul(b, q, B[i - 2], A[i])
        # --- reverse: liberar q (A[5] ya esta restaurado) ---
        invB2 = b.alloc_qubits(DEG)
        vi2 = ValueInv3(b, B[DB], invB2).forward()
        ixor_kmul(b, A[DA], invB2, q)
        vi2.undo()
        b.free(invB2)
    b.free(q)
    return b.finish_circuit(), A, B

def read_reg(sim, reg):
    bits = sim.read_across_shots(km.array(list(reg)))
    return [sum(int(bits[j, 0]) << j for j in range(len(reg)))]

# valores de prueba (A[5] y B[3] != 0)
rng = np.random.default_rng(3)
Avals = [int(v) for v in rng.integers(1, 4096, size=DA + 1)]
Bvals = [int(v) for v in rng.integers(1, 4096, size=DB + 1)]
# clasico: q y A' esperados
q_exp = G.mul(Avals[DA], G.inv(Bvals[DB]))
Aexp = list(Avals)
for i in range(2, DA + 1):
    Aexp[i] ^= G.mul(q_exp, Bvals[i - 2])
print("A:", Avals, "B:", Bvals)
print("q esperado:", q_exp, "A' esperado:", Aexp, "A'[5] debe ser 0:", Aexp[DA] == 0)

for iv in (False, True):
    circ, A, B = build_paso(ida_y_vuelta=iv)
    print(f"paso ida_y_vuelta={iv}: Q={circ.num_qubits} T={circ.operation_statistics().num_toffoli_like}")
    # simular (solo ida para verificar A' y q; ida+vuelta para restaurar)
    sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(circ)
    allq = []
    for reg in A:
        allq.extend(list(reg))
    for reg in B:
        allq.extend(list(reg))
    sim.write_across_shots(km.array(allq), bits_of(Avals + Bvals))
    sim.do(circ)
    def read(r):
        bits = sim.read_across_shots(km.array(list(r)))
        return sum(int(bits[j, 0]) << j for j in range(len(r)))
    a_out = [read(A[i]) for i in range(DA + 1)]
    b_out = [read(B[i]) for i in range(DB + 1)]
    if not iv:
        print("  A' medido:", a_out, "OK" if a_out == Aexp else "MAL")
        print("  B intacto:", b_out == Bvals)
    else:
        print("  A restaurado:", a_out == Avals, a_out)
        print("  B intacto:", b_out == Bvals)
    print("  fase volteada:", int(sim.read_phase_flipped_across_shots().sum()))
