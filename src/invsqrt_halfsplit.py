#!/usr/bin/env python3
"""
invsqrt "mitad-dividida": tabla de 2^(j+1) entradas en vez de 3*2^j (guardada en 4*2^j).

Idea. Tras normalizar por pares, M = x_norm/2^(w-2) esta en [1,4). Si M >= 2 se escribe
M = 2*M' con M' en [1,2) y 1/sqrt(M) = (1/sqrt 2) * 1/sqrt(M'). El factor 1/sqrt 2 se
integra a los coeficientes de la tabla. Con un giro condicional de 1 bit de x
(x' = x<<1 cuando M < 2) el bit lider queda siempre en la posicion w-1 y:

    direccion = [j bits tras el bit lider] + [sel]      (sel = 1 si M < 2)   -> 2^(j+1) entradas
    u_m       = x'[w-1-j-m]

Los tramos miden 2^-j en M' en ambas mitades, asi que el peor caso relativo no cambia.
El lookup cuesta ~1 Toffoli por entrada, de modo que 256 entradas cuestan ~279 contra ~551.
Costo extra: 1 qubit (sel) y un giro controlado de x (ida y vuelta).

Fases (interfaz de invsqrt_bloqs): Normalizar -> GiroMitad -> TablaLookupMitad -> HornerMitad
-> CopiaC0 -> Desnormalizar, luego FasePorBits y el adjunto en orden inverso.
"""

from __future__ import annotations

import functools
import logging
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kickmix as km  # noqa: E402
from invsqrt_bloqs import (  # noqa: E402
    CopiaC0, Desnormalizar, ErrorAncho, ErrorFase, Fase, FasePorBits, Normalizar,
)
from invsqrt_piecewise import PWSpec  # noqa: E402
from nr_reference_circuit import _add_row  # noqa: E402

log = logging.getLogger("halfsplit")


@functools.lru_cache(maxsize=None)
def tabla_mitad(spec: PWSpec, sesgo: int = 0) -> tuple[list[list[int]], list[int]]:
    """b[i][addr], w[i]. addr = f + sel*2^j, sel=1 -> M<2 (factor 1), sel=0 -> M>=2 (factor 1/sqrt2).

    `sesgo` resta ese numero de ulps (2^-wc) a a0: compensa el sesgo positivo de los pisos (c>>m) de Horner.
    """
    d, j, wc = spec.deg, spec.j, spec.wc
    h = 2.0 ** -j
    n_addr = 1 << (j + 1)
    k = np.arange(d + 1)
    nodes = (np.cos((2 * k + 1) * np.pi / (2 * (d + 1))) + 1) / 2
    vander = np.vander(nodes, d + 1, increasing=True)
    b = [[0] * n_addr for _ in range(d + 1)]
    for sel in (0, 1):
        factor = 1.0 if sel else 2.0 ** -0.5
        for f in range(1 << j):
            m0 = 1.0 + f * h
            coefs = np.linalg.solve(vander, factor * (m0 + h * nodes) ** -0.5)
            for i in range(d + 1):
                esperado = 1.0 if i % 2 == 0 else -1.0
                if coefs[i] * esperado <= 0:
                    raise ValueError(f"signos no alternan: sel={sel} f={f} grado={i}")
                mag = int(round(abs(coefs[i]) * 2 ** wc))
                if i == 0:
                    mag = min(max(mag - sesgo, 0), 2 ** wc - 1)
                b[i][f + (sel << j)] = mag
    w = [max(max(row).bit_length(), 1) for row in b]
    return b, w


def modelo(spec: PWSpec, xs: np.ndarray, con_cotas: bool = False, sesgo: int = 0):
    """y1 entero por x (aritmetica identica al circuito); OverflowError si un registro desborda."""
    width, n_p, d, j, wc, dd = spec.width, spec.n_p, spec.deg, spec.j, spec.wc, spec.dd
    if dd > width - 1 - j:
        raise ValueError("dd excede los bits disponibles bajo el tramo.")
    xs = np.asarray(xs, dtype=np.int64)
    b, w = tabla_mitad(spec, sesgo)
    s = (width - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
    x_norm = xs << (2 * s)
    mask = (1 << width) - 1
    top = (x_norm >> (width - 1)) & 1
    sel = 1 - top
    rot = np.where(top == 1, x_norm, (x_norm << 1) & mask)
    f = (rot >> (width - 1 - j)) & ((1 << j) - 1)
    addr = f + (sel << j)
    tab = [np.array(row, dtype=np.int64) for row in b]
    c = {i: tab[i][addr] for i in range(d + 1)}
    u_bits = [(m, (rot >> (width - 1 - j - m)) & 1) for m in range(1, dd + 1)]
    cotas = {}
    for i in range(d - 1, -1, -1):
        prod = np.zeros_like(xs)
        for m, ctl in u_bits:
            prod += ctl * (c[i + 1] >> m)
        acc = c[i] - prod
        if ((acc < 0) | (acc >= 2 ** w[i])).any():
            raise OverflowError(f"c{i} no cabe en su registro de {w[i]} bits.")
        c[i] = acc
        if con_cotas:
            mx, mn = int(acc.max()), int(acc.min())
            cotas[f"c{i}"] = {"min": mn, "max": mx, "bits_necesarios": max(mx, 1).bit_length(),
                              "bits_asignados": w[i]}
    y1 = c[0] << s
    return (y1, cotas) if con_cotas else y1


def error_relativo(spec: PWSpec, xs: np.ndarray, y1: np.ndarray) -> np.ndarray:
    exact = 1.0 / np.sqrt(np.asarray(xs, dtype=np.float64))
    return np.abs(y1 / 2.0 ** spec.out_bits - exact) / exact


class GiroMitad(Fase):
    """sel := (x[w-1] == 0); si sel, x <<= 1 (rotacion). El adjunto deshace ambos pasos."""
    nombre = "giro_mitad"
    consume = ("x", "sel")

    def __init__(self, spec: PWSpec):
        self.spec = spec

    def adapta(self, bits):
        self._exige(bits, "x", self.spec.width)
        self._exige(bits, "sel", 1)

    def aplica(self, b, R, inverse):
        x, sel, top = R["x"], R["sel"][0], R["x"][self.spec.width - 1]
        with b.mark(self.nombre):
            if not inverse:
                b.x(sel)
                b.cx(top, sel)
                b.left_rotate(x, 1, control=sel)
            else:
                b.right_rotate(x, 1, control=sel)
                b.cx(top, sel)
                b.x(sel)


class TablaLookupMitad(Fase):
    nombre = "lookup"
    consume = ("x", "sel", "coef")

    def __init__(self, spec: PWSpec, sesgo: int = 0):
        self.spec = spec
        self.b, self.w = tabla_mitad(spec, sesgo)
        self.offs = [sum(self.w[:i]) for i in range(spec.deg + 1)]
        self.table = [sum(self.b[i][a] << self.offs[i] for i in range(spec.deg + 1))
                      for a in range(1 << (spec.j + 1))]

    def adapta(self, bits):
        self._exige(bits, "x", self.spec.width)
        self._exige(bits, "coef", sum(self.w))

    def aplica(self, b, R, inverse):
        s = self.spec
        address = km.array([R["x"][s.width - 1 - s.j + k] for k in range(s.j)] + [R["sel"][0]])
        with b.mark(self.nombre):
            (b.del_lookup if inverse else b.init_lookup)(table=self.table, address=address, target=R["coef"])


class HornerMitad(Fase):
    nombre = "horner"
    consume = ("x", "coef", "scratch")

    def __init__(self, spec: PWSpec, w: list[int], offs: list[int]):
        self.spec, self.w, self.offs = spec, w, offs

    def adapta(self, bits):
        self._exige(bits, "scratch", max(self.w))
        self._exige(bits, "coef", sum(self.w))
        if self.spec.dd > self.spec.width - 1 - self.spec.j:
            raise ErrorAncho(self.nombre, "x", self.spec.dd + 1 + self.spec.j, self.spec.width)

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
                        _add_row(b, inverse, ctl, terms, c[i], R["scratch"], subtract=True)


class PipelineMitad:
    def __init__(self, spec: PWSpec, sesgo: int = 0):
        self.spec = spec
        t = TablaLookupMitad(spec, sesgo)
        self.w, self.offs = t.w, t.offs
        self.fases: list[Fase] = [Normalizar(spec), GiroMitad(spec), t,
                                  HornerMitad(spec, t.w, t.offs),
                                  CopiaC0(spec, t.w, t.offs), Desnormalizar(spec)]
        self.media = FasePorBits()

    def anchos(self) -> dict[str, int]:
        s = self.spec
        return {"x": s.width, "y1": s.out_bits, "flags": s.n_p, "sel": 1,
                "coef": sum(self.w), "scratch": max(self.w)}

    def adapta_o_reajusta(self, max_intentos: int = 8) -> dict[str, int]:
        bits = self.anchos()
        for intento in range(max_intentos):
            try:
                for f in [*self.fases, self.media]:
                    f.adapta(bits)
                return bits
            except ErrorAncho as e:
                log.warning("intento %d: %s", intento, e)
                if e.registro not in ("scratch", "coef", "y1", "flags", "sel"):
                    raise
                bits[e.registro] = e.necesarios
        raise ErrorFase("no converge el reajuste de anchos")

    def construye(self) -> km.Circuit:
        bits = self.adapta_o_reajusta()
        b = km.CircuitBuilder()
        R = {"x": b.create_quantum_register(bits["x"], name="x")}
        for nombre in ("y1", "flags", "sel", "coef", "scratch"):
            R[nombre] = b.alloc_qubits(bits[nombre])
        for f in self.fases:
            f.aplica(b, R, False)
        self.media.aplica(b, R, False)
        for f in reversed(self.fases):
            f.aplica(b, R, True)
        for nombre in ("y1", "flags", "sel", "coef", "scratch"):
            b.free(R[nombre])
        return b.finish_circuit()


if __name__ == "__main__":
    import argparse
    import hashlib
    import time

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--deg", type=int, default=2)
    ap.add_argument("--j", type=int, default=7)
    ap.add_argument("--wc", type=int, default=28)
    ap.add_argument("--dd", type=int, default=13)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--sesgo", type=int, default=0)
    ap.add_argument("--solo-modelo", action="store_true")
    a = ap.parse_args()
    spec = PWSpec(deg=a.deg, j=a.j, wc=a.wc, dd=a.dd)
    max_x = 3 * (2 ** spec.n_p - 2) ** 2
    xs = np.arange(1, max_x + 1, dtype=np.int64)
    t0 = time.time()
    y1, cot = modelo(spec, xs, con_cotas=True, sesgo=a.sesgo)
    err = float(error_relativo(spec, xs, y1).max()) / 2.0 ** -24
    log.info("%s error/tol (dominio completo) = %.4f [%.1fs]", spec, err, time.time() - t0)
    for k, v in cot.items():
        log.info("   %s min=%d max=%d bits %d/%d", k, v["min"], v["max"], v["bits_necesarios"], v["bits_asignados"])
    if not a.solo_modelo:
        circ = PipelineMitad(spec, a.sesgo).construye()
        log.info("circuito: Q=%d T=%d", circ.num_qubits, int(circ.operation_statistics().num_toffoli_like))
        if a.out:
            circ.to_file(str(a.out), format="kmb")
            log.info("sha256 %s", hashlib.sha256(a.out.read_bytes()).hexdigest())
