"""Script 1 (V34): construye el cluster q28 con faseo por bits de fase
(mecanismo V34) y mide Q, Toffolis y C. Uso:
  python3.13 build_v34_q28.py
"""
import json, sys
import os as _os, pathlib as _pl
_R = _pl.Path(__file__).resolve().parents[2]  # raiz del repo
sys.path.insert(0, str(_R / 'src'))
if _os.environ.get('KICKMIX_PATH'):  # opcional: ruta del paquete kickmix si no esta instalado
    sys.path.insert(0, _os.environ['KICKMIX_PATH'])
sys.path.insert(0, str(_R / 'verifiers' / 'invsqrt'))
import kickmix as km
from invsqrt_poly import PolyPhaseBuilder

BASE = str(_R / 'data' / 'invsqrt-sweep')
rots = json.load(open(f'{BASE}/rotaciones_q28_en_x.json'))
# Modelo de costo: x (22) + 5 intermedios como entradas = 27 qubits.
extra = ['q23', 'q24', 'q25', 'q26', 'q40']
qmap = {f'q{i}': i for i in range(22)}
for j, q in enumerate(extra):
    qmap[q] = 22 + j
b = km.CircuitBuilder()
xin = b.create_quantum_register(27, name="x")
scratch = b.create_quantum_register(4, name="scratch")
emitter = PolyPhaseBuilder(b, xin, None, scratch)
total_and = 0
for rot in rots:
    monos = [[xin[qmap[q]] for q in m] for m in rot["monomials"]]
    total_and += emitter.emit_phase_bit(monos, rot["angle"])
circ = b.finish_circuit()
n_rot = len(rots)
t_rot = n_rot * 29  # ~29 T por rotacion sintetizada
c = total_and + t_rot / 4.0
q = 27 + 4
print("=== V34 (cluster q28, modo bit-de-fase) ===")
print(f"rotaciones: {n_rot}")
print(f"monomios emitidos: {emitter.n_monomials}")
print(f"ANDs (Toffoli): {total_and}")
print(f"T rotaciones: ~{t_rot}")
print(f"Q: {q}")
print(f"C (Toffoli + T/4): {c:.1f}")
print(f"score si fuera circuito completo (Q x C): {q * c:.0f}")
print(f"(logshift2: Q=139, C=2805.79, score=390005)")
out = f'{BASE}/invsqrt-poly-q28.kmb'
circ.to_file(out, format="kmb")
json.dump({"q": q, "toffoli": total_and, "rotations": n_rot, "c": c,
           "score_if_full": q * c}, open(f'{BASE}/v34_q28_medicion.json', 'w'), indent=1)
print(f"guardado: {out} y v34_q28_medicion.json")
