#!/usr/bin/env python3
"""Etapa A del decodificador DQI estilo BM: barrido de fase por traza.

Dado (en registros cuanticos) sigma(0..LS), omega(0..LO-1), psi(0..LP-1), con coeficientes en GF(2^12), y las mascaras
clasicas M_p, aplica la fase (-1)^{ sum_{raices r=alpha^{-p}} Tr( mu(M_p) * omega(r) * psi(r) ) }, que (verificado en
tools/dqi_phase_model.py) es (-1)^{ sum_j popcount(e_j & M_j) } cuando psi = (sigma')^{-1} mod sigma y omega = S*sigma mod x^n.

Coste por posicion p (r = alpha^{-p}):
  * s = sigma(r): 12 bits, LINEAL en los bits de sigma (r^i constantes)  -> solo CNOT (0 Toffoli)
  * f = [s == 0]: cadena de 11 AND con descomputacion por medicion       -> 11 Toffoli
  * u = omega(r), w = psi(r): lineales -> CNOT
  * t_a = sum_k M_k * z_{a,k}(w): CNOT condicionados por el bit clasico M_k (0 Toffoli)
  * g_a = f AND u_a (12 AND), CZ(g_a, t_a), del_and                      -> 12 Toffoli
  => 23 Toffoli por posicion.  Tr(c*u*w) = sum_a u_a * t_a con t_a = Tr(c*alpha^a*w) lineal en w (coef. clasicos).
Logs: logging 'dqi_scan' (nivel INFO) con conteos; etiquetas INFO_TAG por posicion ('scan_pos').
"""
from __future__ import annotations
import sys, logging
from pathlib import Path
from typing import List, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import kickmix as km
import dqi_bm_model as G

log = logging.getLogger("dqi_scan")
DEG = G.DEG


def _mulmat_cols(c: int) -> List[int]:
    """columnas de la matriz de multiplicar por c: col b = bits de c*alpha^b (entero)."""
    return [G.mul(c, 1 << b) for b in range(DEG)]


def _alpha_pow_bits(s: int) -> int:
    return int(G.EXP[s % (G.Q - 1)])


def _linear_sources(coef_consts: Sequence[int], regs: Sequence[km.array]):
    """Para cada bit de salida o: lista de qubits fuente de sum_i const_i * reg_i, (bit o de const*valor)."""
    srcs = [[] for _ in range(DEG)]
    for c, reg in zip(coef_consts, regs):
        if c == 0:
            continue
        cols = _mulmat_cols(c)
        for b in range(DEG):
            col = cols[b]
            for o in range(DEG):
                if (col >> o) & 1:
                    srcs[o].append(reg[b])
    return srcs


def _emit_linear(builder: km.CircuitBuilder, srcs, targets: km.array):
    for o in range(DEG):
        if srcs[o]:
            builder.cx(km.array(srcs[o]), km.array([targets[o]] * len(srcs[o])))


def build_scan(builder: km.CircuitBuilder, sig: Sequence[km.array], om: Sequence[km.array],
               psi: Sequence[km.array], E: Sequence[km.array], positions: Sequence[int] | None = None) -> None:
    n_pos = len(E)
    if positions is None:
        positions = range(min(n_pos, G.Q - 1))
    # bits de alpha^s para s en 0..2*(DEG-1)  (producto de dos elementos de grado < DEG)
    apow = [_alpha_pow_bits(s) for s in range(2 * DEG - 1)]
    for p in positions:
        r = _alpha_pow_bits(-p)
        with builder.mark('scan_pos'):
            s = builder.alloc_qubits(DEG); u = builder.alloc_qubits(DEG); w = builder.alloc_qubits(DEG)
            t = builder.alloc_qubits(DEG)
            f = builder.alloc_qubits(1)[0]
            lad = builder.alloc_qubits(DEG - 2)          # escalera de ANDs (10) + el bit f (11-esimo)
            g = builder.alloc_qubits(DEG)
            pw = [1]
            for i in range(1, max(len(sig), len(om), len(psi))):
                pw.append(G.mul(pw[-1], r))
            src_s = _linear_sources(pw[:len(sig)], sig)
            src_u = _linear_sources(pw[:len(om)], om)
            src_w = _linear_sources(pw[:len(psi)], psi)
            # --- raiz: s = sigma(r); f = [s == 0] ---
            _emit_linear(builder, src_s, s)
            builder.x(s)
            builder.init_and(s[0], s[1], lad[0])
            for i in range(2, DEG - 1):
                builder.init_and(lad[i - 2], s[i], lad[i - 1])
            builder.init_and(lad[DEG - 3], s[DEG - 1], f)
            # --- u = omega(r), w = psi(r) ---
            _emit_linear(builder, src_u, u)
            _emit_linear(builder, src_w, w)
            # --- t_a = sum_k M_k * (sum_{b: bit k de alpha^{a+b}} w_b)   (CNOT condicionados por el bit clasico M_k) ---
            for k in range(DEG):
                builder.push_condition(E[p][k])
                for a in range(DEG):
                    srcs = [w[b] for b in range(DEG) if (apow[a + b] >> k) & 1]
                    if srcs:
                        builder.cx(km.array(srcs), km.array([t[a]] * len(srcs)))
                builder.pop_condition()
            # --- fase: sum_a f u_a t_a  (CZ(g_a, t_a) con g_a = f AND u_a) ---
            for a in range(DEG):
                builder.init_and(f, u[a], g[a])
                builder.cz(g[a], t[a])
                builder.del_and(f, u[a], g[a])
            # --- descomputar t, w, u, f, s en orden inverso ---
            for k in reversed(range(DEG)):
                builder.push_condition(E[p][k])
                for a in reversed(range(DEG)):
                    srcs = [w[b] for b in range(DEG) if (apow[a + b] >> k) & 1]
                    if srcs:
                        builder.cx(km.array(srcs), km.array([t[a]] * len(srcs)))
                builder.pop_condition()
            _emit_linear(builder, src_w, w)
            _emit_linear(builder, src_u, u)
            builder.del_and(lad[DEG - 3], s[DEG - 1], f)
            for i in reversed(range(2, DEG - 1)):
                builder.del_and(lad[i - 2], s[i], lad[i - 1])
            builder.del_and(s[0], s[1], lad[0])
            builder.x(s)
            _emit_linear(builder, src_s, s)
            for q in (s, u, w, t, lad, g):
                builder.free(q)
            builder.free(f)


def build_stage_a(LS: int = 36, LO: int = 35, LP: int = 35, m: int = 4095, positions=None) -> km.Circuit:
    b = km.CircuitBuilder()
    sig = [b.create_quantum_register(DEG, name=f'sig{i}') for i in range(LS)]
    om = [b.create_quantum_register(DEG, name=f'om{i}') for i in range(LO)]
    psi = [b.create_quantum_register(DEG, name=f'psi{i}') for i in range(LP)]
    E = [b.create_classical_register(DEG, name=f'E{j}') for j in range(m)]
    build_scan(b, sig, om, psi, E, positions)
    return b.finish_circuit()


if __name__ == "__main__":
    try:  # logs estructurados (qcc_log): una linea por script
        import sys as _qs
        from pathlib import Path as _qp
        _qs.path.insert(0, str(_qp(__file__).resolve().parent.parent / "tools"))
        from qcc_log import auto as _qcc_auto
        _qcc_auto(__file__)
    except Exception:  # noqa: BLE001
        pass
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    c = build_stage_a(positions=range(8))
    st = c.operation_statistics()
    log.info("8 posiciones: toffoli-like=%d (esperado 8*23=%d) qubits=%d", st.num_toffoli_like, 8 * 23, c.num_qubits)
