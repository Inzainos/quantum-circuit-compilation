"""Barrido del umbral de cache: el optimo es por Q*C, no solo por ANDs.
Q base capa 1: 22 x + 10 intermedios + 4 scratch = 36 (sin cache).
C base: cluster q28 1341 + tercera tuberia 4 = 1345 (sin capa 1).
"""
import json, sys
sys.path.insert(0, '/home/hatch/workspace/qcc-zip-final/src')
sys.path.insert(0, '/home/hatch/workspace/qcc-data/kickmix')
sys.path.insert(0, '/home/hatch/workspace/qcc-zip-final/verifiers/invsqrt')
import kickmix as km
from invsqrt_poly import PolyPhaseBuilder, build_layer1_dynamic

BASE = '/home/hatch/workspace/qcc-data/invsqrt-sweep'
inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))
inter_anf = {q: v['monomials'] for q, v in inter.items()}

def medir(umbral):
    b = km.CircuitBuilder()
    x = b.create_quantum_register(22, name="x")
    n2q = {f'q{i}': x[i] for i in range(22)}
    for q in ['q23','q24','q25','q26','q27','q40','q41','q50','q51','q57']:
        n2q[q] = b.create_quantum_register(1, name=q)[0]
    scratch = b.create_quantum_register(4, name="scratch")
    em = PolyPhaseBuilder(b, x, None, scratch)
    n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, cache_threshold=umbral)
    b.finish_circuit()
    return n_and, n_cache

print("umbral | ANDs capa1 | cache Q | Q capa1 | C q28 total | Q*C (q28, Q=38 base)")
print("       |            |         | (36+cache)| (1345+ANDs)  |  (38+cache)*C")
for umbral in [2, 3, 4, 5, 99]:
    n_and, n_cache = medir(umbral)
    q_capa1 = 36 + n_cache
    c_total = 1345 + n_and
    # Q del circuito: max(Q cluster 38, Q capa1). El cluster usa 38 qubits;
    # la capa 1 usa 36+cache. Si cache hace Q capa1 > 38, el pico sube.
    q_pico = max(38, q_capa1)
    print(f"  {umbral:<4} | {n_and:<10} | {n_cache:<7} | {q_capa1:<8} | {c_total:<11} | {q_pico} x {c_total} = {q_pico*c_total}")
print("\nSin cache (estatica): 75 ANDs, 0 cache -> Q=38, C=1420, Q*C=53960")
print("Umbral 2: 35 ANDs, 16 cache -> Q=52, C=1380, Q*C=71760  (peor por Q)")
