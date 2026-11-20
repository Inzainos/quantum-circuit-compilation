#!/usr/bin/env python3
"""Etapa BM v1 con bloque alpha FUSIONADO (F1b): inversion directo en alpha + seleccion por CSWAP.

Fusion: alpha = p ? inv(P) : P sin materializar Pinv por separado.
  * forward:  P = init_gf2_mul(X, D);  ValueInv3(P, alpha).forward()  (alpha = inv(P));
              CSWAP(!p, P, alpha)  ->  alpha = p ? inv(P) : P ;  P = p ? P : inv(P).
  * undo:     CSWAP(!p, P, alpha)  (restaura P y alpha=inv(P));  ValueInv3.undo() (hmr en alpha -> 0);
              del_gf2_mul(X, D, target=P) (P -> 0).
El CSWAP(!p) se hace con x(p) antes y despues (p se restaura; X = 0 Toffoli).
Costo de seleccion: 12 CSWAP = 12 Toffoli + 24 CX (vs 12 CCX + 36 CX del mux original).
Ahorro: registro Pinv (12 qubits). Andamios: los 18 son de la torre (el mul usa 0); no hay nada que compartir ahi.
"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # SCRATCH rama-t-eliminada: prioridad sobre el repo
import kickmix as km
from dqi_bm_stage_v1 import BMStageV1, DEG

class BMStageFused(BMStageV1):
    def _alpha_sel_fused(self, P, alpha, p):
        """alpha = p ? inv(P) : P  (alpha ya trae inv(P); P trae P). Intercambia P<->alpha si p==0.
        Es su propio inverso (CSWAP + X son autoinversos), asi que la misma llamada deshace la seleccion."""
        b = self.b
        b.x(p)
        b.cswap(p, P, alpha)
        b.x(p)

    def forward_round(self, r: int):
        b = self.b
        p = b.alloc_qubits(1)[0]
        D = b.alloc_qubits(DEG)                       # QF: X y alpha se reservan justo cuando se usan
        self._disc(r, D)
        self._flags(D, p, inverse=False)
        self._dupd(p, inverse=False)                 # QF: d no lo usa ni alpha ni el update; aqui el vivo es minimo
        X = b.alloc_qubits(DEG)
        b.cx(self.sigma[0], X)
        with b.mark('bm_alpha'):
            P = b.init_gf2_mul(X, D, field=self.f)
            alpha = b.alloc_qubits(DEG)
            scaf = self._inv_init(P, alpha)          # inv(P) directo en alpha
            self._alpha_sel_fused(P, alpha, p)
        with b.mark('bm_swap'):
            for i in range(self.bu(r) + 1):
                b.cswap(p, self.sigma[i], self.tau[i])
        with b.mark('bm_update'):
            for i in range(self.bu(r) + 1):
                self._mul(alpha, self.tau[i], self.sigma[i])
        with b.mark('bm_alpha'):
            self._alpha_sel_fused(P, alpha, p)       # restaura P y alpha=inv(P)
            self._inv_del(scaf, P, alpha)            # undo inv (hmr en alpha -> 0)
            b.del_gf2_mul(X, D, target=P, field=self.f); b.free(P)
            b.free(alpha)                            # QF: alpha == 0 aqui
        self._xmux(X, p)
        b.free(X)                                    # QF: X == 0 tras el xmux
        self._dclear(D, p)
        b.free(D)
        self.tau = [self.tau[-1]] + self.tau[:-1]
        self.flags.append(p)

    def reverse_round(self, r: int):
        b = self.b
        p = self.flags.pop()
        self.tau = self.tau[1:] + [self.tau[0]]
        D = b.alloc_qubits(DEG)
        self._dclear(D, p)
        X = b.alloc_qubits(DEG)
        self._xmux(X, p)
        with b.mark('bm_alpha'):
            P = b.init_gf2_mul(X, D, field=self.f)
            alpha = b.alloc_qubits(DEG)
            scaf = self._inv_init(P, alpha)
            self._alpha_sel_fused(P, alpha, p)
        with b.mark('bm_update'):
            for i in reversed(range(self.bu(r) + 1)):
                self._mul(alpha, self.tau[i], self.sigma[i])
        with b.mark('bm_swap'):
            for i in reversed(range(self.bu(r) + 1)):
                b.cswap(p, self.sigma[i], self.tau[i])
        with b.mark('bm_alpha'):
            self._alpha_sel_fused(P, alpha, p)
            self._inv_del(scaf, P, alpha)
            b.del_gf2_mul(X, D, target=P, field=self.f); b.free(P)
            b.free(alpha)
        b.cx(self.sigma[0], X)
        b.free(X)
        self._dupd(p, inverse=True)                  # QF: espejo exacto del lugar nuevo de la ida
        self._flags(D, p, inverse=True)
        self._disc_clear(r, D)
        b.free(D); b.free(p)


def build_stage_fused(n=70, LS=36, degree=12, ida_y_vuelta=True) -> km.Circuit:
    b = km.CircuitBuilder(); gf = km.GF2Field(degree)
    S = [b.create_quantum_register(degree, name=f'S{i}') for i in range(n)]
    bm = BMStageFused(b, gf, S, LS, n)
    bm.forward()
    if ida_y_vuelta:
        bm.reverse()
    return b.finish_circuit()
