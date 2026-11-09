#!/usr/bin/env python3
"""Prototipo kickmix a escala chica: un paso rombo del q-d (Schur por bloques).
Nucleo: division de campo a/b = a * inv(b) con TowerInv3 (75 T) + Karatsuba
(54 T), y la multiplicacion previa e*q (54 T). Un q-entry del q-d cuesta
1 division + 1 multiplicacion = 129 + 54 = 183 T (estimado). Aqui se MIDE
la division en contexto y se verifica correctitud + limpieza en simulador.
Tambien se mide un multiplicador GF(2^12) (54 T, ya medido en dqi_kmul).
n=6 (serie corta) para el rombo completo: q' = e1*q1/e0, e' = q1' + q' + e1
donde q1' es el q del rombo vecino (se pasa como entrada).
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_kmul import ixor_kmul
from dqi_tower_inv3 import ValueInv3

DEG = 12

def bits(v):
    return ((np.asarray(v)[None, :] >> np.arange(DEG)[:, None]) & 1) == 1

def build_division():
    """target = a * inv(b). a,b,target registros de 12 qubits. Devuelve circuito."""
    b = km.CircuitBuilder()
    a = b.create_quantum_register(DEG, name='a')
    bb = b.create_quantum_register(DEG, name='b')
    t = b.create_quantum_register(DEG, name='t')   # target, inicia en 0
    # inv(b) en un registro temporal w (12 qubits) via TowerInv3
    w = b.alloc_qubits(DEG)
    inv = ValueInv3(b, bb, w)
    inv.forward()
    # t ^= a * w  (Karatsuba)
    ixor_kmul(b, a, w, t)
    # deshacer la inversion (TowerInv3.undo) para limpiar w
    inv.undo()
    return b.finish_circuit()

def build_rombo():
    """Un rombo q-d completo (escala chica, n=6 -> valores de 12 bits):
    entradas: q0=q_k^(n), q1=q_k^(n+1), e0=e_k^(n), e1=e_k^(n+1),
              q1p=q_{k+1}^(n+1) (vecino, precomputado), em1=e_{k-1}^(n+1).
    salidas: qp = e1*q1/e0  (q_{k+1}^(n)),  ep = q1p + qp + e1  (e_{k+1}^(n)).
    qp y ep se escriben en registros frescos (se mide el costo forward).
    """
    b = km.CircuitBuilder()
    q0 = b.create_quantum_register(DEG, name='q0')
    q1 = b.create_quantum_register(DEG, name='q1')
    e0 = b.create_quantum_register(DEG, name='e0')
    e1 = b.create_quantum_register(DEG, name='e1')
    q1p = b.create_quantum_register(DEG, name='q1p')
    em1 = b.create_quantum_register(DEG, name='em1')
    qp = b.create_quantum_register(DEG, name='qp')
    ep = b.create_quantum_register(DEG, name='ep')
    # qp = e1*q1/e0 : (e1*q1) * inv(e0)
    tmp = b.alloc_qubits(DEG)   # e1*q1
    ixor_kmul(b, e1, q1, tmp)
    w = b.alloc_qubits(DEG)     # inv(e0)
    inv = ValueInv3(b, e0, w)
    inv.forward()
    ixor_kmul(b, tmp, w, qp)
    inv.undo()
    b.free(tmp); b.free(w)
    # ep = q1p + qp + e1  (XORs, Clifford)
    for i in range(DEG):
        b.cx(q1p[i], ep[i])
        b.cx(qp[i], ep[i])
        b.cx(e1[i], ep[i])
    return b.finish_circuit()

rng = np.random.default_rng(3)
B = 64
# --- division ---
c = build_division()
print(f"division a/b: qubits={c.num_qubits} toffoli={c.operation_statistics().num_toffoli_like}")
# verificar en simulador
xs = rng.integers(1, 4096, B); ys = rng.integers(1, 4096, B)
sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=True, seed=1)
sim.use_same_registers_as(c)
sim.write_across_shots(km.array([km.q(i) for i in range(36)]),
                       np.concatenate([bits(xs), bits(ys), bits(np.zeros(B, dtype=int))]))
sim.do(c)
out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
tvals = np.zeros(B, dtype=int)
for i in range(DEG):
    tvals |= (out[24+i].astype(int) << i)
esp = np.array([G.mul(int(x), G.inv(int(y))) for x, y in zip(xs, ys)])
print(f"  division correcta: {bool((tvals==esp).all())} ; fase volteada={int(sim.read_phase_flipped_across_shots().sum())} ; ancillas limpias={not out[36:].any()}")
# --- rombo ---
c2 = build_rombo()
print(f"rombo q-d (1 q-entry + 1 e-entry): qubits={c2.num_qubits} toffoli={c2.operation_statistics().num_toffoli_like}")
# verificar rombo con valores del q-d real (n=6, k=2): tabla escalar manual
def syndrome_local(rng, k, n):
    pos = rng.choice(4095, size=k, replace=False)
    vals = rng.integers(1, 4096, size=k)
    X = [int(G.EXP[p % 4095]) for p in pos]
    S = []
    for t in range(n):
        s = 0
        for xj, e in zip(X, vals):
            s ^= G.mul(int(e), int(G.EXP[(G.LOG[xj] * t) % 4095]))
        S.append(s)
    return S
S = syndrome_local(np.random.default_rng(7), 2, 6)
# reconstruir tabla escalar para sacar un rombo: uso qd_col0 internals via recomputo manual
# q1^(n)=S_{n+1}/S_n ; e1^(n)=q1^(n+1)+q1^(n) ; q2^(n)=e1^(n+1)*q1^(n+1)/e1^(n)
def q1(n): return G.mul(S[n+1], G.inv(S[n]))
def e1(n): return q1(n+1)^q1(n)
def q2(n): return G.mul(G.mul(e1(n+1), q1(n+1)), G.inv(e1(n)))
n = 0
vals = {'q0': q1(n), 'q1': q1(n+1), 'e0': e1(n), 'e1': e1(n+1), 'q1p': q2(n+1), 'em1': 0}
qp_esp = q2(n)
ep_esp = q2(n+1)^qp_esp^e1(n+1)
print(f"  valores rombo n=0: q0={vals['q0']} q1={vals['q1']} e0={vals['e0']} e1={vals['e1']} q1p={vals['q1p']} -> qp_esp={qp_esp} ep_esp={ep_esp}")
# simulador del rombo (1 tiro por cada entrada fija; uso batch con el mismo caso repetido)
B2 = 8
order = ['q0','q1','e0','e1','q1p','em1']
inp = np.zeros((c2.num_qubits, B2), dtype=bool)
inp[:96] = np.concatenate([bits(np.full(B2, vals[k])) for k in order] + [bits(np.zeros(B2,dtype=int)), bits(np.zeros(B2,dtype=int))])
sim2 = km.Simulator(batch_size=B2, debug_print=False, counting_operations=True, seed=1)
sim2.use_same_registers_as(c2)
sim2.write_across_shots(km.array([km.q(i) for i in range(c2.num_qubits)]), inp)
sim2.do(c2)
out2 = sim2.read_across_shots(km.array([km.q(i) for i in range(c2.num_qubits)]))
# registros: q0(0-11) q1(12-23) e0(24-35) e1(36-47) q1p(48-59) em1(60-71) qp(72-83) ep(84-95)
def regval(out, base):
    v = np.zeros(out.shape[1], dtype=int)
    for i in range(DEG):
        v |= (out[base+i].astype(int) << i)
    return v
qp_sim = regval(out2, 72); ep_sim = regval(out2, 84)
print(f"  rombo qp correcto: {bool((qp_sim==qp_esp).all())} (sim={qp_sim[0]} esp={qp_esp}) ; ep correcto: {bool((ep_sim==ep_esp).all())} (sim={ep_sim[0]} esp={ep_esp})")
print(f"  rombo fase volteada={int(sim2.read_phase_flipped_across_shots().sum())}")
