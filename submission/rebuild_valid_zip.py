#!/usr/bin/env python3
"""Reconstruye el zip de envio valido (invsqrt halfsplit + dqi v10 + dfthcsos del zip bueno fb4e95b).

Uso (desde la raiz del repo):
    python3 submission/rebuild_valid_zip.py salida/submission.zip [--dfthcsos-commit fb4e95b]

Regenera invsqrt.kmb y dqi.kmb con los scripts del repo, extrae dfthcsos/ del zip
versionado en --dfthcsos-commit y empaqueta todo en la RAIZ del zip. Imprime el sha256
de cada archivo; despues corre los verificadores oficiales sobre esos mismos archivos.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import logging
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("rebuild_valid_zip")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], env: dict) -> None:
    log.info("ejecutando: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output", type=Path)
    ap.add_argument("--dfthcsos-commit", default="fb4e95b",
                    help="commit que contiene submission/submission.zip con dfthcsos/ valido")
    a = ap.parse_args()

    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'verifiers' / 'invsqrt'}:{ROOT / 'src'}"}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        run([sys.executable, "src/invsqrt_halfsplit.py", "--deg", "2", "--j", "8", "--wc", "28", "--dd", "13",
             "--out", str(tmp / "invsqrt.kmb")], env)
        run([sys.executable, "src/dqi_optimized_v10.py", str(tmp / "dqi.kmb"),
             "--m", "4095", "--n", "70", "--degree", "12"], env)
        blob = subprocess.run(["git", "show", f"{a.dfthcsos_commit}:submission/submission.zip"],
                              cwd=ROOT, check=True, capture_output=True).stdout
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(blob)) as old, \
                zipfile.ZipFile(a.output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as out:
            for name in ("invsqrt.kmb", "dqi.kmb"):
                out.write(tmp / name, name)
                log.info("%s sha256=%s", name, sha256(tmp / name))
            for info in old.infolist():
                if info.filename.startswith("dfthcsos/") and not info.is_dir():
                    data = old.read(info.filename)
                    out.writestr(info.filename, data)
                    log.info("%s sha256=%s", info.filename, hashlib.sha256(data).hexdigest())
    log.info("escrito %s (%d bytes)", a.output, a.output.stat().st_size)


if __name__ == "__main__":
    main()
