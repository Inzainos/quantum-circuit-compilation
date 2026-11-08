#!/usr/bin/env python3
"""Valida las ANF trazadas de V34 contra el circuito real simulado (ver docs/VALIDACION_ANF_V34_2026-11-08.md).
Para cada rotacion de rotaciones_anf.json (campo line = indice 0-based de su Z_POW): simula el prefijo del .kmx justo antes de ese Z_POW,
lee el qubit objetivo y lo compara con la ANF evaluada de dos formas: H1 (todas las variables = valor actual del qubit nombrado) y
H3 (qN con N<22 = bit de entrada x; N>=22 = valor actual). Uso: python3.13 tools/validar_anf_v34.py <v34.kmx> <anf.json> [tiros] [H1|H3]
"""
import json, logging, sys, re
import numpy as np
import kickmix as km
log = logging.getLogger("validar_anf")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
kmx, anf = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 256
MODO = sys.argv[4] if len(sys.argv) > 4 else 'H1'
lines = open(kmx).read().split("\n")
rots = json.load(open(anf))
rng = np.random.default_rng(7)
xs = np.concatenate([rng.integers(1, 1 << 22, size=N - 6), [1, 2, 3, (1 << 22) - 1, (1 << 22) - 2, 1 << 21]]).astype(np.int64)
bits_in = ((xs[None, :] >> np.arange(22)[:, None]) & 1) == 1

def prefix_state(L):
    """Estado de todos los qubits tras ejecutar las lineas [0, L-1) (L = indice 0-based de la linea Z_POW; se ejecuta lo anterior)."""
    pre = lines[:L]
    depth = 0
    for l in pre:
        t = l.split(None, 1)[0] if l.strip() else ""
        if t == "PUSH_CONDITION": depth += 1
        elif t == "POP_CONDITION": depth -= 1
    txt = "\n".join(pre + ["POP_CONDITION"] * depth) + "\n"
    open("/tmp/_validar_anf_pre.kmx", "w").write(txt)
    c = km.Circuit.from_file("/tmp/_validar_anf_pre.kmx")
    sim = km.Simulator(batch_size=N, debug_print=False, counting_operations=False, seed=3)
    sim.use_same_registers_as(c)
    sim.write_across_shots(km.array([km.q(i) for i in range(22)]), bits_in)
    sim.do(c)
    return sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))

res = []
for k, r in enumerate(rots):
    L = r["line"]
    tgt_line = lines[L].split()
    st = prefix_state(L)
    q = int(r["qubit"][1:])
    nm = lambda s: int(s[1:])
    par = np.zeros(N, dtype=bool)
    for m in r["monomials"]:
        t = np.ones(N, dtype=bool)
        for v in m:
            t &= (bits_in[nm(v)] if (MODO == 'H3' and nm(v) < 22) else st[nm(v)])
        par ^= t
    if r.get("constant"):
        par ^= True
    objetivo = st[int(tgt_line[1][1:])] if tgt_line[0] == "Z_POW" else None
    acuerdo = float((par == objetivo).mean()) if objetivo is not None else float("nan")
    acuerdo_q = float((par == st[q]).mean())
    log.info("rot %2d linea %5d %s/%s %-5s q=%s monos=%d acuerdo(ANF vs qubit objetivo del Z_POW)=%.3f acuerdo(vs campo qubit)=%.3f",
             k, L, tgt_line[0], tgt_line[1] if len(tgt_line) > 1 else "", r["qubit"], r["qubit"], len(r["monomials"]), acuerdo, acuerdo_q)
    res.append(acuerdo)
log.info("resumen: %d rotaciones, acuerdo minimo=%.3f, con acuerdo==1.0: %d", len(res), np.nanmin(res), sum(1 for a in res if a == 1.0))
