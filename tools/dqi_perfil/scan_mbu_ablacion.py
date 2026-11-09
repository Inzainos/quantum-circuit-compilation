#!/usr/bin/env python3
"""Ablacion: ¿que descomputo cambia la fase? MBU vs Bennett por separado.

El test anterior mostro: MBU fase=1 (correcta), Bennett (f+g) fase=0.
Aqui separamos: Bennett solo en g, Bennett solo en la escalera f.
Si uno de ellos cambia la fase, ahi esta la diferencia MBU vs Bennett.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/tools")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_scan_stage import _linear_sources, _emit_linear, _alpha_pow_bits
from dqi_tower_inv3 import TowerInv3 as TowerInv
from dqi_tower_inv import CCOLS
from dqi_phase_model import tr, mu, peval, pderiv

DEG = 12
LS, LO = 6, 5
positions = [1, 5, 17, 100]
p0 = positions[0]
r0 = int(G.EXP[(-p0) % 4095])
sig = [r0, 1 ^ r0, 1, 0, r0, 1]
rng = np.random.default_rng(11)
om = [int(x) for x in rng.integers(0, 4096, size=LO)]
Evals = [int(x) for x in rng.integers(0, 4096, size=4)]
dsig = pderiv(sig)
fase_esp = 0
for p, M in zip(positions, Evals):
    r = int(G.EXP[(-p) % 4095])
    if peval(sig, r) == 0:
        fase_esp ^= tr(G.mul(mu(M), G.mul(peval(om, r), G.inv(peval(dsig, r)))))
print("fase clasica esperada:", fase_esp)


def _to_coords(srcs):
    out = []
    for o in range(DEG):
        par = {}
        for k in range(DEG):
            if (CCOLS[k] >> o) & 1:
                for q in srcs[k]:
                    par[q] = par.get(q, 0) ^ 1
        out.append([q for q, v in par.items() if v])
    return out


def build_scan_gen(b, field, sig_r, om_r, E_r, positions, bennett_f, bennett_g):
    n_pos = len(E_r)
    apow = [_alpha_pow_bits(s) for s in range(2 * DEG - 1)]
    s = b.alloc_qubits(DEG); dd = b.alloc_qubits(DEG); w = b.alloc_qubits(DEG)
    tmp = b.alloc_qubits(1)[0]; f = b.alloc_qubits(1)[0]; lad = b.alloc_qubits(DEG - 2); g = b.alloc_qubits(1)[0]
    clean_f = b.init_and if bennett_f else b.del_and
    clean_g = b.init_and if bennett_g else b.del_and
    for p in positions:
        r = _alpha_pow_bits(-p)
        with b.mark("scan_pos"):
            pw = [1]
            for i in range(1, max(len(sig_r), len(om_r))):
                pw.append(G.mul(pw[-1], r))
            src_s = _linear_sources(pw[:len(sig_r)], sig_r)
            src_u = _linear_sources(pw[:len(om_r)], om_r)
            dco = [pw[i - 1] if i % 2 == 1 else 0 for i in range(len(sig_r))]
            src_d = _linear_sources(dco, sig_r)
            src_d = _to_coords(src_d)
            _emit_linear(b, src_s, s)
            b.x(s)
            b.init_and(s[0], s[1], lad[0])
            for i in range(2, DEG - 1):
                b.init_and(lad[i - 2], s[i], lad[i - 1])
            b.init_and(lad[DEG - 3], s[DEG - 1], f)
            _emit_linear(b, src_d, dd)
            TI = TowerInv(b, dd, w); TI.forward()
            for a in range(DEG):
                for q in src_u[a]:
                    b.cx(q, tmp)
                b.init_and(f, tmp, g)
                for k in range(DEG):
                    srcs = [w[bb] for bb in range(DEG) if (apow[a + bb] >> k) & 1]
                    if srcs:
                        b.push_condition(E_r[p][k])
                        b.cz(km.array(srcs), km.array([g] * len(srcs)))
                        b.pop_condition()
                clean_g(f, tmp, g)
                for q in src_u[a]:
                    b.cx(q, tmp)
            TI.undo()
            _emit_linear(b, src_d, dd)
            clean_f(lad[DEG - 3], s[DEG - 1], f)
            for i in reversed(range(2, DEG - 1)):
                clean_f(lad[i - 2], s[i], lad[i - 1])
            clean_f(s[0], s[1], lad[0])
            b.x(s)
            _emit_linear(b, src_s, s)
    for q in (s, dd, w, lad):
        b.free(q)
    b.free(tmp); b.free(f); b.free(g)


def bits_of(vals_list, deg=DEG, nshots=1):
    out = np.zeros((len(vals_list) * deg, nshots), dtype=bool)
    for idx, v in enumerate(vals_list):
        for j in range(deg):
            out[idx * deg + j, 0] = bool((v >> j) & 1)
    return out


def run(bennett_f, bennett_g, tag):
    b = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    sig_r = [b.create_quantum_register(DEG, name=f"sig{i}") for i in range(LS)]
    om_r = [b.create_quantum_register(DEG, name=f"om{i}") for i in range(LO)]
    E_r = [b.create_classical_register(DEG, name=f"E{j}") for j in range(max(positions) + 1)]
    build_scan_gen(b, gf, sig_r, om_r, E_r, positions, bennett_f, bennett_g)
    circ = b.finish_circuit()
    nq = circ.num_qubits
    sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(circ)
    q_in = []
    for reg in sig_r + om_r:
        q_in.extend(list(reg))
    sim.write_across_shots(km.array(q_in), bits_of(sig + om))
    Efull = [0] * (max(positions) + 1)
    for p, M in zip(positions, Evals):
        Efull[p] = M
    sim.write_across_shots(km.array([km.b(i) for i in range(len(Efull) * DEG)]), bits_of(Efull))
    sim.do(circ)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(nq)]))
    resto = out[(LS + LO) * DEG:, 0]
    fase = int(sim.read_phase_flipped_across_shots().sum())
    print(f"[{tag}] T={int(circ.operation_statistics().num_toffoli_like)} "
          f"sucios={int(resto.sum())} fase_sim={fase} fase_esp={fase_esp} ok={fase == fase_esp and int(resto.sum()) == 0}")
    return fase == fase_esp and int(resto.sum()) == 0


run(False, False, "MBU todo        ")
run(False, True, "Bennett solo g  ")
run(True, False, "Bennett solo f  ")
run(True, True, "Bennett f+g     ")
