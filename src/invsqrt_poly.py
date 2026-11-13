"""Faseo polinomico directo (direct polynomial phasing) en nuestro motor.

Mecanismo (descifrado del circuito publico V34, invsqrt-public-v34.kmb):
la fase theta(x) = 2/sqrt(x) se escribe como suma de monomios en los bits
de entrada, theta = sum_m angulo_m * m(x), donde m(x) es un producto de
bits (AND). Cada monomio se emite asi:
  1. AND de sus bits en una ancila reutilizable (init_and / cadena CCX).
  2. Z_POW(ancila, angulo_m): la rotacion imprime la fase por kickback.
  3. HMR(ancila, bit): se mide la ancila en base X y se resetea a |0>
     (la ancila se reusa para el siguiente monomio: por eso Q se queda
     chico y no hay espejo que duplique los Toffolis).
  4. Fixup: Z condicionada al bit medido sobre un qubit del monomio
     (el byproduct de la medicion; en el circuito publico es una Z por
     medicion, sobre un solo qubit del monomio).
Los terminos lineales (monomios de 1 bit) son Z_POW directos sobre el
bit de entrada: cuestan 0 Toffolis.

TERCERA TUBERIA (bandera secuencial, idea de Elan):
un intermedio es SECUENCIAL si su ANF se contiene a si mismo
(retroalimentacion, p. ej. q23 = 1 ^ q20 ^ q21 ^ q23). No es funcion
pura de x, es un qubit que evoluciona. Cuando se detecta (bandera),
ese intermedio NO va por la red de ANDs (que explotaria al componerlo)
sino por una tercera tuberia: se mantiene como qubit persistente y se
actualiza con XOR (la parte no-retroalimentada del ANF). El XOR es
Clifford (CX gratis, 0 Toffolis). El termino propio es el estado
anterior y se salta, no se calcula. `emit_intermediate` aplica esto
automaticamente: detecta la bandera y enruta en consecuencia.

Este modulo es el MOTOR (el emisor de monomios + MBU). La lista de
monomios y angulos es DATO (se llena con la extraccion del circuito
publico o con un ajuste propio); el motor no depende de ella.
"""


def is_sequential(anf, qname):
    """Bandera secuencial: True si el ANF contiene al propio intermedio
    (un monomio que es exactamente [qname]). anf: lista de monomios,
    cada uno una lista de nombres de qubit (str)."""
    return any(m == [qname] for m in anf)


def split_feedback(anf, qname):
    """Separa el ANF en (resto, es_secuencial). El resto es el ANF sin el
    termino propio; eso es lo que se XOR-ea en la tercera tuberia."""
    rest = [m for m in anf if m != [qname]]
    return rest, is_sequential(anf, qname)
from fractions import Fraction

import kickmix as km

from invsqrt_nr_bin import _normalize_bin


class PolyPhaseBuilder:
    """Emite la fase como suma de monomios con MBU en un circuito kickmix."""

    def __init__(self, b, x_reg, s_reg, scratch):
        """
        b: CircuitBuilder.
        x_reg: registro de entrada x (22 qubits, km.array).
        s_reg: registro del exponente binario s (4 qubits).
        scratch: qubits de trabajo reutilizables (km.array), al menos 2.
        """
        self.b = b
        self.x = x_reg
        self.s = s_reg
        self.scratch = scratch
        self.n_bits = 0
        self.n_monomials = 0
        self.n_and = 0
        self.n_sequential = 0  # intermedios enrutados por la tercera tuberia

    def _and_into(self, qubits, anc, tmps=None):
        """Calcula el AND de `qubits` en `anc` (anc debe estar en |0>).
        Los temporales intermedios se descomputan con del_and (gratis).
        Devuelve (n_toffoli, lista_de_ANDs_a_limpiar) donde la lista
        incluye TODOS los ANDs en orden de creacion (el ultimo es el
        que cae en `anc`); para limpiar, recorrerla en orden inverso
        con del_and."""
        if tmps is None:
            tmps = [self.scratch[1], self.scratch[2]]
        if len(qubits) == 0:
            # monomio constante 1: la ancila queda en |1>
            self.b.x(anc)
            return 0, []
        if len(qubits) == 1:
            self.b.cx(qubits[0], anc)
            return 0, []
        if len(qubits) == 2:
            self.b.init_and(qubits[0], qubits[1], anc)
            return 1, [(qubits[0], qubits[1], anc)]
        # arbol binario con dos temporales que se alternan; el ultimo AND
        # cae en `anc`. Se guardan los pares (control1, control2, temporal)
        # para descomputarlos en orden inverso con del_and.
        made = []  # (c1, c2, target) de cada init_and, en orden
        cur = list(qubits)
        ti = 0
        while len(cur) > 2:
            a, b = cur[0], cur[1]
            t = tmps[ti % 2]
            self.b.init_and(a, b, t)
            made.append((a, b, t))
            cur = [t] + cur[2:]
            ti += 1
        # ultimo AND en anc
        self.b.init_and(cur[0], cur[1], anc)
        made.append((cur[0], cur[1], anc))
        return len(made), made

    def emit_monomial(self, qubits, angle):
        """Emite un monomio: AND -> rotacion -> HMR -> fixup.
        qubits: lista de qubits de entrada (el monomio es su AND).
        angle: angulo de la rotacion, en vueltas (Fraction o float)."""
        b = self.b
        anc = self.scratch[0]
        bit = km.b(self.n_bits)
        self.n_bits += 1
        self.n_monomials += 1
        if len(qubits) == 1:
            # termino lineal: rotacion directa sobre el bit, 0 Toffolis
            b.z_pow(qubits[0], angle)
            return 0
        n, made = self._and_into(qubits, anc)
        self.n_and += n
        b.z_pow(anc, angle)
        # descomputar los ANDs intermedios (del_and es gratis); el AND
        # final (en anc) lo descomputa el HMR que sigue.
        for c1, c2, t in reversed(made[:-1]):
            b.del_and(c1, c2, t)
        b.hmr(anc, bit)
        # fixup MBU: Z condicionada sobre el primer qubit del monomio
        # (si el monomio es constante, no hay qubit: no hay fixup)
        if len(qubits) >= 1:
            b.push_condition(bit)
            b.z(qubits[0])
            b.pop_condition()
        return n

    def emit_phase_bit(self, monomials, angle):
        """Emite UN bit de fase: XOR de los monomios de su ANF en una
        ancila, UNA rotacion por el angulo del bit, HMR + fixup.
        monomials: lista de listas de qubits (cada una es un monomio,
        el AND de sus qubits). angle: angulo de la rotacion.
        Los XOR (CX) son gratis; solo los ANDs cuestan Toffolis.
        Devuelve los Toffolis usados."""
        b = self.b
        p = self.scratch[0]          # ancila del bit de fase (se reusa)
        t = self.scratch[1]          # temporal del monomio
        tmps = [self.scratch[2], self.scratch[3]]
        bit = km.b(self.n_bits)
        self.n_bits += 1
        self.n_monomials += len(monomials)
        fixup_qubit = None
        n_and = 0
        for qubits in monomials:
            if fixup_qubit is None and len(qubits) >= 1:
                fixup_qubit = qubits[0]
            d = len(qubits)
            if d == 0:
                # monomio constante 1: XOR 1 en el bit de fase
                b.x(p)
            elif d == 1:
                # lineal: CX directo, 0 Toffolis
                b.cx(qubits[0], p)
            else:
                n, made = self._and_into(qubits, t, tmps)
                n_and += n
                self.n_and += n
                # XOR del monomio en el bit de fase (CX gratis)
                b.cx(t, p)
                # descomputar el AND del monomio (del_and gratis, en
                # orden inverso: el final primero, luego intermedios)
                for c1, c2, tgt in reversed(made):
                    b.del_and(c1, c2, tgt)
        # UNA rotacion por el bit de fase completo
        b.z_pow(p, angle)
        b.hmr(p, bit)
        # fixup MBU: Z condicionada sobre un qubit del bit de fase
        if fixup_qubit is not None:
            b.push_condition(bit)
            b.z(fixup_qubit)
            b.pop_condition()
        return n_and

    def emit_intermediate(self, target_name, anf, name_to_qubit):
        """Calcula un intermedio en su qubit destino (tercera tuberia
        integrada). target_name: nombre del intermedio (str). anf: su ANF,
        lista de monomios, cada uno una lista de nombres de qubit (str).
        name_to_qubit: dict nombre -> objeto qubit de kickmix.
        - Detecta la BANDERA secuencial: si el ANF contiene [target_name],
          el intermedio es secuencial y va por la tercera tuberia: el
          termino propio se salta (es el estado anterior) y el resto se
          XOR-ea en el destino (XOR gratis; los ANDs de grado >=2 cuestan).
        - Si es funcion pura, se calcula igual (ANDs + XORs en el destino).
        Devuelve (es_secuencial, n_and_usados). El destino debe empezar
        en |0> si es funcion pura; si es secuencial, es un qubit
        persistente que ya trae su valor anterior."""
        b = self.b
        t = self.scratch[1]
        tmps = [self.scratch[2], self.scratch[3]]
        target = name_to_qubit[target_name]
        rest, seq = split_feedback(anf, target_name)
        if seq:
            self.n_sequential += 1
        n_and = 0
        for m in rest:
            d = len(m)
            if d == 0:
                b.x(target)  # constante 1
            elif d == 1:
                b.cx(name_to_qubit[m[0]], target)  # lineal, gratis
            else:
                qubits = [name_to_qubit[q] for q in m]
                n, made = self._and_into(qubits, t, tmps)
                n_and += n
                self.n_and += n
                b.cx(t, target)
                for c1, c2, tgt in reversed(made):
                    b.del_and(c1, c2, tgt)
        self.n_monomials += len(rest)
        return seq, n_and

    def emit(self, monomials):
        """monomials: lista de (qubits, angle). Devuelve Toffolis usados."""
        total = 0
        for qubits, angle in monomials:
            total += self.emit_monomial(qubits, angle)
        return total


def build_poly_circuit(monomials, out_path=None):
    """Construye el circuito completo: normaliza x y emite la fase por
    monomios. monomials: lista de (indices_de_bit_de_x_norm, angle) donde
    los indices se refieren a los bits de x_norm (0 = LSB)."""
    b = km.CircuitBuilder()
    x = b.create_quantum_register(22, name="x")
    s = b.create_quantum_register(4, name="s")
    scratch = b.create_quantum_register(4, name="scratch")
    x_norm, s_out = _normalize_bin(b, x, s, scratch)
    # los monomios se expresan sobre los bits de x_norm
    emitter = PolyPhaseBuilder(b, x_norm, s_out, scratch)
    mono = [([x_norm[i] for i in idxs], ang) for idxs, ang in monomials]
    n_and = emitter.emit(mono)
    circ = b.finish_circuit()
    if out_path:
        circ.to_file(out_path, format="kmb")
    return circ, emitter


def build_layer1(emitter, inter_anf, name_to_qubit, order=None):
    """Construye la capa 1 (red de intermedios) con la tercera tuberia
    integrada. inter_anf: dict nombre -> lista de monomios (listas de
    nombres de qubit). name_to_qubit: dict nombre -> qubit kickmix (debe
    incluir x y los intermedios destino). order: orden en que se calculan
    los intermedios (por defecto, el orden del dict). Devuelve
    (n_and_total, secuenciales) donde secuenciales es la lista de nombres
    que salieron por la tercera tuberia (bandera prendida)."""
    n_and = 0
    seqs = []
    for q in (order or list(inter_anf.keys())):
        seq, n = emitter.emit_intermediate(q, inter_anf[q], name_to_qubit)
        n_and += n
        if seq:
            seqs.append(q)
    return n_and, seqs


def _topo_order(inter_anf):
    """Orden topologico de los intermedios por sus dependencias (un
    intermedio que usa a otro en su ANF va despues de el). El termino
    propio (retroalimentacion) no cuenta como dependencia."""
    from collections import deque

    names = list(inter_anf.keys())
    deps = {q: set() for q in names}
    for q, monos in inter_anf.items():
        for m in monos:
            for v in m:
                if v in deps and v != q:
                    deps[q].add(v)
    order, done = [], set()
    dq = deque([q for q in names if not deps[q]])
    while dq:
        q = dq.popleft()
        order.append(q)
        done.add(q)
        for r in names:
            if q in deps[r]:
                deps[r].discard(q)
                if not deps[r] and r not in done and r not in dq:
                    dq.append(r)
    # si quedo un ciclo (no deberia, salvo retroalimentacion), se agrega
    # lo que falte al final en el orden dado
    for q in names:
        if q not in order:
            order.append(q)
    return order


def sweep_layer1_thresholds(inter_anf, n_x=22, n_scratch=4):
    """Barrido del umbral de cache para la capa 1 (condicional por Q*C).
    Construye la capa 1 en circuitos desechables para cada umbral y
    devuelve {umbral: (n_and, n_cache)}. El umbral optimo depende de
    Q y C del resto del circuito: cachear mucho baja ANDs pero sube Q.
    Umbrales probados: 2, 3, 4, 5 y 99 (sin cache)."""
    out = {}
    for umbral in (2, 3, 4, 5, 99):
        b = km.CircuitBuilder()
        x = b.create_quantum_register(n_x, name="x")
        n2q = {f"q{i}": x[i] for i in range(n_x)}
        for q in inter_anf:
            n2q[q] = b.create_quantum_register(1, name=q)[0]
        # q24 (si se usa) entra como entrada; su ANF no esta en el JSON
        for q in ("q24",):
            if q not in n2q and any(q in m for monos in inter_anf.values() for m in monos):
                n2q[q] = b.create_quantum_register(1, name=q)[0]
        scratch = b.create_quantum_register(n_scratch, name="scratch")
        em = PolyPhaseBuilder(b, x, None, scratch)
        n_and, n_cache, _ = build_layer1_dynamic(
            em, inter_anf, n2q, cache_threshold=umbral
        )
        b.finish_circuit()
        out[umbral] = (n_and, n_cache)
    return out


def pick_layer1_threshold(inter_anf, q_base, c_base, n_x=22, n_scratch=4):
    """Elige el umbral de cache que minimiza Q*C (la condicional).
    q_base: Q del resto del circuito (sin capa 1). c_base: C del resto
    (sin capa 1). Q de la capa 1 = n_x + n_intermedios + n_scratch +
    n_cache; Q total = max(q_base, Q capa 1); C total = c_base + n_and.
    Devuelve (mejor_umbral, tabla {umbral: (n_and, n_cache, q_total,
    c_total, q_por_c)})."""
    # intermedios = los del dict + los que entran como entrada (p. ej. q24,
    # referenciado en un ANF pero sin ANF propia en el dict)
    refs = set()
    for monos in inter_anf.values():
        for m in monos:
            refs.update(m)
    x_names = {f"q{i}" for i in range(n_x)}
    extra = {r for r in refs if r not in x_names and r not in inter_anf}
    n_inter = len(inter_anf) + len(extra)
    tabla = sweep_layer1_thresholds(inter_anf, n_x=n_x, n_scratch=n_scratch)
    mejor, mejor_qc = None, None
    res = {}
    for umbral, (n_and, n_cache) in tabla.items():
        q_capa1 = n_x + n_inter + n_scratch + n_cache
        q_total = max(q_base, q_capa1)
        c_total = c_base + n_and
        qc = q_total * c_total
        res[umbral] = (n_and, n_cache, q_total, c_total, qc)
        if mejor_qc is None or qc < mejor_qc:
            mejor, mejor_qc = umbral, qc
    return mejor, res


def build_layer1_dynamic(emitter, inter_anf, name_to_qubit, cache_threshold=2,
                         mode="fixed", q_base=None, c_base=None):
    """Capa 1 DINAMICA: el constructor elige solo el diseno mas optimo.
    - Detecta la bandera secuencial y enruta esos intermedios por la
      tercera tuberia (XOR gratis).
    - Ordena los intermedios topologicamente (respetando dependencias).
    - Comparte los ANDs entre intermedios: los productos (prefijos) de
      bits x que se reusan >= cache_threshold veces se calculan UNA vez
      en un qubit de cache y se reusan; el resto se calcula en scratch
      y se limpia con del_and (gratis).
    - CONDICIONAL (otra bandera): mode="auto" elige el umbral que
      minimiza Q*C dados q_base y c_base (el resto del circuito); mode=
      "min_c" usa umbral 2 (minimiza ANDs, sin importar Q); mode="min_q"
      usa umbral 99 (sin cache, minimiza Q). mode="fixed" usa el
      cache_threshold dado.
    Devuelve (n_and_total, n_cache_qubits, secuenciales)."""
    from collections import Counter

    # condicional: resolver el umbral segun la bandera (mode)
    if mode == "min_c":
        cache_threshold = 2
    elif mode == "min_q":
        cache_threshold = 99
    elif mode == "auto":
        if q_base is None or c_base is None:
            raise ValueError("mode='auto' requiere q_base y c_base")
        cache_threshold, _ = pick_layer1_threshold(
            inter_anf, q_base, c_base,
            n_x=len(emitter.x), n_scratch=len(emitter.scratch),
        )

    b = emitter.b
    # orden canonico de variables por frecuencia (para maximizar prefijos)
    cnt = Counter()
    for monos in inter_anf.values():
        for m in monos:
            cnt.update(m)
    order_var = {q: i for i, q in enumerate(sorted(cnt, key=lambda q: -cnt[q]))}
    # conteo de reuso de cada prefijo (de bits x, sin intermedios) entre
    # los monomios de los intermedios PUROS (los secuenciales no se
    # componen, van por XOR)
    x_names = {q for q in cnt if q not in inter_anf}
    reuse = Counter()
    for q, monos in inter_anf.items():
        if is_sequential(monos, q):
            continue
        for m in monos:
            ms = sorted(set(m), key=lambda v: order_var[v])
            for k in range(2, len(ms) + 1):
                pref = frozenset(ms[:k])
                if pref <= x_names:
                    reuse[pref] += 1
    # cache: productos de bits x con reuso >= umbral
    cache = {}  # frozenset -> qubit
    n_and = 0
    n_cache_reg = 0
    for pref, c in sorted(reuse.items(), key=lambda kv: (len(kv[0]), -kv[1])):
        if c < cache_threshold:
            continue
        # prefijo ordenado; el ultimo bit se agrega al prefijo anterior
        ms = sorted(pref, key=lambda v: order_var[v])
        prev = frozenset(ms[:-1])
        if len(prev) == 1:
            # producto de 2 bits: init_and directo en un qubit de cache
            cq = b.create_quantum_register(1, name=f"cache_{n_cache_reg}")[0]
            n_cache_reg += 1
            b.init_and(name_to_qubit[ms[0]], name_to_qubit[ms[1]], cq)
            cache[pref] = cq
            n_and += 1
        elif prev in cache:
            cq = b.create_quantum_register(1, name=f"cache_{n_cache_reg}")[0]
            n_cache_reg += 1
            b.init_and(cache[prev], name_to_qubit[ms[-1]], cq)
            cache[pref] = cq
            n_and += 1
        # si el prefijo anterior no esta en cache, no se cachea este
    # construir cada intermedio en orden topologico
    seqs = []
    for q in _topo_order(inter_anf):
        monos = inter_anf[q]
        if is_sequential(monos, q):
            # tercera tuberia: XOR del resto (sin el termino propio)
            rest, _ = split_feedback(monos, q)
            seq, n = emitter.emit_intermediate(q, monos, name_to_qubit)
            n_and += n
            seqs.append(q)
            continue
        target = name_to_qubit[q]
        for m in monos:
            ms = sorted(set(m), key=lambda v: order_var[v])
            if len(ms) == 0:
                b.x(target)
            elif len(ms) == 1:
                b.cx(name_to_qubit[ms[0]], target)
            else:
                # cadena de productos: usar cache cuando exista, si no
                # calcular en scratch (y limpiarlo despues). El temporal
                # destino siempre es distinto de los dos controles
                # (si no, kickmix rechaza el CCX por colision).
                cur = None  # qubit con el producto acumulado
                made = []  # ANDs en scratch a limpiar
                pool = [emitter.scratch[0], emitter.scratch[1],
                        emitter.scratch[2], emitter.scratch[3]]
                for k in range(2, len(ms) + 1):
                    pref = frozenset(ms[:k])
                    if pref in cache:
                        cur = cache[pref]
                        # limpiar los temporales previos de la cadena
                        for c1, c2, tgt in reversed(made):
                            b.del_and(c1, c2, tgt)
                        made = []
                    else:
                        if k == 2:
                            a1, a2 = name_to_qubit[ms[0]], name_to_qubit[ms[1]]
                        else:
                            a1, a2 = cur, name_to_qubit[ms[k - 1]]
                        t = next(tq for tq in pool if tq is not a1 and tq is not a2)
                        b.init_and(a1, a2, t)
                        made.append((a1, a2, t))
                        cur = t
                        n_and += 1
                        emitter.n_and += 1
                b.cx(cur, target)
                for c1, c2, tgt in reversed(made):
                    b.del_and(c1, c2, tgt)
        emitter.n_monomials += len(monos)
    return n_and, len(cache), seqs


def build_poly_circuit_from_rotations(rotations, out_path=None):
    """Construye el circuito de faseo por bits de fase, con los monomios
    directos sobre x (sin normalizar, como el circuito publico V34).
    rotations: lista de dicts {"angle": float, "monomials": [[qubit...]]}
    donde cada monomio es una lista de qubits de x (objetos km) y angle
    es el angulo de esa rotacion en vueltas. Devuelve (circ, emitter)."""
    b = km.CircuitBuilder()
    x = b.create_quantum_register(22, name="x")
    scratch = b.create_quantum_register(4, name="scratch")
    emitter = PolyPhaseBuilder(b, x, None, scratch)
    total_and = 0
    for rot in rotations:
        total_and += emitter.emit_phase_bit(rot["monomials"], rot["angle"])
    circ = b.finish_circuit()
    if out_path:
        circ.to_file(out_path, format="kmb")
    return circ, emitter
