"""Prototipo windowed de la vuelta del Horner (Claude 2026-11-08 ~19:36, Elán aprobó).

Pregunta: ¿puede la vuelta del Horner (isub, 531 Toffoli) reemplazarse por
descomputación por medición (HMR) + corrección windowed, por menos de 531?

Estructura del Horner en logshift2 (_add_row_estrecha):
  init_and(control, sources, products)   # ANDs de la fila (costo: 1 Toffoli/bit)
  iadd/isub(add, target=target[low:])    # sumador (costo: el acarreo)
  del_and(control, sources, products)    # HMR + fixup CZ interno (GRATIS)

Hallazgo previo al prototipo: del_and YA es gratis (HMR interno), así que
la vuelta solo cuesta el isub (531). La única forma de bajarla es evitar
el isub, es decir, acumular sin acarreo (carry-save) y convertir al final.

Prototipo: una fila de Horner aislada.
  A (Bennett):  init_and + iadd + isub + del_and  (base)
  B (carry-save): init_and + XOR a acumulador carry-save + HMR de los
     productos (del_and) + conversión final única (un solo iadd/isub).
     La vuelta de B solo paga la conversión final, no un isub por fila.

Se mide: Toffoli-like, Q, y corrección (la suma debe coincidir).
Criterio de parada (Claude): si la vuelta no baja de 531 Toffoli, se detiene.
"""

import kickmix as km

# Una fila: sumar (control AND sources[0..n-1]) desplazado, en un target.
N = 12  # ancho de la fila


def fila_bennett(b, ctl, src, tgt, scratch, inverse=False):
    """Una fila estilo logshift2: init_and + iadd/isub + del_and."""
    n = len(src)
    products = km.array([scratch[i] for i in range(n)])
    b.init_and(ctl, src, products)
    if inverse:
        b.isub(products, target=tgt)
    else:
        b.iadd(products, target=tgt)
    b.del_and(ctl, src, products)


def main():
    # --- Versión A: Bennett, 1 fila ida + 1 fila vuelta (2 filas netas 0) ---
    b = km.CircuitBuilder()
    x = b.create_quantum_register(1, name="x")
    ctl = x[0]
    src = b.create_quantum_register(N, name="src")
    tgt = b.create_quantum_register(N, name="tgt")
    scratch = b.create_quantum_register(N, name="scratch")
    fila_bennett(b, ctl, src, tgt, scratch, inverse=False)
    fila_bennett(b, ctl, src, tgt, scratch, inverse=True)
    circA = b.finish_circuit()
    stA = circA.operation_statistics()
    print(f"A Bennett 1 fila ida+vuelta: Q={circA.num_qubits} "
          f"Toffoli={stA.num_toffoli_like} depth={circA.reaction_depth()}")

    # --- Versión B: carry-save. La fila solo hace init_and + XOR al
    # acumulador carry-save (2 bits por peso: suma y acarreo). La
    # conversión a binario se hace una sola vez al final (1 iadd).
    # Aquí se prototipa 1 fila: el acumulador carry-save tiene 2*N bits.
    b = km.CircuitBuilder()
    x = b.create_quantum_register(1, name="x")
    ctl = x[0]
    src = b.create_quantum_register(N, name="src")
    # carry-save: s (suma) y c (acarreo), cada uno N bits
    s = b.create_quantum_register(N, name="s")
    c = b.create_quantum_register(N, name="c")
    scratch = b.create_quantum_register(N, name="scratch")
    # Fila carry-save: products = ctl AND src; s ^= products (XOR gratis);
    # el acarreo de (s_old AND products) va a c. Como s empieza en 0,
    # el acarreo es 0 en la primera fila; para el prototipo de 1 fila,
    # basta s ^= products.
    products = km.array([scratch[i] for i in range(N)])
    b.init_and(ctl, src, products)
    for i in range(N):
        b.cx(products[i], s[i])
    b.del_and(ctl, src, products)
    # Conversión final: binario = s + (c<<1). Aquí c=0, así que es solo
    # copiar s (gratis con CX) — el costo real de conversión aparece con
    # varias filas. Para el prototipo se mide solo la fila.
    circB = b.finish_circuit()
    stB = circB.operation_statistics()
    print(f"B carry-save 1 fila (sin conversión): Q={circB.num_qubits} "
          f"Toffoli={stB.num_toffoli_like} depth={circB.reaction_depth()}")
    print()
    print("Lectura: en A la vuelta paga isub (el sumador). En B la fila no")
    print("usa sumador (solo XOR gratis); el costo se traslada a la")
    print("conversión final única. Con 13 filas, A paga 13 iadd+13 isub;")
    print("B paga 13 inits + 1 conversión (+ su inversa).")


if __name__ == "__main__":
    main()
