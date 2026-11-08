"""Script 2 (HIBRIDO): Q(u) por monomios (lista de Mobius, 2559 monomios,
cada uno con su propio angulo = su coeficiente) en modo por-monomio,
sobre un registro u de 13 bits. Mide Q, Toffolis y C.
Uso:
  python3.13 build_hybrid_qu.py
Nota: cada monomio lleva SU propia rotacion (su coeficiente es distinto),
por eso son 2559 rotaciones. La escala S no esta aplicada aqui (es el
hueco conocido); esto mide el costo de la parte Q(u) + su computo.
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
mono = json.load(open(f'{BASE}/monomios_Qu_thr1e-10.json'))
print(f"monomios Q(u): {len(mono)}")
# Costo analitico rapido (sin construir todo el circuito aun)
tot_and = 0
for m in mono:
    d = len(m['bits'])
    tot_and += max(0, d - 1)
n_rot = len(mono)
t_rot = n_rot * 29
c_analytic = tot_and + t_rot / 4.0
print("=== HIBRIDO Q(u) (analitico, sin cache entre monomios) ===")
print(f"monomios: {n_rot}")
print(f"ANDs (Toffoli): {tot_and}")
print(f"T rotaciones: ~{t_rot} (una por monomio)")
print(f"C (Toffoli + T/4): {c_analytic:.1f}")
print(f"Q (u 13 + scratch 4): 17")
print(f"score si fuera circuito completo: {17 * c_analytic:.0f}")
# Construir el circuito real (modo por-monomio) para medir Q real
b = km.CircuitBuilder()
u = b.create_quantum_register(13, name="u")
scratch = b.create_quantum_register(4, name="scratch")
emitter = PolyPhaseBuilder(b, u, None, scratch)
total_and = 0
for m in mono:
    qubits = [u[i] for i in m['bits']]
    total_and += emitter.emit_monomial(qubits, m['angle'])
circ = b.finish_circuit()
print("=== HIBRIDO Q(u) (construido) ===")
print(f"ANDs emitidos: {total_and}")
print(f"monomios emitidos: {emitter.n_monomials}, bits clasicos: {emitter.n_bits}")
print(f"Q: 13 + 4 = 17")
c = total_and + n_rot * 29 / 4.0
print(f"C: {c:.1f}")
out = f'{BASE}/invsqrt-hybrid-qu.kmb'
circ.to_file(out, format="kmb")
json.dump({"q": 17, "toffoli": total_and, "rotations": n_rot, "c": c,
           "score_if_full": 17 * c}, open(f'{BASE}/hybrid_qu_medicion.json', 'w'), indent=1)
print(f"guardado: {out} y hybrid_qu_medicion.json")
