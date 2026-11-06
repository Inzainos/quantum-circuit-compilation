#!/usr/bin/env python3
"""Decodificador DQI completo v1 (BM + omega in place + barrido con inversion por posicion).

  BM (v1, sin basura)  ->  sigma, tau, d, H
  delta = sigma_0^-1 (andamiaje persistente durante omega)  ->  omega in place sobre S (etapa C)
  barrido por posicion p (r = alpha^-p):  s=sigma(r), dd=sigma'(r), u=omega(r) lineales; f=[s==0];
        w = dd^-1 (inversion con andamiaje, 315 Toffoli, del gratis); fase (-1)^{f * Tr(mu(M_p) u w)}   (Forney: e = omega/sigma')
  luego se deshace todo en orden inverso.
Esta version reemplaza Psi=(sigma')^-1 mod sigma (EEA) por inversion por posicion; la etapa B (EEA) es la mejora pendiente.
Logs: logger 'dqi_decoder'; etiquetas INFO_TAG: scan_pos, omega_fwd/rev, bm_*.
"""
from __future__ import annotations
import sys, logging
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
try:
    from qcc_log import emit as _qcc_emit
    _HAS_QCC_LOG = True
except Exception:  # noqa: BLE001 - logging opcional; el circuito no depende de el
    _HAS_QCC_LOG = False
import kickmix as km
import dqi_bm_model as G
from dqi_bm_stage_v1 import BMStageV1
from dqi_omega_stage import build_omega
from dqi_tower_inv2 import ValueInv
from dqi_scan_stage import _linear_sources, _emit_linear, _alpha_pow_bits
from dqi_tower_inv import CCOLS
from dqi_tower_inv2 import TowerInv2 as TowerInv

log = logging.getLogger("dqi_decoder")
DEG = 12


def _to_coords(srcs):
    """fuentes de cada bit de valor -> fuentes (paridad) de cada coordenada de torre."""
    out = []
    for o in range(DEG):
        par = {}
        for k in range(DEG):
            if (CCOLS[k] >> o) & 1:
                for q in srcs[k]:
                    par[q] = par.get(q, 0) ^ 1
        out.append([q for q, v in par.items() if v])
    return out


def build_scan_inv(b, field, sig, om, E, positions=None, tower=True):
    n_pos = len(E)
    positions = range(min(n_pos, G.Q - 1)) if positions is None else positions
    apow = [_alpha_pow_bits(s) for s in range(2 * DEG - 1)]
    for p in positions:
        r = _alpha_pow_bits(-p)
        with b.mark('scan_pos'):
            s = b.alloc_qubits(DEG); u = b.alloc_qubits(DEG); dd = b.alloc_qubits(DEG); w = b.alloc_qubits(DEG)
            t = b.alloc_qubits(DEG); f = b.alloc_qubits(1)[0]; lad = b.alloc_qubits(DEG - 2); g = b.alloc_qubits(DEG)
            pw = [1]
            for i in range(1, max(len(sig), len(om))):
                pw.append(G.mul(pw[-1], r))
            src_s = _linear_sources(pw[:len(sig)], sig)
            src_u = _linear_sources(pw[:len(om)], om)
            # sigma'(r) = sum_{i impar} sigma_i r^{i-1}
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
            _emit_linear(b, src_u, u)
            _emit_linear(b, src_d, dd)
            if tower:
                TI = TowerInv(b, dd, w); TI.forward()
            else:
                _, scaf = b.init_gf2_inverse_with_scaffold(dd, target=w, field=field)
            for k in range(DEG):
                b.push_condition(E[p][k])
                for a in range(DEG):
                    srcs = [w[bb] for bb in range(DEG) if (apow[a + bb] >> k) & 1]
                    if srcs:
                        b.cx(km.array(srcs), km.array([t[a]] * len(srcs)))
                b.pop_condition()
            for a in range(DEG):
                b.init_and(f, u[a], g[a]); b.cz(g[a], t[a]); b.del_and(f, u[a], g[a])
            for k in reversed(range(DEG)):
                b.push_condition(E[p][k])
                for a in reversed(range(DEG)):
                    srcs = [w[bb] for bb in range(DEG) if (apow[a + bb] >> k) & 1]
                    if srcs:
                        b.cx(km.array(srcs), km.array([t[a]] * len(srcs)))
                b.pop_condition()
            if tower:
                TI.undo()
            else:
                b.del_gf2_inverse_with_scaffold(dd, target=w, scaffold=scaf, field=field)
                b.free(scaf)
            _emit_linear(b, src_d, dd)
            _emit_linear(b, src_u, u)
            b.del_and(lad[DEG - 3], s[DEG - 1], f)
            for i in reversed(range(2, DEG - 1)):
                b.del_and(lad[i - 2], s[i], lad[i - 1])
            b.del_and(s[0], s[1], lad[0])
            b.x(s)
            _emit_linear(b, src_s, s)
            for q in (s, u, dd, w, t, lad, g):
                b.free(q)
            b.free(f)


def build_omega_tmp(b, field, sig, S, LO, adjoint):
    """omega in place como dqi_omega_stage.build_omega, pero delta = sigma_0^-1 se calcula (torre, 75 Toffoli) solo durante cada escalado."""
    with b.mark('omega_rev' if adjoint else 'omega_fwd'):
        orden = range(LO) if adjoint else range(LO - 1, -1, -1)
        for i in orden:
            if not adjoint:
                delta = b.alloc_qubits(DEG); vi = ValueInv(b, sig[0], delta).forward()
                P = b.init_gf2_mul(sig[0], S[i], field=field)
                b.del_gf2_mul(delta, P, target=S[i], field=field)
                b.swap(S[i], P); b.free(P)
                vi.undo(); b.free(delta)
                for j in range(1, i + 1):
                    b.ixor_gf2_mul(sig[j], S[i - j], target=S[i], field=field)
            else:
                for j in range(i, 0, -1):
                    b.ixor_gf2_mul(sig[j], S[i - j], target=S[i], field=field)
                delta = b.alloc_qubits(DEG); vi = ValueInv(b, sig[0], delta).forward()
                P = b.init_gf2_mul(delta, S[i], field=field)
                b.del_gf2_mul(sig[0], P, target=S[i], field=field)
                b.swap(S[i], P); b.free(P)
                vi.undo(); b.free(delta)


def build_decoder(n=70, LS=36, LO=35, m=4095, positions=None, ida_y_vuelta=True):
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f'S{i}') for i in range(n)]
    E = [b.create_classical_register(DEG, name=f'E{j}') for j in range(m)]
    bm = BMStageV1(b, gf, S, LS, n)
    bm.forward()
    build_omega_tmp(b, gf, bm.sigma, S, LO, adjoint=False)
    build_scan_inv(b, gf, bm.sigma, S[:LO], E, positions)
    build_omega_tmp(b, gf, bm.sigma, S, LO, adjoint=True)
    if ida_y_vuelta:
        bm.reverse()
        b.x(bm.sigma[0][0]); b.x(bm.tau[1][0]); b.x(bm.d[0])
    return b.finish_circuit(), bm


if __name__ == "__main__":
    import hashlib
    import time

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) > 1:
        t0 = time.time()
        c, _ = build_decoder()
        out = Path(sys.argv[1])
        c.to_file(str(out), format="kmb")
        toff = int(c.operation_statistics().num_toffoli_like)
        q = int(c.num_qubits)
        log.info("escrito %s: toffoli=%d qubits=%d", out, toff, q)
        if _HAS_QCC_LOG:
            _qcc_emit("dqi_decoder_v1", "build", "ok",
                      inputs={"n": 70, "LS": 36, "LO": 35, "m": 4095,
                              "positions": "all", "ida_y_vuelta": True},
                      outputs={"toffoli": toff, "qubits": q},
                      duration_s=time.time() - t0)
            _qcc_emit("dqi_decoder_v1", "write", "ok",
                      inputs={"out": str(out)},
                      outputs={"sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                               "bytes": out.stat().st_size})
    else:
        t0 = time.time()
        c, _ = build_decoder(positions=range(16))
        toff = int(c.operation_statistics().num_toffoli_like)
        q = int(c.num_qubits)
        log.info("16 posiciones: toffoli=%d qubits=%d", toff, q)
        if _HAS_QCC_LOG:
            _qcc_emit("dqi_decoder_v1", "build", "ok",
                      inputs={"n": 70, "LS": 36, "LO": 35, "m": 4095,
                              "positions": "0..15", "ida_y_vuelta": True},
                      outputs={"toffoli": toff, "qubits": q},
                      duration_s=time.time() - t0)
