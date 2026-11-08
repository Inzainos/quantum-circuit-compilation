"""Prueba la condicional (otra bandera): mode auto/min_c/min_q."""
import json, sys
import os as _os, pathlib as _pl
_R = _pl.Path(__file__).resolve().parents[2]  # raiz del repo
sys.path.insert(0, str(_R / 'src'))
if _os.environ.get('KICKMIX_PATH'):  # opcional: ruta del paquete kickmix si no esta instalado
    sys.path.insert(0, _os.environ['KICKMIX_PATH'])
sys.path.insert(0, str(_R / 'verifiers' / 'invsqrt'))
import kickmix as km
from invsqrt_poly import (PolyPhaseBuilder, build_layer1_dynamic,
                          pick_layer1_threshold)

BASE = str(_R / 'data' / 'invsqrt-sweep')
inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))
inter_anf = {q: v['monomials'] for q, v in inter.items()}

print("=== pick_layer1_threshold (q28: Q base 38, C base 1345) ===")
mejor, tabla = pick_layer1_threshold(inter_anf, q_base=38, c_base=1345)
for u, (n_and, n_cache, q_tot, c_tot, qc) in sorted(tabla.items()):
    print(f"  umbral {u:<3}: ANDs={n_and:<3} cache={n_cache:<3} Q={q_tot} C={c_tot} Q*C={qc}")
print(f"  MEJOR UMBRAL: {mejor} (esperado 5)")
assert mejor == 5

def armar():
    b = km.CircuitBuilder()
    x = b.create_quantum_register(22, name="x")
    n2q = {f'q{i}': x[i] for i in range(22)}
    for q in ['q23','q24','q25','q26','q27','q40','q41','q50','q51','q57']:
        n2q[q] = b.create_quantum_register(1, name=q)[0]
    scratch = b.create_quantum_register(4, name="scratch")
    return b, x, scratch, n2q

print("\n=== mode='auto' (debe elegir umbral 5) ===")
b, x, scratch, n2q = armar()
em = PolyPhaseBuilder(b, x, None, scratch)
n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, mode="auto", q_base=38, c_base=1345)
print(f"  ANDs={n_and} cache={n_cache} seqs={seqs} (esperado 56, 2, ['q23'])")
assert (n_and, n_cache, seqs) == (56, 2, ['q23'])
b.finish_circuit()

print("\n=== mode='min_c' (umbral 2: minimiza ANDs) ===")
b, x, scratch, n2q = armar()
em = PolyPhaseBuilder(b, x, None, scratch)
n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, mode="min_c")
print(f"  ANDs={n_and} cache={n_cache} (esperado 35, 16)")
assert (n_and, n_cache) == (35, 16)
b.finish_circuit()

print("\n=== mode='min_q' (umbral 99: sin cache, minimiza Q) ===")
b, x, scratch, n2q = armar()
em = PolyPhaseBuilder(b, x, None, scratch)
n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, mode="min_q")
print(f"  ANDs={n_and} cache={n_cache} (esperado 75, 0)")
assert (n_and, n_cache) == (75, 0)
b.finish_circuit()

print("\nCONDICIONAL OK: la bandera (mode) enruta a la tuberia optima por Q*C.")
