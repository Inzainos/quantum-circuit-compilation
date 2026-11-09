"""Prototipo: un paso de Horner (t1 = c1 + u*c2) con 13 filas.
Compara:
  A (Bennett, como logshift2): por fila init_and + iadd + del_and;
     vuelta: isub + del_and.
  B (carry-save): por fila init_and + XOR al acumulador (gratis);
     al final UNA conversión carry-save -> binario (Wallace + adder);
     vuelta: inversa de la conversión + del_and (gratis).

Se mide Toffoli-like y Q. Si B no gana en un paso, no gana en dos.
Anchos: c1 19 bits, c2 11 bits, u 13 bits (como logshift2, w=[28,19,11]).
"""

import kickmix as km

W_C1, W_C2, DD = 19, 11, 13


def paso_bennett(b, c1, c2, u, tgt, scratch):
    """tgt = c1 + u*c2 con iadd por fila (ida). Devuelve Toffoli aprox."""
    # u_ctl: bit m de u controla la fila que suma c2 desplazado m.
    for m in range(DD):
        terms = [(c2[t], t - m) for t in range(m, W_C2)]
        if not terms:
            continue
        low = min(i for _, i in terms)
        hi = max(i for _, i in terms) + 1
        sources = km.array([q for q, _ in terms])
        products = km.array([scratch[i - low] for _, i in terms])
        b.init_and(u[m], sources, products)
        b.iadd(products, target=tgt[low:hi])
        b.del_and(u[m], sources, products)
    # sumar c1 (constante en registro): iadd directo
    b.iadd(c1, target=tgt)


def main():
    # --- A: Bennett, ida + vuelta ---
    b = km.CircuitBuilder()
    c1 = b.create_quantum_register(W_C1, name="c1")
    c2 = b.create_quantum_register(W_C2, name="c2")
    u = b.create_quantum_register(DD, name="u")
    tgt = b.create_quantum_register(W_C1, name="tgt")
    scratch = b.create_quantum_register(W_C2, name="scratch")
    paso_bennett(b, c1, c2, u, tgt, scratch)
    # vuelta: restar c1 y deshacer filas en orden inverso
    b.isub(c1, target=tgt)
    for m in reversed(range(DD)):
        terms = [(c2[t], t - m) for t in range(m, W_C2)]
        if not terms:
            continue
        low = min(i for _, i in terms)
        hi = max(i for _, i in terms) + 1
        sources = km.array([q for q, _ in terms])
        products = km.array([scratch[i - low] for _, i in terms])
        b.init_and(u[m], sources, products)
        b.isub(products, target=tgt[low:hi])
        b.del_and(u[m], sources, products)
    circA = b.finish_circuit()
    stA = circA.operation_statistics()
    print(f"A Bennett 1 paso ida+vuelta: Q={circA.num_qubits} "
          f"Toffoli={stA.num_toffoli_like} depth={circA.reaction_depth()}")

    # --- B: carry-save, 13 filas + conversión ---
    # Acumulador carry-save: por cada peso, hasta 13 bits acumulados.
    # Se usan 2 registros (s y c) de ancho W_C1 y se reducen con
    # full-adders cuando un peso acumula 3 bits. Para el prototipo se
    # acumula en 2 bits por peso (s, c) con reducción perezosa: cada
    # fila hace XOR a s y el acarreo (s_old AND products) a c.
    b = km.CircuitBuilder()
    c1 = b.create_quantum_register(W_C1, name="c1")
    c2 = b.create_quantum_register(W_C2, name="c2")
    u = b.create_quantum_register(DD, name="u")
    s = b.create_quantum_register(W_C1, name="s")
    c = b.create_quantum_register(W_C1, name="c")
    scratch = b.create_quantum_register(W_C2, name="scratch")
    # c1 va directo a s (XOR gratis, c1 es el primer sumando)
    for i in range(W_C1):
        b.cx(c1[i], s[i])
    for m in range(DD):
        terms = [(c2[t], t - m) for t in range(m, W_C2)]
        if not terms:
            continue
        low = min(i for _, i in terms)
        sources = km.array([q for q, _ in terms])
        products = km.array([scratch[i - low] for _, i in terms])
        b.init_and(u[m], sources, products)
        # Sumar products a (s, c) en carry-save: para cada bit,
        # nuevo_s = s ^ p, nuevo_c = c ^ (s_old & p). El acarreo
        # (s_old & p) necesita un AND temporal por bit.
        for j, (_, i) in enumerate(terms):
            w = i  # peso = índice en s/c (low ya está en el índice)
            # tmp = s[w] AND products[j]; c[w] ^= tmp; luego limpiar
            # tmp ANTES de cambiar s[w] (del_and necesita s[w] original).
            tmp = b.alloc_qubits(1)[0]
            b.init_and(s[w], products[j], tmp)
            b.cx(tmp, c[w])               # c ^= (s_old & p)
            b.del_and(s[w], products[j], tmp)
            b.free(tmp)
            b.cx(products[j], s[w])       # s ^= p
        b.del_and(u[m], sources, products)
    # Conversión: binario = s + (c << 1). Un iadd de (c<<1) a s.
    b.iadd(c, target=s[1:])
    circB = b.finish_circuit()
    stB = circB.operation_statistics()
    print(f"B carry-save 1 paso (ida, sin vuelta): Q={circB.num_qubits} "
          f"Toffoli={stB.num_toffoli_like} depth={circB.reaction_depth()}")
    print()
    print("Nota: B no incluye la vuelta (inversa de conversión + HMR).")
    print("Si B-ida ya supera a A-ida+vuelta, no hay ahorro.")


if __name__ == "__main__":
    main()
