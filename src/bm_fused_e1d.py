#!/usr/bin/env python3
"""BM fusionado con ValueInv3E1d SOLO en el bloque alpha (140 inversiones).
_dclear / omega / scan usan ValueInv3 original (sin recompute, sin costo T extra).

E1d no baja el pico de la torre (medido standalone Q=57 en ambos), asi que se espera
Q=1937 sin cambio y T=784172+140*6=785012. Esta build lo confirma a nivel circuito completo.
"""
import os
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/redisenio_inversor")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # SCRATCH rama-t-eliminada: prioridad sobre el repo
import kickmix as km
from dqi_bm_stage_v1 import BMStageV1, DEG
from bm_fused import BMStageFused
from tower_inv3_e1d import ValueInv3E1d


class BMStageFusedE1d(BMStageFused):
    """Alpha usa E1d; _dclear usa la torre original."""

    def _inv_init(self, src, tgt):
        # solo el bloque alpha llama a este _inv_init (ver _dclear abajo, que usa el original)
        return ValueInv3E1d(self.b, src, tgt).forward()

    def _dclear(self, D, p):
        # copia de BMStageV1._dclear (rama sin t) pero con la torre ORIGINAL
        # (no E1d) para la inversion de sigma_0. El control del cswap es
        # w = _t_recon(p) (9 T), calculado tras liberar la torre y descomputado
        # justo despues del cswap. Misma funcion en ida y vuelta.
        b = self.b
        with b.mark('bm_dclear'):
            u = b.alloc_qubits(DEG)
            h = BMStageV1._inv_init(self, self.sigma[0], u)
            b.ccx(p, u, D)
            BMStageV1._inv_del(self, h, self.sigma[0], u)
            b.free(u)
            w = self._t_recon(p)
            b.cswap(w, D, self.H)
            self._t_recon_del(p, w)
