#!/usr/bin/env python3
"""
Arquitectura por fases-clase (estilo Bloq de Qualtran) que emite circuitos kickmix.

Hecho verificado: qualtran 0.7.0 NO tiene puente Bloq -> kickmix, asi que los Bloq
reales no pueden generar la sumision. Aqui se copia la *interfaz* del Bloq:
  * `consume`: registros (nombre -> bitsize) que la fase necesita.
  * `adapta(bits)`: recalcula sus parametros a partir de los registros recibidos;
    si no caben lanza `ErrorAncho` (el orquestador lo captura y reajusta o rechaza).
  * `aplica(b, R, inverse)`: emite las compuertas kickmix (y su adjunto con inverse=True).
  * `toffoli_analitico()`: costo analitico opcional (como build_call_graph).
Entre fases se pueden insertar clases `Pesada` (operaciones pesadas arbitrarias en Python).

Invariante: `Pipeline.construye()` reproduce byte a byte el circuito de
invsqrt_piecewise.construye (mismo orden de alocacion y de compuertas).
"""

from __future__ import annotations

import dataclasses
import logging
import sys
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "verifiers" / "invsqrt"))

import kickmix as km  # noqa: E402
from invsqrt_piecewise import PWSpec, tabla_coeficientes  # noqa: E402
from nr_reference_circuit import (  # noqa: E402
    _add_row,
    _denormalize,
    _normalize,
    _phase_by_bits,
)

log = logging.getLogger("bloqs")


class ErrorFase(Exception):
    """Base de los errores de fase capturables por el orquestador."""


class ErrorAncho(ErrorFase):
    """Un registro recibido es mas chico que el que la fase necesita."""

    def __init__(self, fase: str, registro: str, necesarios: int, recibidos: int):
        super().__init__(f"{fase}: registro '{registro}' necesita {necesarios} bits, recibio {recibidos}")
        self.fase, self.registro, self.necesarios, self.recibidos = fase, registro, necesarios, recibidos


class Fase:
    nombre = "fase"
    consume: tuple[str, ...] = ()

    def _exige(self, bits: dict[str, int], reg: str, n: int) -> None:
        if bits.get(reg, 0) < n:
            raise ErrorAncho(self.nombre, reg, n, bits.get(reg, 0))

    def adapta(self, bits: dict[str, int]) -> None:  # noqa: D401
        """Valida/recalcula parametros segun los registros recibidos."""

    def aplica(self, b: km.CircuitBuilder, R: dict, inverse: bool) -> None:
        raise NotImplementedError

    def toffoli_analitico(self) -> Optional[int]:
        return None


class Normalizar(Fase):
    nombre = "normalize"
    consume = ("x", "flags")

    def __init__(self, spec: PWSpec):
        self.spec = spec

    def adapta(self, bits):
        self._exige(bits, "x", self.spec.width)
        self._exige(bits, "flags", self.spec.n_p)

    def aplica(self, b, R, inverse):
        with b.mark(self.nombre):
            _normalize(b, inverse, R["x"], R["flags"])


class TablaLookup(Fase):
    nombre = "lookup"
    consume = ("x", "coef")

    def __init__(self, spec: PWSpec):
        self.spec = spec
        self.b, self.w = tabla_coeficientes(spec)
        self.offs = [sum(self.w[:i]) for i in range(spec.deg + 1)]
        self.table = [sum(self.b[i][A] << self.offs[i] for i in range(spec.deg + 1))
                      for A in range(1 << (spec.j + 2))]

    def adapta(self, bits):
        self._exige(bits, "x", self.spec.width)
        self._exige(bits, "coef", sum(self.w))

    def aplica(self, b, R, inverse):
        s = self.spec
        address = R["x"][s.width - 2 - s.j:s.width]
        with b.mark(self.nombre):
            (b.del_lookup if inverse else b.init_lookup)(table=self.table, address=address, target=R["coef"])

    def toffoli_analitico(self):
        return len(self.table)  # ~1 Toffoli por entrada (init) -- medido: 551 init+del


class Horner(Fase):
    nombre = "horner"
    consume = ("x", "coef", "scratch")

    def __init__(self, spec: PWSpec, w: list[int], offs: list[int]):
        self.spec, self.w, self.offs = spec, w, offs

    def adapta(self, bits):
        self._exige(bits, "scratch", max(self.w))
        self._exige(bits, "coef", sum(self.w))
        if self.spec.dd > self.spec.width - 2 - self.spec.j:
            raise ErrorAncho(self.nombre, "x", self.spec.dd + 2 + self.spec.j, self.spec.width)

    def aplica(self, b, R, inverse):
        s, w, offs = self.spec, self.w, self.offs
        c = [R["coef"][offs[i]:offs[i] + w[i]] for i in range(s.deg + 1)]
        x = R["x"]
        u_ctl = [(m, x[s.width - 2 - s.j - m]) for m in range(1, s.dd + 1)]
        order = range(0, s.deg) if inverse else range(s.deg - 1, -1, -1)
        with b.mark(self.nombre):
            for i in order:
                for m, ctl in (reversed(u_ctl) if inverse else u_ctl):
                    terms = [(c[i + 1][t], t - m) for t in range(m, w[i + 1])]
                    if terms:
                        _add_row(b, inverse, ctl, terms, c[i], R["scratch"], subtract=True)


class CopiaC0(Fase):
    nombre = "copy_c0"
    consume = ("coef", "y1")

    def __init__(self, spec: PWSpec, w: list[int], offs: list[int]):
        self.spec, self.w, self.offs = spec, w, offs

    def adapta(self, bits):
        self._exige(bits, "y1", self.spec.wc)
        if self.w[0] > self.spec.wc:
            raise ErrorAncho(self.nombre, "y1", self.w[0], self.spec.wc)

    def aplica(self, b, R, inverse):
        b.cx(R["coef"][self.offs[0]:self.offs[0] + self.w[0]], R["y1"][:self.spec.wc])


class Desnormalizar(Fase):
    nombre = "denormalize"
    consume = ("flags", "y1")

    def __init__(self, spec: PWSpec):
        self.spec = spec

    def adapta(self, bits):
        self._exige(bits, "y1", self.spec.out_bits)

    def aplica(self, b, R, inverse):
        with b.mark(self.nombre):
            _denormalize(b, inverse, R["flags"], R["y1"])


class FasePorBits(Fase):
    nombre = "phase"
    consume = ("y1",)

    def aplica(self, b, R, inverse):
        _phase_by_bits(b, R["y1"])


class Pesada(Fase):
    """Punto de insercion para una operacion pesada arbitraria: fn(b, R, inverse)."""

    def __init__(self, nombre: str, fn: Callable, consume: tuple[str, ...] = ()):
        self.nombre, self.fn, self.consume = nombre, fn, consume

    def aplica(self, b, R, inverse):
        with b.mark(self.nombre):
            self.fn(b, R, inverse)


class Pipeline:
    """Cadena de fases: forward, fase por bits, y el adjunto en orden inverso."""

    def __init__(self, spec: PWSpec):
        self.spec = spec
        t = TablaLookup(spec)
        self.w, self.offs = t.w, t.offs
        self.fases: list[Fase] = [Normalizar(spec), t, Horner(spec, t.w, t.offs),
                                  CopiaC0(spec, t.w, t.offs), Desnormalizar(spec)]
        self.media: Fase = FasePorBits()

    def inserta(self, fase: Fase, despues_de: str) -> None:
        idx = next(i for i, f in enumerate(self.fases) if f.nombre == despues_de)
        self.fases.insert(idx + 1, fase)

    def anchos(self) -> dict[str, int]:
        s = self.spec
        return {"x": s.width, "y1": s.out_bits, "flags": s.n_p,
                "coef": sum(self.w), "scratch": max(self.w)}

    def adapta(self, bits: dict[str, int]) -> dict[str, int]:
        """Cada fase se reajusta a los registros recibidos; ErrorAncho sube al orquestador."""
        for f in [*self.fases, self.media]:
            f.adapta(bits)
        return bits

    def adapta_o_reajusta(self, max_intentos: int = 8) -> dict[str, int]:
        """Captura ErrorAncho y agranda el registro pedido (solo scratch/coef/y1/flags)."""
        bits = self.anchos()
        for intento in range(max_intentos):
            try:
                return self.adapta(bits)
            except ErrorAncho as e:
                log.warning("intento %d: %s", intento, e)
                if e.registro not in ("scratch", "coef", "y1", "flags"):
                    raise
                bits[e.registro] = e.necesarios
        raise ErrorFase("no converge el reajuste de anchos")

    def toffoli_analitico(self) -> dict[str, Optional[int]]:
        return {f.nombre: f.toffoli_analitico() for f in self.fases}

    def construye(self) -> km.Circuit:
        bits = self.adapta_o_reajusta()
        s = self.spec
        b = km.CircuitBuilder()
        R = {}
        R["x"] = b.create_quantum_register(bits["x"], name="x")
        R["y1"] = b.alloc_qubits(bits["y1"])
        R["flags"] = b.alloc_qubits(bits["flags"])
        R["coef"] = b.alloc_qubits(bits["coef"])
        R["scratch"] = b.alloc_qubits(bits["scratch"])
        for f in self.fases:
            f.aplica(b, R, False)
        self.media.aplica(b, R, False)
        for f in reversed(self.fases):
            f.aplica(b, R, True)
        for nombre in ("y1", "flags", "coef", "scratch"):
            b.free(R[nombre])
        return b.finish_circuit()


if __name__ == "__main__":
    import argparse
    import hashlib

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--deg", type=int, default=2)
    ap.add_argument("--j", type=int, default=7)
    ap.add_argument("--wc", type=int, default=28)
    ap.add_argument("--dd", type=int, default=13)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    pipe = Pipeline(PWSpec(deg=a.deg, j=a.j, wc=a.wc, dd=a.dd))
    circ = pipe.construye()
    log.info("Q=%d T=%d analitico=%s", circ.num_qubits,
             int(circ.operation_statistics().num_toffoli_like), pipe.toffoli_analitico())
    if a.out:
        circ.to_file(str(a.out), format="kmb")
        log.info("sha256 %s", hashlib.sha256(a.out.read_bytes()).hexdigest())
