"""Capa 1 con conteo CORRECTO: arbol de prefijos (trie).
Cada monomio de grado d se construye por una cadena de ANDs; los prefijos
comunes se comparten. El costo minimo (para un orden fijo de variables) es
el numero de nodos del trie a profundidad >= 2.
"""
import json
BASE = str(__import__('pathlib').Path(__file__).resolve().parent)
inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))

# Orden canonico de variables (las que mas aparecen primero, para compartir mas)
from collections import Counter
cnt = Counter()
for v in inter.values():
    for m in v['monomials']:
        cnt.update(m)
order = {q: i for i, q in enumerate(sorted(cnt, key=lambda q: -cnt[q]))}
print("orden de variables (por frecuencia):", sorted(cnt, key=lambda q: -cnt[q]))

# Trie
class Node:
    __slots__ = ('ch',)
    def __init__(self): self.ch = {}
root = Node()
n_and = 0
for v in inter.values():
    for m in v['monomials']:
        ms = sorted(set(m), key=lambda q: order[q])
        node = root
        for depth, q in enumerate(ms, start=1):
            if q not in node.ch:
                node.ch[q] = Node()
                if depth >= 2:
                    n_and += 1
            node = node.ch[q]
print(f"\nANDs capa 1 (trie, orden por frecuencia): {n_and}")
# Sin compartir (suma de (grado-1))
sin = sum(max(0, len(m)-1) for v in inter.values() for m in v['monomials'])
print(f"ANDs capa 1 sin compartir: {sin}")

C_Q28_OTRO = 1341.0
C_ACTUAL = 2805.79
print(f"\nC cluster q28 (otro agente): {C_Q28_OTRO}")
print(f"C actual (logshift2): {C_ACTUAL}")
print(f"Resto maximo: {C_ACTUAL - C_Q28_OTRO:.1f}")
print(f"q28 completo (cluster + capa1 trie): {C_Q28_OTRO + n_and:.1f}")
print(f"Margen para normalizacion + decodificacion + otros clusters: {C_ACTUAL - C_Q28_OTRO - n_and:.1f}")
print("\nPendiente (no medido aun): normalizacion, decodificacion de tramo,")
print("clusters q50/q41/q40, y la cadena q23->q24->q25->q26->q27 (retroalimentacion).")
