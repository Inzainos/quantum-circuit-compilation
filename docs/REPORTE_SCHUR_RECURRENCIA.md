# Recurrencia de Schur para el decodificador BM in-place del DQI

**Fecha:** 2026-11-08
**Estado:** Recurrencia de Stieltjes derivada y validada clásicamente (L=1..34),
**pero DESCARTADA como base del circuito cuántico** — costo O(L·n²) en operaciones
de campo (~7.5M Toffolis) y almacenamiento 2n en el setting reversible.
El camino que queda es el Schur por bloques 2×2 / complemento de Schur O(n²)
(el diseño público jday96314/QuantumAI). Este reporte documenta la recurrencia,
su validación, su costo medido, el prototipo cuántico, y por qué no es el camino,
con el plan concreto del siguiente paso.

**Reglas:** No se tocó main ni el ZIP vigente. Scratch en
`~/workspace/qcc-data/dqi-perfil/`. El verificador DQI completo no corre en esta
caja (8 GB, `reaction_depth` → `bad_alloc`); validación por muestreo y escala chica.
Cero datos sintéticos. Todo número está marcado como **medido** o **estimación**.

---

## 1. La recurrencia de Schur (Stieltjes) — derivada y validada

### 1.1 Definición

Ecuación clave: **σ·S ≡ ω (mod xⁿ)**, σ₀=1, deg σ=L, deg ω<L.
Campo GF(2¹²), POLY 0x1053. n=70 síndromes, L≤35.

La recurrencia de Schur es la **fracción continua de Stieltjes** de la serie
de síndromes S(x)=S₀+S₁x+S₂x²+…:

```
f₀ = S
γ_k = f_k(0)                         # parámetro de Schur (escalar)
f_{k+1} = x / (f_k − γ_k) = 1 / ((f_k − γ_k)/x)     # paso de Schur
```

Los convergentes p_k/q_k de la fracción continua se construyen por:

```
p₋₁=1, p₀=γ₀;  p_k = γ_k·p_{k−1} + x·p_{k−2}
q₋₁=0, q₀=1;   q_k = γ_k·q_{k−1} + x·q_{k−2}
```

**Resultado (validado): el convergente de índice 2L da (ω, σ)** — es decir,
q_{2L} = σ (normalizado a q₀=1) y p_{2L} = ω.

El "breakdown" del algoritmo en k=2L (f[1]==0, no hay recíproco) es el
agotamiento natural de la serie, no un fallo: las 2L+1 gammas γ₀..γ_{2L}
ya están calculadas y el convergente [2L] usa exactamente esas.

### 1.2 Validación clásica (MEDIDO)

Script: `schur_explora_stieltjes.py`, `schur_valida.py`, `schur_umbral.py`.

| Caso | L | σ == BM | Ec. clave σ·S≡ω (mod xⁿ) | deg ω | cola cero | gammas | breakdown |
|------|---|---------|--------------------------|-------|-----------|--------|-----------|
| k=2, n=6 | 2 | ✓ | ✓ | 1 | ✓ | 5 | k=4 |
| k=2, n=10 | 2 | ✓ | ✓ | 1 | ✓ | 5 | k=4 |
| k=5, n=20 | 5 | ✓ | ✓ | 4 | ✓ | 11 | k=10 |
| k=3, n=70 | 3 | ✓ | ✓ | 2 | ✓ | 7 | k=6 |
| k=8, n=70 | 8 | ✓ | ✓ | 7 | ✓ | 17 | k=16 |
| k=1, n=70 | 1 | ✓ | ✓ | 0 | ✓ | 3 | k=2 |
| k=12, n=70 | 12 | ✓ | ✓ | 11 | ✓ | 25 | k=24 |
| k=20, n=70 | 20 | ✓ | ✓ | 19 | ✓ | 41 | k=40 |
| k=35, n=70 | 35 | **✗** | **✗** | **35** | **✗** | 142 | — |

Barrido de umbral (`schur_umbral.py`, k=1..35 a n=70, semilla 123):
**Schur funciona para L=1..34 (todos correctos) y falla SOLO en L=35 (2L=n).**

El convergente [2L] es el aproximante de Padé [L−1/L]. Para L<35 coincide
con el convergente de Stieltjes; en el borde L=35 (2L=n) la tabla de Padé
tiene un bloque singular y el [34/35] **no es convergente** de la fracción
de Stieltjes (verificado: ninguno de los 142 convergentes da σ_BM).

### 1.3 El borde L=35 — impacto real (MEDIDO)

Distribución de L con el muestreador del verificador
(`verify_submission_dqi.sample_shots`, pesos óptimos, 2000 tiros, semilla 20261108):

| L | fracción |
|---|----------|
| 28 | 0.0525 |
| 29 | 0.0935 |
| 30 | 0.1385 |
| 31 | 0.1755 |
| 32 | 0.1935 |
| 33 | 0.1645 |
| 34 | 0.0895 |
| **35** | **0.0230** |

**P(L=35) = 0.0230 (2.30%), P(L≤34) = 0.9770.** (P(k=35)=0.0277 por los pesos;
L es a veces < k.)

Si un decodificador fallara en todos los L=35, ε≈0.023 y
R(ε)=ln2/−ln(½+2√ε) ≈ **3.17** (vs R≈1.20 actual, ε≈0.00094).
Eso es un factor 2.64× en R — se comería gran parte de la ganancia de Q².
**El borde L=35 no es despreciable; el decodificador final debe manejarlo.**

Intentos de arreglo del borde (todos medidos, todos negativos):
- **Síndrome revertido** (`schur_reverso_L35.py`): L*=35 también; rev(σ_BM)≠σ*_BM;
  ningún convergente de S* da σ*. No funciona.
- **Corrección lineal del convergente [70]** (`schur_corr_L35.py`): σ' XOR σ es
  un polinomio completo de grado 35 (no monomial, no múltiplo de ω ni de σ);
  σ'/σ tiene cociente constante [1733] y resto de grado 34. **No hay corrección
  lineal simple.** El [34/35] no se recupera de los convergentes de Stieltjes.

### 1.4 Estado in-place (clásico) — MEDIDO

La serie f_k vive en el arreglo S (n slots); el paso de Schur (shift + recíproco)
se hace en sitio; solo O(1) escalares extra (γ, pivote, temporal).
**max_slots = n+3** (medido en `schur_valida.py`: n=70 → 73 slots).
A escala completa: 73 coeficientes × 12 bits = **876 qubits de estado clásico**
(840 de S + 36 de trabajo). Esto es consistente con la frontera pública
(Q≈892 = 840 + ~52) **en el conteo clásico**.

**Pero (ver §3.3): este conteo clásico NO se traslada al circuito reversible.**

---

## 2. Costo en operaciones de campo — el Stieltjes es O(L·n²) (MEDIDO)

Script: `schur_costo_dist.py` (contador de `G.mul`/`G.inv`).

| Caso | L | BM (mul) | Schur (mul) | ratio | Schur a 42 ANDs/mul |
|------|---|----------|-------------|-------|---------------------|
| k=2, n=6 | 2 | 41 | 80 | 2.0× | ~3,360 T |
| k=5, n=20 | 5 | 301 | 2,090 | 6.9× | ~87,780 T |
| k=8, n=70 | 8 | 1,695 | 39,744 | 23.4× | ~1,669,248 T |
| k=20, n=70 | 20 | 3,891 | 99,360 | 25.5× | ~4,173,120 T |
| k=35, n=70 | 35 | 6,231 | **178,848** | **28.7×** | **~7,511,616 T** |

El Stieltjes hace un **recíproco completo O(n²) por paso de Schur**, y hay
2L+1 pasos → O(L·n²) operaciones de campo. BM es O(n²) (6,231 muls a L=35).
**El Stieltjes es ~29× más caro que BM a L=35, solo en multiplicaciones.**

A 42 ANDs por multiplicación GF(2¹²) (multiplicador por evaluación/interpolación
del diseño público): **~7.5M Toffolis solo en multiplicaciones** a L=35.
El DQI completo actual tiene 784,172 T. El Stieltjes costaría ~10× todo el DQI
solo en la etapa BM. **Inviable por costo, independientemente de Q.**

Inversiones: Schur 72 vs BM 70 a L=35 (no es el cuello; son las multiplicaciones).

---

## 3. Prototipo cuántico a escala chica (MEDIDO)

### 3.1 Recíproco de serie GF(2¹²), n=6

Script: `schur_proto_reciproco.py`. Usa `ixor_kmul` (Karatsuba, 54 AND) e
`init_kinv`/`del_kinv` (Itoh-Tsujii, 270 T) del DQI.
h[0]=inv(g[0]); h[k]=inv0·Σ_{i=1..k} g[i]·h[k−i].

**Resultado (simulador kickmix, 1 shot, semilla 1):**

| Métrica | Valor |
|---------|-------|
| Q | **243** |
| T (Toffoli-like) | **2,160** |
| reaction_depth | 20 |
| g intacto | ✓ |
| h correcto | ✓ (g·h ≡ 1 mod x⁶) |
| inv0 limpio | ✓ (0) |
| acc limpio | ✓ (0) |
| fase | 0 ✓ |

**T medido = 2,160 = exactamente el modelo teórico:**
35 productos GF(2¹²) × 54 AND = 1,890 + 1 inversión × 270 = **2,160**.
(35 = Σ_{k=1..5}(2k+1) = 3+5+7+9+11; el factor 2k+1 es k productos para el
acumulador + 1 para h[k] + k para limpiar el acumulador.)
El modelo de costo por operación está **validado exactamente** por el prototipo.

Q=243 = g 72 + h 72 + inv0 12 + acc 12 (=168) + 75 transitorios
(los ANDs de Karatsuba y el andamiaje de la inversión).

### 3.2 Extrapolación del recíproco a escala completa (ESTIMACIÓN)

Costo de un recíproco de longitud m: T_recip(m) ≈ 54·(m²−1) + 270
(verificado exactamente a m=6: 54·35+270=2,160).

El Schur hace 2L+1 recíprocos, con la serie encogiéndose (m=70−k).
T_Schur ≈ Σ_{k=0}^{2L} [54·((70−k)²−1) + 270].
A L=35: ≈ 54·Σ_{m=0}^{70} m² + 71·270 ≈ 54·116,795 + 19,170 ≈ **6.33M T**.
(El conteo clásico de longitud completa da 178,848 muls × 54 ≈ 9.66M T;
el rango honesto es **~6–10M T**.)

**Incluso la estimación optimista (6.33M T) es ~8× el DQI completo (784k T).**

### 3.3 Corrección al "in-place": el recíproco necesita 2n en el setting reversible

El conteo clásico (n+3 slots, §1.4) es engañoso para el circuito cuántico.
El recíproco h=1/g necesita **g y h vivas simultáneamente** (h[k] depende de
g[1..k] original y de h[0..k−1] ya calculados; sobrescribir g[k] con h[k]
destruye g[k] que se necesita para h[j>k]). El prototipo lo confirma:
usa g (72) **y** h (72) como registros separados.

En el circuito, la serie necesita **2 arreglos de n coeficientes (ping-pong)**:
paso k calcula h en B desde g en A; paso k+1 calcula en A desde B.
**Q_serie ≈ 2·70·12 = 1,680 qubits** (+ inv0 12 + acc 12 + transitorios),
es decir **Q ≈ 1,704+**, NO los ~892 del conteo clásico.

(Un recíproco verdaderamente in-place en un solo arreglo existe clásicamente
— recuperando g_i desde h_0..h_i por inversión del sistema triangular — pero
es complejo de reversibilizar y **no cambia el costo T ~6–10M**, que ya es
inviable por sí solo.)

**Conclusión: el Stieltjes Schur, como circuito cuántico, tendría
Q ≈ 1,704 y T ≈ 6–10M, PEOR que BM v1 (Q=1,949, T=784k) en T por ~8–12×.
Costo DQI estimado: R·Q²·T ≈ 1.20·1704²·6.33M ≈ 2.2e13, vs 3.57e12 actual
(ratio ~0.16×, es decir ~6× PEOR). Definitivamente descartado.**

---

## 4. Lo que queda: el Schur O(n²) por bloques 2×2 (el diseño público)

El decodificador público (jday96314/QuantumAI → Alex Chilton → SomeJoint)
logra Q≈889–897, T≈407–440k, ratio 59–63×, con R≈1.26 (ε≈0.0015, o sea
**sí maneja L=35**). Sus señas, de `docs/PANORAMA_PUBLICO.md`:

- 840 de síndromes + ≈52 de trabajo.
- **Palabras de 24 bits** (2 coeficientes GF(2¹²) por palabra).
- Multiplicador GF(2¹²) de 42 ANDs (evaluación/interpolación sobre GF(8):
  7 puntos × 6 ANDs); **GF(2²⁴) de 99 ANDs**.
- Inversos en torre; fase vía producto Clifford; banderas de polo/acarreo
  con poda de eventos raros.

Esto apunta a un **Schur por bloques 2×2** (Schur matricial / "matrix BM"):
la recurrencia opera sobre palabras de 24 bits (pares de coeficientes) y el
estado de trabajo es un bloque 2×2 (≈4 palabras ≈ 48–52 qubits). Un bloque
2×2 absorbe el bloque singular de la tabla de Padé (el borde L=35) procesando
2 pasos a la vez — por eso maneja L=35 y por eso es O(n²) y no O(L·n²):
cada paso 2×2 actualiza el bloque y consume 2 coeficientes de S, sin
recíprocos de serie completa.

**Plan concreto del siguiente paso (no hecho en esta sesión):**
1. Formular la ecuación clave como problema de polinomios matriciales 2×2
   (la "matrix Berlekamp-Massey" / algoritmo de Schur para 2×2).
2. Derivar la recurrencia 2×2 (los parámetros de Schur son matrices 2×2
   sobre GF(2¹²), o equivalentemente elementos de GF(2²⁴)).
3. Validarla clásicamente (σ correcto, L=1..35 incluido el borde, ec. clave).
4. Contar operaciones de campo (debe ser O(n²), ~6k muls como BM, no ~179k).
5. Diseñar el circuito (S + bloque 2×2 ≈ 840+52 qubits) y prototipar a
   escala chica en kickmix; medir Q y T; extrapolar.
6. Si Q≈892 y T≈407k se reproducen, el DQI pasaría a ratio ~60× y el
   geomean de ~3.31× a ~6.9× (estimación, T sin medir).

**Alternativa si el 2×2 no cierra:** el "Schur complement" de Kailath para
sistemas Hankel (desplazamiento de rango 2) — pero ese mantiene 2 generadores
(2n de estado), igual que BM, por lo que no es el camino a Q≈892. El 2×2 es
el candidato que encaja con las señas públicas.

---

## 5. Resumen de resultados (medido vs estimación)

| Ítem | Valor | Tipo |
|------|-------|------|
| Recurrencia de Schur (Stieltjes) derivada | f_{k+1}=1/((f_k−γ_k)/x), convergente [2L]=(ω,σ) | derivación |
| Validación clásica | σ correcto, ec. clave, L=1..34 (9 casos + barrido k=1..35) | **medido** |
| Borde L=35 | falla (ningún convergente da σ); P(L=35)=0.0230, P(L≤34)=0.9770 (2000 tiros) | **medido** |
| Arreglos del borde | revertido ✗, corrección lineal ✗ | **medido** |
| Estado clásico | n+3 slots (73 a n=70) | **medido** |
| Costo campo (L=35) | Schur 178,848 muls vs BM 6,231 (28.7×); ~7.5M T a 42 ANDs | **medido** |
| Prototipo recíproco n=6 | Q=243, T=2,160 (exacto al modelo), g intacto, h correcto, ancillas limpios, fase 0 | **medido** |
| Extrapolación Stieltjes (L=35) | T ≈ 6–10M, Q ≈ 1,704 (ping-pong 2n) | **estimación** |
| Costo DQI si se usara Stieltjes | ≈2.2e13, ratio ~0.16× (~6× peor que actual) | **estimación** |
| Diseño público (referencia) | Q≈892, T≈407k, ratio 59–63×, R≈1.26 | referencia pública |
| Siguiente paso | Schur 2×2 por bloques (O(n²), maneja L=35) | pendiente |

**Veredicto:** la recurrencia de Schur (Stieltjes) es correcta matemáticamente
e in-place en el sentido clásico, pero **no es la recurrencia del decodificador
público ni es viable como circuito**: su costo O(L·n²) (~7.5M T) y su
almacenamiento reversible 2n (Q≈1,704) la dejan fuera. El proyecto mayor que
queda es derivar el Schur por bloques 2×2 O(n²), que es el que encaja con
todas las señas del diseño público (24-bit words, GF(2²⁴) 99 ANDs, ~52 trabajo,
maneja L=35).

---

## 6. Archivos

En `~/workspace/qcc-data/dqi-perfil/`:
- `schur_explora_stieltjes.py` — Schur (Stieltjes) + convergentes (validado).
- `schur_valida.py` — validación completa (σ, ec. clave, cola, slots) 9 casos.
- `schur_umbral.py` — barrido k=1..35 (umbral L=35).
- `schur_diag_L35.py` — diagnóstico del borde (ningún convergente da σ).
- `schur_reverso_L35.py` — intento revertido (negativo).
- `schur_corr_L35.py` — intento corrección lineal (negativo).
- `schur_costo_dist.py` — conteo de ops de campo + distribución real de L.
- `schur_proto_reciproco.py` — prototipo kickmix del recíproco n=6
  (Q=243, T=2,160, correcto y limpio).
- `REPORTE_SCHUR_RECURRENCIA.md` — este reporte.

Reportes previos (contexto): `REPORTE_PERFIL_DQI.md`, `REPORTE_BANDERAS_RECOMPUTO.md`,
`REPORTE_BM_INPLACE.md`, `REPORTE_SCAN_MBU.md`.
