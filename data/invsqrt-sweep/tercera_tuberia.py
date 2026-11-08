"""Tercera tuberia (idea de Elan): bandera para intermedios SECUENCIALES.
- Un intermedio es secuencial si su ANF se contiene a si mismo (retroalimentacion).
- Cuando se detecta, se pone una BANDERA y ese intermedio NO va por la red de
  ANDs (que explotaria) sino por una TERCERA TUBERIA: se mantiene como qubit
  persistente y se actualiza con XOR (CX, gratis en Toffoli).
- La actualizacion es la parte NO-retroalimentada del ANF: q ^= (resto).
  El termino propio (q23) es el estado anterior, no se calcula.
Uso: python3.13 tercera_tuberia.py
"""
import json
BASE = '/home/hatch/workspace/qcc-data/invsqrt-sweep'
inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))
# q24 no esta en ese archivo; se trazo aparte (14 monomios, 13 en x, uno q19*q23)
q24_monos = None
try:
    q24_monos = json.load(open(f'{BASE}/intermedio_q24.json'))['monomials']
except Exception:
    q24_monos = [['q19','q23']]  # el unico que importa para la cadena (los demas son en x)

def es_secuencial(q, monos):
    """Bandera: True si el ANF contiene al propio intermedio."""
    return any(m == [q] for m in monos)

def parte_no_retro(monos, q):
    """El ANF sin el termino propio (eso es lo que se XOR-ea)."""
    return [m for m in monos if m != [q]]

print("=== BANDERA SECUENCIAL (ANF se contiene a si mismo) ===")
for q in sorted(inter.keys()):
    monos = inter[q]['monomials']
    flag = es_secuencial(q, monos)
    resto = parte_no_retro(monos, q) if flag else monos
    print(f"  {q}: secuencial={flag}  monomios={len(monos)}  resto-a-XOR={resto if flag else '(n/a, funcion pura)'}")

# --- Tercera tuberia: actualizar q23 con XOR (gratis) ---
# q23 ANF: [] , [q20], [q21], [q23]  ->  q23 ^= 1 ^ q20 ^ q21
# En el circuito: X(q23) [constante 1], CX(q20,q23), CX(q21,q23). 0 Toffoli.
print("\n=== TERCERA TUBERIA: actualizacion de q23 (XOR, 0 Toffoli) ===")
print("  q23 ^= 1 ^ q20 ^ q21")
print("  compuertas: X(q23), CX(q20,q23), CX(q21,q23)  ->  0 Toffoli, 0 T")
print("  (la constante 1 es una X; los CX son Clifford, gratis)")

# --- Cadena q23 -> q24 -> q25 -> q26 -> q27 ---
# Una vez actualizado q23, q24 se calcula (su unico termino con q23 es q19*q23:
# 1 AND), luego q25 (depende de q24: q18*q24 = 1 AND), q26 (q17*q25 = 1 AND),
# q27 (q16*q26 = 1 AND). Los demas monomios de q24-q27 son en x (ya contados
# en la capa 1). Costo extra de la cadena secuencial: 4 ANDs.
print("\n=== CADENA SECUENCIAL (despues de actualizar q23) ===")
print("  q24: +1 AND (q19*q23)")
print("  q25: +1 AND (q18*q24)")
print("  q26: +1 AND (q17*q25)")
print("  q27: +1 AND (q16*q26)")
print("  Total cadena secuencial: 4 ANDs (los monomios en x ya estan en capa 1)")
print("\n=== COSTO TOTAL TERCERA TUBERIA ===")
print("  q23 (XOR): 0 Toffoli")
print("  cadena q24-q27: 4 ANDs = 4 Toffoli")
print("  TOTAL: 4 Toffoli  (contra 2433-2641 monomios si se compone q23 a x)")
print("  Ahorro: la retroalimentacion NO se compone; se actualiza con XOR.")
