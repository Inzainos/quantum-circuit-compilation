"""Mide el costo del RESTO (capa 1: red de intermedios q28 + normalizacion
+ decodificacion de tramo) para decidir si el polinomio cabe en ~1400 de C.
- Capa 1: intermedios q23,q25,q26,q27,q40,q41,q50,q51,q57 (ANF en x).
  Costo = ANDs por clausura de prefijos (productos compartidos entre
  intermedios). q23 tiene retroalimentacion (depende de si mismo) -> no es
  funcion pura de x: se marca como ENTRADA (no se cuenta su computo).
- Normalizacion + decodificacion: estimacion por el ruteo CSWAP del V34
  (201 CSWAP en todo el circuito) y por la normalizacion del LUT.
Uso: python3.13 medir_resto.py
"""
import json
from itertools import combinations

BASE = str(__import__('pathlib').Path(__file__).resolve().parent)
inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))

# --- Clausula de prefijos: todos los productos (ANDs) necesarios ---
# Un monomio de grado d necesita sus prefijos de grado 2..d-1 (los de grado 1
# son los bits mismos, gratis). Compartir = un producto hecho una sola vez.
needed = set()  # frozenset de qubits (producto)
for q, v in inter.items():
    for m in v['monomials']:
        ms = frozenset(m)
        if len(ms) >= 2:
            # todos los prefijos de tamano >=2 (cerradura por prefijos)
            for k in range(2, len(ms) + 1):
                for sub in combinations(sorted(ms), k):
                    needed.add(frozenset(sub))
print("=== CAPA 1: red de intermedios q28 ===")
print(f"intermedios: {sorted(inter.keys())}")
print(f"productos (ANDs) unicos por clausura de prefijos: {len(needed)}")
# Desglose por intermedio (sin compartir, para referencia)
for q, v in sorted(inter.items()):
    monos = v['monomials']
    a_sin = sum(max(0, len(m) - 1) for m in monos)
    print(f"  {q}: {len(monos)} monomios, ANDs sin compartir={a_sin}, status={v.get('status')}, n_x_only={v.get('n_x_only')}")
# q23 es retroalimentacion: su ANF contiene q23 mismo -> no es funcion pura.
q23_monos = inter['q23']['monomials']
print(f"\nq23 ANF: {q23_monos}  <-- contiene q23 mismo (retroalimentacion, no es funcion pura de x)")
print("  -> q23 se trata como ENTRADA (qubit que evoluciona), no se cuenta su computo.")
# ANDs que dependen de q23 (via q24->q25->q26->q27) no se pueden materializar
# sin q23; se cuentan igual en la clausura (son productos con q23/q24/q25/q26).
dep_q23 = [p for p in needed if any(x in ('q23','q24','q25','q26') for x in p)]
print(f"productos que dependen de q23/q24/q25/q26 (cadena con retroalimentacion): {len(dep_q23)}")

# --- Presupuesto ---
C_Q28_OTRO = 1341.0   # medido por el otro agente (cluster q28, C)
C_ACTUAL = 2805.79     # invsqrt logshift2 completo
C_RESTO_MAX = C_ACTUAL - C_Q28_OTRO
print(f"\n=== PRESUPUESTO ===")
print(f"C cluster q28 (otro agente, medido): {C_Q28_OTRO}")
print(f"C invsqrt actual (logshift2): {C_ACTUAL}")
print(f"Resto maximo para NO perder: {C_RESTO_MAX:.1f}")
print(f"Capa 1 (ANDs por clausura, Toffoli): {len(needed)}")
print(f"  -> q28 completo (cluster + capa1): {C_Q28_OTRO + len(needed):.1f}")
print(f"  -> margen que queda para normalizacion + decodificacion + otros clusters: {C_RESTO_MAX - len(needed):.1f}")
print("\nNota: la capa 1 aqui es SOLO los ANDs de los intermedios (sin contar")
print("los qubits extra ni la normalizacion/decodificacion ni los clusters")
print("q50/q41/q40. Si el margen sale negativo, el polinomio NO cabe.")
