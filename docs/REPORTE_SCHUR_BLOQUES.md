# Schur por bloques 2×2 O(n²) — Decodificador BM in-place del DQI

**Fecha:** 2026-11-08 ~23:30. **Estado:** núcleo O(n²) validado clásicamente;
el salto 2×2 está caracterizado y su pivote matricial verificado; el circuito
completo con el bloque es trabajo pendiente (sección 7).
**No se tocó main ni el ZIP.** Todo el trabajo es scratch en
`~/workspace/qcc-data/dqi-perfil/`. El verificador DQI completo no corre en
esta caja; validación por muestreo y escala chica.

## 0. Resumen ejecutivo (números)

| Magnitud | Actual (BM v1) | Schur por bloques (q-d, extrapolado) |
|---|---|---|
| Q (qubits) | 1,949 | **≈ 892** (840 S + ~52 trabajo) |
| T (Toffolis, solo BM+omega) | 382,862 | **≈ 643k** (369k ida + 274k vuelta) |
| T total DQI (con scan 401,310) | 784,172 | **≈ 1,044k** |
| Costo DQI R·Q²·T (R≈1.20) | ≈ 3.5745e12 | **≈ 1.0e12** |
| Ratio DQI | 6.77× | **≈ 24×** |
| Geomean (3 tareas) | ≈ 3.31× | **≈ 5.1×** |

**Veredicto:** el Schur por bloques SÍ es el camino (Q² domina: (1949/892)² =
4.77×), pero el T del q-d escalar es MAYOR que el BM actual (643k vs 383k),
así que la ganancia neta es ~3.6× en DQI, no los 59× del público. El público
(T total 407k) implica ADEMÁS un scan con inversión compartida (~94k en vez de
401k) y un BM de ~313k; mi q-d escalar es una cota superior de T — el bloque
2×2 verdadero (menos inversas, GF(2²⁴)) debe bajarlo. Ver §6.

**Caveat de R:** los números de arriba suponen ε=0 (bloque perfecto, R≈1.20).
Sin el bloque perfecto, la ruta Hankel falla ~1% (ε≈0.01) y R subiría
(estimado ~2.0, interpolado, NO medido), lo que bajaría el ratio a ~15× y el
geomean a ~4.3× (estimación). El bloque es, por tanto, necesario, no un
refinamiento. Ver §3.4.

## 1. Formulación matricial 2×2 del Schur por bloques

### 1.1 La ecuación clave en forma matricial (even/odd)

S(x)=A(y)+x·B(y), σ(x)=C(y)+x·D(y), ω(x)=E(y)+x·F(y), y=x². La ecuación clave
σ·S≡ω (mod xⁿ) se parte en:

```
[[C, yD],[D, C]] · [[A],[B]] = [[E],[F]]   (mod y³⁵)
M(y) · S~(y) = Ω(y),  M=[[C,yD],[D,C]], S~=[[A,yB],[B,A]], Ω=[[E,yF],[F,E]]
```

Las matrices de la forma [[a, yb],[b, a]] forman un anillo isomorfo a
GF(2¹²)[x] vía a+b√y. **Pero:** el apareamiento ingenuo a GF(2²⁴) NO
preserva la ecuación clave (desajuste de término cruzado / desplazamiento de
índice, verificado algebraicamente) — la "y" es una variable, no una
constante. El bloque 2×2 correcto NO es el apareamiento even/odd como
elemento de GF(2²⁴); es el bloque de la tabla q-d / de Hankel (§1.3).

### 1.2 El algoritmo q-d (Rutishauser) — el núcleo O(n²)

El q-d calcula los coeficientes de la fracción continua de la serie S con
reglas rombo O(1) por entrada, O(n²) total, estado O(n) (una diagonal):

```
e_0^(n) = 0
q_1^(n) = c_{n+1} / c_n
e_k^(n) = q_k^(n+1) + q_k^(n) + e_{k-1}^(n+1)        (car 2: - = +)
q_{k+1}^(n) = e_k^(n+1) · q_k^(n+1) / e_k^(n)
```

La J-fracción con (q_k^(0), e_k^(0)) da convergentes; el convergente J[2L−1]
es (ω, σ): q==σ_BM y σ·S≡ω (mod xⁿ). **Esto es el "Schur" O(n²):** a
diferencia del Stieltjes (un recíproco de serie O(n²) POR PASO → O(L·n²)),
el q-d hace O(1) por entrada de tabla. Estado: la serie S transformada en
sitio + O(1) palabras (la diagonal vive en el registro S).

### 1.3 El bloque 2×2 (qué es y cómo absorbe el singular)

Un cero aislado e_k^(n)=0 (o H_K^(n)=0) rompe la regla rombo escalar
(división por cero). El bloque 2×2 lo absorbe porque **la división escalar
se vuelve inversa de matriz 2×2**: una matriz 2×2 puede ser invertible
aunque una entrada escalar sea 0. Concretamente, el bloque es el bloque 2×2
de determinantes de Hankel

```
B(K,n0) = [[H_K^(n0),   H_K^(n0+1)  ],
           [H_{K+1}^(n0), H_{K+1}^(n0+1)]]
```

**Medido (§3.3):** en los 3 casos singulares reales (H_20^(1)=0, H_33^(1)=0 a
L=35; H_11^(0)=0 a L=24), det(B)≠0 (1820, 2504, 3403) aunque la entrada
H_K^(n0)=0. El pivote matricial EXISTE. Un bloque 2×2 procesa 2 pasos a la
vez sin recíprocos de serie completa.

**Lo que NO funcionó:** el q-d matricial sobre la serie even/odd
(S~_j=[[S_{2j},S_{2j-1}],[S_{2j+1},S_{2j}]]) se rompe en TODOS los casos
(matrices E singulares, det=0). El bloqueo even/odd no admite q-d matricial
directo. El bloque correcto es el de Hankel / de la tabla q-d, no el even/odd.

## 2. Validación clásica (incl. borde L=35)

### 2.1 q-d escalar + J-fracción (medido)

Script `schur_bloques_qd2.py`. σ==BM y ecuación clave σ·S≡ω en todos los
casos que no se rompen. Convergente J[2L−1].

| Barrido | Resultado |
|---|---|
| Casos dirigidos L=1..34 (9 casos) | 9/9 OK |
| Barrido aleatorio L=1..34 (120 casos) | **109/120 OK (91%)** |
| L=35 (60 casos) | **40/60 OK (67%)** |

Fallo SIEMPRE por un cero aislado e_k^(n)=0 en la tabla (bloque singular),
en CUALQUIER L, no solo en L=35. Posiciones dispersas (21 distintas en L=35).

### 2.2 Ruta Hankel (medido) — bypass de los ceros de propagación

Script `schur_bloques_hankel.py`. La columna n=0 se calcula DIRECTO desde
determinantes de Hankel (eliminación gaussiana exacta, solo validación):

```
q_k^(0) = H_k^(1)·H_{k-1}^(0) / (H_k^(0)·H_{k-1}^(1))
e_k^(0) = H_{k+1}^(0)·H_{k-1}^(1) / (H_k^(0)·H_k^(1))
```

**Diagnóstico confirmado:** 10 de los 11 fallos del q-d escalar se arreglan
así (σ correcto, ec. clave OK). Esos ceros estaban en n≥2: son artefacto de
propagación de la tabla rombo, NO afectan a la columna n=0. Solo 1/11 es
bloque singular real (H_11^(0)=0).

| Barrido | Ruta Hankel |
|---|---|
| Los 11 fallos del q-d (L≤34) | 10/11 arreglados |
| L=35 (60 casos) | **58/60 OK (97%)** |
| Global, todos los L (100 casos) | **99/100 OK (99%), ε≈0.01** |

### 2.3 El bloque singular real (residual ~1–3%)

Quedan 2/60 casos a L=35 (H_20^(1)=0, H_33^(1)=0) y 1/120 a L≤34
(H_11^(0)=0) que fallan AMBAS rutas. En cada uno hay EXACTAMENTE UN
determinante de Hankel que se anula en el rango válido (k≤35, n≤5). El
"salto" simple (omitir el par (q_k,e_k) indefinido en la J-fracción) NO
basta (sigue 58/60): el bloque son 2 k consecutivos y sus B hay que
reemplazarlos por el coeficiente de bloque (matriz 2×2), no omitirlos.
**Pendiente:** implementar la J-fracción matricial con el coeficiente de
bloque derivado de B(K,n0) (§1.3, det≠0 verificado). Es el paso que falta
para ε=0.

## 3. Conteo O(n²) (medido)

### 3.1 Operaciones de campo del q-d (tabla)

Medido en `schur_bloques_qd2.py` (muls + divs de campo GF(2¹²)):

| L | ops tabla (mul+div) |
|---|---|
| 2 | 11 | 5 | 71 | 8 | 185 | 12 | 421 | 20 | 1,181 | 34 | **3,435** |

Escala O(L²) (34²≈1156 → 3,435 ≈ 3·L²). A L=35: L(L+1)=1,260 q-entries.
BM clásico: 6,231 multiplicaciones. El q-d (tabla) usa MENOS ops de campo
que BM; el costo total depende del costo por op en el circuito (§3.2) y de
los convergentes (§3.3).

### 3.2 Costo por operación de campo en kickmix (MEDIDO)

Prototipo `schur_bloques_proto_rombo.py` (simulador kickmix, verificado):

| Operación | Toffolis (medido) | Correctitud |
|---|---|---|
| Multiplicación GF(2¹²) Karatsuba (`dqi_kmul.py`) | **54** | correcta, ancillas limpias |
| Inversa GF(2¹²) torre (`ValueInv3`, fwd+undo) | **75** | correcta |
| División a/b = a·inv(b) | **129** | correcta, fase 0, ancillas limpias |
| Un rombo q-entry + e-entry (q'=e1·q1/e0, e'=q1'+q'+e1) | **183** | qp y ep correctos, fase 0 |

(El constructor `ixor_gf2_mul` da 63; el Karatsuba 54. El panorama cita 42
ANDs teóricos por evaluación/interpolación — NO medido aquí; uso 54.)

**Corrección importante del prototipo:** `TowerInv3` exige la entrada en
coordenadas de torre; para valor (polinomio) hay que usar `ValueInv3`. Con
`TowerInv3` directo el valor salía mal (fase 0, pero valor incorrecto).

### 3.3 Costo total del q-d a escala completa (L=35, extrapolación)

- Tabla: 1,260 q-entries × 183 T = **230,580 T** (ida).
- Convergentes J: ~2,556 mults × 54 T = **~138,000 T** (ida).
- **Ida total ≈ 369k T.**
- Vuelta (restaurar S): las inversas se deshacen por MBU (~0 T); las mults
  se reaplican (~108 T por q-entry + convergentes) ≈ **274k T**.
- **Total q-d ≈ 643k T** (rango 620k–737k según ahorro MBU en la vuelta).

El q-d da (σ, ω) a la vez, así que reemplaza bm_forward + omega_fwd +
omega_rev + bm_reverse (382,862 T actuales). No hace falta omega aparte.

### 3.4 R y el ε residual

- Con bloque perfecto (ε=0): R≈1.20–1.26 (como ahora / público).
- Sin bloque (ruta Hankel, ε≈0.01): R subiría (estimado ~2.0 por
  interpolación desde ε=0.023→R=3.17; NO medido). Con R≈2.0 el ratio DQI
  caería a ~15× y el geomean a ~4.3× (estimación). Por eso el bloque es
  necesario.

## 4. Diseño del circuito cuántico in-place

- **Estado:** registro S (840 qubits, la entrada) transformado en sitio.
  La diagonal de la tabla q-d y los convergentes (σ, ω) viven EN el registro
  S, sobrescribiéndolo por etapas: S → diagonal q-d → (q,e) → σ+ω.
  σ (36 coefs) + ω (35 coefs) = 71 coefs ≈ los 70 de S: caben.
- **Trabajo extra O(1) palabras (~52 qubits):** ~4 palabras de 12 bits
  (q/e corrientes, pivote, inverso temporal) + banderas de polo/acarreo.
  Consistente con el público (840 + ≈52 = 892).
- **Estructura fija:** la tabla se recorre por diagonales con reglas rombo
  (cada paso: 1 división + 1 multiplicación por q-entry, XORs para e).
  El bloque 2×2 es un paso de bloque (matriz 2×2) en lugar del rombo
  escalar cuando el pivote escalar es 0; la estructura no ramifica por
  datos (el bloque se aplica siempre como paso 2×2, o se detecta por
  pivote cero con un circuito fijo — ver §7).
- **Reversible:** cada rombo es reversible (la división usa ValueInv3 con
  undo por MBU); la vuelta restaura S. El scan (401,310 T) y el resto del
  DQI no cambian.

## 5. Prototipo a escala chica en kickmix (medido)

`schur_bloques_proto_rombo.py` (n=6, valores reales del q-d):

- División a/b: 69 qubits, **129 T**, correcta, fase 0, ancillas limpias.
- Un rombo completo (q' + e'): 141 qubits (registros frescos, no in-place),
  **183 T**, qp=1502 y ep=0 correctos, fase 0.
- Esto valida el costo por q-entry (183 T) usado en §3.3 y la reversibilidad
  del núcleo (inversa por torre + Karatsuba + MBU).

No se construyó el q-d completo a escala chica en kickmix (la tabla + los
convergentes con el cableado in-place es el trabajo de implementación del
§7); el prototipo valida el átomo (rombo) y su costo.

## 6. Extrapolación y comparación con el objetivo público

| | Actual | q-d escalar (este trabajo) | Objetivo público |
|---|---|---|---|
| Q | 1,949 | **≈ 892** | 889–897 |
| T total DQI | 784,172 | **≈ 1,044k** | 407–440k |
| Ratio DQI | 6.77× | **≈ 24×** | 59–63× |
| Geomean | 3.31× | **≈ 5.1×** | ~6.9× |

Cálculo: costo = 1.20 × 892² × 1,044,018 ≈ 1.0e12; baseline ≈ 2.42e13;
ratio ≈ 24.3×; geomean = 3.31 × (24.3/6.77)^(1/3) ≈ 5.1×.

**Por qué no llego a 59×:** mi T total (1,044k) es mayor que el público
(407k) por dos razones: (a) mi q-d escalar cuesta ~643k en BM (vs ~313k
implícitos en el público) — el bloque 2×2 verdadero debe bajarlo (menos
inversas: un inverso 2×2 por bloque en vez de 2 escalares; GF(2²⁴) 99 ANDs
por 2 valores en vez de 2×54=108); (b) el público implica un scan con
inversión COMPARTIDA ("frontier DQI shares ONE inversion": ~94k en vez de
401k), que es un trabajo aparte del decodificador. El Q≈892 SÍ se reproduce.
La ganancia en Q² (4.77×) es el grueso del avance; el T es donde el bloque
y el scan compartido deben recortar.

## 7. Pendiente (para Claude / continuación)

1. **J-fracción matricial con coeficiente de bloque:** implementar el salto
   2×2 para el H_K^(n)=0 aislado usando el bloque B(K,n0) (det≠0
   verificado, §1.3/§2.3), validar ε=0 en barrido (L=1..35, incl. los 2
   casos L=35 y el L=24 que hoy fallan). Esto fija R≈1.20.
2. **Circuito q-d completo in-place** (tabla por diagonales + convergentes
   en el registro S, ~52 trabajo), medir Q/T a escala chica y extrapolar;
   confirmar el T de §3.3 y el ahorro del bloque 2×2 (menos inversas).
3. **Scan con inversión compartida** (aparte del decodificador): es lo que
   falta para acercarse al T total público de 407k.
4. **R(ε) exacto** para ε≈0.01 (medir con el verificador / fórmula oficial),
   para cuantificar la penalización sin bloque.

## 8. Archivos

- `schur_bloques_qd.py` — q-d escalar, primera versión (límites
  triangulares corregidos en qd2; no usar).
- `schur_bloques_qd2.py` — q-d escalar + J-fracción (validado §2.1).
- `schur_bloques_matriz.py` — q-d matricial even/odd: FALLA (E singular).
  No es la formulación correcta del bloque.
- `schur_bloques_hankel.py` — (q,e) desde determinantes de Hankel
  (validación, §2.2).
- `schur_bloques_proto_rombo.py` — prototipo kickmix del rombo (§5).
- `REPORTE_SCHUR_RECURRENCIA.md` — Stieltjes descartado (antecedente).
- `REPORTE_BM_INPLACE.md`, `REPORTE_PERFIL_DQI.md`,
  `REPORTE_SCAN_MBU.md`, `REPORTE_BANDERAS_RECOMPUTO.md` — antecedentes.

## 9. Caminos descartados en este trabajo (no reintentar sin evidencia nueva)

- Stieltjes (O(L·n²), ~7.5M T, Q≈1,704) — ver REPORTE_SCHUR_RECURRENCIA.
- Szegő (φ_L≠σ_BM, herramienta equivocada para Hankel).
- Levinson (funciona, σ correcto, pero 2 vectores → Q≈1,680, no in-place).
- q-d matricial even/odd (E singular siempre) — el bloque no es even/odd.
- "Saltar" el par (q_k,e_k) indefinido en la J-fracción (no da σ).
- EEA ingenuo (~1,680 qubits de estado, peor que BM v1).
