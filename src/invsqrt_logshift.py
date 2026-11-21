#!/usr/bin/env python3
"""
Variante de invsqrt_halfsplit con desnormalizacion logaritmica.

Las banderas unarias (termometro) `flags[k] = (s > k)` se convierten en `s` binario de 4 bits
con puros CNOT (0 Toffoli):
    s0 = XOR de todas las banderas, s1 = f1^f3^f5^f7^f9, s2 = f3^f7, s3 = f7.
y la desnormalizacion `y1 = c0 << s` se hace con 4 etapas de rotacion controlada (1,2,4,8)
en lugar de 10 rotaciones controladas de 1 bit. Cuesta 4 qubits extra (registro `sb`).
Todo se valida con el verificador oficial; aqui no se asume ninguna ganancia.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kickmix as km  # noqa: E402
from invsqrt_bloqs import ErrorAncho, Fase  # noqa: E402
from invsqrt_halfsplit import PipelineMitad  # noqa: E402
from invsqrt_piecewise import PWSpec  # noqa: E402

log = logging.getLogger("logshift")

# bit b de s = XOR de flags[k] para k en _TAPS[b]  (flags[k] = s > k, termometro)
_TAPS = {0: range(0, 10), 1: (1, 3, 5, 7, 9), 2: (3, 7), 3: (7,)}


class BinarizaS(Fase):
    nombre = "binariza_s"
    consume = ("flags", "sb")

    def __init__(self, spec: PWSpec):
        self.spec = spec

    def adapta(self, bits):
        self._exige(bits, "flags", 10)
        self._exige(bits, "sb", 4)
        if self.spec.n_p != 10:
            raise ErrorAncho(self.nombre, "flags", 10, self.spec.n_p)

    def aplica(self, b, R, inverse):  # CNOT puros: auto-inversa
        with b.mark(self.nombre):
            for bit, taps in _TAPS.items():
                for k in taps:
                    b.cx(R["flags"][k], R["sb"][bit])


class DesnormLog(Fase):
    nombre = "denormalize_log"
    consume = ("sb", "y1")

    def __init__(self, spec: PWSpec, w=None, offs=None, fold_copy: bool = False, trunc_low: bool = False):
        self.spec = spec
        # R5 (2026-11-19): copy_c0 plegado en denorm (PipelineLog2 --r5).
        # w/offs son los anchos/offsets de los coeficientes (como CopiaC0);
        # solo se usan cuando fold_copy=True. Sin el flag, comportamiento
        # idéntico al original (PipelineLog no se toca).
        # R1+R5 (2026-11-19): con trunc_low=True, la truncación de R1 (que
        # vivía en CopiaC0, eliminada por R5) se re-ubica en esta copia
        # plegada: se copia c0[1:] a y1[1:] (27 CX) y y1[0] queda en |0>.
        self.w, self.offs, self.fold_copy, self.trunc_low = w, offs, fold_copy, trunc_low
        if fold_copy:
            self.consume = ("sb", "y1", "coef")

    def adapta(self, bits):
        self._exige(bits, "y1", self.spec.out_bits)
        if self.fold_copy and self.w[0] > self.spec.wc:
            raise ErrorAncho(self.nombre, "y1", self.w[0], self.spec.wc)

    def _longitudes(self):
        wc, out = self.spec.wc, self.spec.out_bits
        cum, res = 0, []
        for bit in range(4):
            cum = min(cum + (1 << bit), 10)
            res.append(min(wc + cum, out))
        return res

    def _copia_c0(self, b, R):
        """Copia CX c[0] -> y1 (la lógica de la antigua fase CopiaC0, 28 CX, 0 T).
        La copia sigue siendo necesaria: denorm rota el carril y1 (hasta
        out_bits) y los bits que salen por arriba de wc deben ser 0, no
        envolver dentro de 28 bits; operar in situ sobre el slice c[0] de
        coef sería incorrecto (el carril se saldría del slice y corrompería
        c[1]). Fuera del mark, como la CopiaC0 original (sin mark).
        R1+R5: con trunc_low, la truncación de R1 (que vivía en CopiaC0, ya
        eliminada) se re-ubica aquí: se copia c0[1:] a y1[1:] (27 CX) y
        y1[0] queda en |0>, igual que en CopiaC0 con trunc_low."""
        if self.trunc_low:
            b.cx(R["coef"][self.offs[0] + 1:self.offs[0] + self.w[0]],
                 R["y1"][1:self.w[0]])
        else:
            b.cx(R["coef"][self.offs[0]:self.offs[0] + self.w[0]], R["y1"][:self.spec.wc])

    def aplica(self, b, R, inverse):
        # R5: ida = copia y luego rotaciones; vuelta = rotaciones inversas y
        # luego copia (deshacer), orden inverso exacto de la ida.
        if self.fold_copy and not inverse:
            self._copia_c0(b, R)
        largos = self._longitudes()
        etapas = list(range(4))
        with b.mark(self.nombre):
            for bit in (reversed(etapas) if inverse else etapas):
                lane = R["y1"][:largos[bit]]
                (b.right_rotate if inverse else b.left_rotate)(lane, 1 << bit, control=R["sb"][bit])
        if self.fold_copy and inverse:
            self._copia_c0(b, R)


class PipelineLog(PipelineMitad):
    def __init__(self, spec: PWSpec, sesgo: int = 0):
        super().__init__(spec, sesgo)
        self.fases = [f for f in self.fases if f.nombre != "denormalize"]
        self.fases += [BinarizaS(spec), DesnormLog(spec)]

    def anchos(self):
        d = super().anchos()
        d["sb"] = 4
        return d

    def construye(self) -> km.Circuit:
        bits = self.adapta_o_reajusta()
        b = km.CircuitBuilder()
        R = {"x": b.create_quantum_register(bits["x"], name="x")}
        orden = ("y1", "flags", "sel", "sb", "coef", "scratch")
        for nombre in orden:
            R[nombre] = b.alloc_qubits(bits[nombre])
        for f in self.fases:
            f.aplica(b, R, False)
        self.media.aplica(b, R, False)
        for f in reversed(self.fases):
            f.aplica(b, R, True)
        for nombre in orden:
            b.free(R[nombre])
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
    import argparse
    import hashlib

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--deg", type=int, default=2)
    ap.add_argument("--j", type=int, default=8)
    ap.add_argument("--wc", type=int, default=28)
    ap.add_argument("--dd", type=int, default=13)
    ap.add_argument("--sesgo", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    spec = PWSpec(deg=a.deg, j=a.j, wc=a.wc, dd=a.dd)
    circ = PipelineLog(spec, a.sesgo).construye()
    log.info("circuito: Q=%d T=%d", circ.num_qubits, int(circ.operation_statistics().num_toffoli_like))
    if a.out:
        circ.to_file(str(a.out), format="kmb")
        log.info("sha256 %s", hashlib.sha256(a.out.read_bytes()).hexdigest())
