#!/usr/bin/env python3
"""Perfilador estatico por etiquetas de un circuito kickmix (.kmx de texto, o .kmb que se convierte con to_file).

Lee en streaming (los circuitos pesan GB) y atribuye cada instruccion Toffoli-like (CCX, CCZ, CSWAP) a la pila de
etiquetas INFO_TAG "@enter:x" / "@exit:x". Reporta por ruta de etiquetas: Toffolis incondicionales (siempre
ejecutados) y condicionados (con 'if b..': solo cuentan cuando el bit clasico es 1), inclusivo y exclusivo.
Es conteo ESTATICO (no sabe que ramas se ejecutan por tiro): usar para ver donde esta el costo; el T oficial es el
medio por tiro del simulador. Los circuitos propios pueden anadir etiquetas con builder.info_tag("@enter:nombre").
Uso: python tools/kmx_profile.py circuito.kmb|kmx [--profundidad 3] [--top 40]   Log: logs/kmx_profile.log
"""
import sys, argparse, logging, collections, tempfile, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TOF = ("CCX ", "CCZ ", "CSWAP ")
log = logging.getLogger("kmx_profile")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("circuito")
    ap.add_argument("--profundidad", type=int, default=3); ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "kmx_profile.log", mode="w")])
    path = a.circuito; tmp = None
    if path.endswith(".kmb"):
        import kickmix as km
        tmp = tempfile.NamedTemporaryFile(suffix=".kmx", delete=False); tmp.close()
        km.Circuit.from_file(path).to_file(tmp.name); path = tmp.name
    incond = collections.Counter(); cond = collections.Counter()   # clave: tupla de la pila (ruta completa)
    pila = []; total_i = total_c = 0
    with open(path, "r") as f:
        for linea in f:
            if linea.startswith("INFO_TAG"):
                t = linea.split('"')[1]
                if t.startswith("@enter:"): pila.append(t[7:])
                elif t.startswith("@exit:") and pila: pila.pop()
                continue
            if linea.startswith(TOF):
                if " if " in linea: cond[tuple(pila)] += 1; total_c += 1
                else: incond[tuple(pila)] += 1; total_i += 1
    if tmp: os.unlink(tmp.name)
    log.info("TOTAL toffoli-like estatico: incondicionales=%d  condicionados=%d", total_i, total_c)
    def agrega(cnt, prof):
        out = collections.Counter()
        for k, v in cnt.items(): out[k[:prof]] += v      # inclusivo hasta la profundidad pedida
        return out
    for prof in range(1, a.profundidad + 1):
        inc = agrega(incond, prof); con = agrega(cond, prof)
        claves = sorted(set(inc) | set(con), key=lambda k: -(inc[k] + con[k]))[: a.top]
        log.info("--- profundidad %d (ruta: incond | cond | %% del total) ---", prof)
        for k in claves:
            log.info("%-70s %10d | %9d | %5.1f%%", "/".join(k) or "(sin etiqueta)", inc[k], con[k],
                     100.0 * (inc[k] + con[k]) / max(1, total_i + total_c))
if __name__ == "__main__":
    main()
