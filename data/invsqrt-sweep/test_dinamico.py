"""Compara la capa 1 estatica vs dinamica (q28)."""
import json, sys
sys.path.insert(0, '/home/hatch/workspace/qcc-zip-final/src')
sys.path.insert(0, '/home/hatch/workspace/qcc-data/kickmix')
sys.path.insert(0, '/home/hatch/workspace/qcc-zip-final/verifiers/invsqrt')
import kickmix as km
from invsqrt_poly import PolyPhaseBuilder, build_layer1, build_layer1_dynamic, _topo_order

BASE = '/home/hatch/workspace/qcc-data/invsqrt-sweep'
inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))
inter_anf = {q: v['monomials'] for q, v in inter.items()}
# q24 como entrada (su ANF completa no esta en el JSON)
print("orden topologico:", _topo_order(inter_anf))

def armar():
    b = km.CircuitBuilder()
    x = b.create_quantum_register(22, name="x")
    name_to_qubit = {f'q{i}': x[i] for i in range(22)}
    for q in ['q23','q24','q25','q26','q27','q40','q41','q50','q51','q57']:
        name_to_qubit[q] = b.create_quantum_register(1, name=q)[0]
    scratch = b.create_quantum_register(4, name="scratch")
    return b, x, scratch, name_to_qubit

print("\n=== ESTATICA (build_layer1, sin compartir entre intermedios) ===")
b, x, scratch, n2q = armar()
em = PolyPhaseBuilder(b, x, None, scratch)
n_and, seqs = build_layer1(em, inter_anf, n2q)
print(f"  ANDs: {n_and} | secuenciales: {seqs}")
b.finish_circuit()

print("\n=== DINAMICA (build_layer1_dynamic, cache por reuso >=2) ===")
b, x, scratch, n2q = armar()
em = PolyPhaseBuilder(b, x, None, scratch)
n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, cache_threshold=2)
print(f"  ANDs: {n_and} | qubits de cache: {n_cache} | secuenciales: {seqs}")
circ = b.finish_circuit()
circ.to_file(f'{BASE}/capa1-dinamica.kmb', format="kmb")
print(f"  circuito guardado: capa1-dinamica.kmb")
print(f"\n  (trie estimaba 35 ANDs con compartir total; la estatica da 75)")
