#!/usr/bin/env python3
"""Etapa C del decodificador DQI estilo BM: evaluador omega IN PLACE sobre los sindromes.

omega_i = sum_{j=0}^{i} sigma_j * S_i-j  (S lista 0-based: S[t-1] = S_t), para i = 0..LO-1 (LO = 35).
In place, i descendente (S_{i-j} aun sin sobrescribir):
   escalado  S_i <- sigma_0 * S_i :  P = init_gf2_mul(sigma_0, S_i)  [63 Toffoli];
             del_gf2_mul(delta, P, target=S_i) limpia S_i con MBU [0 Toffoli] porque S_i = delta*P (delta = sigma_0^-1);
             swap(S_i, P)  -> S_i = sigma_0*S_i ; P = 0
   acumulado S_i ^= sigma_j * S_{i-j}, j=1..i      [63 c/u]
Inverso (adjoint): se deshace en orden contrario (acumulados autoinversos; el escalado inverso usa delta y sigma_0 al reves).
Coste por pasada: (LO + LO(LO-1)/2) * 63 = 630*63 = 39,690 Toffoli para LO=35.
Requiere delta = sigma_0^-1 en un registro (el invariante sigma_0*delta=1 del BM reescalado).
Logs: logger 'dqi_omega'; etiquetas INFO_TAG 'omega_fwd' / 'omega_rev'.
"""
from __future__ import annotations
import logging
from typing import Sequence
import kickmix as km

log = logging.getLogger("dqi_omega")


def _escala(b: km.CircuitBuilder, field, a: km.array, inv_a: km.array, s: km.array):
    """s <- a * s  usando inv_a = a^-1 (63 Toffoli)."""
    P = b.init_gf2_mul(a, s, field=field)
    b.del_gf2_mul(inv_a, P, target=s, field=field)
    b.swap(s, P)
    b.free(P)


def build_omega(b: km.CircuitBuilder, field, sig: Sequence[km.array], delta: km.array, S: Sequence[km.array],
                LO: int = 35, adjoint: bool = False) -> None:
    with b.mark('omega_rev' if adjoint else 'omega_fwd'):
        orden = range(LO) if adjoint else range(LO - 1, -1, -1)
        for i in orden:
            if not adjoint:
                _escala(b, field, sig[0], delta, S[i])
                for j in range(1, i + 1):
                    b.ixor_gf2_mul(sig[j], S[i - j], target=S[i], field=field)
            else:
                for j in range(i, 0, -1):
                    b.ixor_gf2_mul(sig[j], S[i - j], target=S[i], field=field)
                _escala(b, field, delta, sig[0], S[i])      # S_i <- delta * S_i  (inverso del escalado)


def build_stage_c(LS=36, LO=35, n=70, degree=12, ida_y_vuelta=False) -> km.Circuit:
    b = km.CircuitBuilder(); gf = km.GF2Field(degree)
    sig = [b.create_quantum_register(degree, name=f'sig{i}') for i in range(LS)]
    delta = b.create_quantum_register(degree, name='delta')
    S = [b.create_quantum_register(degree, name=f'S{i}') for i in range(n)]
    build_omega(b, gf, sig, delta, S, LO, adjoint=False)
    if ida_y_vuelta:
        build_omega(b, gf, sig, delta, S, LO, adjoint=True)
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
    for iv in (False, True):
        c = build_stage_c(ida_y_vuelta=iv)
        st = c.operation_statistics()
        log.info("ida_y_vuelta=%s toffoli-like=%d (esperado %d) qubits=%d", iv, st.num_toffoli_like,
                 (2 if iv else 1) * 630 * 63, c.num_qubits)
