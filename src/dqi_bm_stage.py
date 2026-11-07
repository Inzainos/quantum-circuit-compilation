#!/usr/bin/env python3
"""Etapa D (v0) del decodificador DQI estilo BM: Berlekamp-Massey REVERSIBLE con enrutamiento condicional.

Variante del paper (empate -> replace), contador d = L_tau~ - L_sigma (replace sii D != 0 y d >= 0):
    cero/retain: d <- d+1 ;  replace: d <- 1-d ;  d inicial = 1.
Estado: sigma[0..LS-1], tau~[0..LS-1] (plantilla ya desplazada, x^s*tau), contador d (8 bits, complemento a 2).
Invariante del BM reescalado: sigma_0 * delta_plantilla = 1, asi que c = D/delta = D*sigma_0 (sin dividir) y en replace
se usa c^-1 (replace reescala sigma por c). Una sola actualizacion compartida:
    p = [D != 0] and [d >= 0]
    alpha = p ? (D*sigma_0)^-1 : D*sigma_0
    si p: swap(sigma, tau~)             (CSWAP controlado por p)
    sigma += alpha * tau~               (36 productos)
    tau~ <- x * tau~                    (reetiquetado de registros, gratis)
Basura por ronda (v0): D (12), alpha (12), p (1).  La pasada inversa la limpia (v1 la eliminara recomputando desde el estado).
Salidas: sigma proporcional al localizador (escala arbitraria; irrelevante para omega/Psi/fase porque todo es homogeneo).
Etiquetas INFO_TAG: bm_disc, bm_flags, bm_alpha, bm_swap, bm_update, bm_d.   Log: logger 'dqi_bm'.
"""
from __future__ import annotations
import logging
from typing import List, Sequence
import kickmix as km

log = logging.getLogger("dqi_bm")
DEG = 12
DW = 8   # bits del contador d


class BMStage:
    def __init__(self, b: km.CircuitBuilder, field, S: Sequence[km.array], LS: int = 36, n: int | None = None):
        self.b, self.f, self.S, self.LS = b, field, list(S), LS
        self.n = len(S) if n is None else n
        self.sigma: List[km.array] = [b.alloc_qubits(DEG) for _ in range(LS)]
        self.tau: List[km.array] = [b.alloc_qubits(DEG) for _ in range(LS)]
        self.d = b.alloc_qubits(DW)
        b.x(self.sigma[0][0])           # sigma = 1
        b.x(self.tau[1][0])             # tau~ = x  (plantilla 1 con desplazamiento 1)
        b.x(self.d[0])                  # d = 1
        self.hist = []                  # por ronda: (D, alpha, p)
        # cotas de bucle medidas (tools/dqi_bm_bounds.py, 0 violaciones en 20,000 muestras con k ~ w_k^2):
        self.bd = lambda r: min(LS - 1, r // 2 + 1)      # grado maximo de sigma (discrepancia)
        self.bu = lambda r: min(LS - 1, r // 2 + 2)      # grado maximo en rondas activas (swap/update)

    # ---------- bloques ----------
    def _disc(self, r, D):
        with self.b.mark('bm_disc'):
            for i in range(0, min(r, self.bd(r)) + 1):
                self.b.ixor_gf2_mul(self.sigma[i], self.S[r - i], target=D, field=self.f)

    def _flag_p(self, D, p_target, inverse: bool):
        """p = [D != 0] AND [d >= 0].  inverse=False: computa p (init_and); True: la limpia (del_and)."""
        b = self.b
        with b.mark('bm_flags'):
            lad = b.alloc_qubits(DEG - 2); z = b.alloc_qubits(1)[0]; nz = b.alloc_qubits(1)[0]
            b.x(D)
            b.init_and(D[0], D[1], lad[0])
            for i in range(2, DEG - 1):
                b.init_and(lad[i - 2], D[i], lad[i - 1])
            b.init_and(lad[DEG - 3], D[DEG - 1], z)          # z = [D == 0]
            b.cx(z, nz); b.x(nz)                              # nz = [D != 0]
            b.x(self.d[DW - 1])                               # bit alto de d: 1 si d >= 0
            if not inverse:
                b.init_and(nz, self.d[DW - 1], p_target)
            else:
                b.del_and(nz, self.d[DW - 1], p_target)
            b.x(self.d[DW - 1])
            b.x(nz); b.cx(z, nz)
            b.del_and(lad[DEG - 3], D[DEG - 1], z)
            for i in reversed(range(2, DEG - 1)):
                b.del_and(lad[i - 2], D[i], lad[i - 1])
            b.del_and(D[0], D[1], lad[0])
            b.x(D)
            b.free(lad); b.free(z); b.free(nz)

    def _alpha(self, D, p, alpha):
        """alpha ^= p ? (D*sigma0)^-1 : D*sigma0   (se aplica igual para computar y para limpiar)."""
        b = self.b
        with b.mark('bm_alpha'):
            P = b.init_gf2_mul(self.sigma[0], D, field=self.f)
            Pinv = b.alloc_qubits(DEG)
            _, scaf = b.init_gf2_inverse_with_scaffold(P, target=Pinv, field=self.f)
            b.cx(P, alpha)
            b.cx(Pinv, P)
            b.ccx(p, P, alpha)
            b.cx(Pinv, P)
            b.del_gf2_inverse_with_scaffold(P, target=Pinv, scaffold=scaf, field=self.f)
            b.free(scaf); b.free(Pinv)
            b.del_gf2_mul(self.sigma[0], D, target=P, field=self.f)
            b.free(P)

    def _swap(self, p, r):
        with self.b.mark('bm_swap'):
            for i in range(self.bu(r) + 1):
                self.b.cswap(p, self.sigma[i], self.tau[i])

    def _update(self, alpha, r):
        with self.b.mark('bm_update'):
            for i in range(self.bu(r) + 1):
                self.b.ixor_gf2_mul(alpha, self.tau[i], target=self.sigma[i], field=self.f)

    def _dupd(self, p, inverse: bool):
        b = self.b
        with b.mark('bm_d'):
            if not inverse:
                b.cx(p, self.d); b.iadd(1, target=self.d); b.iadd(1, target=self.d, control=p)
            else:
                b.isub(1, target=self.d, control=p); b.isub(1, target=self.d); b.cx(p, self.d)

    # ---------- rondas ----------
    def forward_round(self, r: int):
        b = self.b
        D = b.alloc_qubits(DEG); alpha = b.alloc_qubits(DEG); p = b.alloc_qubits(1)[0]
        self._disc(r, D)
        self._flag_p(D, p, inverse=False)
        self._alpha(D, p, alpha)
        self._swap(p, r)
        self._update(alpha, r)
        self._dupd(p, inverse=False)
        self.tau = [self.tau[-1]] + self.tau[:-1]            # tau~ <- x*tau~  (el registro superior debe valer 0)
        self.hist.append((D, alpha, p))

    def reverse_round(self, r: int):
        b = self.b
        D, alpha, p = self.hist.pop()
        self.tau = self.tau[1:] + [self.tau[0]]
        self._dupd(p, inverse=True)
        with b.mark('bm_update'):
            for i in reversed(range(self.bu(r) + 1)):
                b.ixor_gf2_mul(alpha, self.tau[i], target=self.sigma[i], field=self.f)
        with b.mark('bm_swap'):
            for i in reversed(range(self.bu(r) + 1)):
                b.cswap(p, self.sigma[i], self.tau[i])
        self._alpha(D, p, alpha)                              # alpha ^= alpha -> 0 (sigma_0 ya restaurado)
        self._flag_p(D, p, inverse=True)
        self._disc(r, D)                                      # D ^= D -> 0
        b.free(D); b.free(alpha); b.free(p)

    def forward(self, rounds=None):
        for r in range(self.n if rounds is None else rounds):
            self.forward_round(r)

    def reverse(self, rounds=None):
        for r in reversed(range(self.n if rounds is None else rounds)):
            self.reverse_round(r)


def build_stage_d(n=70, LS=36, degree=12, ida_y_vuelta=True, rounds=None) -> km.Circuit:
    b = km.CircuitBuilder(); gf = km.GF2Field(degree)
    S = [b.create_quantum_register(degree, name=f'S{i}') for i in range(n)]
    bm = BMStage(b, gf, S, LS, n)
    bm.forward(rounds)
    if ida_y_vuelta:
        bm.reverse(rounds)
    return b.finish_circuit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for iv in (False, True):
        c = build_stage_d(ida_y_vuelta=iv)
        st = c.operation_statistics()
        log.info("ida_y_vuelta=%s toffoli-like=%d qubits=%d", iv, st.num_toffoli_like, c.num_qubits)
