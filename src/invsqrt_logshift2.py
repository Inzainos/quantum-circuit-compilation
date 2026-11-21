#!/usr/bin/env python3
"""
invsqrt con normalizacion Y desnormalizacion logaritmicas (s binario de 4 bits, sin banderas unarias).

Normalizacion: contador de pares de ceros iniciales por etapas 8,4,2,1 (pares).
Etapa b (b=3..0): sb[b] := los 2*2^b bits superiores de x son 0 (cadena de ANDs, los
intermedios se borran con del_and y usan como temporales los qubits de `coef`, que valen 0 en
esta fase); luego x := x << 2*2^b controlado por sb[b] (rotacion; los bits que dan la vuelta son 0).
Como x >= 1 y x < 2^22, s <= 10 y esta descomposicion codifica exactamente el numero de pares nulos.
Desnormalizacion: y1 := c0 << s con 4 etapas controladas (invsqrt_logshift.DesnormLog).
Registro `flags` eliminado: Q baja 6 respecto a invsqrt_logshift. Validar con el verificador oficial.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(_ROOT / "tools"))
try:
    from qcc_log import emit as _qcc_emit, phase as _qcc_phase
    _HAS_QCC_LOG = True
except Exception:  # noqa: BLE001 - logging opcional; el circuito no depende de el
    _HAS_QCC_LOG = False

import kickmix as km  # noqa: E402
from invsqrt_bloqs import Fase  # noqa: E402
from invsqrt_logshift import DesnormLog  # noqa: E402
from invsqrt_halfsplit import PipelineMitad, HornerMitad  # noqa: E402
from invsqrt_piecewise import PWSpec  # noqa: E402

log = logging.getLogger("logshift2")


def _nor(b: km.CircuitBuilder, inverse: bool, bits, target, temps) -> None:
    """target ^= (todos los `bits` son 0). Cadena de ANDs; `temps` debe estar en 0 y queda en 0."""
    n = len(bits)
    b.x(bits)
    if n == 2:
        (b.del_and if inverse else b.init_and)(bits[0], bits[1], target)
    else:
        chain = [(bits[0], bits[1], temps[0])]
        for i in range(2, n - 1):
            chain.append((temps[i - 2], bits[i], temps[i - 1]))
        last = (temps[n - 3], bits[n - 1], target)
        for c in chain:
            b.init_and(*c)
        (b.del_and if inverse else b.init_and)(*last)
        for c in reversed(chain):
            b.del_and(*c)
    b.x(bits)


class NormalizarLog(Fase):
    nombre = "normalize_log"
    consume = ("x", "sb", "coef")

    def __init__(self, spec: PWSpec):
        self.spec = spec

    def adapta(self, bits):
        self._exige(bits, "x", self.spec.width)
        self._exige(bits, "sb", 4)
        self._exige(bits, "coef", 14)

    def aplica(self, b, R, inverse):
        x, sb, tmp = R["x"], R["sb"], R["coef"]
        w = len(x)
        with b.mark(self.nombre):
            for bit in (range(4) if inverse else (3, 2, 1, 0)):
                r = 2 << bit
                top = x[w - r:w]
                if inverse:
                    b.right_rotate(x, r, control=sb[bit])
                    _nor(b, True, top, sb[bit], tmp)
                else:
                    _nor(b, False, top, sb[bit], tmp)
                    b.left_rotate(x, r, control=sb[bit])


def _add_row_estrecha(b, inverse, control, terms, target, scratch, subtract):
    """Como _add_row del verificador, pero el sumando ocupa solo `span` bits de scratch (iadd con sumando mas corto que el destino)."""
    low = min(i for _, i in terms)
    hi = max(i for _, i in terms) + 1
    sources = km.array([q for q, _ in terms])
    products = km.array([scratch[i - low] for _, i in terms])
    b.init_and(control, sources, products)
    add = scratch[0:hi - low]
    if subtract != inverse:
        b.isub(add, target=target[low:])
    else:
        b.iadd(add, target=target[low:])
    b.del_and(control, sources, products)


class HornerEstrecho(HornerMitad):
    """Horner con scratch de ancho max(w[i+1]) (en vez de max(w))."""

    def adapta(self, bits):
        self._exige(bits, "scratch", max(self.w[1:]))
        self._exige(bits, "coef", sum(self.w))

    def aplica(self, b, R, inverse):
        s, w, offs = self.spec, self.w, self.offs
        c = [R["coef"][offs[i]:offs[i] + w[i]] for i in range(s.deg + 1)]
        u_ctl = [(m, R["x"][s.width - 1 - s.j - m]) for m in range(1, s.dd + 1)]
        order = range(0, s.deg) if inverse else range(s.deg - 1, -1, -1)
        with b.mark(self.nombre):
            for i in order:
                for m, ctl in (reversed(u_ctl) if inverse else u_ctl):
                    terms = [(c[i + 1][t], t - m) for t in range(m, w[i + 1])]
                    if terms:
                        _add_row_estrecha(b, inverse, ctl, terms, c[i], R["scratch"], True)


class PipelineLog2(PipelineMitad):
    def __init__(self, spec: PWSpec, sesgo: int = 0, estrecho: bool = False,
                 trunc: tuple[int, int] = (0, 0), skip_low: bool = False, trunc_low: bool = False, r5: bool = False):
        super().__init__(spec, sesgo, trunc, skip_low, trunc_low)
        self.estrecho = estrecho
        # R5 (2026-11-19): sin --r5, pipeline idéntico al original (CopiaC0
        # presente, DesnormLog sin copia). Con --r5, CopiaC0 sale de la lista
        # y su copia CX vive dentro de DesnormLog (fold_copy=True).
        # R1+R5 (2026-11-19): con --r1 --r5, la truncación de R1 (que vivía en
        # CopiaC0) se re-ubica en la copia plegada (DesnormLog trunc_low=True).
        self.r5 = r5
        self.fases = [NormalizarLog(spec) if f.nombre == "normalize" else (HornerEstrecho(spec, f.w, f.offs) if (estrecho and f.nombre == "horner") else f)
                      for f in self.fases if f.nombre != "denormalize"]
        if r5:
            self.fases = [f for f in self.fases if f.nombre != "copy_c0"]
            self.fases.append(DesnormLog(spec, self.w, self.offs, fold_copy=True, trunc_low=trunc_low))
        else:
            self.fases.append(DesnormLog(spec))

    def anchos(self):
        d = super().anchos()
        del d["flags"]
        d["sb"] = 4
        if self.estrecho:
            d["scratch"] = max(self.w[1:])
        return d

    def construye(self) -> km.Circuit:
        """Igual que antes, pero `scratch` (solo Horner) e `y1` (solo copia/desnorm/fase) no coexisten: y1 se asigna tras liberar scratch."""
        bits = self.adapta_o_reajusta()
        b = km.CircuitBuilder()
        R = {"x": b.create_quantum_register(bits["x"], name="x")}
        for nombre in ("sel", "sb", "coef"):
            R[nombre] = b.alloc_qubits(bits[nombre])

        def vivos_antes(f, inverse):
            return None

        def asigna(nombre):
            R[nombre] = b.alloc_qubits(bits[nombre])

        def libera(nombre):
            b.free(R.pop(nombre))

        # R5: el intercambio scratch/y1 se dispara en copy_c0 (original) o en
        # denormalize_log (con --r5, cuando copy_c0 ya no está en la lista).
        # Es el mismo punto del pipeline (tras Horner, antes de denorm) y el
        # mismo orden de alloc/free, así que los índices de qubit no cambian.
        swap = "denormalize_log" if self.r5 else "copy_c0"

        # --- ida ---
        for f in self.fases:
            if f.nombre == swap:
                libera("scratch")
                asigna("y1")
            if f.nombre == "horner":
                asigna("scratch")
            f.aplica(b, R, False)
        self.media.aplica(b, R, False)
        # --- vuelta ---
        for f in reversed(self.fases):
            f.aplica(b, R, True)
            if f.nombre == swap:
                libera("y1")
                asigna("scratch")
            if f.nombre == "horner":
                libera("scratch")
        for nombre in ("coef", "sb", "sel"):
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
    import time

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--deg", type=int, default=2)
    ap.add_argument("--j", type=int, default=8)
    ap.add_argument("--wc", type=int, default=28)
    ap.add_argument("--dd", type=int, default=13)
    ap.add_argument("--sesgo", type=int, default=0)
    ap.add_argument("--k1", type=int, default=0, help="B+C (C): bits bajos a 0 en c1")
    ap.add_argument("--k2", type=int, default=0, help="B+C (C): bits bajos a 0 en c2")
    ap.add_argument("--skip-low", action="store_true", help="B+C (B): quitar el z_pow bajo (bit 0 de y1)")
    ap.add_argument("--r1", action="store_true", help="R1 (espiral Fase 1): y1 nace sin bit 0 (micro-tuberia bit 0 nativa; CopiaC0 trunca, FasePorBits recibe y1[1:])")
    ap.add_argument("--r5", action="store_true", help="R5 (espiral Fase 1): eliminar copy_c0 (etapa fantasma); su copia CX c[0]->y1 vive dentro de denorm (DesnormLog fold_copy)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    spec = PWSpec(deg=a.deg, j=a.j, wc=a.wc, dd=a.dd)
    params = {"deg": a.deg, "j": a.j, "wc": a.wc, "dd": a.dd, "sesgo": a.sesgo,
              "k1": a.k1, "k2": a.k2, "skip_low": a.skip_low, "r1": a.r1, "r5": a.r5}
    t0 = time.time()
    circ = PipelineLog2(spec, a.sesgo, trunc=(a.k1, a.k2), skip_low=a.skip_low, trunc_low=a.r1, r5=a.r5).construye()
    q = int(circ.num_qubits)
    t_toff = int(circ.operation_statistics().num_toffoli_like)
    log.info("circuito: Q=%d T=%d", q, t_toff)
    if _HAS_QCC_LOG:
        _qcc_emit("invsqrt_logshift2", "build", "ok", inputs=params,
                  outputs={"Q": q, "T": t_toff},
                  duration_s=time.time() - t0)
    if a.out:
        t0 = time.time()
        circ.to_file(str(a.out), format="kmb")
        digest = hashlib.sha256(a.out.read_bytes()).hexdigest()
        log.info("sha256 %s", digest)
        if _HAS_QCC_LOG:
            _qcc_emit("invsqrt_logshift2", "write", "ok",
                      inputs={"out": str(a.out)},
                      outputs={"sha256": digest, "bytes": a.out.stat().st_size},
                      duration_s=time.time() - t0)
