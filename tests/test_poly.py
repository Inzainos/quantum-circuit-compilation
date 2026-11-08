"""Pruebas del motor de faseo polinomico (src/invsqrt_poly.py) y de la
tercera tuberia (bandera secuencial)."""
import sys

import kickmix as km

from invsqrt_poly import (
    PolyPhaseBuilder,
    build_layer1,
    is_sequential,
    split_feedback,
)


def _builder():
    b = km.CircuitBuilder()
    x = b.create_quantum_register(22, name="x")
    scratch = b.create_quantum_register(4, name="scratch")
    return b, x, scratch


def test_bandera_secuencial_solo_q23():
    # q23: ANF se contiene a si mismo -> secuencial
    assert is_sequential([[], ["q20"], ["q21"], ["q23"]], "q23") is True
    # los demas no se contienen
    assert is_sequential([["q17"], ["q18"], ["q14", "q17"]], "q25") is False
    assert is_sequential([["q14", "q16"], ["q14", "q15", "q3"]], "q40") is False


def test_split_feedback_quita_el_termino_propio():
    rest, seq = split_feedback([[], ["q20"], ["q21"], ["q23"]], "q23")
    assert seq is True
    assert rest == [[], ["q20"], ["q21"]]


def test_q23_tercera_tuberia_cero_toffoli():
    b, x, scratch = _builder()
    name_to_qubit = {f"q{i}": x[i] for i in range(22)}
    name_to_qubit["q23"] = b.create_quantum_register(1, name="q23")[0]
    emitter = PolyPhaseBuilder(b, x, None, scratch)
    seq, n = emitter.emit_intermediate(
        "q23", [[], ["q20"], ["q21"], ["q23"]], name_to_qubit
    )
    assert seq is True
    assert n == 0  # XOR gratis: X + 2 CX
    assert emitter.n_sequential == 1
    b.finish_circuit()


def test_intermedio_puro_usa_ands():
    b, x, scratch = _builder()
    name_to_qubit = {f"q{i}": x[i] for i in range(22)}
    name_to_qubit["q40"] = b.create_quantum_register(1, name="q40")[0]
    emitter = PolyPhaseBuilder(b, x, None, scratch)
    # q40: dos monomios de grado 2 -> 2 ANDs
    seq, n = emitter.emit_intermediate(
        "q40", [["q14", "q16"], ["q14", "q18"]], name_to_qubit
    )
    assert seq is False
    assert n == 2
    b.finish_circuit()


def test_build_layer1_enruta_q23_por_la_tercera_tuberia():
    b, x, scratch = _builder()
    name_to_qubit = {f"q{i}": x[i] for i in range(22)}
    for q in ["q23", "q25", "q40"]:
        name_to_qubit[q] = b.create_quantum_register(1, name=q)[0]
    emitter = PolyPhaseBuilder(b, x, None, scratch)
    inter_anf = {
        "q23": [[], ["q20"], ["q21"], ["q23"]],
        "q25": [["q17"], ["q14", "q17"]],
        "q40": [["q14", "q16"]],
    }
    n_and, seqs = build_layer1(emitter, inter_anf, name_to_qubit)
    assert seqs == ["q23"]
    # q25: 1 AND (q14*q17); q40: 1 AND (q14*q16); q23: 0
    assert n_and == 2
    b.finish_circuit()


def test_topo_order_respeta_dependencias():
    from invsqrt_poly import _topo_order

    inter_anf = {
        "q23": [[], ["q20"], ["q21"], ["q23"]],
        "q25": [["q17"], ["q18", "q24"]],
        "q26": [["q16"], ["q17", "q25"]],
        "q40": [["q14", "q16"]],
        "q41": [["q14", "q15"], ["q2", "q40"]],
    }
    order = _topo_order(inter_anf)
    assert order.index("q25") > order.index("q24") if "q24" in order else True
    assert order.index("q26") > order.index("q25")
    assert order.index("q41") > order.index("q40")


def test_layer1_dinamica_comparte_ands_y_enruta_secuencial():
    from invsqrt_poly import build_layer1_dynamic

    b, x, scratch = _builder()
    name_to_qubit = {f"q{i}": x[i] for i in range(22)}
    for q in ["q23", "q25", "q40", "q41"]:
        name_to_qubit[q] = b.create_quantum_register(1, name=q)[0]
    emitter = PolyPhaseBuilder(b, x, None, scratch)
    # q14*q15 se reusa en q40 y q41 -> con umbral 2 se cachea (1 AND)
    inter_anf = {
        "q23": [[], ["q20"], ["q21"], ["q23"]],
        "q40": [["q14", "q15"], ["q14", "q16"]],
        "q41": [["q14", "q15"]],
    }
    n_and, n_cache, seqs = build_layer1_dynamic(
        emitter, inter_anf, name_to_qubit, cache_threshold=2
    )
    assert seqs == ["q23"]
    assert n_cache == 1  # solo q14*q15 (reuso 2)
    # q40: q14*q15 (cache) + q14*q16 (1 AND); q41: q14*q15 (cache, 0 AND)
    assert n_and == 2
    b.finish_circuit()


def test_condicional_elige_umbral_por_q_por_c():
    # otra bandera: mode="auto" elige el umbral que minimiza Q*C
    from invsqrt_poly import pick_layer1_threshold

    inter_anf = {
        "q23": [[], ["q20"], ["q21"], ["q23"]],
        "q40": [["q14", "q16"], ["q14", "q18"], ["q14", "q15", "q16"]],
        "q41": [["q14", "q15"], ["q2", "q40"]],
        "q51": [["q14", "q15"], ["q14", "q16"], ["q15", "q16"]],
    }
    mejor, tabla = pick_layer1_threshold(inter_anf, q_base=38, c_base=1345)
    # el mejor es el de menor Q*C de la tabla
    assert mejor == min(tabla, key=lambda u: tabla[u][4])
    # con Q base 38, el cache no debe subir Q por encima de 38 si no conviene
    assert tabla[mejor][2] <= 38 or tabla[mejor][4] <= tabla[99][4]


def test_mode_min_c_y_min_q():
    from invsqrt_poly import build_layer1_dynamic

    inter_anf = {
        "q23": [[], ["q20"], ["q21"], ["q23"]],
        "q40": [["q14", "q15"], ["q14", "q16"]],
        "q41": [["q14", "q15"]],
    }
    # min_c: umbral 2, cachea q14*q15 (reuso 2) -> 2 ANDs, 1 cache
    b, x, scratch = _builder()
    n2q = {f"q{i}": x[i] for i in range(22)}
    for q in ["q23", "q40", "q41"]:
        n2q[q] = b.create_quantum_register(1, name=q)[0]
    em = PolyPhaseBuilder(b, x, None, scratch)
    n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, mode="min_c")
    assert (n_and, n_cache, seqs) == (2, 1, ["q23"])
    b.finish_circuit()
    # min_q: umbral 99, sin cache -> 3 ANDs, 0 cache
    b, x, scratch = _builder()
    n2q = {f"q{i}": x[i] for i in range(22)}
    for q in ["q23", "q40", "q41"]:
        n2q[q] = b.create_quantum_register(1, name=q)[0]
    em = PolyPhaseBuilder(b, x, None, scratch)
    n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, mode="min_q")
    assert (n_and, n_cache, seqs) == (3, 0, ["q23"])
    b.finish_circuit()


def test_layer1_dinamica_verificada_con_simulador():
    # prueba de fuego: la capa 1 dinamica (auto) calcula los intermedios
    # correctos en el simulador kickmix (x aleatoria, pocos tiros)
    import numpy as np

    from invsqrt_poly import build_layer1_dynamic

    inter_anf = {
        "q23": [[], ["q20"], ["q21"], ["q23"]],
        "q25": [["q17"], ["q18"], ["q21"], ["q14", "q17"], ["q15", "q17"],
                ["q15", "q20"], ["q16", "q17"], ["q18", "q24"]],
        "q40": [["q14", "q16"], ["q14", "q18"]],
    }
    tiros = 64
    b = km.CircuitBuilder()
    x = b.create_quantum_register(22, name="x")
    n2q = {f"q{i}": x[i] for i in range(22)}
    for q in ["q23", "q24", "q25", "q40"]:
        n2q[q] = b.create_quantum_register(1, name=q)[0]
    scratch = b.create_quantum_register(4, name="scratch")
    em = PolyPhaseBuilder(b, x, None, scratch)
    n_and, n_cache, seqs = build_layer1_dynamic(
        em, inter_anf, n2q, mode="auto", q_base=38, c_base=1345
    )
    assert seqs == ["q23"]
    circ = b.finish_circuit()
    rng = np.random.default_rng(1)
    xs = rng.integers(0, 1 << 22, size=tiros, dtype=np.int64)
    sim = km.Simulator(batch_size=tiros, debug_print=False, seed=3)
    sim.use_same_registers_as(circ)
    bits = ((xs[None, :] >> np.arange(22)[:, None]) & 1) == 1
    sim.write_across_shots(km.array([km.q(i) for i in range(22)]), bits)
    sim.do(circ)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(circ.num_qubits)]))
    assert bool((out[:22] == bits).all())  # x restaurada
    # q23 = 1 ^ q20 ^ q21 (sin el termino propio, estado previo 0)
    q23_esp = np.ones(tiros, dtype=bool) ^ bits[20] ^ bits[21]
    assert bool((out[22] == q23_esp).all())
    # q40 = (q14&q16) ^ (q14&q18)
    q40_esp = (bits[14] & bits[16]) ^ (bits[14] & bits[18])
    assert bool((out[25] == q40_esp).all())


def test_layer1_dinamica_sin_colision_de_qubits():
    # regresion: el temporal destino nunca es igual a un control
    # (antes daba ValueError por CCX con control == target)
    from invsqrt_poly import build_layer1_dynamic

    b, x, scratch = _builder()
    name_to_qubit = {f"q{i}": x[i] for i in range(22)}
    for q in ["q23", "q25", "q26", "q27", "q40", "q41", "q50", "q51", "q57"]:
        name_to_qubit[q] = b.create_quantum_register(1, name=q)[0]
    # q24 como entrada (su ANF no esta en el JSON)
    name_to_qubit["q24"] = b.create_quantum_register(1, name="q24")[0]
    emitter = PolyPhaseBuilder(b, x, None, scratch)
    inter_anf = {
        "q23": [[], ["q20"], ["q21"], ["q23"]],
        "q25": [["q17"], ["q18"], ["q21"], ["q14", "q17"], ["q15", "q17"],
                ["q15", "q20"], ["q16", "q17"], ["q18", "q24"]],
        "q26": [["q16"], ["q18"], ["q19"], ["q20"], ["q21"],
                ["q14", "q15"], ["q14", "q17"], ["q14", "q19"],
                ["q15", "q18"], ["q17", "q25"]],
        "q27": [["q14"], ["q15"], ["q16"], ["q17"], ["q18"], ["q19"],
                ["q20"], ["q21"], ["q14", "q15"], ["q14", "q17"],
                ["q16", "q26"]],
        "q40": [["q14", "q16"], ["q14", "q18"], ["q14", "q19"],
                ["q14", "q20"], ["q14", "q3"], ["q16", "q3"],
                ["q14", "q15", "q16"], ["q14", "q15", "q17"],
                ["q14", "q15", "q18"], ["q14", "q15", "q19"],
                ["q14", "q15", "q20"], ["q14", "q15", "q3"],
                ["q14", "q16", "q3"], ["q14", "q17", "q3"],
                ["q14", "q19", "q20"], ["q14", "q21", "q3"],
                ["q15", "q16", "q3"], ["q14", "q15", "q17", "q3"],
                ["q14", "q15", "q18", "q3"], ["q14", "q15", "q20", "q3"]],
        "q41": [["q14", "q15"], ["q2", "q40"]],
        "q50": [["q14"], ["q17"], ["q18"], ["q14", "q15"],
                ["q16", "q17"], ["q14", "q15", "q18"],
                ["q14", "q16", "q17"]],
        "q51": [["q15"], ["q16"], ["q18"], ["q21"], ["q14", "q15"],
                ["q14", "q16"], ["q14", "q17"], ["q14", "q18"],
                ["q14", "q20"], ["q14", "q21"], ["q15", "q16"],
                ["q15", "q18"], ["q15", "q19"], ["q16", "q17"],
                ["q19", "q20"]],
        "q57": [[], ["q15"], ["q16"], ["q17"], ["q18"], ["q20"],
                ["q21"], ["q14", "q19"], ["q14", "q21"], ["q15", "q16"],
                ["q15", "q20"], ["q16", "q17"], ["q19", "q20"]],
    }
    n_and, n_cache, seqs = build_layer1_dynamic(
        emitter, inter_anf, name_to_qubit, cache_threshold=2
    )
    assert seqs == ["q23"]
    assert n_and == 35  # igual que el trie (compartir total)
    assert n_cache == 16
    b.finish_circuit()  # no debe lanzar ValueError por colision
