import sys
sys.path.insert(0,'src'); sys.path.insert(0,'verifiers/invsqrt'); sys.path.insert(0,'/home/claude/tmphorner')
import kickmix as km
from invsqrt_halfsplit import HornerMitad
from invsqrt_logshift2 import PipelineLog2
from invsqrt_piecewise import PWSpec
from nr_reference_circuit import _add_row

class HornerTrunc(HornerMitad):
    """Horner donde el sumando del paso i descarta sus k_i bits bajos (t < m + k_i) y usa solo `dd` bits de u."""
    def __init__(self, spec, w, offs, ks, dd):
        super().__init__(spec, w, offs); self.ks = ks; self.dd = dd
    def aplica(self, b, R, inverse):
        s, w, offs = self.spec, self.w, self.offs
        c = [R["coef"][offs[i]:offs[i] + w[i]] for i in range(s.deg + 1)]
        u_ctl = [(m, R["x"][s.width - 1 - s.j - m]) for m in range(1, self.dd + 1)]
        order = range(0, s.deg) if inverse else range(s.deg - 1, -1, -1)
        with b.mark(self.nombre):
            for i in order:
                k = self.ks[i]
                for m, ctl in (reversed(u_ctl) if inverse else u_ctl):
                    terms = [(c[i + 1][t], t - m) for t in range(m + k, w[i + 1])]
                    if terms:
                        _add_row(b, inverse, ctl, terms, c[i], R["scratch"], subtract=True)

class PipelineTrunc(PipelineLog2):
    def __init__(self, spec, sesgo, ks, dd):
        super().__init__(spec, sesgo)
        self.fases = [HornerTrunc(spec, f.w, f.offs, ks, dd) if f.nombre == "horner" else f for f in self.fases]

def costo(sesgo, ks, dd):
    spec = PWSpec(deg=2, j=8, wc=28, dd=13)
    c = PipelineTrunc(spec, sesgo, ks, dd).construye()
    return c, int(c.num_qubits), int(c.operation_statistics().num_toffoli_like)
if __name__ == '__main__':
    for ks, dd in (((0,0),13), ((0,1),13), ((1,2),13), ((2,3),12)):
        c, q, t = costo(1, ks, dd); print('ks',ks,'dd',dd,'Q',q,'toffoli',t)
