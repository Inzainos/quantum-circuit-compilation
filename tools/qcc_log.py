#!/usr/bin/env python3
"""Structured JSON-lines logging for the QCC pipeline (stdlib only).

Every script in the pipeline logs the same way, from inside, so the
phases of a run are reconstructable later ("radiografía completa"):

    {"ts": ..., "run_id": ..., "script": ..., "phase": ...,
     "status": "start" | "ok" | "error",
     "inputs": {...}, "outputs": {...},
     "duration_s": ..., "error": ...}

Fields:
  ts         ISO-8601 UTC timestamp.
  run_id     One id per process run (env QCC_RUN_ID, else generated).
             Export QCC_RUN_ID from a driver to group child scripts.
  script     Script name (defaults to the caller's module).
  phase      Phase name, e.g. "build", "verify", "write".
  status     "start" (phase began), "ok" (finished), "error" (failed).
  inputs     Dict of inputs: parameters, paths, hashes.
  outputs    Dict of outputs: counts, scores, hashes, file sizes.
  duration_s Seconds the phase took (on "ok"/"error" events).
  error      Error message (on "error" only).

Destination: one JSON object per line appended to
``~/workspace/qcc-data/logs/qcc.jsonl`` (env QCC_LOG_PATH overrides;
QCC_LOG_OFF=1 disables file logging). Events are also echoed through
the standard ``logging`` module so they show up in existing log
streams. Nothing here imports kickmix, JAX or any third-party package.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("qcc_log")

_DEFAULT_PATH = Path.home() / "workspace" / "qcc-data" / "logs" / "qcc.jsonl"

_RUN_ID = os.environ.get("QCC_RUN_ID") or uuid.uuid4().hex[:12]


def get_run_id() -> str:
    """Shared id for this process run (stable within the process)."""
    return _RUN_ID


def get_log_path() -> Path | None:
    """Where JSON lines go, or None when file logging is disabled."""
    if os.environ.get("QCC_LOG_OFF") == "1":
        return None
    return Path(os.environ.get("QCC_LOG_PATH", _DEFAULT_PATH))


def _jsonable(value):
    """Best-effort conversion to JSON-serializable values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def emit(script: str, phase: str, status: str = "ok", inputs=None,
         outputs=None, duration_s: float | None = None,
         error: str | None = None, log_path: Path | None = None) -> dict:
    """Emit one JSON-lines event. Returns the event dict."""
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": _RUN_ID,
        "script": script,
        "phase": phase,
        "status": status,
        "inputs": _jsonable(inputs or {}),
        "outputs": _jsonable(outputs or {}),
    }
    if duration_s is not None:
        event["duration_s"] = round(float(duration_s), 3)
    if error is not None:
        event["error"] = str(error)
    path = log_path if log_path is not None else get_log_path()
    if path is not None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as exc:  # logging must never break the pipeline
            log.warning("qcc_log: no se pudo escribir %s: %s", path, exc)
    log.info("qcc %s/%s %s %s", script, phase, status,
             json.dumps(_jsonable(outputs or {}), ensure_ascii=False)[:400])
    return event


@contextmanager
def phase(script: str, name: str, inputs=None, log_path: Path | None = None):
    """Context manager: emits "start" on entry and "ok"/"error" on exit.

    Usage::

        with qcc_phase("invsqrt_logshift2", "build", {"deg": 2, ...}):
            circ = build(...)
    """
    t0 = time.time()
    emit(script, name, "start", inputs=inputs, log_path=log_path)
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - logged, then re-raised
        emit(script, name, "error", inputs=inputs,
             duration_s=time.time() - t0, error=exc, log_path=log_path)
        raise
    emit(script, name, "ok", inputs=inputs,
         duration_s=time.time() - t0, log_path=log_path)


def emit_outputs(script: str, phase_name: str, outputs, inputs=None,
                 duration_s: float | None = None,
                 log_path: Path | None = None) -> dict:
    """Shortcut: emit a single "ok" event carrying outputs."""
    return emit(script, phase_name, "ok", inputs=inputs, outputs=outputs,
                duration_s=duration_s, log_path=log_path)


# ---------------------------------------------------------------------------
# Instrumentación automática de scripts ("logs en cada script")
# ---------------------------------------------------------------------------
import atexit
import sys
from collections import deque


class _TailHandler(logging.Handler):
    """Guarda las últimas líneas de log del proceso para adjuntarlas al evento final."""

    def __init__(self, maxlen: int = 25):
        super().__init__(level=logging.INFO)
        self.lines = deque(maxlen=maxlen)

    def emit(self, record):  # noqa: D401
        if record.name == "qcc_log":
            return
        try:
            self.lines.append(self.format(record)[:300])
        except Exception:  # noqa: BLE001
            pass


def auto(script_path: str, phase_name: str = "run") -> None:
    """Instrumenta el proceso actual con UNA línea al inicio del bloque __main__.

    Emite ``start`` con argv y, al terminar (atexit), ``ok`` o ``error`` con
    código de salida, duración, memoria pico (MB) y las últimas líneas de log.
    No cambia el comportamiento del script; si algo falla aquí se ignora.
    """
    try:
        script = Path(script_path).stem
        t0 = time.time()
        tail = _TailHandler()
        tail.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        # OJO: no añadir el handler al logger raíz aquí: con handlers presentes,
        # logging.basicConfig() de cada script pasa a ser un no-op y se pierden
        # la consola y los logs de archivo. Se engancha DESPUÉS de basicConfig.
        _orig_basic = logging.basicConfig

        def _basic(*args, **kwargs):
            _orig_basic(*args, **kwargs)
            if tail not in logging.getLogger().handlers:
                logging.getLogger().addHandler(tail)

        logging.basicConfig = _basic
        state = {"exc": None}
        prev_hook = sys.excepthook

        def _hook(tp, val, tb):
            state["exc"] = f"{tp.__name__}: {val}"
            prev_hook(tp, val, tb)

        sys.excepthook = _hook
        inputs = {"argv": sys.argv[1:], "cwd": os.getcwd()}
        emit(script, phase_name, "start", inputs=inputs)

        def _fin():
            try:
                import resource
                peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
            except Exception:  # noqa: BLE001
                peak = None
            out = {"peak_rss_mb": None if peak is None else round(peak, 1),
                   "log_tail": list(tail.lines)}
            if state["exc"]:
                emit(script, phase_name, "error", inputs=inputs, outputs=out,
                     duration_s=time.time() - t0, error=state["exc"])
            else:
                emit(script, phase_name, "ok", inputs=inputs, outputs=out,
                     duration_s=time.time() - t0)

        atexit.register(_fin)
    except Exception:  # noqa: BLE001 - nunca romper el script
        pass
