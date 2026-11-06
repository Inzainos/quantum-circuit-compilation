# DQI — estado real, qué falta y qué no se puede (2026-11-04)

Base: circuito de referencia (Q=1893, T=5,725,461) y `src/dqi_optimized_v10.py` (Q=1888, T máx 5,708,829, PASS oficial 2,560 shots).
Score = R(eps+)·Q²·T. Ratio actual contra la referencia ≈ 1.0. Cifras de otros participantes (repos públicos, NO verificadas): ratio ≈ 63 con Q=892 y T≈407k.

## 1. Implementado y verificado
| Elemento | Estado |
|---|---|
| Referencia ProosAndZalka (EEA sincronizado + Chien + Forney + MBUC) | PASS |
| v10: contadores 7 bits, longitud activa | PASS, mejora 0.3 % en T y 5 qubits |
| Reproducción desde el repo (`submission/rebuild_valid_zip.py`) | sha256 ef1fc095…a41 |

Nota: la etapa `horner_iqft_forney_mbuc` de v10 es el Chien+Forney de la referencia (registros multiplicados por constantes, lineal; una inversión con scaffold por posición, 4095 posiciones). `galois_iqft.py` y `cooley_tukey_iqft.py` NO se usan en el camino real.

## 2. Documentado pero roto, incompleto o falso
| Elemento | Problema |
|---|---|
| `dqi_cmq.py` (Gauss-Jordan + bloque topológico) | T=19,031 es falso: no calcula σ/ω, phase_errors 112/256. No es resultado. |
| `dqi_bma_v11.py`, `berlekamp_massey.py` | Esqueletos/placeholder; Q=2184 sin decodificar. |
| `dqi_from_zero.py`, `dqi_optimized_v5.py`, `bma_bloq.py` y demás bloqs | Esqueletos o mocks (qualtran, sin puente a kickmix). |
| Docs: "contadores 7 bits fallan" (v2/v4) | Desactualizado: v10 lo logra con contadores 7 bits y PASS. |
| "Horner iQFT reemplaza Chien+Forney" | No es cierto en el código de v10. |
| "dqi Q=138 / 245,000×" (README/notebook anteriores) | Sin verificar; descartado. |

## 3. Se puede implementar (hipótesis, sin medir salvo lo indicado)
1. **Poda guiada por simulación (dead-op elimination).** Correr N tiros, registrar qué compuertas controladas nunca actúan (registro conocido en 0 en esa iteración), y eliminarlas; los fallos raros se pagan en eps+ (cada fallo ≈0.45 % en el ratio a N=102,400). Un repo público reporta T 5.73M→5.16M (−10 %) así. Es automatizable con el simulador de kickmix.
2. **Truncar n_iters.** `default_n_iters(70)` = 222 iteraciones del EEA sincronizado; medir la distribución real de iteraciones útiles con los pesos del verificador (28–35 concentran ≈87 %) y recortar al percentil que dé el mejor R·T. Medición pendiente.
3. **BM reversible con historia.** Modelo clásico validado (`src/dqi_bm_model.py`, 60/60 correctos). Costos medidos: ixor_gf2_mul 63 Toffolis, división 378. Un pase ≈ 3,780 mac + 70 divisiones ≈ 265k; ida y vuelta ≈ 600k. Riesgo: historia ≈ 840 qubits (o pebbling). Ahorro potencial en T frente al EEA, a validar a escala chica contra el baseline (m=15, n=6, grado 4: Q=140, T=33,258, score 775,871,398.78).
4. **Reusar el scaffold de inversión entre posiciones** (hoy se crea/borra por posición); requiere división/inversión manual porque la API no acepta scaffold preexistente.
5. **Poda de ramas raras** (banderas de polo recomputadas, bajar el pico de ancho en 1 qubit): ahorro ≈0.1 %. Bajo impacto.
6. **Ancilla: 1,053 qubits de scratch** reportados como optimizables en la documentación; medir el pico real por etapa y reusar registros entre etapas (Q² pesa el doble que T).

## 4. No se puede (con la razón)
- **Medir σ o guardar hashes en un arreglo clásico:** colapsa la superposición sobre soportes de error que DQI necesita; el contrato solo admite compuertas reversibles, fases y uncomputación por medición en base X.
- **Hash como bandera para limpiar:** no lleva el valor a borrar; limpiar con control cuesta lo mismo. Sirve como bandera de validez, no ahorra T ni Q. (La regla hash_in==hash_out ya existe en `qubit_temporal_manager.py`.)
- **Transformada completa de 4095 puntos:** ≈49,000 qubits vivos; Q²·T lo hace inviable. En flujo es la búsqueda de Chien actual.
- **Fase como función lineal de S:** (-1)^Σ popcount(e_j & M_j) depende de e, que no es lineal en S salvo que μ_j esté en el span de grado <70.
- **Costos "declarados" (Plan B `_t_complexity_`) o ciclos que dependen de datos:** no entran al verificador kickmix; el circuito es estático.

## 5. Ideas nuevas / de otros
- Fase como una sola traza: Σ_j popcount(e_j & M_j) = Tr(Σ_j μ_j e_j) con μ_j = M_j mapeado a la base dual (clásico). Reduce la acumulación de fase a una sola traza, pero no elimina la división de Forney.
- Inversión por lotes (Montgomery): ≈3 mult por elemento vs 4–5 de una inversión suelta, pero exige guardar todas las posiciones; solo sirve si se compacta el soporte.
- Elegir j: la fracción de posiciones con M_j=0 es 1/4096; no hay ahorro por condiciones clásicas.
- Rediseño en sitio (840 qubits de entrada + ≈52 de trabajo, ≈100 Toffolis/posición) como el de referencia pública: es el único camino al orden de magnitud faltante; requiere rediseñar la etapa por posición.

## 6. Mediciones (2026-11-04, herramientas en `tools/`)
**Desglose de T de v10 (medido con el builder):** EEA directo 222 it = 2,132,454; ×2 (ida y vuelta) = 4,264,908 (74.7 %); Forney + desplazamiento inicial = 1,443,921 (25.3 %). ≈9.6k Toffolis por iteración del EEA y dirección (≈73 multiplicaciones de 63 por barrido).

**Recorte de n_iters** (`tools/dqi_sweep_niters.py`, 10,240 tiros, mismos pesos que el verificador):
| n_iters | fallos | T |
|---|---|---|
| 222 (default) | 0 / 2,560 | 5,708,480 |
| 221 | 0 / 10,240 | 5,689,138 |
| 220 | 0 / 10,240 | 5,669,792 |
| 218 | 2 / 10,240 | 5,631,100 |
| 216 | 5 / 10,240 | 5,592,408 |
| 214 | 5,073 / 10,240 | — |
| ≤210 | ≈50 % de tiros fallan | — |
Hay un precipicio en ≈214–216: casi todos los tiros necesitan ≈215–217 iteraciones (pesos de error concentrados en 28–35). Ganancia máxima realista ≈0.7–1.9 % en T, a costa de fallos que suben R. Descartado como palanca grande.

**Actividad de registros** (`tools/dqi_activity.py`, 2,560 tiros, prefijos k=0..100): reg_a[i] está activo (≠0) en ≈100 % de los tiros en casi todas las posiciones e iteraciones (2 de 1,898 sitios (k,i) por debajo de 1e-3); reg_b en ≈94.5 % de media, 123 sitios inactivos. La poda por "registro siempre en cero" ahorra ≈0 %: los polinomios del EEA ocupan casi toda la ventana en casi todos los tiros. El −10 % reportado por otros repos viene de otros sitios (multiplicador/CSWAP), no de registros en cero.

**Desglose del EEA directo por paso** (T de 222 iteraciones, anulando un paso a la vez en el generador):
| Paso | T | % del EEA directo |
|---|---|---|
| `_multiply_and_add_or_sub` | 1,611,890 | 75.6 % |
| `_shift_b_array_right` | 236,710 | 11.1 % |
| `_update_flag` | 29,748 | 1.4 % |
| `_update_metadata` | 11,100 | 0.5 % |
| resto (swap, contadores, halting) | ≈242,000 | ≈11 % |
Dentro de `_multiply_and_add_or_sub` (≈7.26k por iteración): 2 divisiones (≈756), ≈73 multiplicaciones-acumulación de 63 (≈4.6k) y ≈1.9k de iteración unaria/comparadores.

**Corrección de la estimación de BM reversible** (la estimación anterior de ≈300k/pase era optimista):
- El mapa (σ, B̃) → (σ + c·B̃, x·σ) tiene determinante c·x ≠ 1: requiere escalar en sitio por un escalar cuántico (≈72 multiplicaciones + una inversión) en cada iteración, porque la rama es dependiente de datos y el circuito es estático. Una iteración queda en ≈144 multiplicaciones ≈ 9–10k Toffolis, parecido al EEA actual.
- BM necesita solo 70 iteraciones (contra 222 del EEA sincronizado): ≈0.7M por pase en vez de 2.13M.
- Pero no es reversible sin historia: c_r (12 bits por paso, ≈840 qubits) no es recuperable desde el estado posterior. Q pasaría de ≈1888 a ≈2,700. Con Q²·T el efecto neto sería ≈1.0×.
- Conclusión: BM con historia no mejora Q²·T. Queda abierta solo una variante que escale B en vez de σ y evite la historia, sin demostrar.

**Análisis estructural del barrido (sin medir salvo lo indicado)**
- Los arreglos `reg_a`/`reg_b` guardan cada uno [resto | cofactor] concatenados (grado del resto + grado del cofactor ≈ n), por eso la actividad medida es ≈100 % en todas las posiciones: no hay ventana activa que recortar.
- Un barrido de ≈73 multiplicaciones corre en las 222 iteraciones, pero solo ≈n+1 ≈ 73 de ellas hacen multiplicación efectiva por tiro (≈1/3): holgura teórica de ≈2/3 del 76 % del EEA, pero el esquema síncrono (un tiro puede necesitar k multiplicaciones seguidas) impide agruparlas en iteraciones fijas sin cambiar el algoritmo.
- Cota de información: en el paradigma (resto, cofactor) hay que guardar S (840) + otro arreglo de ≈876; BM sin restos guarda en su lugar ≈840 de historia. El Q=892 que reporta un repo público (840 de entrada + ≈52) implica un paradigma distinto, no una variante de este EEA ni de BM.
- Próximo paso útil: estudiar la estructura (nombres de marcas, histograma de compuertas) de circuitos públicos de otros participantes. Requiere adjuntar esos repos a la sesión (add_repo) y revisar las reglas de la competencia antes de reutilizar nada.
