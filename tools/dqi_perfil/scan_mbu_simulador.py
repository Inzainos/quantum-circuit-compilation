#!/usr/bin/env python3
"""Parte C: correctitud del scan a escala chica en el simulador kickmix.

Verifica para el scan MBU (codigo actual, build_scan_inv) y para la variante
Bennett (del_and -> re-init_and):
  - la fase aplicada coincide con el modelo clasico (Forney por posicion),
  - sig y om no cambian,
  - TODOS los temporales (s, dd, w, tmp, f, lad, g) quedan en |0⟩ al final.
El scan es una fase; un simulador que solo checara el resultado daria falso
positivo si los ancillas quedaran sucios, por eso se leen TODOS los qubits.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/tools")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import numpy as np
import kickmix as km
import dqi_bm_model as G
from dqi_scan_stage import _linear_sources, _emit_linear, _alpha_pow_bits
from dqi_decoder_v1 import build_scan_inv
from dqi_tower_inv3 import TowerInv3 as TowerInv
from dqi_tower_inv import CCOLS
from dqi_phase_model import tr, mu, peval, pderiv

DEG = 12
LS, LO = 6, 5
NPOS = 4


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


def build_scan_inv_bennett(b, field, sig, om, E, positions=None, tower=True):
    # Bennett CORRECTO: Toffoli propio (multi_controlled_x), NO re-init_and
    # (init_and es AND de fase relativa, no autoinverso; re-init_and no deshace).
    n_pos = len(E)
    positions = range(min(n_pos, G.Q - 1)) if positions is None else positions
    apow = [_alpha_pow_bits(s) for s in range(2 * DEG - 1)]
    s = b.alloc_qubits(DEG); dd = b.alloc_qubits(DEG); w = b.alloc_qubits(DEG)
    tmp = b.alloc_qubits(1)[0]; f = b.alloc_qubits(1)[0]; lad = b.alloc_qubits(DEG - 2); g = b.alloc_qubits(1)[0]

    def toff(a, c, t):
        b.multi_controlled_x(km.array([a, c]), t)

    for p in positions:
        r = _alpha_pow_bits(-p)
        with b.mark("scan_pos"):
            pw = [1]
            for i in range(1, max(len(sig), len(om))):
                pw.append(G.mul(pw[-1], r))
            src_s = _linear_sources(pw[:len(sig)], sig)
            src_u = _linear_sources(pw[:len(om)], om)
            dco = [pw[i - 1] if i % 2 == 1 else 0 for i in range(len(sig))]
            src_d = _linear_sources(dco, sig)
            if tower:
                src_d = _to_coords(src_d)
            _emit_linear(b, src_s, s)
            b.x(s)
            b.init_and(s[0], s[1], lad[0])
            for i in range(2, DEG - 1):
                b.init_and(lad[i - 2], s[i], lad[i - 1])
            b.init_and(lad[DEG - 3], s[DEG - 1], f)
            _emit_linear(b, src_d, dd)
            if tower:
                TI = TowerInv(b, dd, w); TI.forward()
            for a in range(DEG):
                for q in src_u[a]:
                    b.cx(q, tmp)
                b.init_and(f, tmp, g)
                for k in range(DEG):
                    srcs = [w[bb] for bb in range(DEG) if (apow[a + bb] >> k) & 1]
                    if srcs:
                        b.push_condition(E[p][k])
                        b.cz(km.array(srcs), km.array([g] * len(srcs)))
                        b.pop_condition()
                toff(f, tmp, g)  # Bennett con Toffoli propio
                for q in src_u[a]:
                    b.cx(q, tmp)
            if tower:
                TI.undo()
            _emit_linear(b, src_d, dd)
            toff(lad[DEG - 3], s[DEG - 1], f)  # Bennett
            for i in reversed(range(2, DEG - 1)):
                toff(lad[i - 2], s[i], lad[i - 1])
            toff(s[0], s[1], lad[0])
            b.x(s)
            _emit_linear(b, src_s, s)
    for q in (s, dd, w, lad):
        b.free(q)
    b.free(tmp); b.free(f); b.free(g)


# ---- Entrada: sigma con raiz en p0, omega aleatoria, mascaras E aleatorias ----
rng = np.random.default_rng(11)
positions = [1, 5, 17, 100]
p0 = positions[0]
r0 = int(G.EXP[(-p0) % 4095])
# sigma(x) = (x + r0)(x^4 + x + 1) -> coefs [r0, 1^r0, 1, 0, r0, 1]
sig = [r0, 1 ^ r0, 1, 0, r0, 1]
om = [int(x) for x in rng.integers(0, 4096, size=LO)]
Evals = [int(x) for x in rng.integers(0, 4096, size=NPOS)]
dsig = pderiv(sig)
print("sigma:", sig, " sigma(r0)==0:", peval(sig, r0) == 0,
      " sigma'(r0)=", peval(dsig, r0), "(!=0:", peval(dsig, r0) != 0, ")")
print("omega:", om)
print("E:", Evals)
print("f por posicion (s==0):", [peval(sig, int(G.EXP[(-p) % 4095])) == 0 for p in positions])

# fase clasica esperada: suma sobre posiciones con s==0 de Tr(mu(E) * u * w)
fase_esp = 0
for p, M in zip(positions, Evals):
    r = int(G.EXP[(-p) % 4095])
    if peval(sig, r) == 0:
        w = G.inv(peval(dsig, r))
        u = peval(om, r)
        fase_esp ^= tr(G.mul(mu(M), G.mul(u, w)))
print("fase clasica esperada:", fase_esp)


def bits_of(vals_list, deg=DEG, nshots=1):
    out = np.zeros((len(vals_list) * deg, nshots), dtype=bool)
    for idx, v in enumerate(vals_list):
        for j in range(deg):
            out[idx * deg + j, 0] = bool((v >> j) & 1)
    return out


def run_scan(builder_fn, tag):
    b = km.CircuitBuilder()
    gf = km.GF2Field(DEG)
    sig_r = [b.create_quantum_register(DEG, name=f"sig{i}") for i in range(LS)]
    om_r = [b.create_quantum_register(DEG, name=f"om{i}") for i in range(LO)]
    E_r = [b.create_classical_register(DEG, name=f"E{j}") for j in range(max(positions) + 1)]
    builder_fn(b, gf, sig_r, om_r, E_r, positions=positions)
    circ = b.finish_circuit()
    nq = circ.num_qubits
    sim = km.Simulator(batch_size=1, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(circ)
    # escribir sig y om (qubits)
    q_in = []
    for reg in sig_r + om_r:
        q_in.extend(list(reg))
    sim.write_across_shots(km.array(q_in), bits_of(sig + om))
    # escribir E (bits clasicos; E se indexa por posicion p, no por indice)
    Efull = [0] * (max(positions) + 1)
    for p, M in zip(positions, Evals):
        Efull[p] = M
    sim.write_across_shots(km.array([km.b(i) for i in range(len(Efull) * DEG)]), bits_of(Efull))
    sim.do(circ)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(nq)]))
    # sig/om sin cambios
    got_sig = [sum(int(out[i * DEG + j, 0]) << j for j in range(DEG)) for i in range(LS)]
    got_om = [sum(int(out[(LS + i) * DEG + j, 0]) << j for j in range(DEG)) for i in range(LO)]
    resto = out[(LS + LO) * DEG:, 0]
    fase = int(sim.read_phase_flipped_across_shots().sum())
    print(f"[{tag}] Q={nq} T={int(circ.operation_statistics().num_toffoli_like)} "
          f"sig_ok={got_sig == sig} om_ok={got_om == om} "
          f"temporales_sucios={int(resto.sum())} fase_sim={fase} fase_esp={fase_esp} "
          f"fase_ok={fase == fase_esp}")
    return got_sig == sig and got_om == om and int(resto.sum()) == 0 and fase == fase_esp


ok_mbu = run_scan(build_scan_inv, "MBU (actual)")
ok_ben = run_scan(build_scan_inv_bennett, "Bennett")
print()
print("MBU correcto y limpio:", ok_mbu)
print("Bennett correcto y limpio:", ok_ben)
print("MBU y Bennett coinciden en fase y limpieza:", ok_mbu and ok_ben)
