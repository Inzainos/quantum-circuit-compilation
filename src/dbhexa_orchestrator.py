#!/usr/bin/env python3
"""
Orquestador dbhexa para invsqrt (Benchmark I): cada fase llama a una medicion REAL.

FASE -1 (piedra angular): la factorizacion/arquitectura se decide ANTES del bucle.
Cada arquitectura se ajusta una sola vez (tabla de coeficientes en cache):
  * nr : polinomio cubico de 4 tramos + 1 paso de Newton-Raphson (referencia).
  * pw : polinomio de grado `deg` por tramos de ancho 2^-j con QROM + Horner,
         sin Newton-Raphson (src/invsqrt_piecewise.py).

Flujo por candidato (arquitectura + anchos):

  F0 generacion   : se propone un candidato de la rejilla.
  F1 cotas        : modelo de punto fijo instrumentado sobre TODO el dominio
                    [1, max_x]; minimo y maximo exactos por registro (invsqrt es
                    determinista y el dominio es finito: no es una estimacion).
                    Un desbordamiento rechaza el candidato.
  F2 precision    : error relativo maximo / 2^-24 sobre todo el dominio (< margen).
  F3 circuito     : construccion real -> qubits y Toffolis; si no mejora el mejor
                    costo conocido se descarta SIN pasar al verificador.
  F4 verificador  : verify_submission_invsqrt.py oficial (restauracion de x,
                    scratch limpio, fase) sobre el dominio completo, 1 tirada por x
                    (CRIBA). La afirmacion final exige la especificacion completa
                    (64 tiradas por x): ver `comando_verificacion_final` en summary.json.
  F5 record       : solo si F4 paso y Q x toffoli_equivalent baja el record.

Ninguna bandera se levanta sin que su fase haya calculado algo. Todo queda en
orchestrator.log y candidates.jsonl (una linea JSON por candidato).

Uso:
    python src/dbhexa_orchestrator.py --arch pw --out results/fusion_energy/orchestrator
"""

from __future__ import annotations

import argparse
import dataclasses
import itertools
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "verifiers" / "invsqrt"))
sys.path.insert(0, str(ROOT / "src"))

import kickmix as km  # noqa: E402
import invsqrt_piecewise as pw  # noqa: E402
from nr_reference_circuit import Precision, build_nr_circuit  # noqa: E402

VERIFIER = ROOT / "verifiers" / "invsqrt" / "verify_submission_invsqrt.py"
TOL = 2.0 ** -24  # tolerancia relativa (beta = 1)
BASELINE_SCORE = 2070562.565826548  # Q x toffoli_equivalent del baseline (260, 7963.70)

logger = logging.getLogger("dbhexa")


# ═══════════════════════════════════════════════════════════════════════════
# Banderas
# ═══════════════════════════════════════════════════════════════════════════
@dataclasses.dataclass
class Banderas:
    generacion: bool = False
    cotas: bool = False
    precision: bool = False
    circuito: bool = False
    verificador: bool = False
    record: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# Arquitecturas (fase -1)
# ═══════════════════════════════════════════════════════════════════════════
def modelo_nr_con_cotas(n_p: int, prec: Precision, xs: np.ndarray):
    """Igual que `fixed_point_model` de la referencia, devolviendo tambien min/max por registro.

    Lanza OverflowError exactamente cuando lo haria el modelo de referencia.
    """
    width, d, wc, wsq, wz, wp = 2 * n_p + 2, *dataclasses.astuple(prec)
    xs = np.asarray(xs, dtype=np.int64)
    if not ((1 <= xs) & (xs < 2**width)).all():
        raise ValueError("x fuera de [1, 2^(width-1)).")
    cotas: dict[str, dict] = {}

    def anota(nombre: str, v: np.ndarray, asignados: int) -> None:
        mx, mn = int(v.max()), int(v.min())
        cotas[nombre] = {"min": mn, "max": mx, "bits_necesarios": max(mx, 1).bit_length(),
                         "bits_asignados": asignados}

    def bit(v: np.ndarray, i: int) -> np.ndarray:
        return (v >> i) & 1

    def product(rows, operand, out_bits, operand_bits, limit):
        acc = np.zeros_like(xs)
        for ctl, weight in rows:
            e = out_bits - operand_bits + weight
            acc += ctl * (operand << e if e >= 0 else operand >> -e)
        if (acc >= 2**limit).any():
            raise OverflowError("Registro intermedio desbordado.")
        return acc

    s = (width - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
    x_norm = xs << (2 * s)
    top, second, third = bit(x_norm, width - 1), bit(x_norm, width - 2), bit(x_norm, width - 3)
    table = np.array(prec.coefficient_table(), dtype=np.int64)
    c0, c1, c2, c3 = (table[np.where(top == 0, third, 2 + second), j] for j in range(4))
    delta = [(top & third, -1)] + [
        (bit(x_norm, width - 2 - m), -m) for m in range(2, min(d, width - 2) + 1)]
    y0, mult = c0, c3
    for nombre, acc in (("r1", c2), ("r2", c1), ("y0", c0)):
        y0 = mult = acc - product(delta, mult, wc, wc, wc)
        if ((y0 <= 0) | (y0 >= 2**wc)).any():
            raise OverflowError("Intermedio de Horner no cabe en su registro.")
        anota(nombre, y0, wc)
    y = {k: bit(y0, wc - k) for k in range(1, wc + 1)}
    square = np.zeros_like(xs)
    for k in range(1, wc + 1):
        if 2 * k <= wsq:
            square += y[k] << (wsq - 2 * k)
        for l in range(k + 1, wc + 1):
            if k + l - 1 <= wsq:
                square += (y[k] & y[l]) << (wsq - (k + l - 1))
    anota("square", square, wsq)
    m_rows = [(bit(x_norm, i), i - width + 2) for i in range(width)]
    z = product(m_rows, square, wz, wsq, wz + 2)
    anota("z=M*y0^2", z, wz + 2)
    correction = (3 << wz) - z
    anota("3-z", correction, wz + 2)
    p = product([(y[k], -k) for k in range(1, wc + 1)], correction, wp, wz, wp + 1)
    anota("p", p, wp + 1)
    return p << s, cotas


class ArqNR:
    """Referencia: cubico de 4 tramos + Newton-Raphson, anchos `Precision`."""
    nombre = "nr"

    def __init__(self, prec: Precision, n_p: int):
        self.prec, self.n_p = prec, n_p

    def etiqueta(self) -> str:
        p = self.prec
        return f"nr_d{p.delta_bits}_c{p.coef_bits}_sq{p.square_bits}_pr{p.product_bits}_rs{p.result_bits}"

    def descr(self) -> dict:
        return {"arquitectura": "nr", **dataclasses.asdict(self.prec)}

    def out_bits(self) -> int:
        return self.prec.output_bits(self.n_p)

    def modelo(self, xs: np.ndarray):
        return modelo_nr_con_cotas(self.n_p, self.prec, xs)

    def construye(self) -> km.Circuit:
        return build_nr_circuit(self.n_p, prec=self.prec, compute_only=False)


class ArqPW:
    """Sin Newton: polinomio por tramos + QROM + Horner (src/invsqrt_piecewise.py)."""
    nombre = "pw"

    def __init__(self, spec: pw.PWSpec):
        self.spec = spec

    def etiqueta(self) -> str:
        s = self.spec
        return f"pw_deg{s.deg}_j{s.j}_wc{s.wc}_dd{s.dd}"

    def descr(self) -> dict:
        return {"arquitectura": "pw", **dataclasses.asdict(self.spec)}

    def out_bits(self) -> int:
        return self.spec.out_bits

    def modelo(self, xs: np.ndarray):
        return pw.modelo(self.spec, xs, con_cotas=True)

    def construye(self) -> km.Circuit:
        return pw.construye(self.spec)


# ═══════════════════════════════════════════════════════════════════════════
# Orquestador
# ═══════════════════════════════════════════════════════════════════════════
class Orquestador:
    def __init__(self, args: argparse.Namespace, out: Path):
        self.n_p = args.n_p
        self.max_x = 3 * (2**self.n_p - 2) ** 2
        self.xs = np.arange(1, self.max_x + 1, dtype=np.int64)
        self.xs_sub = np.unique(np.concatenate([
            np.arange(1, 4097),
            np.arange(self.max_x - 4096, self.max_x + 1),
            np.arange(1, self.max_x + 1, args.stride),
        ]))
        self.margin = args.margin
        self.out = out
        self.jsonl = out / "candidates.jsonl"
        self.verify_extra = ["--max-x", str(args.verify_max_x), "--shots-per-x", str(args.verify_shots)]
        self.best_proxy = args.beat_qt  # Q x toffolis a superar (estricto)
        self.best_score = args.beat_score  # Q x toffoli_equivalent verificado
        self.best_arq = None
        self.best_kmb: Path | None = None
        self.stats = {"candidatos": 0, "rechazo_precision_subconjunto": 0, "rechazo_desborde": 0,
                      "rechazo_precision": 0, "descartado_costo": 0, "verificados": 0,
                      "verificados_pass": 0, "records": 0}

    def registra(self, d: dict) -> None:
        with self.jsonl.open("a") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    def verifica_oficial(self, kmb: Path) -> dict:
        cmd = [sys.executable, str(VERIFIER), str(kmb), "--n-p", str(self.n_p), *self.verify_extra]
        t = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        try:
            r = json.loads(p.stdout)
        except Exception:
            r = {"status": "ERROR", "error": (p.stderr or p.stdout).strip()[-400:]}
        r["_segundos"] = round(time.time() - t, 1)
        return r

    def _error(self, arq, y1: np.ndarray, xs: np.ndarray) -> float:
        exact = 1.0 / np.sqrt(xs.astype(np.float64))
        approx = y1 / 2.0 ** arq.out_bits()
        return float((np.abs(approx - exact) / exact).max())

    def _cierra(self, reg: dict, fl: Banderas) -> dict:
        reg["banderas"] = dataclasses.asdict(fl)
        self.registra(reg)
        return reg

    def evalua(self, arq) -> dict:
        self.stats["candidatos"] += 1
        fl = Banderas()
        tag = arq.etiqueta()
        reg: dict = {"candidato": arq.descr(), "etiqueta": tag}

        fl.generacion = True  # F0

        # F1a/F2a: rechazo barato sobre un subconjunto (si falla en el subconjunto,
        # falla seguro en el dominio completo: el subconjunto esta contenido en el).
        try:
            y1, _ = arq.modelo(self.xs_sub)
        except (OverflowError, ValueError) as e:
            self.stats["rechazo_desborde"] += 1
            reg.update(estado="RECHAZO_DESBORDE_SUBCONJUNTO", detalle=str(e))
            logger.info("[%s] F1 desborde/invalido en subconjunto: descartado.", tag)
            return self._cierra(reg, fl)
        err_sub = self._error(arq, y1, self.xs_sub)
        if err_sub / TOL >= self.margin:
            self.stats["rechazo_precision_subconjunto"] += 1
            reg.update(estado="RECHAZO_PRECISION_SUBCONJUNTO", err_sobre_tol=err_sub / TOL)
            logger.info("[%s] F2 error/tol=%.3f en subconjunto: descartado.", tag, err_sub / TOL)
            return self._cierra(reg, fl)

        # F1b: cotas exactas sobre TODO el dominio
        try:
            y1, cotas = arq.modelo(self.xs)
        except (OverflowError, ValueError) as e:
            self.stats["rechazo_desborde"] += 1
            reg.update(estado="RECHAZO_DESBORDE", detalle=str(e))
            logger.info("[%s] F1 desborde en dominio completo: descartado.", tag)
            return self._cierra(reg, fl)
        fl.cotas = True
        reg["cotas"] = cotas

        # F2: precision sobre todo el dominio
        err = self._error(arq, y1, self.xs)
        reg["err_sobre_tol"] = err / TOL
        if err / TOL >= self.margin:
            self.stats["rechazo_precision"] += 1
            reg.update(estado="RECHAZO_PRECISION")
            logger.info("[%s] F2 error/tol=%.4f >= margen %.3f: descartado.", tag, err / TOL, self.margin)
            return self._cierra(reg, fl)
        fl.precision = True

        # F3: circuito real
        c = arq.construye()
        q, t = c.num_qubits, int(c.operation_statistics().num_toffoli_like)
        reg.update(qubits=q, toffolis=t, proxy_qt=q * t)
        fl.circuito = True
        logger.info("[%s] F3 Q=%d T=%d Q*T=%d (a superar: %d) err/tol=%.4f",
                    tag, q, t, q * t, self.best_proxy, err / TOL)
        if q * t >= self.best_proxy:
            self.stats["descartado_costo"] += 1
            reg.update(estado="VALIDO_SIN_MEJORA")
            return self._cierra(reg, fl)

        # F4: verificador oficial (criba: 1 tirada por x)
        kmb = self.out / f"invsqrt_{tag}.kmb"
        c.to_file(str(kmb), format="kmb")
        self.stats["verificados"] += 1
        v = self.verifica_oficial(kmb)
        reg["verificador"] = {k: v.get(k) for k in (
            "status", "error", "worst_error_over_tolerance", "worst_x", "verified_shots",
            "num_qubits", "max_toffoli_count", "toffoli_equivalent", "t_count",
            "rotation_count", "circuit_sha256", "_segundos")}
        if v.get("status") != "PASS":
            reg.update(estado="FALLA_VERIFICADOR")
            logger.warning("[%s] F4 el verificador oficial RECHAZA: %s", tag, v.get("error"))
            return self._cierra(reg, fl)
        fl.verificador = True
        self.stats["verificados_pass"] += 1

        # F5: record
        teq = v.get("toffoli_equivalent")
        if teq is None:
            teq = v.get("max_toffoli_count", t) + v.get("t_count", 0) / 4
        score = v.get("num_qubits", q) * teq
        reg["score_q_x_c"] = score
        if score < self.best_score:
            fl.record = True
            self.stats["records"] += 1
            self.best_score, self.best_proxy, self.best_arq, self.best_kmb = score, q * t, arq, kmb
            reg.update(estado="RECORD", mejora_vs_baseline_pct=(BASELINE_SCORE - score) / BASELINE_SCORE * 100)
            logger.info("[%s] F5 NUEVO RECORD (criba 1 tirada/x): Q*C=%.1f (%.2f%% menos que el baseline).",
                        tag, score, reg["mejora_vs_baseline_pct"])
        else:
            reg.update(estado="VERIFICADO_SIN_RECORD")
            logger.info("[%s] F5 verificado pero no baja el record (%.1f >= %.1f).", tag, score, self.best_score)
        return self._cierra(reg, fl)


# ═══════════════════════════════════════════════════════════════════════════
def candidatos(args: argparse.Namespace):
    if args.arch in ("nr", "ambas"):
        for d, c, sq, pr, rs in itertools.product(args.delta, args.coef, args.square, args.product, args.result):
            yield ArqNR(Precision(delta_bits=d, coef_bits=c, square_bits=sq, product_bits=pr, result_bits=rs),
                        args.n_p)
    if args.arch in ("pw", "ambas"):
        for deg, j, wc, rec in itertools.product(args.deg, args.j, args.wc, args.dd_recorte):
            dd = 2 * args.n_p + 2 - 2 - j - rec  # bits de u disponibles bajo el tramo, menos `rec`
            if dd < 1:
                continue
            yield ArqPW(pw.PWSpec(deg=deg, j=j, wc=wc, dd=dd, n_p=args.n_p))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "fusion_energy" / "orchestrator")
    ap.add_argument("--n-p", type=int, default=10)
    ap.add_argument("--arch", choices=("nr", "pw", "ambas"), default="pw")
    # nr
    ap.add_argument("--delta", type=int, nargs="+", default=[13, 14, 15])
    ap.add_argument("--coef", type=int, nargs="+", default=[16, 17, 18])
    ap.add_argument("--square", type=int, nargs="+", default=[26, 27, 28])
    ap.add_argument("--product", type=int, nargs="+", default=[26, 27, 28])
    ap.add_argument("--result", type=int, nargs="+", default=[26, 27, 28])
    # pw
    ap.add_argument("--deg", type=int, nargs="+", default=[2, 3])
    ap.add_argument("--j", type=int, nargs="+", default=[5, 6, 7, 8])
    ap.add_argument("--wc", type=int, nargs="+", default=[27, 28, 29, 30])
    ap.add_argument("--dd-recorte", type=int, nargs="+", default=[0, 1, 2, 3, 4, 5],
                    help="Bits de u que se QUITAN respecto al maximo disponible (menos filas de Horner).")
    ap.add_argument("--margin", type=float, default=1.0,
                    help="Se acepta error/tol < margen (1.0 = el limite del verificador).")
    ap.add_argument("--stride", type=int, default=997, help="Paso del subconjunto de rechazo rapido.")
    ap.add_argument("--beat-qt", type=int, default=254 * 7405,
                    help="Q x toffolis a superar (default: el 27/27/27 ya verificado).")
    ap.add_argument("--beat-score", type=float, default=254 * 7618.122468768528,
                    help="Q x toffoli_equivalent a superar para declarar record.")
    ap.add_argument("--verify-max-x", type=int, default=3133440,
                    help="Multiplo de 256 (requisito del verificador) <= max_x.")
    ap.add_argument("--verify-shots", type=int, default=1)
    args = ap.parse_args()

    run = args.out / time.strftime("run_%Y%m%dT%H%M%S")
    run.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.FileHandler(run / "orchestrator.log"), logging.StreamHandler()],
    )
    logger.info("kickmix=%s | n_p=%d | max_x=%d | arch=%s | salida=%s", getattr(km, "__file__", "?"),
                args.n_p, 3 * (2**args.n_p - 2) ** 2, args.arch, run)

    orq = Orquestador(args, run)
    t0 = time.time()
    for arq in candidatos(args):
        try:
            orq.evalua(arq)
        except Exception:  # un candidato roto no detiene la busqueda, pero queda registrado
            logger.exception("Candidato %s fallo con excepcion", arq.etiqueta())
            orq.registra({"candidato": arq.descr(), "estado": "EXCEPCION"})

    final_cmd = None
    if orq.best_kmb is not None:
        final_cmd = f"python verifiers/invsqrt/verify_submission_invsqrt.py {orq.best_kmb} --n-p {args.n_p}"
    resumen = {
        "segundos": round(time.time() - t0, 1),
        "estadisticas": orq.stats,
        "mejor_candidato": orq.best_arq.descr() if orq.best_arq else None,
        "mejor_score_q_x_c": orq.best_score,
        "mejor_circuito": str(orq.best_kmb) if orq.best_kmb else None,
        "comando_verificacion_final": final_cmd,
        "baseline_score": BASELINE_SCORE,
        "nota": ("El record se declaro con 1 tirada por x (criba). Ejecutar comando_verificacion_final "
                 "(especificacion completa, 64 tiradas por x) antes de afirmarlo."),
    }
    (run / "summary.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False) + "\n")
    logger.info("RESUMEN: %s", json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
