# Rediseño BM in-place del DQI — 2026-11-08

## 0. Resumen ejecutivo

**Veredicto: el BM in-place (Q≈1,150, geomean 4.70x) NO se logra retocando BM v1.
Requiere un rediseño tipo Schur con estado de O(1) palabras, donde el estado
vive en el arreglo del síndrome S en vez de en registros sigma/tau separados.**
Esto ya lo anticipaban los docs del repo (`DQI_estado_e_ideas.md` §6,
`PANORAMA_PUBLICO.md`); aquí queda medido y con el mecanismo prototipado.

**Lo medido en esta sesión:**
- **BM v1 no se puede comprimir por reuso de registros.** El pico Q=1,949
  está fijado por dos polinomios completos (sigma 432 + tau 432) + S 840 +
  d/H/banderas 160 + transitorios 85. Los dos polinomios son necesarios
  en esta formulación (la actualización necesita ambos simultáneamente) y
  las banderas ya se probaron necesarias (dependencia circular). El piso
  de BM v1 es Q≈1,864 (sin transitorios), no 1,150.
- **El EEA ingenuo NO es la respuesta.** El modelo clásico del EEA
  produce el σ correcto y cumple la ecuación clave, pero su estado es
  ~2n coeficientes (143 slots a n=70), **peor** que sigma+tau de BM (72).
  Un EEA ingenuo como circuito cuántico usaría MÁS qubits que BM v1.
- **El mecanismo in-place SÍ funciona (prototipo cuántico medido).** Un
  paso de división EEA/Schur con el estado en el arreglo de entrada:
  ida Q=165, T=345, A' correcto, fase 0; ida+vuelta Q=165, T=690, A
  restaurado, fase 0. El estado vive en el arreglo (A se sobrescribe),
  la vuelta lo restaura, y el trabajo extra es O(1) (~45 qubits).
  Esto valida el mecanismo del decodificador tipo Schur: Q ≈ 840 (S) +
  ~52 (trabajo) ≈ **892**, consistente con la frontera pública (Q≈889).

**Proyección (T sin cambio salvo lo indicado):**

| Escenario | Q | T | ratio DQI | geomean |
|---|---|---|---|---|
| Actual | 1,949 | 784,172 | 6.77x | 3.31x |
| **BM in-place Q≈1,150 (conservador)** | 1,150 | 784,172 | **19.45x** | **4.70x** |
| **BM in-place Q≈892 (frontera, estado en S)** | 892 | 784,172 | **32.32x** | **5.57x** |

**Qué falta:** la derivación completa de la recurrencia de Schur (el
diseño clásico de jday96314/QuantumAI) y la construcción del decodificador
in-place completo como circuito. Este reporte deja el diseño de
arquitectura, el mecanismo validado a escala chica y la extrapolación;
el circuito completo es un proyecto mayor (el propio doc del repo lo
marca así). Main y ZIP intactos; todo es scratch.

---

## 1. BM v1: el piso estructural (medido)

### 1.1 Baseline a escala chica

BM v1 (`src/dqi_bm_stage_v1.py`) a escala chica (n=6, LS=6, k=2), script
`bm_inplace_baseline_chico.py`:

| Circuito | Q | T |
|---|---|---|
| BM v1 forward+reverse | 333 | 7,680 |
| BM v1 forward solo | 333 | 4,302 |

Composición de Q (forward): S 72 + sigma 72 + tau 72 + d 8 + H 12 +
banderas 12 + transitorios 85 = 333. Sigma+tau son el 43% de Q (a escala
completa, 864/1,949 = 44%). El modelo clásico confirma sigma final
[1, 281, 2301], L=2, correcto para k=2.

### 1.2 Por qué dos polinomios son necesarios en BM v1

La actualización de BM es `sigma[i] ^= alpha * tau[i]` (para
i=0..bu(r)), donde tau es el sigma anterior (el polinomio B). En cada
ronda se necesitan AMBOS simultáneamente: tau se lee y sigma se escribe.
En un `replace` (p=1) además se intercambian (cswap) y tau rota
(reetiquetado). Después del intercambio, sigma_nuevo = tau_viejo +
alpha*sigma_viejo y tau_nuevo = sigma_viejo: ambos arreglos guardan
datos distintos. No hay reordenamiento que los funda en uno solo:

- **Orden decreciente no ahorra almacenamiento.** El truco clásico
  (procesar i en orden decreciente para que la escritura `sig[i+m]`
  no pise la lectura `B[i]`) evita un temporal, pero B y sigma siguen
  necesitando 2·(L+1) coeficientes en total. El almacenamiento es el
  mismo; solo cambia el temporal.
- **La cota de grados no ayuda.** L + L' ≤ r+1 (L = grado actual,
  L' = grado anterior). Al final (r=69) L+L' ≤ 70, o sea 72
  coeficientes como máximo — igual que 36+36. No hay holgura.
- **Compartir un arreglo de 36 no cabe.** Sigma ocupa [0..L] y tau
  [0..L']; en el peor caso (L=35, L'=34) se solapan. Un solo arreglo
  de 36 no los contiene; haría falta uno de 72, que es lo mismo que
  dos de 36.
- **Reutilizar S no baja el pico.** S[j] se usa en `_disc` hasta la
  ronda ~2j y S[0..34] lo usa omega después de BM. El pico Q=1,949 se
  fija en la ronda 69 de bm_forward, cuando S está totalmente vivo.
  Sobrescribir S con sigma/tau exigiría guardar los valores de S
  (son entrada, no se pueden recomputar) — solo mueve el
  almacenamiento. Además el verificador exige S restaurado
  (`verifiers/dqi/verify_submission_dqi.py`: "S0..S{n-1} must be
  restored, all other qubits must return to |0>").

**Piso de BM v1:** S 840 + sigma 432 + tau 432 + d 8 + H 12 +
banderas 140 = 1,864 vivos (1,949 con transitorios). Las banderas ya
se probaron necesarias (dependencia circular,
`REPORTE_BANDERAS_RECOMPUTO.md`). **Ningún reuso de registros dentro
de BM v1 baja de ~1,864. El Q≈1,150 exige cambiar de paradigma.**

### 1.3 El verificador y la restauración

El contrato del verificador DQI (`verify_submission_dqi.py`): S debe
restaurarse y todos los demás qubits deben volver a |0⟩. Por eso el
decodificador hace `bm.reverse()` y luego `x(sigma[0][0])`,
`x(tau[1][0])`, `x(d[0])`. Cualquier variante in-place debe cumplir
lo mismo: S restaurado y ancillas a |0⟩. El prototipo de §4 lo verifica
(S restaurado, fase 0).

---

## 2. El EEA ingenuo NO es la respuesta (modelo clásico verificado)

### 2.1 El modelo

`bm_inplace_eea_modelo.py`: EEA sobre (x^n, S(x)) para la ecuación
clave σ(x)·S(x) ≡ ω(x) (mod x^n), con regla de parada estándar
(deg r < deg t). Verifica que σ coincide con `dqi_bm_model.bm` y que
la ecuación clave se cumple.

| k | n | L (BM) | L (EEA) | σ igual | ec. clave | max_slots |
|---|---|---|---|---|---|---|
| 2 | 6 | 2 | 2 | sí | sí | 15 |
| 2 | 10 | 2 | 2 | sí | sí | 23 |
| 5 | 20 | 5 | 5 | sí | sí | 43 |
| 3 | 70 | 3 | 3 | sí | sí | 143 |
| 8 | 70 | 8 | 8 | sí | sí | 143 |

El EEA produce el σ correcto (ej. k=2, n=6: σ=[1, 281, 2301],
igual que BM). El algoritmo es correcto.

### 2.2 El hallazgo: el estado del EEA es ~2n coeficientes

`max_slots` = máximo número de coeficientes almacenados
simultáneamente en el estado (r_prev, r, t_prev, t). Trazo a n=70,
k=8:

| it | deg r_prev | deg r | deg t_prev | deg t | slots |
|---|---|---|---|---|---|
| 0 | 70 | 69 | 0 | 0 | 143 |
| 1–7 | 69–63 | 68–62 | 0–6 | 1–7 | 142 |
| 8 | 62 | 7 | 7 | 8 | 88 |

El estado es ~2n coeficientes durante casi toda la iteración
(142–143 a n=70) y colapsa a 88 solo al converger. A escala completa
eso son ~140 coeficientes × 12 bits ≈ **1,680 qubits de estado**,
**peor** que sigma+tau de BM v1 (72 coeficientes, 864 qubits).

Razón: el EEA mantiene dos pares (r_prev, r) y (t_prev, t), con
deg(r_i) + deg(t_i) ≈ n por par, o sea ~2n en total. El "in-place"
del EEA solo reutiliza la memoria (r_next sobrescribe r_prev), no
reduce la cantidad de coeficientes. Y además el EEA tiene control
dependiente de datos (los grados y el número de pasos dependen del
sindrome), difícil de volver circuito estático.

**Conclusión:** un EEA ingenuo como circuito cuántico usaría MÁS
qubits que BM v1. No es el camino a Q≈1,150. La frontera pública
(Q≈889) usa un paradigma distinto (Schur con estado O(1)), no un EEA
ingenuo. Esto coincide con `DQI_estado_e_ideas.md` §6: "El Q=892 que
reporta un repo público (840 de entrada + ≈52) implica un paradigma
distinto, no una variante de este EEA ni de BM."

---

## 3. Diseño in-place tipo Schur (arquitectura)

### 3.1 Idea central

El estado del decodificador vive **en el arreglo del síndrome S**
(840 qubits, entrada que debe persistir), transformado en sitio, y
el trabajo extra es O(1) palabras (~52 qubits). No hay registros
sigma/tau separados. Es el mismo patrón que ya usa la etapa omega
del decodificador actual (`build_omega_tmp` transforma S en sitio y
`omega_rev` lo restaura): la diferencia es que aquí **toda** la etapa
BM se reformula como transformaciones reversibles sobre S.

Flujo de datos:

```
S (70×12, entrada)
  │  Schur/BM in-place: transformaciones reversibles sobre S
  │  (cada paso consume valores de S y escribe estado en su lugar;
  │   el estado total se conserva: 70 valores)
  ▼
S transformado: contiene σ (o su equivalente) + resto
  │  omega in-place sobre S (ya existe) + scan (leen σ y S)
  ▼
  │  vuelta: se deshacen las transformaciones en orden inverso
  ▼
S restaurado (verificador), ancillas a |0⟩
```

### 3.2 Qué debe cumplir la recurrencia (requisitos)

Para que el diseño cierre, la recurrencia de Schur debe:

1. **Estado O(1) palabras además de S.** Solo unos pocos elementos
   de campo (d, banderas, temporales de inversión/multiplicación)
   fuera de S. El resto del estado vive en S.
2. **Cada valor de S se consume una vez.** A diferencia de BM v1
   (donde `_disc` relee S[r-i] en muchas rondas), la recurrencia de
   Schur usa cada valor de S para calcular un coeficiente y luego lo
   sobrescribe con estado. Por eso el estado cabe en S.
3. **Transformaciones reversibles.** Cada paso es una operación
   reversible sobre S (como el paso prototipado en §4), así que la
   vuelta deshace los pasos en orden inverso y restaura S.
4. **Estructura fija (circuito estático).** Número fijo de pasos y
   tamaños fijos (sin control dependiente de datos en los grados),
   como BM v1 (70 rondas fijas). El EEA ingenuo falla aquí (grados
   dependientes de datos).
5. **σ disponible para omega/scan.** Al final, σ (o los valores
   σ(r), ω(r) que necesita el scan) se leen del S transformado
   (fuentes lineales, como el scan actual lee σ y S).

### 3.3 La vuelta sin historia

La vuelta no necesita historia (ni banderas p/t guardadas ni D_old)
porque cada paso es reversible por construcción: deshacer el paso
i-ésimo solo requiere el estado actual (transformado) y los
temporales del paso, no los valores originales. Es el mismo principio
que omega_rev y que el paso prototipado en §4 (la vuelta reaplica la
misma multiplicación-acumulación y restaura A). La información no se
pierde: se transforma, y la transformación es invertible.

### 3.4 Qué falta (trabajo restante, honesto)

- **Derivar la recurrencia de Schur concreta.** El diseño clásico
  es el de jday96314/QuantumAI (citado en `PANORAMA_PUBLICO.md`).
  Hay que estudiarlo y reescribirlo, como ya marca
  `DQI_estado_e_ideas.md` §6 ("requiere estudiar la estructura...
  de circuitos públicos"). Este reporte NO deriva la recurrencia
  completa; deja la arquitectura, los requisitos y el mecanismo
  validado.
- **Construir el decodificador in-place completo** como circuito
  kickmix a escala completa y validarlo con el verificador oficial
  (muestreo + escala chica primero; el verificador DQI completo no
  corre en esta caja).
- **Medir T a escala completa.** El per-paso medido (§4) es 345 T;
  el T total del decodificador in-place depende del número de pasos
  y de los grados de los cocientes, que son de la recurrencia de
  Schur (no medidos aquí).

---

## 4. Prototipo cuántico del paso in-place (medido)

### 4.1 Qué es

`bm_inplace_paso_eea.py`: un paso de división EEA/Schur con grados
fijos (A grado 5, B grado 3, GF(2^12)), el núcleo del decodificador
in-place:

```
q = A[5] / B[3]              (1 inversión torre + 1 multiplicación)
A[i] ^= q * B[i-2], i=2..5   (4 multiplicaciones-acumulación, EN EL SITIO)
```

Tras el paso, A[5]=0 (término líder eliminado). El cociente q es
salida legítima del paso (en el EEA completo actualiza t). La vuelta
reaplica la multiplicación-acumulación (restaura A) y libera q.

### 4.2 Resultados (simulador kickmix)

Valores de prueba: A=[3324, 351, 735, 970, 743, 3282],
B=[3560, 2384, 162, 386]. q esperado 2010.

| Circuito | Q | T | Verificación |
|---|---|---|---|
| Paso, solo ida | 165 | 345 | A'=[3324, 351, 3087, 3957, 1040, 0] **OK** (A'[5]=0), B intacto, fase 0 |
| Paso, ida+vuelta | 165 | 690 | A restaurado **OK**, B intacto, fase 0 |

Desglose de T (ida, 345): inversión torre (~38) + q (63) + 4×
multiplicación-acumulación (4×63=252) ≈ 353 (medido 345). La vuelta
es exactamente 2× (690), como corresponde a un paso reversible.

Desglose de Q (165): A 72 + B 48 (el "arreglo S", 120) + q 12 +
temporales ~33 (inversión + multiplicadores, reutilizados). **No hay
registro sigma/tau separado**: el estado vive en A (se sobrescribe)
y el trabajo extra es O(1) (~45 qubits). A escala completa, esto es
lo que da Q ≈ 840 (S) + ~52 (trabajo) ≈ **892**.

### 4.3 Comparación con BM v1 a escala chica

| | BM v1 (n=6, LS=6) | Paso in-place (A₅, B₃) |
|---|---|---|
| Q | 333 (S 72 + σ 72 + τ 72 + d/H/banderas 32 + trans. 85) | 165 (A 72 + B 48 + q 12 + temp. 33) |
| T (ida+vuelta) | 7,680 | 690 (un paso) |

No son directamente comparables (el paso es una sola división; BM v1
son 6 rondas completas), pero muestran el mecanismo: el in-place no
necesita los 144 qubits de σ+τ, solo el arreglo de entrada + O(1)
trabajo. El ahorro de Q es estructural, no un ajuste.

---

## 5. Extrapolación a escala completa (medido vs estimado)

**Medido:**
- BM v1 a escala chica: Q=333, T=7,680 (forward+reverse).
- EEA clásico: σ correcto, ecuación clave OK; estado ~2n
  coeficientes (143 slots a n=70) — peor que BM.
- Paso in-place: Q=165, T=345 (ida) / 690 (ida+vuelta); A'
  correcto, A restaurado, fase 0.

**Estimado (no medido, marcar como tal):**
- Q del decodificador in-place completo: ≈ 840 (S) + ~52 (trabajo)
  ≈ **892**, por el mecanismo medido en §4 y consistente con la
  frontera pública (Q≈889). La proyección conservadora del perfil
  (Q≈1,150) deja margen por si el trabajo es mayor.
- T del decodificador in-place completo: **no medido**. El per-paso
  es 345 T (medido), pero el número de pasos y los grados de los
  cocientes dependen de la recurrencia de Schur (no derivada aquí).
  La tabla de abajo usa T sin cambio (784,172) como cota conservadora;
  si el in-place además baja T (el BM actual son 298,232 T entre ida
  y vuelta), la ganancia sería mayor.

| Escenario | Q | T | costo R·Q²·T | ratio DQI | geomean |
|---|---|---|---|---|---|
| Actual | 1,949 | 784,172 | 3.5745e12 | 6.77x | 3.31x |
| **In-place Q≈1,150 (conservador)** | 1,150 | 784,172 | 1.2445e12 | **19.45x** | **4.70x** |
| **In-place Q≈892 (frontera)** | 892 | 784,172 | 7.4873e11 | **32.32x** | **5.57x** |
| In-place Q≈892 + scan MBU (T=689,987) | 892 | 689,987 | 6.5880e11 | 36.73x | 5.82x |

(R≈1.20, baseline≈2.42e13, invsqrt 5.32x, dfthcsos 1.00583x; cifras
de R/baseline de la recalibración 2026-11-07, no medidas aquí. El
scan MBU es teórico, no medido.)

---

## 6. Conclusión

1. **BM v1 está en su piso.** Dos polinomios completos son
   necesarios en su formulación y las banderas también. Q≈1,864 es
   el piso; el Q≈1,150 no sale de retocar BM v1.
2. **El EEA ingenuo empeora Q** (~2n coeficientes de estado). No es
   el camino.
3. **El camino es el decodificador tipo Schur con estado O(1) en S.**
   El mecanismo está validado a escala chica (paso in-place: Q=165,
   T=345, correcto y reversible). La Q proyectada ≈892–1,150
   (geomean 4.70x–5.57x) es consistente con la frontera pública.
4. **Falta derivar la recurrencia de Schur** (diseño clásico
   jday96314/QuantumAI) y construir el decodificador completo. Es
   el siguiente paso, y es un proyecto mayor que un prototipo.

## 7. Archivos

- `REPORTE_BM_INPLACE.md` — este archivo
- `bm_inplace_baseline_chico.py` — baseline BM v1 a escala chica +
  perfil de grados por ronda
- `bm_inplace_eea_modelo.py` — modelo clásico EEA (σ correcto,
  ecuación clave, conteo de slots)
- `bm_inplace_paso_eea.py` — prototipo cuántico del paso in-place
  (Q=165, T=345 ida / 690 ida+vuelta, verificado en simulador)

Caveats: el verificador DQI completo no corre en esta caja (8 GB,
`reaction_depth` → bad_alloc); R≈1.20 y baseline≈2.42e13 son de la
recalibración 2026-11-07. Las pruebas son a escala chica (n=6) con el
simulador kickmix; la extrapolación a escala completa está marcada
como estimación. Main y el ZIP vigente no se tocaron; todo el trabajo
es scratch en `~/workspace/qcc-data/dqi-perfil/`.
