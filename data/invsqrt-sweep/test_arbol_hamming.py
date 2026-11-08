"""Prueba aislada del árbol de peso Hamming (Wallace tree, Boyar-Peralta).

Un full-adder (3 bits del mismo peso -> suma del mismo peso + acarreo
del doble de peso) con 2 Toffolis (2 half-adders: c1=a&b, c2=s1&cin,
cout=c1^c2; sum=a^b^cin con CXs). Un half-adder (2 bits -> suma + acarreo)
con 1 Toffoli.

El árbol reduce n bits de peso 1 al conteo binario (peso Hamming) en
n - hw(n) ANDs (Boyar-Peralta 2008). Para n=49: 46 ANDs.

Se prueba con n=49 bits aleatorios: el conteo debe ser exacto y todos
los qubits temporales deben quedar en 0 tras deshacer el árbol.
"""
import sys
import os

sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")

import numpy as np
import kickmix as km


def half_adder(b, a, c):
    """Half-adder: a,b -> sum (en a, in-place) y carry (qubit nuevo c).
    c debe estar en |0>. Costo: 1 Toffoli (init_and)."""
    b.init_and(a, c, c)  # placeholder, se redefine abajo
    raise NotImplementedError


def build_full_adder(b, a, bb, cin):
    """Full-adder sobre (a, bb, cin). Devuelve (sum_q, cout_q), qubits nuevos.
    a, bb, cin NO se modifican. Costo: 2 Toffolis.
    sum = a^bb^cin (CXs). cout = (a&bb) ^ ((a^bb)&cin)."""
    # s1 = a ^ bb (temporal)
    s1 = b.alloc_qubits(1)[0]
    b.cx(a, s1)
    b.cx(bb, s1)
    # c1 = a & bb
    c1 = b.alloc_qubits(1)[0]
    b.init_and(a, bb, c1)
    # c2 = s1 & cin
    c2 = b.alloc_qubits(1)[0]
    b.init_and(s1, cin, c2)
    # cout = c1 ^ c2 (en c1)
    b.cx(c2, c1)
    # limpiar c2 (del_and) y s1 (CXs inversos)
    b.del_and(s1, cin, c2)
    b.cx(bb, s1)
    b.cx(a, s1)
    b.free(c2)
    b.free(s1)
    # sum = a ^ bb ^ cin (nuevo qubit)
    sum_q = b.alloc_qubits(1)[0]
    b.cx(a, sum_q)
    b.cx(bb, sum_q)
    b.cx(cin, sum_q)
    return sum_q, c1


def build_half_adder(b, a, bb):
    """Half-adder sobre (a, bb). Devuelve (sum_q, cout_q), qubits nuevos.
    Costo: 1 Toffoli."""
    cout_q = b.alloc_qubits(1)[0]
    b.init_and(a, bb, cout_q)
    sum_q = b.alloc_qubits(1)[0]
    b.cx(a, sum_q)
    b.cx(bb, sum_q)
    return sum_q, cout_q


def hamming_weight_tree(b, bits):
    """Reduce `bits` (todos peso 1) al conteo binario (LSB primero).
    Devuelve la lista de qubits del conteo. Registra las operaciones para
    poder deshacerlas (el árbol es reversible: se deshace en orden inverso
    revirtiendo cada adder). Por simplicidad, aquí solo construimos hacia
    adelante y devolvemos también la lista de (tipo, qubits) para el reverso.
    """
    # columnas por peso: peso -> lista de qubits
    from collections import defaultdict
    cols = defaultdict(list)
    cols[0] = list(bits)
    ops = []  # (kind, a, bb, cin, sum_q, cout_q) para deshacer
    w = 0
    while True:
        # buscar el peso más bajo con >=2 bits (procesar de menor a mayor)
        ws = sorted([k for k, v in cols.items() if len(v) >= 2])
        if not ws:
            break
        w = ws[0]
        lst = cols[w]
        if len(lst) >= 3:
            a, bb, cin = lst.pop(), lst.pop(), lst.pop()
            sum_q, cout_q = build_full_adder(b, a, bb, cin)
            ops.append(("FA", a, bb, cin, sum_q, cout_q))
            cols[w].append(sum_q)
            cols[w + 1].append(cout_q)
        else:  # exactamente 2
            a, bb = lst.pop(), lst.pop()
            sum_q, cout_q = build_half_adder(b, a, bb)
            ops.append(("HA", a, bb, None, sum_q, cout_q))
            cols[w].append(sum_q)
            cols[w + 1].append(cout_q)
    # conteo: un bit por peso, de menor a mayor
    maxw = max(cols.keys())
    count = []
    for w in range(maxw + 1):
        if cols[w]:
            assert len(cols[w]) == 1, f"peso {w} tiene {len(cols[w])} bits"
            count.append(cols[w][0])
    return count, ops


def undo_tree(b, ops):
    """Deshace el árbol en orden inverso. Cada adder se revierte:
    FA: deshacer sum (CXs), deshacer cout (revertir el majority), liberar.
    Como los adders se construyeron con init_and/del_and y CXs, el reverso
    es: repetir las CXs de sum, y para cout: re-aplicar la construcción
    inversa. Más simple: reconstruir el mismo adder y luego aplicar su
    inverso no es trivial; en su lugar, deshacemos usando del_and/CXs
    en orden inverso a la construcción.
    """
    # El reverso de build_full_adder(a,bb,cin)->(sum_q,cout_q):
    # - sum_q se hizo con CX(a,sum),CX(bb,sum),CX(cin,sum): revertir con las
    #   mismas CXs (son su propio inverso).
    # - cout_q (=c1) se hizo: s1=a^bb (CXs), c1=a&bb (init_and),
    #   c2=s1&cin (init_and), CX(c2,c1), del_and(s1,cin,c2), CXs para limpiar s1.
    #   Para deshacer cout: revertir en orden inverso.
    for kind, a, bb, cin, sum_q, cout_q in reversed(ops):
        if kind == "HA":
            # sum_q: CX(a,sum),CX(bb,sum) -> revertir igual
            b.cx(bb, sum_q)
            b.cx(a, sum_q)
            # cout_q: init_and(a,bb,cout) -> del_and
            b.del_and(a, bb, cout_q)
            b.free(sum_q)
            b.free(cout_q)
        else:
            # sum_q: CX(a,sum),CX(bb,sum),CX(cin,sum) -> revertir
            b.cx(cin, sum_q)
            b.cx(bb, sum_q)
            b.cx(a, sum_q)
            b.free(sum_q)
            # cout_q: reconstruir los pasos inversos.
            # Paso inverso de "CX(c2,c1) + del_and(s1,cin,c2) + limpiar s1":
            # Primero re-crear s1 y c2, luego deshacer CX(c2,c1), luego
            # deshacer c2 y c1 con del_and, luego limpiar s1.
            # s1 = a^bb
            s1 = b.alloc_qubits(1)[0]
            b.cx(a, s1)
            b.cx(bb, s1)
            # c2 = s1&cin
            c2 = b.alloc_qubits(1)[0]
            b.init_and(s1, cin, c2)
            # deshacer CX(c2, c1): CX(c2, cout_q) de nuevo
            b.cx(c2, cout_q)
            # ahora cout_q = c1, c2 = s1&cin. Deshacer c2 y c1:
            b.del_and(s1, cin, c2)
            b.del_and(a, bb, cout_q)
            # limpiar s1
            b.cx(bb, s1)
            b.cx(a, s1)
            b.free(s1)
            b.free(c2)
            b.free(cout_q)


def main():
    for n in (7, 13, 49):
        rng = np.random.default_rng(1234)
        vals = rng.integers(0, 2, size=n).astype(bool)
        expected = int(vals.sum())
        b = km.CircuitBuilder()
        inp = b.create_quantum_register(n, name="inp")
        # La entrada se escribe SOLO vía sim.write_across_shots (no b.x,
        # que la voltearía dos veces).
        count, ops = hamming_weight_tree(b, list(inp))
        print(f"n={n}: bits de conteo={len(count)}, ops={len(ops)}, "
              f"esperado={expected}")
        # leer el conteo
        circ = b.finish_circuit()
        st = circ.operation_statistics()
        print(f"  Toffoli-like (solo árbol, sin deshacer): {st.num_toffoli_like}")
        sim = km.Simulator(batch_size=1, debug_print=False, seed=1)
        sim.use_same_registers_as(circ)
        sim.write_across_shots(km.array([km.q(i) for i in range(n)]),
                               vals[:, None])
        sim.do(circ)
        got_bits = sim.read_across_shots(km.array(count))
        got = sum(int(got_bits[i, 0]) << i for i in range(len(count)))
        print(f"  conteo leído={got} esperado={expected} {'OK' if got == expected else 'MAL'}")
        # deshacer el árbol y verificar que todo vuelve a 0 (excepto inp)
        b2 = km.CircuitBuilder()
        inp2 = b2.create_quantum_register(n, name="inp")
        count2, ops2 = hamming_weight_tree(b2, list(inp2))
        undo_tree(b2, ops2)
        circ2 = b2.finish_circuit()
        sim2 = km.Simulator(batch_size=1, debug_print=False, seed=1)
        sim2.use_same_registers_as(circ2)
        sim2.write_across_shots(km.array([km.q(i) for i in range(n)]),
                                vals[:, None])
        sim2.do(circ2)
        nq = circ2.num_qubits
        allq = sim2.read_across_shots(km.array([km.q(i) for i in range(nq)]))
        dirty = [qq for qq in range(nq) if qq >= n and bool(allq[qq, 0])]
        print(f"  tras deshacer: qubits sucios (no-inp)={len(dirty)} "
              f"{'OK' if not dirty else 'MAL: ' + str(dirty[:10])}")
        st2 = circ2.operation_statistics()
        print(f"  Toffoli-like (árbol + deshacer): {st2.num_toffoli_like}")


if __name__ == "__main__":
    main()
