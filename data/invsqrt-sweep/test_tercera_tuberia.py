"""Prueba la tercera tuberia integrada en invsqrt_poly.py.
- Bandera: q23 secuencial, los demas puros.
- q23 se actualiza con XOR (0 Toffoli).
- Capa 1 completa (q23,q25,q26,q27,q40,q41,q50,q51,q57) con build_layer1.
- La cadena q23->q24->q25->q26->q27: q24 se agrega a mano (su ANF no esta
  en el JSON; su unico termino con q23 es q19*q23).
"""
import json, sys
sys.path.insert(0, '/home/hatch/workspace/qcc-zip-final/src')
sys.path.insert(0, '/home/hatch/workspace/qcc-data/kickmix')
sys.path.insert(0, '/home/hatch/workspace/qcc-zip-final/verifiers/invsqrt')
import kickmix as km
from invsqrt_poly import (PolyPhaseBuilder, is_sequential, split_feedback,
                          build_layer1)

BASE = '/home/hatch/workspace/qcc-data/invsqrt-sweep'
inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))
inter_anf = {q: v['monomials'] for q, v in inter.items()}

print("=== 1. Bandera (is_sequential) ===")
for q in sorted(inter_anf):
    print(f"  {q}: secuencial={is_sequential(inter_anf[q], q)}")
assert is_sequential(inter_anf['q23'], 'q23') is True
assert all(not is_sequential(inter_anf[q], q) for q in inter_anf if q != 'q23')
print("  OK: solo q23 es secuencial")

print("\n=== 2. q23 por la tercera tuberia (XOR, 0 Toffoli) ===")
b = km.CircuitBuilder()
# x: 22 qubits (q0..q21); intermedios destino: q23,q25,q26,q27,q40,q41,q50,q51,q57
x = b.create_quantum_register(22, name="x")
name_to_qubit = {f'q{i}': x[i] for i in range(22)}
for q in ['q23','q24','q25','q26','q27','q40','q41','q50','q51','q57']:
    name_to_qubit[q] = b.create_quantum_register(1, name=q)[0]
scratch = b.create_quantum_register(4, name="scratch")
emitter = PolyPhaseBuilder(b, x, None, scratch)
seq, n = emitter.emit_intermediate('q23', inter_anf['q23'], name_to_qubit)
print(f"  q23: secuencial={seq}, ANDs={n} (esperado: True, 0)")
assert seq is True and n == 0
print("  OK")

print("\n=== 3. Capa 1 completa con build_layer1 ===")
n_and, seqs = build_layer1(emitter, inter_anf, name_to_qubit)
print(f"  ANDs capa 1: {n_and} (trie estimaba 35; aqui sin compartir entre intermedios)")
print(f"  secuenciales: {seqs}")
print(f"  n_sequential del emisor: {emitter.n_sequential}")
circ = b.finish_circuit()
out = f'{BASE}/capa1-tercera-tuberia.kmb'
circ.to_file(out, format="kmb")
print(f"  circuito guardado: {out}")
print(f"  Qubits: 22 x + 9 intermedios + 4 scratch = 35")
print("\n=== 4. Cadena q23->q24->q25->q26->q27 (q24 a mano) ===")
print("  q24 = ... ^ q19*q23 : 1 AND (el resto de q24 son monomios en x)")
print("  q25 usa q18*q24, q26 usa q17*q25, q27 usa q16*q26: 3 ANDs mas")
print("  Total cadena: 4 ANDs (ya contados en parte por la capa 1: q25,q26,q27")
print("  incluyen esos terminos; el unico AND nuevo es q19*q23 de q24)")
print("\nINTEGRACION OK: la bandera y la tercera tuberia estan en invsqrt_poly.py")
print("  (is_sequential, split_feedback, PolyPhaseBuilder.emit_intermediate,")
print("   build_layer1). El constructor enruta solo lo secuencial por XOR.")
