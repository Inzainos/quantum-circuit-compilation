"""Compone los intermedios del cluster q28 (ventana ~15012) a bits de x (q0..q21)."""
import json, sys
from collections import defaultdict
sys.path.insert(0, '.')
from trace_back import trace_back, MAX_MONOMIALS

lines = open('invsqrt-public-v34.kmx').read().splitlines()
print(f"lineas totales: {len(lines)}")
rots = json.load(open('rotaciones_anf.json'))
# intermedios del cluster q28 (lineas 15012..15100 aprox): recolectar los qubits
# que aparecen en los monomios y no son x (q0..q21)
xbits = {f"q{i}" for i in range(22)}
inter = set()
for r in rots:
    for m in r["monomials"]:
        for q in m:
            if q not in xbits:
                inter.add(q)
print(f"intermedios distintos en rotaciones_anf.json: {len(inter)}")
# tomar los que aparecen en el cluster q28 (primeras rotaciones)
q28_inter = set()
for r in rots[:16]:
    for m in r["monomials"]:
        for q in m:
            if q not in xbits:
                q28_inter.add(q)
print(f"intermedios del cluster q28: {sorted(q28_inter)}")
# linea de inicio de ventana del cluster q28: la primera rotacion menos 300
line0 = rots[0]["line"] - 300
print(f"ventana cluster q28 inicia en linea {line0}")
# rastrear cada intermedio hacia atras hasta linea 0
result = {}
for q in sorted(q28_inter):
    f, start, status = trace_back(lines, q, line0, back=line0)
    fn = f.get(q, set())
    n_x = sum(1 for m in fn if all(v in xbits for v in m))
    print(f"{q}: {len(fn)} monomios, {n_x} solo en x, status={status}, llego a linea {start}")
    result[q] = {
        "n_monomials": len(fn),
        "n_x_only": n_x,
        "status": status,
        "monomials": [sorted(m) for m in sorted(fn, key=lambda s: (len(s), sorted(s)))],
    }
with open("intermedios_q28_to_x.json", "w") as fh:
    json.dump(result, fh, indent=1)
print("guardado en intermedios_q28_to_x.json")
