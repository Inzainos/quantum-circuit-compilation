#!/usr/bin/env python3
"""
Arquitectura "sin Newton" para invsqrt (Benchmark I): polinomio por tramos + Horner.

Idea (fase -1, la factorizacion como piedra angular): en vez de un polinomio
cubico de 4 tramos seguido de un paso de Newton-Raphson (que es ~60 % de los
Toffolis), se usa un polinomio de grado `deg` sobre tramos de ancho 2^-j
alineados a los bits de x_norm. Los coeficientes se cargan con un QROM
(`init_lookup`) y se evaluan con Horner. No hay `y0^2`, `M*y0^2` ni `y0*(3-z)`.

Convenciones (identicas al circuito de referencia, para reusar sus etapas):
  * x_norm = x * 4^s en [2^(w-2), 2^w), w = 2*n_p + 2.  M = x_norm / 2^(w-2) en [1, 4).
  * y1 = p * 2^s con  y1 / 2^F ~= 1/sqrt(x),  F = wc + n_p,  p = c0 (wc bits),
    c0 / 2^wc ~= 1/sqrt(M).
  * Tramo A = x_norm >> (w-2-j)  (j+2 bits), de ancho 2^-j en M; validos
    A en [2^j, 4*2^j).  u = bits siguientes de x_norm, u in [0,1) con pesos 2^-m.
  * p(u) = a0 - a1 u + a2 u^2 - a3 u^3 + ...   (signos alternos, coeficientes
    en magnitud) -> Horner:  c_i = a_i - c_{i+1} * u   (restas con filas AND-suma).
  * El coeficiente a_i es ~2^(-i*j): su registro mide menos bits (w_i).

Modelo clasico (`modelo`) y circuito (`construye`) comparten la misma aritmetica
entera; el verificador oficial es el arbitro final.
"""

from __future__ import annotations

import dataclasses
import functools
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "verifiers" / "invsqrt"))

import kickmix as km  # noqa: E402
from nr_reference_circuit import (  # noqa: E402
    _add_row,
    _denormalize,
    _normalize,
    _phase_by_bits,
)


@dataclasses.dataclass(frozen=True)
class PWSpec:
    """Parametros de la arquitectura por tramos."""
    deg: int = 3        # grado del polinomio
    j: int = 5          # ancho de tramo 2^-j  (tramos validos: 3 * 2^j)
    wc: int = 28        # bits fraccionarios de coeficientes (= ancho de c0 = bits de p)
    dd: int = 22        # bits de u usados en Horner (filas por paso)
    n_p: int = 10

    @property
    def width(self) -> int:
        return 2 * self.n_p + 2

    @property
    def out_bits(self) -> int:
        return self.wc + self.n_p

    def etiqueta(self) -> str:
        return f"PW(d={self.deg},j={self.j},wc={self.wc},dd={self.dd})"


@functools.lru_cache(maxsize=None)
def tabla_coeficientes(spec: PWSpec) -> tuple[list[list[int]], list[int]]:
    """(En cache: el ajuste se hace UNA vez por arquitectura.)

    Devuelve (b[i][A], w[i]): magnitudes enteras (unidades 2^-wc) por tramo A y ancho por grado i.

    Interpolacion en nodos de Chebyshev (casi minimax) de f(u) = (M0 + h u)^(-1/2),
    con signos alternos verificados. Para A < 2^j (tramos inalcanzables) la entrada es 0.
    """
    d, j, wc = spec.deg, spec.j, spec.wc
    h = 2.0 ** -j
    n_addr = 1 << (j + 2)
    k = np.arange(d + 1)
    nodes = (np.cos((2 * k + 1) * np.pi / (2 * (d + 1))) + 1) / 2  # u en (0,1)
    vander = np.vander(nodes, d + 1, increasing=True)
    b = [[0] * n_addr for _ in range(d + 1)]
    for A in range(1 << j, n_addr):
        m0 = A * h
        coefs = np.linalg.solve(vander, (m0 + h * nodes) ** -0.5)
        for i in range(d + 1):
            expected_sign = 1.0 if i % 2 == 0 else -1.0
            if coefs[i] * expected_sign <= 0:
                raise ValueError(f"Signos no alternan en A={A}, grado {i}: {coefs}")
            mag = int(round(abs(coefs[i]) * 2**wc))
            if i == 0:
                mag = min(mag, 2**wc - 1)  # x=4^s da 1/sqrt(M)=1 exacto: satura 1 ulp
            b[i][A] = mag
    w = [max(max(row).bit_length(), 1) for row in b]
    return b, w


def modelo(spec: PWSpec, xs: np.ndarray, con_cotas: bool = False):
    """y1 de la arquitectura (entero) para cada x; lanza OverflowError si un registro desborda."""
    width, n_p, d, j, wc, dd = spec.width, spec.n_p, spec.deg, spec.j, spec.wc, spec.dd
    if dd > width - 2 - j:
        raise ValueError("dd excede los bits disponibles bajo el tramo.")
    xs = np.asarray(xs, dtype=np.int64)
    b, w = tabla_coeficientes(spec)
    cotas: dict[str, dict] = {}

    def anota(nombre: str, v: np.ndarray, asignados: int) -> None:
        mx, mn = int(v.max()), int(v.min())
        cotas[nombre] = {"min": mn, "max": mx, "bits_necesarios": max(mx, 1).bit_length(),
                         "bits_asignados": asignados}

    s = (width - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
    x_norm = xs << (2 * s)
    A = x_norm >> (width - 2 - j)
    tab = [np.array(row, dtype=np.int64) for row in b]
    c = {i: tab[i][A] for i in range(d + 1)}  # carga del QROM
    u_bits = [(m, (x_norm >> (width - 2 - j - m)) & 1) for m in range(1, dd + 1)]
    for i in range(d - 1, -1, -1):
        acc = c[i]
        prod = np.zeros_like(xs)
        for m, ctl in u_bits:
            prod += ctl * (c[i + 1] >> m)
        acc = acc - prod
        if ((acc < 0) | (acc >= 2 ** w[i])).any():
            raise OverflowError(f"c{i} no cabe en su registro de {w[i]} bits.")
        c[i] = acc
        if con_cotas:
            anota(f"c{i}", acc, w[i])
    y1 = c[0] << s
    return (y1, cotas) if con_cotas else y1


def error_relativo(spec: PWSpec, xs: np.ndarray, y1: np.ndarray) -> np.ndarray:
    exact = 1.0 / np.sqrt(np.asarray(xs, dtype=np.float64))
    approx = y1 / 2.0 ** spec.out_bits
    return np.abs(approx - exact) / exact


def construye(spec: PWSpec) -> km.Circuit:
    """Circuito completo (computa, fasea, descomputa) listo para el verificador oficial."""
    width, n_p, d, j, wc, dd = spec.width, spec.n_p, spec.deg, spec.j, spec.wc, spec.dd
    b, w = tabla_coeficientes(spec)
    offs = [sum(w[:i]) for i in range(d + 1)]
    n_addr = 1 << (j + 2)
    table = [sum(b[i][A] << offs[i] for i in range(d + 1)) for A in range(n_addr)]

    builder = km.CircuitBuilder()
    x = builder.create_quantum_register(width, name="x")
    y1 = builder.alloc_qubits(spec.out_bits)
    flags = builder.alloc_qubits(n_p)
    coef = builder.alloc_qubits(sum(w))
    c = [coef[offs[i]:offs[i] + w[i]] for i in range(d + 1)]
    scratch = builder.alloc_qubits(max(w))
    address = x[width - 2 - j:width]
    u_ctl = [(m, x[width - 2 - j - m]) for m in range(1, dd + 1)]

    def horner(inverse: bool) -> None:
        order = range(0, d) if inverse else range(d - 1, -1, -1)
        for i in order:
            for m, ctl in (reversed(u_ctl) if inverse else u_ctl):
                terms = [(c[i + 1][t], t - m) for t in range(m, w[i + 1])]
                if terms:
                    _add_row(builder, inverse, ctl, terms, c[i], scratch, subtract=True)

    def computa(inverse: bool) -> None:
        if not inverse:
            with builder.mark("normalize"):
                _normalize(builder, False, x, flags)
            with builder.mark("lookup"):
                builder.init_lookup(table=table, address=address, target=coef)
            with builder.mark("horner"):
                horner(False)
            builder.cx(c[0], y1[:wc])
            with builder.mark("denormalize"):
                _denormalize(builder, False, flags, y1)
        else:
            with builder.mark("denormalize"):
                _denormalize(builder, True, flags, y1)
            builder.cx(c[0], y1[:wc])
            with builder.mark("horner"):
                horner(True)
            with builder.mark("lookup"):
                builder.del_lookup(table=table, address=address, target=coef)
            with builder.mark("normalize"):
                _normalize(builder, True, x, flags)

    computa(False)
    _phase_by_bits(builder, y1)
    computa(True)
    for reg in (y1, flags, coef, scratch):
        builder.free(reg)
    return builder.finish_circuit()


def metricas_circuito(circ: km.Circuit) -> tuple[int, int]:
    return circ.num_qubits, int(circ.operation_statistics().num_toffoli_like)


if __name__ == "__main__":
    import argparse
    import time

    ap = argparse.ArgumentParser()
    ap.add_argument("--deg", type=int, default=3)
    ap.add_argument("--j", type=int, default=5)
    ap.add_argument("--wc", type=int, default=28)
    ap.add_argument("--dd", type=int, default=0, help="0 = todos los bits disponibles bajo el tramo")
    ap.add_argument("--out", type=Path, default=None, help="Escribe el .kmb aqui")
    a = ap.parse_args()
    spec = PWSpec(deg=a.deg, j=a.j, wc=a.wc, dd=a.dd or (2 * 10 + 2 - 2 - a.j))
    max_x = 3 * (2 ** spec.n_p - 2) ** 2
    xs = np.arange(1, max_x + 1, dtype=np.int64)
    t = time.time()
    y1, cot = modelo(spec, xs, con_cotas=True)
    err = float(error_relativo(spec, xs, y1).max()) / 2.0 ** -24
    print(f"{spec.etiqueta()}  error/tol (dominio completo) = {err:.4f}   [{time.time()-t:.1f}s]")
    for k, v in cot.items():
        print(f"   {k}: min={v['min']} max={v['max']} bits {v['bits_necesarios']}/{v['bits_asignados']}")
    circ = construye(spec)
    q, tf = metricas_circuito(circ)
    print(f"circuito: Q={q} Toffolis={tf}  (referencia 27/27/27: Q=254 T=7405)")
    if a.out:
        circ.to_file(str(a.out), format="kmb")
        print("escrito", a.out)
