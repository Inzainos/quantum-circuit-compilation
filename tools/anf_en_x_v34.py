#!/usr/bin/env python3
"""Forma algebraica EXACTA en x (22 bits) del qubit objetivo de cada Z_POW de V34: enumera las 2^22 entradas con el simulador
(prefijo del .kmx hasta cada Z_POW) y aplica la transformada de Moebius. Salida: <salida>/rotaciones_x.json (misma forma que rotaciones_anf.json,
monomios en q0..q21, angulo = argumento del Z_POW en el .kmx).
Uso: python3.13 anf_en_x.py <v34.kmx> <rotaciones_anf.json> <salida>
"""
import json, logging, sys, time
from pathlib import Path
import numpy as np
import kickmix as km
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
log = logging.getLogger("anf_en_x")
kmx, anf, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
lines = open(kmx).read().split("\n")
rots = json.load(open(anf))
NV = 22; TOT = 1 << NV; B = 1 << 16
pre_path = "/tmp/_anf_x_pre.kmx"

def valores(L, q):
    depth = 0
    for l in lines[:L]:
        t = l.split(None, 1)[0] if l.strip() else ""
        if t == "PUSH_CONDITION": depth += 1
        elif t == "POP_CONDITION": depth -= 1
    open(pre_path, "w").write("\n".join(lines[:L] + ["POP_CONDITION"] * depth) + "\n")
    c = km.Circuit.from_file(pre_path)
    v = np.zeros(TOT, dtype=bool)
    for s in range(0, TOT, B):
        sim = km.Simulator(batch_size=B, debug_print=False, counting_operations=False, seed=3)
        sim.use_same_registers_as(c)
        xs = np.arange(s, s + B, dtype=np.int64)
        bits = ((xs[None, :] >> np.arange(NV)[:, None]) & 1) == 1
        sim.write_across_shots(km.array([km.q(i) for i in range(NV)]), bits)
        sim.do(c)
        v[s:s + B] = sim.read_across_shots(km.array([km.q(q)]))[0]
    return v

def moebius(v):
    a = v.copy()
    for i in range(NV):
        a.reshape(-1, 2, 1 << i)[:, 1, :] ^= a.reshape(-1, 2, 1 << i)[:, 0, :]
    return a

res = []
t0 = time.time()
for k, r in enumerate(rots):
    L = r["line"]; tok = lines[L].split()
    assert tok[0] == "Z_POW" and tok[1] == r["qubit"], (k, lines[L])
    q = int(tok[1][1:]); ang = float(tok[2])
    a = moebius(valores(L, q))
    idx = np.nonzero(a)[0]
    monos = [[f"q{i}" for i in range(NV) if (m >> i) & 1] for m in idx.tolist()]
    grados = np.bincount([bin(m).count("1") for m in idx.tolist()], minlength=NV + 1)
    log.info("rot %2d %s linea %5d angulo=%.3e monomios_en_x=%d (ANF trazada: %d) grado max=%d  t=%.0fs",
             k, r["qubit"], L, ang, len(monos), r["n_monomials"], int(np.nonzero(grados)[0].max()) if len(idx) else 0, time.time() - t0)
    res.append({"line": L, "qubit": r["qubit"], "angle": ang, "n_monomials": len(monos), "monomials": monos})
json.dump(res, open(out / "rotaciones_x.json", "w"))
log.info("guardado %s", out / "rotaciones_x.json")
