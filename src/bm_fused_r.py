#!/usr/bin/env python3
"""BM fusionado con ValueInv3R (E1='N' o E2='all') SOLO en el bloque alpha.
_dclear / omega / scan usan ValueInv3 original."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import kickmix as km
from dqi_bm_stage_v1 import BMStageV1, DEG
from bm_fused import BMStageFused
from tower_inv3r import ValueInv3R


class BMStageFusedR(BMStageFused):
    """Alpha usa ValueInv3R(recompute=modo); _dclear usa la torre original."""

    def __init__(self, *args, recompute='N', **kwargs):
        super().__init__(*args, **kwargs)
        self.recompute = recompute

    def _inv_init(self, src, tgt):
        return ValueInv3R(self.b, src, tgt, recompute=self.recompute).forward()

    def _dclear(self, D, p, t):
        b = self.b
        with b.mark('bm_dclear'):
            u = b.alloc_qubits(DEG)
            h = BMStageV1._inv_init(self, self.sigma[0], u)
            b.ccx(p, u, D)
            BMStageV1._inv_del(self, h, self.sigma[0], u)
            b.free(u)
            b.cswap(t, D, self.H)
