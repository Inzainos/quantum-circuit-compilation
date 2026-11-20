# SUPERVISIÓN DE DATOS — Gold del QF (parche Claude, −7 qubits): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~14:51 CST
**Supervisor:** Datos (Analista de datos)
**Cadena:** Programación (construye + Gold) → Brujo ✓ → **Datos (este
documento)** → Auditor ✓ → Elán (decide la adopción).
**Veredicto: CONCURRO (PASA).**
**Nota de orden:** el Brujo verificó primero y el Auditor revisó antes que
yo — la cadena está completa en cualquier orden (igual que en P1/P2/P3).
Mi supervisión es por cómputo propio sobre los logs leídos directamente,
no por confianza en el reporte ni en las revisiones.

## 1. Archivos verificados en disco por mí (medidos, no citados de oídas)

| Archivo | Medido por mí | Reportado | ¿Coincide? |
|---|---|---|---|
| `REPORTE_QF_2026-11-19.md` | 257 l. / md5 `83d8791c…` | 257 l. / md5 `83d8791c…` | ✓ |
| `VERIFICACION_BRUJO_QF_2026-11-19.md` | 118 l. / md5 `fba9a522…` | 118 l. / md5 `fba9a522…` | ✓ |
| `REVISION_AUDITOR_QF_2026-11-19.md` | 149 l. / md5 `1f963d7d…` | 149 l. / md5 `1f963d7d…` | ✓ |
| `build_qf.log` | 858 B | 858 B | ✓ |
| `verify_qf_gold.log` | 1,415 B | 1,415 B | ✓ |
| `verify_qf_gold_control.log` | 1,412 B | 1,412 B | ✓ |
| `construir_dqi_qf.py` | 2,746 B | 2,746 B | ✓ |
| `run_verify_qf_gold.sh` / `run_verify_qf_gold_control.sh` | 1,220 B / 934 B | 1,220 B / 934 B | ✓ |
| `dqi_qf.kmb` (esta caja) | 628,685,675 B / sha256 `38b9cbf0…` | mismo sha | ✓ |
| `dqi_qf.kmb` (Kali, por SSH) | sha256 `38b9cbf0…` | mismo sha | ✓ **BYTE-IDÉNTICO** |
| `dqi_qf.kmb` (control del Brujo) | 628,685,675 B / sha256 `38b9cbf0…` | mismo sha | ✓ **BYTE-IDÉNTICO** |

D-QF-1 (bug de mezcla) **no** afectó el build: verificado por identidad
de hash en tres copias (Kali, esta caja, control del Brujo), no por
confianza en el script. El `build_qf.log` además muestra los 4 módulos
desde `/home/deamon/quantum-circuit-compilation-qf/src/`.

## 2. Gold control — leído por mí directamente de `verify_qf_gold_control.log`

13:49:44–14:02:13, exit_gold=0, seed
`52642227205936912575373656611044064096114070193057152544535209180255000077827`:

| Campo | Gold control (mismo seed) | Gold publicado swap42 | ¿Coincide? |
|---|---|---|---|
| status | PASS | PASS | ✓ |
| score | 2,993,914,799,696.024 | 2,993,914,799,696.024 | ✓ EXACTO |
| repetition_factor R | 1.2131052140444296 | 1.2131052140444296 | ✓ EXACTO |
| value_errors | 5 | 5 | ✓ |
| phase_errors | 0 | 0 | ✓ |
| mean_error_weight | 31.046737331746634 | 31.046737331746634 | ✓ |
| reaction_depth | 19,501 | 19,501 | ✓ |
| num_ops | 74,182,884 | 74,182,884 | ✓ |
| num_qubits / T | 1,864 / 710,312 | 1,864 / 710,312 | ✓ |
| num_bits | 198,813 | 198,813 | ✓ |
| circuit_sha256 | `746271d9…` | `746271d9…` | ✓ |

**Seed validado por mí de dos maneras:** (a) empírica — el control
reproduce EXACTO el Gold publicado; (b) por cómputo — el seed es
`int(sha256(swap42), 16)` y verifiqué el roundtrip
(`format(seed, '064x') == hash`, True) y la igualdad con el seed del
log. La comparación con seed fijo es manzana con manzana.

## 3. Gold QF — leído por mí directamente de `verify_qf_gold.log`

14:06:51–14:19:01, exit_gold=0, mismo seed:

| Campo | swap42 (control) | QF | Delta |
|---|---|---|---|
| status | PASS | PASS | — |
| score | 2,993,914,799,696.024 | **2,971,470,537,625.3** | −22,444,262,070.724 (−0.7497%) |
| repetition_factor R | 1.2131052140444296 | **1.2131052140444296** | 0 (idéntico) |
| value_errors | 5 | 5 | 0 |
| phase_errors | 0 | 0 | 0 |
| empirical_error_rate | 4.8828125e-05 | 4.8828125e-05 | 0 |
| effective_error_rate | 0.0010479495500463395 | 0.0010479495500463395 | 0 |
| mean_error_weight | 31.046737331746634 | 31.046737331746634 | 0 |
| log2_delta | −128.0 | −128.0 | 0 |
| toffoli_count | 710,312 | 710,312 | 0 |
| num_qubits | 1,864 | **1,857** | −7 |
| num_bits | 198,813 | 198,813 | 0 |
| num_ops | 74,182,884 | **72,168,849** | −2,014,035 |
| reaction_depth | 19,501 | **3,154** | −16,347 (÷6.183) |

## 4. Aritmética recalculada por mí (cómputo propio, no estimada)

- Factor (1857/1864)² = **0.9925033731510986** — coincide exacto con el
  Brujo y el Auditor.
- Score esperado = 2,993,914,799,696.024 × 0.9925033731510986 =
  **2,971,470,537,625.2993**; medido = 2,971,470,537,625.3; diff
  **0.0005** = redondeo float — **exacto**.
- Mejora real del score: **−0.7497%** (solo el factor Q²; R, errores y
  T idénticos).
- DQI ratio swap42 = 2.4439e13 / 2,993,914,799,696.024 = **8.16289** ✓.
- DQI ratio QF = 2.4439e13 / 2,971,470,537,625.3 = **8.22455** ✓ (y
  8.16289 / 0.9925033731510986 = 8.22455 ✓ por el factor).
- Derivaciones §8 del reporte verificadas: 3.52286 / 0.9925033731510986^(1/3)
  = 3.53170744 → **3.53171** ✓; 3.53019 / 0.9925033731510986^(1/3) =
  3.53905585 → **3.53906** ✓.

### D-QF-2 (precisión del Brujo — el geomean depende del invsqrt) — VERIFICADA

- Geomean medido QF + logshift2 = (5.32499 × 8.22455 × 1.005827)^(1/3) =
  **3.53171** ✓
- Geomean medido QF + R1 = (5.33517 × 8.22455 × 1.005827)^(1/3) =
  **3.53396** ✓
- Geomean Kaggle-escala QF + logshift2 = 3.53171 × (3.53019/3.52286) =
  **3.53906** ✓
- Geomean Kaggle-escala QF + R1 = 3.53396 × (3.53019/3.52286) =
  **3.54131** ✓
- Bases swap42 verificadas: QF+logshift2 3.52286 ✓ (3.52285967);
  swap42+R1 = **3.52510** (3.52510317).
- Al citar el geomean, decir con qué invsqrt va: 3.53171 (logshift2) o
  3.53396 (R1). Los números DQI no cambian.

## 5. Hallazgo reaction_depth 19,501 → 3,154 — VERIFICADO por mí de los dos JSON Gold

Mismo seed, mismas 102,400 muestras. Los `shot_operation_counts` son
sumas sobre los 102,400 tiros (ver D-QF-5):

| Métrica | swap42 (control) | QF | Delta / ratio |
|---|---|---|---|
| reaction_depth | 19,501 | 3,154 | −16,347; ÷6.183 |
| R (total 102,400 tiros) | 67,694,592,000 | 10,311,168,000 | −57,383,424,000; ÷6.565 |
| HMR (total) | 81,564,672,000 | 24,181,248,000 | −57,383,424,000; ÷3.373 |
| CX (total) | 6,569,789,235,200 | 6,535,702,323,200 | −34,086,912,000 |
| CZ (total) | 188,636,410,370 | 159,946,096,370 | −28,690,314,000 |
| CCX (total) | 68,784,128,000 | 68,784,128,000 | 0 (igual — mismo T) |
| X, SWAP, CSWAP, INFO_TAG, POP/PUSH | iguales | iguales | 0 |

Por tiro (÷102,400): R 661,080 → 100,695; HMR 796,530 → 236,145
(796,530 es el HMR por circuito medido en P3 ✓); CCX 671,720 → 671,720
(igual que el CCX por circuito de P3 ✓); CX 64,158,098 → 63,825,218.
**R y HMR caen exactamente lo mismo en total: −57,383,424,000 cada uno.**
CZ por tiro no es entero (1,842,152.44 → 1,561,973.60): el conteo CZ
varía por tiro (dependiente de datos, por los CZ condicionados a HMR) —
el total y el delta son exactos.

El hallazgo es real y medido. El score no cambia por esto (score =
R × Q² × T), pero la profundidad de reacción es tiempo real de ejecución
en hardware: el circuito QF es 6.18× menos profundo. Concurro con la
interpretación del Brujo (las formas en el sitio + Toffoli con fan-out
eliminan las cadenas secuenciales de ancillas HMR/R que dominaban la
profundidad — R y HMR son los que colapsan; CCX no se mueve).

## 6. A-QF-1 (hallazgo del Auditor — 3 números erróneos en el build log) — CONCURRO

Recomputé la fórmula del script (`construir_dqi_qf.py`, líneas 46–48,
leídas por mí) con T=710,312 y reproduzco EXACTO los números erróneos
del `build_qf.log`:

- `ratio_dqi = 7.48129 × (774932/710312)` = **8.16189** (correcto: 8.22455)
- `g_calc = (5.32 × 8.16189 × 1.00583)^(1/3)` = **3.52162** (correcto:
  3.53171 logshift2 / 3.53396 R1)
- `g_esc = 3.42920 × (774932/710312)^(1/3)` = **3.53019** (correcto:
  3.53906 logshift2 / 3.54131 R1)

Causa raíz confirmada: `ratio_dqi` solo depende de **T** (ancla
desactualizada 7.48129 — D-P1-1); el QF cambia **Q**, no T, así que la
fórmula devuelve ~el ratio viejo. `g_esc` = 3.53019 es el geomean Kaggle
de swap42 (el mismo artefacto del ancla). **Impacto: NINGUNO en el
circuito, el Gold ni el reporte** (todos correctos — el reporte trae
8.22455, 3.53171 y 3.53906). El build log hace ver al QF como una
REGRESIÓN (8.16189 < 8.16289) cuando es una mejora. **Se corrige el
script, no el QF. No es bloqueador para la adopción.**

## 7. D-QF-3 (precisión del Brujo — conteo de reinicios) — CONCURRO

La numeración es consistente: el reporte numera el reinicio ~13:19:03
como 3º y el ~14:36:05 como 5º, así que existe un 4º entre las 13:41 y
las 14:36. Verificado por mí en vivo (SSH, 14:52:37): la Kali lleva
16 min arriba → arranque ~14:36 (el 5º reinicio ✓); último checkpoint
bueno `somejoint_long_seg39.npz` (mtime 13:38:47); `seg40.log` existe y
el entrenamiento está CORRIENDO (refit.py PID 4152, desde 14:45, con
`--seed-file somejoint_long_seg39.npz --tag somejoint_long_seg40`) — el
relanzamiento del Brujo desde seg39 está vivo. Nota menor: el mtime del
seg39.npz (13:38:47) difiere ~3 min del DONE del log (13:41:42) —
escritura vs DONE, sin sustancia. Registro menor; no afecta la sustancia
ni el veredicto.

## 8. Precisiones mías

### D-QF-4 (menor — la referencia invsqrt exacta es 2,076,774, no 2,076,773.04)
El Auditor cita "ref invsqrt 2,076,773.04" para el ratio R1. El valor
exacto es **2,076,774**: 390,005.05559761106 × 5.324992510206632 =
2,076,774.0 (verificado por mí). Su valor difiere en 0.96 (4.6e-7
relativo) y el ratio R1 es **5.33517** con cualquiera de los dos
(5.33517087 con 2,076,774; 5.33516840 con 2,076,773.04). Sin impacto en
ningún número citado.

### D-QF-5 (menor — los conteos del §6/§9 son sumas sobre 102,400 tiros)
El reporte y las revisiones dicen "R por tiro: 67,694,592,000" — esos
son los **totales** de `shot_operation_counts` sobre los 102,400 tiros,
no valores por tiro. Por tiro: R 661,080 → 100,695; HMR 796,530 →
236,145; CCX 671,720 → 671,720. Los ratios y los deltas no cambian.

## 9. Criterio de aceptación (§1.3 de la recomendación conjunta Datos + Auditor)

| Requisito | Medido | ¿Cumple? |
|---|---|---|
| Q = 1,857 (−7), T = 710,312 (0) | Q=1,857, T=710,312 | ✓ |
| Gold PASS con seed fijo | PASS, exit_gold=0, mismo seed | ✓ |
| phase_errors = 0 | 0 | ✓ |
| value_errors en el rango de swap42 (5) | 5 | ✓ |
| Score consistente con (1857/1864)² | 2,971,470,537,625.3 = esperado ±0.0005 | ✓ EXACTO |
| Build byte-idéntico al control del Brujo | sha `38b9cbf0…` (3 copias) | ✓ |

**El QF CUMPLE el criterio de aceptación de la recomendación conjunta.**

## 10. Veredicto: CONCURRO (PASA)

QF cumple el criterio: Q=1,857 (−7), T=710,312 (0), Gold PASS con seed
fijo, R idéntico a swap42 (1.2131052140444296), 5 errores de valor / 0
de fase (igual que swap42), score exactamente el esperado
(2,971,470,537,625.3 = swap42 × (1857/1864)²). Mejora real del score:
0.7497% (ratio 8.22455). Hallazgo adicional verificado: reaction_depth
19,501 → 3,154 (÷6.18). Precisiones mías: D-QF-4 y D-QF-5 (menores, sin
impacto). Concurro con D-QF-2, D-QF-3 y A-QF-1.

**Cadena COMPLETA: Programación ✓ → Brujo ✓ → Datos ✓ (este documento)
→ Auditor ✓ → Elán decide la adopción.** Si Elán adopta el QF, la base
DQI cambia a Q=1,857 y P1+P2+P3 se re-basifican sobre el código QF (sha
`38b9cbf0…`) según la recomendación conjunta.
