# REVISIÓN DEL AUDITOR — Gold del QF (parche Claude, −7 qubits)

**Fecha:** 2026-11-19 ~14:52 CST
**Auditor:** Auditor Interno
**Documento revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/claude-qf/VERIFICACION_BRUJO_QF_2026-11-19.md` (118 l. / md5 `fba9a522…`, verificado en disco por mí)
**Reporte de Programación:** `~/workspace/qcc-data/test-dev/espiral-prototipo/claude-qf/REPORTE_QF_2026-11-19.md` (257 l. / md5 `83d8791c…`, verificado en disco por mí)
**Cadena:** Programación (construye + Gold) → Brujo (verifica) → Datos → Auditor (este documento) → Elán (decide la adopción).
**Veredicto: CONCURRO (PASA).**

---

## 1. Archivos verificados en disco por mí (no por confianza en el reporte)

| Archivo | Medido por mí | Reportado por el Brujo | ¿Coincide? |
|---|---|---|---|
| `dqi_qf.kmb` (Kali) | 628,685,675 B / sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` | mismo sha, mismo tamaño | ✓ |
| `dqi_qf.kmb` (control del Brujo, `~/workspace/qcc-data/claude-parche/`) | 628,685,675 B / sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` | mismo sha | ✓ **BYTE-IDÉNTICO** |
| `REPORTE_QF_2026-11-19.md` | 257 l. / md5 `83d8791c…` | 257 l. / md5 `83d8791c…` | ✓ |
| `VERIFICACION_BRUJO_QF_2026-11-19.md` | 118 l. / md5 `fba9a522…` | 118 l. / md5 `fba9a522…` | ✓ |
| `build_qf.log` | 858 B | 858 B | ✓ |
| `verify_qf_gold.log` | 1,415 B | 1,415 B | ✓ |
| `verify_qf_gold_control.log` | 1,412 B | 1,412 B | ✓ |
| `construir_dqi_qf.py` | 2,746 B | 2,746 B | ✓ |
| `run_verify_qf_gold.sh` | 1,220 B | 1,220 B | ✓ |
| `run_verify_qf_gold_control.sh` | 934 B | 934 B | ✓ |

D-QF-1 (bug de mezcla) **no** afectó el build de la Kali: verificado por identidad de hash, no por confianza en el script.

## 2. Gold control — leído por mí directamente de `verify_qf_gold_control.log`

13:49:44–14:02:13, exit_gold=0, seed `52642227205936912575373656611044064096114070193057152544535209180255000077827`:

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
| circuit_sha256 | `746271d9…` | `746271d9…` | ✓ |

**El seed queda validado empíricamente por mí también.** La comparación con seed fijo es manzana con manzana.

## 3. Gold QF — leído por mí directamente de `verify_qf_gold.log`

14:06:51–14:19:01, exit_gold=0, mismo seed:

| Campo | swap42 (control) | QF | Delta |
|---|---|---|---|
| status | PASS | PASS | — |
| score | 2,993,914,799,696.024 | **2,971,470,537,625.3** | −0.7497% |
| repetition_factor R | 1.2131052140444296 | **1.2131052140444296** | 0 (idéntico) |
| value_errors | 5 | 5 | 0 |
| phase_errors | 0 | 0 | 0 |
| mean_error_weight | 31.046737331746634 | 31.046737331746634 | 0 |
| toffoli_count | 710,312 | 710,312 | 0 |
| num_qubits | 1,864 | **1,857** | −7 |
| num_bits | 198,813 | 198,813 | 0 |
| num_ops | 74,182,884 | **72,168,849** | −2,014,035 |
| reaction_depth | 19,501 | **3,154** | −16,347 (÷6.183) |

## 4. Aritmética recalculada por mí (cómputo propio, no estimada)

- Factor (1857/1864)² = **0.9925033731510986** — coincide exacto con el Brujo.
- Score esperado = 2,993,914,799,696.024 × 0.9925033731510986 = **2,971,470,537,625.2993**; medido = 2,971,470,537,625.3; diff **0.0005** = redondeo float — **exacto**.
- Mejora real del score: **−0.7497%** (solo el factor Q²; R, errores y T idénticos).
- DQI ratio swap42 = 2.4439e13 / 2,993,914,799,696.024 = **8.16289** ✓.
- DQI ratio QF = 2.4439e13 / 2,971,470,537,625.3 = **8.22455** ✓.

## 5. Precisión D-QF-2 (geomean depende del invsqrt) — VERIFICADA por mí

El geomean 3.53171 / 3.53906 de Programación es correcto **con logshift2** como invsqrt (ratio 5.32499). Con **R1** (adoptado, ratio 5.33517 — verificado por mí: ref invsqrt 2,076,773.04 / 389,261.01 = 5.33517):

- Geomean medido QF + logshift2 = (5.32499 × 8.22455 × 1.005827)^(1/3) = **3.53171** ✓
- Geomean medido QF + R1 = (5.33517 × 8.22455 × 1.005827)^(1/3) = **3.53396** ✓
- Geomean Kaggle-escala QF + logshift2 = 3.53171 × (3.53019/3.52286) = **3.53906** ✓
- Geomean Kaggle-escala QF + R1 = 3.53396 × (3.53019/3.52286) = **3.54131** ✓

Al citar el geomean, decir con qué invsqrt va: 3.53171 (logshift2) o 3.53396 (R1). Los números DQI no cambian.

## 6. Hallazgo reaction_depth 19,501 → 3,154 — VERIFICADO por mí de los dos JSON Gold

Leídos directamente por mí (mismo seed, mismas 102,400 muestras):

- reaction_depth: 19,501 → 3,154; ratio **6.183×**, diff **16,347** ✓
- R por tiro: 67,694,592,000 → 10,311,168,000; ratio **6.565×** ✓
- HMR por tiro: 81,564,672,000 → 24,181,248,000; ratio **3.373×** ✓
- CX: 6,569,789,235,200 → 6,535,702,323,200; diff **−34,086,912,000** ✓
- CZ: 188,636,410,370 → 159,946,096,370; diff **−28,690,314,000** ✓
- CCX: 68,784,128,000 → 68,784,128,000; **igual** (mismo T) ✓
- X, SWAP, CSWAP, INFO_TAG, POP/PUSH: iguales ✓

El hallazgo es real y medido. El score no cambia por esto (score = R × Q² × T), pero la profundidad de reacción es tiempo real de ejecución en hardware: el circuito QF es 6.18× menos profundo.

## 7. El build — verificado por mí de `build_qf.log`

- 4 módulos desde `/home/deamon/quantum-circuit-compilation-qf/src/` (fuente parcheada) ✓
- live_frontera 1794/1794/1794/1794/1724 (idénticos a swap42) ✓
- TOTAL QF Q=1857 T=710312 en 136 s; Delta Q=−7, Delta T=0 ✓
- sha256 `38b9cbf0…` ✓

## 8. HALLAZGO DEL AUDITOR — A-QF-1 (MENOR): el build log trae 3 números erróneos (fórmula obsoleta en `construir_dqi_qf.py`)

**Lo que dice `build_qf.log`:**
- `DQI ratio nuevo = 8.16189x` — **correcto: 8.22455**
- `geomean calculado = 3.52162x ; geomean escalando Kaggle 3.42920x = 3.53019x` — **correcto: 3.53171 / 3.53906 (logshift2) o 3.53396 / 3.54131 (R1)**

**Causa raíz (líneas 46–48 de `construir_dqi_qf.py`, leídas por mí):**
```python
ratio_dqi = 7.48129 * (774932 / t)
g_calc = (5.32 * ratio_dqi * 1.00583) ** (1/3)
g_esc = 3.42920 * (774932 / t) ** (1/3)
```
- `ratio_dqi` solo depende de **T** (constantes 7.48129 y 774,932 de una versión vieja del DQI). Como el QF cambia **Q** (no T), la fórmula devuelve ~el ratio viejo (8.16189) en vez del QF (8.22455).
- `g_calc` usa además invsqrt obsoleto (5.32 en vez de 5.32499/5.33517) y dfthcsos obsoleto (1.00583 en vez de 1.005827).
- `g_esc` solo escala por T: devuelve 3.53019, que es el geomean Kaggle de Adopted v3 (swap42), no el del QF.

**Impacto: NINGUNO en el circuito, el Gold ni el reporte** (todos correctos — el reporte de Programación trae 8.22455, 3.53171 y 3.53906, líneas 172–177). El error vive solo en las líneas de resumen del build log. Pero el build log hace ver al QF como una REGRESIÓN (8.16189 < 8.16289; 3.52162 < 3.52286) cuando es una mejora, y la fórmula obsoleta seguirá mal en cualquier cambio futuro que solo toque Q. **La verificación del Brujo no revisó estas 3 líneas** (verificó módulos, live_frontera y TOTAL).

**Recomendación:** corregir la fórmula en `construir_dqi_qf.py` (calcular el ratio desde el score, o desde el ratio de swap42 × (Q_QF/Q_swap42)²) o quitar esas líneas de resumen. **No es bloqueador para la adopción.**

## 9. Precisión D-QF-3 (conteo de reinicios) — consistente con el reporte

El reporte numera el reinicio ~13:19:03 como 3º y el ~14:36:05 como 5º, así que existe un 4º entre las 13:41 y las 14:36 (el que probablemente mató el seg40 de SomeJoint). Coincide con la nota del Brujo. Registro menor; no afecta la sustancia ni el veredicto.

## 10. Criterio de aceptación (§1.3 de la recomendación conjunta Datos + Auditor)

| Requisito | Medido | ¿Cumple? |
|---|---|---|
| Q = 1,857 (−7), T = 710,312 (0) | Q=1,857, T=710,312 | ✓ |
| Gold PASS con seed fijo | PASS, exit_gold=0, mismo seed | ✓ |
| phase_errors = 0 | 0 | ✓ |
| value_errors en el rango de swap42 (5) | 5 | ✓ |
| Score consistente con (1857/1864)² | 2,971,470,537,625.3 = esperado ±0.0005 | ✓ EXACTO |
| Build byte-idéntico al control del Brujo | sha `38b9cbf0…` | ✓ |

**El QF CUMPLE el criterio de aceptación de la recomendación conjunta.**

## 11. Veredicto: CONCURRO (PASA)

QF cumple el criterio: Q=1,857 (−7), T=710,312 (0), Gold PASS con seed fijo, R idéntico a swap42 (1.2131052140444296), 5 errores de valor / 0 de fase (igual que swap42), score exactamente el esperado (2,971,470,537,625.3 = swap42 × (1857/1864)²). Mejora real del score: 0.7497% (ratio 8.22455). Hallazgo adicional verificado: reaction_depth 19,501 → 3,154 (÷6.18).

**Un hallazgo menor mío (A-QF-1):** el build log trae 3 números erróneos por fórmula obsoleta en `construir_dqi_qf.py` — no afecta el circuito, el Gold ni el reporte; se corrige el script, no el QF.

**Pasa a Elán para su decisión de adopción.** Si Elán adopta el QF, la base DQI cambia a Q=1,857 y P1+P2+P3 se re-basifican sobre el código QF (sha `38b9cbf0…`) según la recomendación conjunta.
