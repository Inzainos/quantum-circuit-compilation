#!/usr/bin/env python3
"""Separa data/invsqrt-sweep/rotaciones_anf.json (51 rotaciones trazadas de V34) por acumulador (campo 'qubit').
Escribe <salida>/<qubit>.json, que se mide con:
  python3.13 tools/invsqrt_q28_cost.py --json <salida>/q28.json --tiros 512 --eps 2.434e-13
Uso: python3.13 tools/split_anf_por_qubit.py [salida]   (por defecto data/invsqrt-sweep/anf_por_qubit)
"""
import collections
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("split_anf")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/invsqrt-sweep/anf_por_qubit"
    out.mkdir(parents=True, exist_ok=True)
    rots = json.loads((ROOT / "data/invsqrt-sweep/rotaciones_anf.json").read_text())
    por = collections.defaultdict(list)
    for r in rots:
        por[r["qubit"]].append(r)
    for q, v in sorted(por.items()):
        (out / f"{q}.json").write_text(json.dumps(v))
        log.info("%s: %d rotaciones, %d monomios (con repeticion), %d distintos", q, len(v),
                 sum(r["n_monomials"] for r in v), len({tuple(m) for r in v for m in r["monomials"]}))


if __name__ == "__main__":
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from qcc_log import auto as _a
        _a(__file__)
    except Exception:  # noqa: BLE001
        pass
    main()
