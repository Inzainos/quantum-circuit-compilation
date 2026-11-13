#!/usr/bin/env python3
"""Etapa D v1: BM reversible SIN basura por ronda (solo 2 banderas por ronda y UNA entrada de historial H).

Mismo algoritmo que v0 (src/dqi_bm_stage.py).  Cambios para bajar qubits (el score usa Q^2):
  * D, alpha, X, P, Pinv y su andamiaje son transitorios dentro de la ronda.
  * D se limpia al final de la ronda:   replace (p):  D = inv(sigma'_0)   (invariante sigma_0*delta=1, ver docs)
                                        retain (t):  D se mueve a H (una sola entrada; si H ya esta ocupada => fallo ~1e-4)
                                        cero:        D == 0
  * alpha se limpia con el mismo andamiaje de la inversion (0 Toffoli) y deshaciendo la seleccion (12 Toffoli).
  * En la pasada inversa se recomputa D (inversion o H), alpha, y se deshace en orden contrario.
Banderas por ronda: p = [D!=0 y d>=0] (replace), t = [D!=0 y d<0] (retain).  t = nz XOR p.
Etiquetas INFO_TAG: bm_disc, bm_flags, bm_alpha, bm_swap, bm_update, bm_d, bm_dclear, bm_x.  Logger: 'dqi_bm_v1'.
"""
from __future__ import annotations
import logging
from typing import List, Sequence
import kickmix as km
import dqi_bm_model as GM
from dqi_kmul import ixor_kmul
from dqi_tower_inv3 import ValueInv3 as ValueInv

log = logging.getLogger("dqi_bm_v1")
DEG = 12
DW = 8


class BMStageV1:
    def __init__(self, b: km.CircuitBuilder, field, S: Sequence[km.array], LS: int = 36, n: int | None = None):
        self.b, self.f, self.S, self.LS = b, field, list(S), LS
        self.kar = True
        self.tower = True
        self.n = len(S) if n is None else n
        self.sigma: List[km.array] = [b.alloc_qubits(DEG) for _ in range(LS)]
        self.tau: List[km.array] = [b.alloc_qubits(DEG) for _ in range(LS)]
        self.d = b.alloc_qubits(DW)
        self.H = b.alloc_qubits(DEG)                       # unica entrada de historial (discrepancia de una ronda retain)
        b.x(self.sigma[0][0]); b.x(self.tau[1][0]); b.x(self.d[0])
        self.flags = []                                    # por ronda: (p, t)
        self.bd = lambda r: min(LS - 1, r // 2 + 1)
        self.bu = lambda r: min(LS - 1, r // 2 + 2)

    def _inv_init(self, src, tgt):
        if self.tower:
            return ValueInv(self.b, src, tgt).forward()
        _, scaf = self.b.init_gf2_inverse_with_scaffold(src, target=tgt, field=self.f)
        return scaf

    def _inv_del(self, h, src, tgt):
        if self.tower:
            h.undo()
        else:
            self.b.del_gf2_inverse_with_scaffold(src, target=tgt, scaffold=h, field=self.f)
            self.b.free(h)

    def _mul(self, x, y, target):
        if self.kar:
            ixor_kmul(self.b, x, y, target)
        else:
            self.b.ixor_gf2_mul(x, y, target=target, field=self.f)

    # ---------------- primitivas ----------------
    def _disc(self, r, D):
        with self.b.mark('bm_disc'):
            for i in range(0, min(r, self.bd(r)) + 1):
                self._mul(self.sigma[i], self.S[r - i], D)

    def _xor_bits(self, bits):
        """Devuelve un bit clasico con el XOR de 'bits' (solo BIT_STORE con control AND)."""
        b = self.b
        res = b.alloc_bits(1)[0]
        b.bit_store(res, False)
        for x in bits:
            c = b.alloc_bits(1)[0]; nc = b.alloc_bits(1)[0]; nx = b.alloc_bits(1)[0]
            b.bit_store(c, False); b.bit_store(c, True, control=res)          # c = res
            b.bit_store(nc, True); b.bit_store(nc, False, control=c)          # nc = !res
            b.bit_store(nx, True); b.bit_store(nx, False, control=x)          # nx = !x
            b.bit_store(res, False)
            b.push_condition(c); b.bit_store(res, True, control=nx); b.pop_condition()
            b.push_condition(nc); b.bit_store(res, True, control=x); b.pop_condition()
        return res

    def _disc_clear(self, r, D):
        """D (= sum sigma_i S_{r-i}, bilineal) -> 0 por medicion X + fase corregida con CZ condicionados (0 Toffoli)."""
        b = self.b
        with b.mark('bm_disc_mbu'):
            m = b.alloc_bits(DEG)
            b.hmr(D, m)
            h = []
            for k in range(2 * DEG - 1):
                val = int(GM.EXP[k % 4095])
                bs = [m[bb] for bb in range(DEG) if (val >> bb) & 1]
                h.append(self._xor_bits(bs))
            for i in range(0, min(r, self.bd(r)) + 1):
                for k in range(2 * DEG - 1):
                    pares = [(u, k - u) for u in range(DEG) if 0 <= k - u < DEG]
                    b.push_condition(h[k])
                    for u, v in pares:
                        b.cz(self.sigma[i][u], self.S[r - i][v])
                    b.pop_condition()

    def _flags(self, D, p, inverse: bool):
        """Solo p (sin t). p = [D!=0 y d>=0] = nz AND (d>=0).

        CAMBIO rama-t-eliminada: la bandera t ya no se materializa. En la ida
        _flags calcula solo p (la escalera + init_and, 12 T, igual que antes);
        en la vuelta descomputa solo p. El control del cswap de _dclear lo
        reconstruye _dclear como w = (no p) AND (d_post <= 0) (9 T).
        nz se libera dentro de _flags como antes (x(nz); cx(z,nz) + del_and).
        """
        b = self.b
        with b.mark('bm_flags'):
            lad = b.alloc_qubits(DEG - 2); z = b.alloc_qubits(1)[0]; nz = b.alloc_qubits(1)[0]
            b.x(D)
            b.init_and(D[0], D[1], lad[0])
            for i in range(2, DEG - 1):
                b.init_and(lad[i - 2], D[i], lad[i - 1])
            b.init_and(lad[DEG - 3], D[DEG - 1], z)
            b.cx(z, nz); b.x(nz)                           # nz = [D != 0]
            b.x(self.d[DW - 1])                            # 1 si d >= 0
            if not inverse:
                b.init_and(nz, self.d[DW - 1], p)
            else:
                b.del_and(nz, self.d[DW - 1], p)
            b.x(self.d[DW - 1])
            b.x(nz); b.cx(z, nz)
            b.del_and(lad[DEG - 3], D[DEG - 1], z)
            for i in reversed(range(2, DEG - 1)):
                b.del_and(lad[i - 2], D[i], lad[i - 1])
            b.del_and(D[0], D[1], lad[0])
            b.x(D)
            b.free(lad); b.free(z); b.free(nz)

    def _alpha_sel(self, P, Pinv, p, alpha):
        b = self.b
        b.cx(P, alpha); b.cx(Pinv, P); b.ccx(p, P, alpha); b.cx(Pinv, P)

    def _xmux(self, X, p):
        """X ^= (p ? tau~[0] : sigma[0]) (estado posterior a swap+update, anterior al desplazamiento)."""
        b = self.b
        with b.mark('bm_x'):
            b.cx(self.sigma[0], X); b.cx(self.tau[0], self.sigma[0]); b.ccx(p, self.sigma[0], X); b.cx(self.tau[0], self.sigma[0])

    def _dupd(self, p, inverse: bool):
        b = self.b
        with b.mark('bm_d'):
            if not inverse:
                b.cx(p, self.d); b.iadd(1, target=self.d); b.iadd(1, target=self.d, control=p)
            else:
                b.isub(1, target=self.d, control=p); b.isub(1, target=self.d); b.cx(p, self.d)

    def _t_recon(self, p):
        """w = (no p) AND (d_post <= 0). Reconstruccion de t (Frente A).

        d_post <= 0 <=> signo(d_post) O (d_post == 0). Costo 9 T, 11 ancillas
        transitorias (escalera 6 + z0 + s1 + or_out + np + w). La regla es
        exacta salvo la rama (D=0, d<0) (reserva medida del Frente A:
        0/238,000 rondas; el verificador arbitra). Copia de
        frente_a_t_scan/medir_t_recon.py, con el descomputo CORREGIDO (ver
        _t_recon_del): medir_t_recon.py liberaba np_ y s1 sucios (les faltaba
        el cx de vuelta); aqui se descomputan bien (0 T, solo cx).
        """
        b = self.b
        d = self.d  # 8 bits, d_post
        b.x(d)  # flip d para el test de cero
        lad = b.alloc_qubits(DW - 2)  # 6 temps de escalera
        z0 = b.alloc_qubits(1)[0]
        b.init_and(d[0], d[1], lad[0])
        for i in range(2, DW - 1):
            b.init_and(lad[i - 2], d[i], lad[i - 1])
        b.init_and(lad[DW - 3], d[DW - 1], z0)  # z0 = [d == 0]
        b.x(d)  # restaura d
        s1 = b.alloc_qubits(1)[0]
        b.cx(d[DW - 1], s1)
        b.x(s1)  # s1 = NOT d[7]
        b.x(z0)  # NOT z0
        or_out = b.alloc_qubits(1)[0]
        b.init_and(s1, z0, or_out)
        b.x(z0)
        b.x(or_out)  # or_out = [d <= 0]
        np_ = b.alloc_qubits(1)[0]
        b.cx(p, np_)
        b.x(np_)  # np = NOT p
        w = b.alloc_qubits(1)[0]
        b.init_and(or_out, np_, w)  # w = [d<=0] AND (NOT p)
        self._t_recon_scaf = (lad, z0, s1, or_out, np_)
        return w

    def _t_recon_del(self, p, w):
        """Descomputo de _t_recon (0 T). Espejo exacto del computo."""
        b = self.b
        lad, z0, s1, or_out, np_ = self._t_recon_scaf
        b.del_and(or_out, np_, w)
        b.free(w)
        b.x(np_)
        b.cx(p, np_)  # np -> 0 (medir_t_recon.py lo liberaba sucio)
        b.free(np_)
        b.x(or_out)
        b.x(z0)
        b.del_and(s1, z0, or_out)
        b.x(z0)
        b.x(s1)
        b.cx(self.d[DW - 1], s1)  # s1 -> 0 (medir_t_recon.py lo liberaba sucio)
        b.free(s1)
        b.free(or_out)
        b.x(self.d)
        b.del_and(lad[DW - 3], self.d[DW - 1], z0)
        for i in reversed(range(2, DW - 1)):
            b.del_and(lad[i - 2], self.d[i], lad[i - 1])
        b.del_and(self.d[0], self.d[1], lad[0])
        b.x(self.d)
        b.free(lad)
        b.free(z0)

    def _dclear(self, D, p):
        """Forward: lleva D a cero (replace: inverso de sigma_0; retain: a H).  Reverse: lo reconstruye (misma secuencia).

        CAMBIO rama-t-eliminada: el control del cswap es w = _t_recon(p)
        (9 T, transitorio), calculado DESPUES de liberar la torre de inversion
        (el pico de _dclear queda en la inversion, 1,860; w anade 11
        transitorios sobre ~1,830 -> 1,841 < 1,860). w se descomputa justo
        despues del cswap. Misma funcion en ida y vuelta (d = d_post en ambas).
        """
        b = self.b
        with b.mark('bm_dclear'):
            u = b.alloc_qubits(DEG)
            h = self._inv_init(self.sigma[0], u)
            b.ccx(p, u, D)
            self._inv_del(h, self.sigma[0], u)
            b.free(u)
            w = self._t_recon(p)
            b.cswap(w, D, self.H)
            self._t_recon_del(p, w)

    # ---------------- rondas ----------------
    def forward_round(self, r: int):
        b = self.b
        p = b.alloc_qubits(1)[0]
        D = b.alloc_qubits(DEG); X = b.alloc_qubits(DEG); alpha = b.alloc_qubits(DEG)
        self._disc(r, D)
        self._flags(D, p, inverse=False)
        b.cx(self.sigma[0], X)                              # X = sigma_0 anterior
        with b.mark('bm_alpha'):
            P = b.init_gf2_mul(X, D, field=self.f)
            Pinv = b.alloc_qubits(DEG)
            scaf = self._inv_init(P, Pinv)
            self._alpha_sel(P, Pinv, p, alpha)
        with b.mark('bm_swap'):
            for i in range(self.bu(r) + 1):
                b.cswap(p, self.sigma[i], self.tau[i])
        with b.mark('bm_update'):
            for i in range(self.bu(r) + 1):
                self._mul(alpha, self.tau[i], self.sigma[i])
        self._dupd(p, inverse=False)
        with b.mark('bm_alpha'):
            self._alpha_sel(P, Pinv, p, alpha)              # alpha -> 0
            self._inv_del(scaf, P, Pinv)
            b.free(Pinv)
            b.del_gf2_mul(X, D, target=P, field=self.f); b.free(P)
        self._xmux(X, p)                                    # X -> 0
        self._dclear(D, p)                                  # D -> 0
        b.free(alpha); b.free(X); b.free(D)
        self.tau = [self.tau[-1]] + self.tau[:-1]
        self.flags.append(p)

    def reverse_round(self, r: int):
        b = self.b
        p = self.flags.pop()
        self.tau = self.tau[1:] + [self.tau[0]]
        D = b.alloc_qubits(DEG); X = b.alloc_qubits(DEG); alpha = b.alloc_qubits(DEG)
        self._dclear(D, p)                                  # reconstruye D (cswap con H, luego inversion de sigma'_0)
        self._xmux(X, p)                                    # X = sigma_0 anterior
        with b.mark('bm_alpha'):
            P = b.init_gf2_mul(X, D, field=self.f)
            Pinv = b.alloc_qubits(DEG)
            scaf = self._inv_init(P, Pinv)
            self._alpha_sel(P, Pinv, p, alpha)
        self._dupd(p, inverse=True)
        with b.mark('bm_update'):
            for i in reversed(range(self.bu(r) + 1)):
                self._mul(alpha, self.tau[i], self.sigma[i])
        with b.mark('bm_swap'):
            for i in reversed(range(self.bu(r) + 1)):
                b.cswap(p, self.sigma[i], self.tau[i])
        with b.mark('bm_alpha'):
            self._alpha_sel(P, Pinv, p, alpha)
            self._inv_del(scaf, P, Pinv)
            b.free(Pinv)
            b.del_gf2_mul(X, D, target=P, field=self.f); b.free(P)
        b.cx(self.sigma[0], X)                              # X -> 0
        self._flags(D, p, inverse=True)
        self._disc_clear(r, D)                              # D -> 0 (MBU)
        b.free(alpha); b.free(X); b.free(D); b.free(p)

    def forward(self, rounds=None):
        for r in range(self.n if rounds is None else rounds):
            self.forward_round(r)

    def reverse(self, rounds=None):
        for r in reversed(range(self.n if rounds is None else rounds)):
            self.reverse_round(r)


def build_stage_d_v1(n=70, LS=36, degree=12, ida_y_vuelta=True) -> km.Circuit:
    b = km.CircuitBuilder(); gf = km.GF2Field(degree)
    S = [b.create_quantum_register(degree, name=f'S{i}') for i in range(n)]
    bm = BMStageV1(b, gf, S, LS, n)
    bm.forward()
    if ida_y_vuelta:
        bm.reverse()
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
        c = build_stage_d_v1(ida_y_vuelta=iv)
        log.info("v1 ida_y_vuelta=%s toffoli-like=%d qubits=%d", iv, c.operation_statistics().num_toffoli_like, c.num_qubits)
