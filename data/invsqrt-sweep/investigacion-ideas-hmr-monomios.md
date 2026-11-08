# Investigación: ideas para invsqrt — HMR/fixup y conteo de monomios

**Fecha:** 2026-11-08
**Contexto:** competición Google Quantum AI Verifiable Circuit Compilation (kickmix).
Logshift2 es nuestro mejor circuito (score 390,005; Q=139; 2,561 Toffolis). La tubería
propia de monomios funciona pero cuesta ~3.68M (9.4x arriba). Dos bloqueos: (1) el HMR
sobre y1 patea la fase 0.5 vueltas en x=1 y ningún fixup intentado lo corrige;
(2) el conteo exacto de los 748 monomios domina el costo de la tubería propia.

Este informe resume lo encontrado en la literatura, con fuentes citadas. Ningún dato
está inventado: los números propios son los ya medidos por el equipo; las estimaciones
de ideas nuevas van marcadas como ESTIMACIÓN y hay que verificarlas construyendo.

---

## Parte 1. El problema del HMR (measurement-based uncomputation)

### 1.1 La regla exacta del HMR — paper kickmix (Khattar et al. 2026)

La fuente canónica es el paper que acompaña a la competición:

> Khattar, Rubin, Gidney, Broughton, Low, Babbush. "Leveraging verifiable structure
> in quantum circuits to find more efficient compilations with agentic AI", arXiv:2610.23832
> (octubre 2026). https://arxiv.org/abs/2610.23832 — HTML: https://arxiv.org/html/2610.23832v2

Sección II.1, textual:

> "The HMR instruction (pronounced 'hammer') applies a Hadamard gate, measures the
> target qubit q_t in the Z basis, and resets q_t to |0⟩. When q_t holds a function
> f(x) of the remaining qubits, this X-basis measurement yields a random outcome
> b ∈ {0,1} and introduces a phase kickback
> |x⟩|f(x)⟩ —HMR→ (−1)^{b·f(x)} |x⟩|0⟩. (1)
> When b = 1, classically controlled diagonal gates (such as Z, CZ, CCZ, or NEG) can
> fix the phase error (−1)^{f(x)} introduced by the X-basis measurement. For example,
> uncomputing a temporary logical-AND wire |x_1 ∧ x_2⟩ requires only one HMR
> instruction followed by a classically controlled CZ gate when b = 1, saving a
> Toffoli gate [Gidney 2018]. **However, HMR only works when the resulting phase
> error can be corrected cheaply.** If a circuit applies HMR to a junk qubit that
> remains entangled with the system without fixing its phase kickback, classical
> trajectory simulation fails loudly. The simulator samples a uniformly random bit
> b ∈ {0,1}, flips the tracked output phase if q_t·b = 1, and resets q_t to |0⟩.
> Without a matching phase fixup, that random sign flip causes the check on sampled
> inputs to fail with probability 1/2 whenever q_t = 1."

**Consecuencia directa para nosotros.** El kickback es (−1)^{b·f(x)}: depende de
**f(x), la función booleana que guarda el qubit medido**. El fixup debe aplicar
exactamente (−1)^{f(x)} condicionado a b=1. Es decir, el fixup es una puerta
diagonal cuya fase es la propia función f(x). El costo del fixup es, por tanto,
el costo de implementar la fase (−1)^{f(x)}:

| f(x) del qubit medido | Fixup necesario (si b=1) | Costo |
|---|---|---|
| lineal (un bit, o XOR de bits) | Z sobre el bit (o sobre cada bit del XOR) | 0 Toffolis (gratis) |
| AND de 2 bits: x1∧x2 | CZ(x1, x2) | 0 Toffolis (gratis) |
| AND de 3 bits: x1∧x2∧x3 | CCZ(x1, x2, x3) | 1 Toffoli |
| XOR de k monomios | una puerta diagonal por monomio | k puertas (CZ gratis, CCZ 1 Toffoli c/u) |
| ANF densa (millones de monomios, grado alto) | una puerta por monomio | inviable |

**Esto explica exactamente por qué falla el HMR sobre y1.** Cada bit de y1 es la
salida del Horner: una función booleana de x cuya ANF es densa (el equipo ya
midió que la forma exacta en x de los qubits objetivo de V34 tiene cientos de
miles a millones de monomios, grado hasta 22; y1 de logshift2 es del mismo
orden). El fixup para HMR(y1[j]) exigiría una puerta diagonal por cada monomio
de la ANF de y1[j]: millones de CZ/CCZ, mucho más caro que el espejo reversible
(~934 Toffolis) que se quería evitar. El fixup "Z a x condicionada a los bits
HMR" que se intentó es incorrecto porque la fase a corregir no es (−1)^{x[j]}
sino (−1)^{y1[j](x)}, y y1[j](x) no es x[j].

**Regla de oro (para decidir si un registro admite HMR + fixup):** un registro R
se puede limpiar con HMR + fixup barato **si y solo si cada bit R[j] guarda una
función f_j(x) de ANF rala y de grado bajo** (típicamente un solo AND de grado 2,
o una XOR de pocos ANDs). Si f_j es densa, el HMR es inviable y hay que usar el
espejo reversible o `del_lookup`.

### 1.2 Por qué V34 sí puede usar HMR + fixup (y nosotros no, sobre y1)

V34 fasea directamente desde monomios (ANFs) hacia acumuladores (q28/q50). Sus
intermedios son ANDs (monomios de grado 2, vía `init_and`) y términos lineales
(CX). Cuando V34 hace HMR a un intermedio que guarda un AND x1∧x2, el fixup es
**un solo CZ(x1, x2) condicionado al bit de resultado** — gratis. Cuando hace HMR
a un término lineal, el fixup es un Z — gratis. Toda la estructura de V34 está
diseñada para que cada qubit que se mide guarde una función de ANF trivial
(grado ≤ 2, un monomio). Por eso llega a Q=62: nunca paga un espejo.

En logshift2, en cambio, y1 es el resultado de una computación aritmética
(Horner con sumas y multiplicaciones). Sus bits tienen ANF densa. **No hay
fixup barato para y1 porque y1 no es un AND ni una función rala: es aritmética.**

La lección estructural es: **el HMR + fixup no es una técnica de limpieza
genérica; es una técnica que solo funciona si el circuito se diseña desde el
principio para que los qubits a medir guarden funciones de ANF rala.** V34 lo
hace; logshift2 no (y por eso su espejo es necesario).

### 1.3 Por qué el simulador local da falso positivo con HMR

El paper kickmix lo dice explícito: sin fixup, el chequeo falla "con probabilidad
1/2 whenever q_t = 1" por cada input muestreado. Nuestro test local corre **8
shots con una semilla fija (seed=3), un shot por cada x**. Si en esos 8 shots los
bits aleatorios b muestreados no voltean la fase (o se cancelan entre sí), el
test pasa aunque el circuito sea incorrecto. El verificador oficial corre el
**dominio completo (200,540,928 shots)** con semilla derivada del hash del
circuito (Fiat-Shamir) y varios shots por x: la probabilidad de que el error no
aparezca es esencialmente cero. Por eso sin_ruido, todo_en_uno y patada_final
pasan el simulador (fase 9.3e-09) y fallan el verificador oficial (0.5 vueltas
en x=1).

**Consecuencia práctica:** un test local de pocos shots NO valida un circuito con
HMR. Para validar HMR hay que correr muchos shots con varias semillas, o mejor:
convertir el circuito a un solo registro 'x' y pasarlo por el verificador oficial.
Esto también aplica a la tubería propia de monomios (ver §1.6).

### 1.4 El patrón DQI: fixup diferido (deferred phase correction)

Fuente: Khattar et al., "Verifiable Quantum Advantage via Optimized DQI Circuits",
arXiv:2510.10967 (octubre 2025), sección 3, "Measurement-Based Uncomputation
for GF(2) Multiplication". https://arxiv.org/abs/2510.10967

En DQI, el registro de error |e_i⟩ se descomputa con MBU (medición en base X) y
**la fase NO se corrige en el momento**. El fixup se difiere a la etapa de
decodificación reversible, donde cada término de error e_i se **recomputa** a
partir del síndrome (que sigue disponible) y se aplica (−1)^{c_i·e_i} usando el
resultado de medición c_i guardado. La idea clave: **el fixup es posible porque
la función a corregir se puede recomputar barato en el momento del fixup**,
a partir de datos que siguen vivos.

El mismo patrón aparece en Gidney 2025 ("How to factor 2048 bit RSA integers
with less than a million noisy qubits", arXiv:2505.15917): "deferring and merging
phase corrections. In many places in the algorithm, measurement based
uncomputations produce phasing tasks. These phasing tasks don't need to be
performed immediately, and often the phasing tasks produced in one place can be
merged with phasing tasks produced in another place."

**Aplicación a y1:** un fixup diferido para y1 exigiría recomputar y1 en el
momento del fixup — y recomputar y1 ES el Horner (el costo que se quería evitar).
No hay ahorro. La única excepción sería si el fixup pudiera hacerse con una
recomputación más barata que el Horner completo (por ejemplo, recomputar solo
los bits de y1 que son 1 — pero eso sigue siendo el Horner). **Veredicto: el
fixup diferido no resuelve y1.**

La idea de "fusionar fixups" (defer + merge) sí es útil en general: si se hace
HMR a varios qubits, sus fixups (que son fases (−1)^{f_j(x)}) se pueden XORear
en una sola corrección, y si los f_j se solapan, la corrección fusionada es más
barata que la suma. Pero esto solo ayuda si los fixups individuales ya son
baratos. Para y1 no lo son.

### 1.5 El patrón Gidney: descomputar un lookup con MBU cuesta 2√L

Fuente: Gidney, "Windowed quantum arithmetic", arXiv:1905.07682 (mayo 2019),
figuras 3–4. https://arxiv.org/abs/1905.07682

> "To uncompute a table lookup using measurement based uncomputation, start by
> measuring all of the output qubits in the X basis. [...] Fixing the state
> negations is done using a lookup over a significantly smaller table. To be
> specific, the phase negation task is performed by separating the address
> register into a low half and a high half. A binary-to-unary conversion is
> performed on the low half, and then a table lookup addressed by the high half
> and targeting the low half is performed. [...] The Toffoli count of
> uncomputing the lookup is 2√L instead of L."

**Aplicación a logshift2:** el `TablaLookup` carga coef (58 bits) desde una tabla
de 512 entradas (dirección de 9 bits). Descomputarlo reversible cuesta ~551
Toffolis (init+del, medido por el equipo: del_lookup añade solo ~41). Con MBU
puro costaría ~2√512 ≈ 45 Toffolis. Pero **el `del_lookup` de kickmix ya usa
MBU internamente** — por eso es casi gratis (~41 Toffolis extra). Esta
optimización ya está capturada por el builder; no hay ahorro adicional aquí.
La condición para que funcione es que el registro de dirección siga vivo en el
momento del fixup (para hacer el lookup pequeño), lo cual se cumple en
logshift2 (sel/sb siguen vivos).

Trabajo relacionado que mejora el unlookup: "Optimized circuits for windowed
modular arithmetic" (arXiv:2502.17325, febrero 2025) reduce el costo del
unlookup un 66% asintótico y fusiona varios lookup-add en un solo lookup mayor.
Específico a exponenciación modular; no traslada directo a invsqrt, pero el
principio (fusionar lookups) es el mismo que el WideLookup ya probado por el
equipo (muerto por ancillas sucias).

### 1.6 El AND temporal de Gidney (4 T para computar, 0 T para borrar)

Fuente: Gidney, "Halving the cost of quantum addition", Quantum 2, 74 (2018),
arXiv:1709.06648. https://arxiv.org/abs/1709.06648

La construcción "temporary logical-AND": computar el AND de dos qubits con 4
puertas T (en vez de 7 para un Toffoli), y borrarlo con **0 puertas T** usando
medición en base X + CZ condicionada al resultado. En kickmix esto es
`init_and` (1 Toffoli) + `del_and` (HMR + CZ, gratis). Es exactamente lo que ya
usa logshift2 en el Horner y lo que usa la tubería de monomios para los ANDs.
No hay nada nuevo que extraer aquí, pero confirma que el par init_and/del_and
es la forma correcta y óptima de manejar ANDs temporales en kickmix.

Formalización general: "Measurement-based uncomputation of quantum circuits
for modular arithmetic" (arXiv:2407.20167, julio 2024) introduce y demuestra un
"MBU lemma" para el caso de un qubit, y mide reducciones del 10–15% en Toffolis
para sumadores modulares VBE y de casi 25% para otras arquitecturas. El lema
formaliza cuándo el MBU es aplicable; la condición es, de nuevo, que la fase
de kickback sea corregible con puertas diagonales baratas.

### 1.7 Ideas concretas para el HMR en logshift2 (evaluación)

| Idea | Qué ataca | Cómo funcionaría | Veredicto |
|---|---|---|---|
| HMR a y1 con fixup Z/CZ | Espejo de ~934 Toffolis | Aplicar (−1)^{y1[j](x)} condicionado al bit HMR | **NO FUNCIONA.** La ANF de y1[j] es densa (millones de monomios); el fixup costaría millones de puertas. Intentado y medido: falla el verificador en x=1 (0.5 vueltas). |
| HMR a y1 al final (después de restaurar x) | Orden del HMR | La patada cae cuando x ya está limpia | **NO FUNCIONA.** Medido (patada_final): falla igual en x=1. La patada no depende del orden; depende de medir y1. |
| HMR solo a coef/sel, espejo para y1 (híbrido) | Parte del espejo | coef/sel con HMR, y1 con espejo | **NO FUNCIONA.** Medido: HMR en coef/sel también rompe x (coef también tiene ANF densa: es salida de lookup). |
| Fixup diferido (recomputar y1 al corregir) | Costo del fixup | Recomputar y1 en el momento del fixup (patrón DQI) | **NO AHORRA.** Recomputar y1 es el Horner; cuesta lo mismo que el espejo. |
| Fusionar fixups (defer + merge) | Costo agregado de varios HMR | XORear las fases de kickback en una sola corrección | Útil solo si los fixups individuales son baratos. Para y1 no lo son. |
| Cambiar la representación: que y1 sea ralo | La raíz del problema | Si y1 se computara como polinomio ralo (monomios), el fixup sería CZ/CCZ por monomio | **Es la tubería de monomios.** Pero ver §2: el costo se mueve al conteo, no desaparece. Y el HMR del ACC tampoco está validado por el verificador oficial (ver riesgo abajo). |
| No medir y1: espejo reversible | — | logshift2 tal cual | **Es lo que funciona hoy (390,005, PASS oficial).** El espejo de ~934 Toffolis es el precio de la correctitud. |

**Riesgo abierto que el equipo debe verificar (importante):** la tubería propia
de monomios limpia el ACC con HMR vectorial (~500 Toffolis) y pasa el simulador
local (8 shots, seed fija). Pero el verificador oficial **no puede correr** esa
tubería directamente (tiene 13 registros; exige exactamente un 'x'). El mismo
mecanismo de falso positivo que afectó a sin_ruido/todo_en_uno/patada_final
podría estar afectando a la tubería de monomios: el kickback del HMR sobre el
ACC es (−1)^{b·ACC[p](x)}, y ACC[p] también tiene ANF densa (por los acarreos
del conteo). **Recomendación: validar la tubería de monomios con muchos shots
y varias semillas, y/o convertirla a un solo registro 'x' para pasarla por el
verificador oficial, antes de considerarla una entrega válida.** Si el HMR del
ACC también falla, la tubería necesitaría espejo para el ACC (lo que la haría
aún más cara).

**Conclusión de la Parte 1:** el HMR sobre y1 es un callejón sin salida
**dentro de la representación de logshift2**. La literatura es unánime y precisa:
el fixup cuesta lo que cuesta implementar (−1)^{f(x)}, y para una salida
aritmética densa eso es inviable. Las únicas salidas reales son: (a) aceptar el
espejo (logshift2, 390k); (b) cambiar la representación para que lo que se mide
sea ralo (V34 / tubería de monomios), con el costo trasladado a otra parte;
(c) encontrar una representación de y1 cuya ANF sea rala — que es exactamente
el problema abierto de la reconstrucción V34.

---

## Parte 2. Reducir el costo de la tubería de monomios

### 2.1 Dónde está el costo realmente (estimación razonada, no medida)

Tubería actual: Q=273, 13,159 Toffolis, score ~3.68M. Desglose estimado a partir
de la estructura del circuito (no es una medición instrumentada; habría que
confirmarla contando por fase):

- ANDs de los monomios: B 28×0 (grado 1, solo CX) + S*t 225×1 + C2*t² 495×1
  (con pares t[j]·t[k] compartidos, 55 pares) ≈ **720 Toffolis** si se computa
  cada monomio una vez. Pero el conteo actual computa cada monomio **dos veces**
  (una para contar, otra para deshacer el contador): ≈ **1,440**.
- Conteo con iadd/isub por monomio (~7 Toffolis por iadd de 1 bit a un contador
  de 6 bits, ×2 por el deshacer = ~14 por monomio): para ~500 monomios en pesos
  pesados, ≈ **7,000 Toffolis**. **Este es el cuello: ~55–70% del total.**
- Tablas (3× init_lookup + del_lookup), normalización, barrel shift, mux, fase
  (46 rotaciones ≈ 334 de C): ≈ **1,500–2,000**.
- Limpieza HMR vectorial del ACC: ≈ **500**.

**Conclusión: el problema no son los ANDs de los monomios; es el contador.**
Cada monomio paga ~14 Toffolis de iadd/isub para contarse. Cualquier idea que
abarate el conteo ataca el 60–70% del costo.

### 2.2 IDEA MÁS PROMETEDORA: contador de Hamming weight con árbol de full-adders (Boyar–Peralta)

**Fuente:** Boyar & Peralta, "Tight Bounds for the Multiplicative Complexity of
Symmetric Functions", Theoretical Computer Science 396 (2008), pp. 223–246.
https://www.nist.gov/publications/concrete-multiplicative-complexity-symmetric-functions
— también: Boyar & Peralta, "The Exact Multiplicative Complexity of the Hamming
Weight Function", Yale Tech. Report YALEU/DCS/TR-1260 (2003).
https://cs.yale.edu/publications/techreports/tr1260.pdf

**Teorema (Boyar–Peralta 2008):** la complejidad multiplicativa de computar la
representación binaria del peso de Hamming de n bits es **exactamente
n − hw(n)**, donde hw(n) es el peso de Hamming de la representación binaria de
n. Es decir, contar cuántos de n bits son 1 cuesta **n − hw(n) ANDs en total**,
no n ANDs ni 7n Toffolis.

La construcción es un árbol de full-adders (compresores 3:2): cada full-adder
toma 3 bits del mismo peso y produce 1 bit de ese peso (suma, solo XORs) y 1 bit
del peso siguiente (acarreo, **1 solo AND**, porque
acarreo = ((b1+b2)(b2+b3)+b2) mod 2). El árbol reduce n bits a log2(n)+1 bits
de salida (el peso binario) usando n − hw(n) ANDs en total.

**Cómo se aplica a nuestro caso.** Hoy, para cada peso con n monomios, el
circuito hace: por cada monomio, computar el AND, iadd de 1 bit al contador
(~7 Toffolis), limpiar el AND; luego iadd del contador al ACC; luego recomputar
cada monomio, isub (~7 Toffolis), limpiar. Costo de conteo ≈ 14n Toffolis por
peso (más los ANDs de los monomios, ×2).

Con el árbol de Hamming weight: computar los n bits-monomio (1–2 ANDs cada uno,
una sola vez), alimentarlos al árbol de full-adders (**n − hw(n) ANDs en total**,
cada uno un CCX = 1 Toffoli al computar y **gratis al descomputar** con del_and
HMR+CZ), y sumar el peso resultante (6 bits) al ACC **una sola vez** por peso
(~42 Toffolis por el iadd de 6 bits). Los ANDs del árbol se descomputan gratis
con del_and; los bits-monomio también (del_and).

**Números (ESTIMACIÓN, hay que construir y medir):**

| Peso con n monomios | Conteo actual (~14n + 42) | Conteo con árbol (n − hw(n) + 42) | Ahorro |
|---|---|---|---|
| n=49 (el más pesado) | ~728 | ~88 | ~640 |
| n=30 (típico pesado) | ~462 | ~68 | ~394 |
| n=10 | ~182 | ~49 | ~133 |

Si hay ~15 pesos pesados con n promedio ~30, el ahorro total es del orden de
**~6,000 Toffolis**, llevando el total de 13,159 a **~7,000**. Con Q=273, el
score bajaría de ~3.68M a **~1.9M**. Si el árbol sube Q (ver caveat), con
Q≈320 el score sería ~2.2M. En cualquier caso, **~35–45% de mejora**.

**Caveats honestos:**
- El árbol necesita **todos los n bits-monomio vivos a la vez** (hoy se computan
  de uno en uno). Para n=49, eso son ~49 qubits de monomios + ~46 de acarreos
  del árbol vivos temporalmente: el pico de Q sube (estimado +50–80 qubits en
  el peor peso). Como el score es Q×C, parte del ahorro en C se come por la
  subida de Q. Mitigación: procesar el árbol por niveles y liberar cada nivel
  en cuanto se consume (el builder recicla qubits con free()), o dividir un
  peso grande en dos sub-árboles.
- Los ANDs del árbol son ANDs "temporales" (init_and/del_and): su descomputación
  con HMR+CZ es correcta porque cada AND guarda x1∧x2 (grado 2, fixup = un CZ
  gratis). Esto es exactamente el caso bueno del §1.1. No hay riesgo de patada
  como con y1.
- La familia S*t (resta) usa el mismo árbol y luego isub del peso al ACC.
- La familia B (grado 1, 28 monomios) no necesita árbol: son bits directos, se
  pueden alimentar al árbol sin ANDs, o XORear directo si el peso es ligero.

**Veredicto: la idea más prometedora de este informe.** Ataca el cuello real
(el conteo), tiene fundamento teórico exacto (Boyar–Peralta, no heurística), y
usa solo primitivas que ya funcionan en kickmix (init_and/del_and, iadd). Es
construible y medible en un día de trabajo.

### 2.3 Compartir ANDs jerárquicamente (estilo V34, intermedios windowed)

**Contexto:** la familia C2*t² tiene 495 monomios de grado 3 (C2[a]·t[j]·t[k]).
El equipo ya comparte los 55 pares t[j]·t[k] (cada par se computa una vez y se
reusa para todos los a). El costo restante es 495 ANDs (uno por monomio, para
combinar C2[a] con el par compartido).

**¿Se puede compartir más?** Los monomios son C2[a]·p[jk]. Para un par fijo
p[jk], hay varios a que lo usan; para un a fijo, hay varios pares. Una
factorización jerárquica agruparía por (a, ventana de t): por ejemplo, computar
C2[a]·(ventana de t) una vez y derivar los monomios de esa ventana. Pero cada
monomio (a,j,k) es una combinación distinta; el número de ANDs está acotado
inferiormente por el número de monomios distintos que no comparten
subproducto. Con 495 monomios y 55 pares compartidos, el piso es ~495 ANDs
(uno por monomio) salvo que se encuentre una factorización algebraica no
trivial (por ejemplo, si varios monomios comparten el mismo C2[a]·t[j], se
podría factorizar C2[a]·t[j]·(t[k1]⊕t[k2]⊕...) — pero eso solo ayuda si los
monomios que comparten (a,j) también comparten peso, lo cual no es el caso
general: el peso de C2[a]·t[j]·t[k] depende de a, j y k).

**Herramientas de la literatura para buscar sharing automáticamente:**
- **XOR-AND-inverter graphs (XAGs)** y **multiplicative complexity**: el número
  de nodos AND en un XAG es el driver del T-count / Toffoli-count. El paper
  "Back-end-aware Fault-tolerant Quantum Oracle Synthesis" (Yu et al., ASPDAC
  2025, https://si2.epfl.ch/demichel/publications/archive/2025/ASPDAC25_YU.pdf)
  muestra reducciones promedio de 4.49% en T-count y 14.89% en qubits auxiliares
  con optimización XAG. La librería **mockturtle** (EPFL, https://github.com/lsils/mockturtle)
  implementa optimización de XAGs.
- **REVS** (reversible logic synthesis, DATE 2017) factura subexpresiones
  comunes en ESOP con un parámetro de tamaño p acotado.
- **Veredicto:** el sharing adicional que pueden encontrar estas herramientas es
  probablemente **modesto (10–20%)**, porque los 495 monomios son
  combinaciones mayormente distintas. El equipo ya capturó el sharing grande
  (los 55 pares). No es la palanca principal; el conteo (§2.2) lo es.

**El modelo V34 (intermedios windowed con CSWAP):** V34 no computa monomios
sueltos; sus intermedios son valores "windowed" (ventanas de bits ruteadas con
CSWAP) que capturan la dependencia del segmento. La lección aplicable es:
**en vez de expandir V en 748 monomios planos y contarlos, construir
intermedios jerárquicos que ya agrupen muchos monomios** (por ejemplo, un
intermedio que sea el producto de una ventana de t por un coeficiente, computado
una vez por ventana). Pero esto es esencialmente rediseñar la tubería hacia la
arquitectura V34, que es el problema abierto de la reconstrucción. No es una
optimización incremental de la tubería actual.

### 2.4 Aproximar el conteo donde el error lo permite (el cutoff)

El cutoff (-30) ya hace esto: los pesos por debajo de -30 se dejan en XOR
(ignorando acarreos), con residual máximo medido de 2.733e-08 (pasa con margen
2.18x). Palancas:
- **Subir el cutoff** (p. ej. -25 o -20): más pesos van por XOR (barato), menos
  por conteo exacto. El residual crece; hay que medir la curva residual vs.
  cutoff para encontrar el máximo cutoff que pasa. El presupuesto de error es
  5.96e-08 menos las otras fuentes (~1.8e-08 de cuantización de tablas). Es un
  ajuste fino, no un avance: probablemente mueve el score un 10–20% como mucho.
- **Contador de menos bits con wrap:** si un peso tiene ≤7 monomios, un contador
  de 3 bits basta (ahorra unos Toffolis por peso en el ancho del iadd). Menor.
- **Veredicto:** útil como afinación, no como palanca principal.

### 2.5 Phase polynomials (Amy–Maslov–Mosca) — NO aplica (confirmado)

Fuentes: Amy, Maslov, Mosca, "Polynomial-time T-depth Optimization of
Clifford+T circuits via Matroid Partitioning", arXiv:1303.2042 (2013);
Amy & Mosca, "T-count optimization and Reed-Muller codes", arXiv:1601.07363.

Los phase polynomials optimizan el **T-count** en circuitos Clifford+T (CNOT +
T), donde un Toffoli cuesta 7 puertas T. El algoritmo T-par logra hasta 65.7%
de reducción en T-count y 87.6% en T-depth. **Pero en kickmix la métrica es
Q × C con C = Toffolis + T/4.** Un Toffoli cuenta como 1 (no como 7 T), y
nuestro circuito tiene 13,159 Toffolis frente a 2 T-like. Reducir el T-count
es irrelevante cuando el T-count es despreciable; y los phase polynomials no
reducen el número de Toffolis (que es lo que domina). **Veredicto: no aplica,
confirmado por la literatura.** La confusión viene de que en el mundo
Clifford+T el Toffoli se "desmenuza" en T; en kickmix no.

### 2.6 QROM/windowing para los monomios — considerado, no competitivo

Idea: en vez de computar los monomios con ANDs, hacer un lookup por peso
direccionado por (H, t) que devuelva directamente el conteo o la suma. Pero
(H, t) son 18 bits → 2^18 = 262,144 entradas → ~262k Toffolis. Inviable
(el equipo ya lo descartó). Con windowing (dividir t en ventanas de 5 bits),
cada lookup sería de 2^(8+5) = 8,192 entradas por la dependencia del segmento
— sigue siendo caro. **Veredicto: no competitivo.**

### 2.7 Piso teórico de la tubería de monomios (conclusión honesta)

Aun con el contador de Hamming weight (§2.2), el piso de la tubería es:
- ANDs de monomios (una vez): ~720 Toffolis (mínimo, por los 720 monomios de
  grado ≥2).
- Árboles de Hamming weight: ~1,000 Toffolis en total (suma de n − hw(n) por peso).
- Sumas finales al ACC: ~600 Toffolis.
- Tablas + normalización + barrel shift + mux + fase: ~1,500 Toffolis (C).
- **Total C ≈ 3,500–4,000; con Q≈273–320, score ≈ 1.0–1.3M.**

Es decir, **la tubería de monomios, aun optimizada, no puede bajar de ~1M, y
por tanto no puede batir a logshift2 (390,005)**. El piso lo fijan los 748
monomios: cada uno necesita al menos 1 AND. Para batir logshift2 haría falta
C ≈ 1,400 a Q=273, imposible con 748 monomios. La tubería es un buen vehículo
de aprendizaje y una entrega válida, pero no el camino a 97,921. Ese camino es
V34 (fase directa desde ANFs ralas con intermedios jerárquicos) o mejorar el
Horner/tablas de logshift2.

---

## Resumen de ideas y prioridad

| # | Idea | Problema que ataca | Promesa | Esfuerzo |
|---|---|---|---|---|
| 1 | **Contador de Hamming weight (árbol de full-adders, Boyar–Peralta)** | Conteo de monomios (~70% del costo de la tubería) | **Alta.** ESTIMACIÓN: 13,159 → ~7,000 Toffolis; score 3.68M → ~1.9–2.2M (~40%). | Medio (construir el árbol, medir) |
| 2 | **Validar el HMR del ACC con muchos shots / verificador oficial** | Riesgo de falso positivo en la tubería de monomios | **Crítica (no es mejora, es verificación).** Si el HMR del ACC falla, la tubería necesita espejo y sube mucho. | Bajo (correr tests) |
| 3 | Subir el cutoff (aproximar más pesos) | Conteo | Baja–media (~10–20%). Ajuste fino. | Bajo (medir curva residual vs. cutoff) |
| 4 | Sharing jerárquico de ANDs (XAG/mockturtle/REVS) | ANDs de monomios | Baja (~10–20%). El sharing grande ya está capturado. | Medio–alto |
| 5 | HMR + fixup sobre y1 (cualquier variante) | Espejo de logshift2 (~934 Toffolis) | **Nula.** La literatura demuestra que el fixup cuesta la ANF de y1 (densa). Tres intentos medidos fallaron. | — (cerrado) |
| 6 | Phase polynomials / T-par | T-count | **Nula.** Métrica equivocada (Toffolis, no T). | — (cerrado) |
| 7 | QROM/windowing para monomios | ANDs de monomios | **Nula.** 2^18 entradas inviable. | — (cerrado) |

**Recomendación:** construir el contador de Hamming weight (§2.2) y, en paralelo,
validar el HMR del ACC con muchos shots (§1.3/§1.7). Si el HMR del ACC resulta
ser también un falso positivo, la tubería de monomios pierde su ventaja de
limpieza y el esfuerzo debe volcarse a logshift2/V34.

---

## Fuentes

1. Khattar, Rubin, Gidney, Broughton, Low, Babbush. "Leveraging verifiable
   structure in quantum circuits to find more efficient compilations with
   agentic AI." arXiv:2610.23832 (oct 2026). https://arxiv.org/abs/2610.23832
   — Definición de HMR y fixup (§II.1), benchmark invsqrt (§III.1).
2. Gidney. "Windowed quantum arithmetic." arXiv:1905.07682 (may 2019).
   https://arxiv.org/abs/1905.07682 — Uncompute de lookup con MBU: 2√L.
3. Gidney. "Halving the cost of quantum addition." Quantum 2, 74 (2018).
   arXiv:1709.06648. https://arxiv.org/abs/1709.06648 — AND temporal: 4 T
   computar, 0 T borrar (HMR+CZ).
4. Khattar et al. "Verifiable Quantum Advantage via Optimized DQI Circuits."
   arXiv:2510.10967 (oct 2025). https://arxiv.org/abs/2510.10967 — MBU en
   DQI, fixup diferido vía recomputación, uncompute de multiplicación GF(2)
   solo con mediciones y CZ.
5. "Measurement-based uncomputation of quantum circuits for modular
   arithmetic." arXiv:2407.20167 (jul 2024). https://arxiv.org/abs/2407.20167
   — MBU lemma; −10–15% Toffolis (VBE), ~−25% (otras arquitecturas).
6. Gidney. "How to factor 2048 bit RSA integers with less than a million noisy
   qubits." arXiv:2505.15917 (may 2025). https://arxiv.org/abs/2505.15917 —
   Deferir y fusionar correcciones de fase.
7. Gidney. "Measurement based uncomputation for quantum circuit optimization."
   US Patent App. US20200311594A1 (2020).
   https://patentimages.storage.googleapis.com/ee/f0/ac/3d29c2b2239bc0/US20200311594A1.pdf
8. Boyar & Peralta. "Tight Bounds for the Multiplicative Complexity of
   Symmetric Functions." Theoretical Computer Science 396 (2008), pp. 223–246.
   https://www.nist.gov/publications/concrete-multiplicative-complexity-symmetric-functions
   — Peso de Hamming de n bits cuesta exactamente n − hw(n) ANDs.
9. Boyar & Peralta. "The Exact Multiplicative Complexity of the Hamming Weight
   Function." Yale Tech. Report YALEU/DCS/TR-1260 (2003).
   https://cs.yale.edu/publications/techreports/tr1260.pdf
10. Amy, Maslov, Mosca. "Polynomial-time T-depth Optimization of Clifford+T
    circuits via Matroid Partitioning." arXiv:1303.2042 (2013).
    https://arxiv.org/abs/1303.2042 — Phase polynomials / T-par.
11. Amy & Mosca. "T-count optimization and Reed-Muller codes."
    arXiv:1601.07363. https://arxiv.org/abs/1601.07363
12. Yu, Tempia Calvino, Soeken, De Micheli. "Back-end-aware Fault-tolerant
    Quantum Oracle Synthesis." ASPDAC 2025.
    https://si2.epfl.ch/demichel/publications/archive/2025/ASPDAC25_YU.pdf —
    Optimización XAG (−4.49% T-count, −14.89% qubits auxiliares).
13. "Optimized circuits for windowed modular arithmetic." arXiv:2502.17325
    (feb 2025). https://arxiv.org/abs/2502.17325 — Mejoras al unlookup (−66%
    asintótico), fusión de lookups.
14. Qualtran docs, "kickmix instructions".
    https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_instructions.md
    — Documentación de HMR, R, CZ condicional, PUSH/POP_CONDITION.
