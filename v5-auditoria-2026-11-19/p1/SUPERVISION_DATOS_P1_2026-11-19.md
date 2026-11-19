# SUPERVISIÓN DE DATOS — P1 (PROTOTIPO ESPIRAL, FASE 2, DQI)

**Fecha:** 2026-11-19 ~12:39 CST
**Orden:** Elán (11:17, vía Coordinador) — construir el prototipo del motor de la espiral; el Brujo coordina. **Supervisión aceptada por Datos 11:23.**
**Constructor:** Programación (subagente constructor P1).
**Diseño:** `~/workspace/qcc-data/dfthcsos-refit/espiral-rediseno/FASE2_DQI_2026-11-19.md` §1 y §P1.
**Reporte supervisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p1/REPORTE_P1_2026-11-19.md` — **175 l. / md5 `6340d78ffe9b189e6f27545db9792191`**.
**Verificación del Brujo:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p1/VERIFICACION_BRUJO_P1_2026-11-19.md` — **142 l. / md5 `7fb9eebf9b0f8e39d7f16a76669b80d2`**, CONCURRO (PASA).
**Cadena:** Programación (construye) → **Datos (esta supervisión)** → Brujo ✓ (verifica) → Auditor (revisa) → Elán (decide).
**Regla 0:** cada número aquí viene de un log leído o de un cómputo propio en python; lo estimado se marca [ESTIMADO]. Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.

## Veredicto: CONCURRO (PASA)

P1 PASA. El multiplicador Toom-4 emite su plan de 42 ANDs como matriz 6×7 explícita, con exactamente 42 ANDs por llamada y los 3 transitorios reutilizados, Q = 1,864 y T = 710,312 sin cambio, y el circuito resultante es **byte-idéntico a swap42** (sha `746271d9…`, `cmp` confirma). El Gold de swap42 lo cubre por identidad de bytes. Impacto en score: 0, como estima el diseño. Concurro con las tres precisiones del Brujo (D-P1-1, D-P1-2, D-P1-3 — las tres verificadas por mí) y añado una menor mía (D-P1-4, la hora del encabezado del reporte).

## 1. Circuito — VERIFICADO (byte-identidad)

| Archivo | Tamaño | sha256 medido por Datos |
|---|---|---|
| `dqi_p1.kmb` | 646,811,990 B | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |
| `dqi_p1_control.kmb` | 646,811,990 B | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |
| `dqi_swap42.kmb` (referencia) | 646,811,990 B | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |
| `dqi_p1_rowmajor.kmb` (sonda) | 646,811,990 B | `192ae5d4df5f7801c6d498d91807f731dc7691ba9563d777daf196530f346d8c` |

`cmp dqi_p1.kmb dqi_swap42.kmb`: **idéntico** ✓. `cmp dqi_p1.kmb dqi_p1_control.kmb`: **idéntico** ✓ — la ruta de build es reproducible en esta caja (control Q=1,864 T=710,312 en 119 s, mismo `live_frontera`).

## 2. Estadísticas — VERIFICADAS (carga directa mía de los 3 .kmb)

Leídas por mí con `km.Circuit.from_file` (script propio, sin `reaction_depth` — ver §9):

| Variante | Q | T | num_bits | num_instructions |
|---|---|---|---|---|
| swap42 | 1,864 | 710,312 | 198,813 | 74,182,884 |
| P1 (col-mayor) | 1,864 | 710,312 | 198,813 | 74,182,884 |
| P1 sonda (fila-mayor) | 1,864 | 710,312 | 198,813 | 74,182,884 |

**Idénticos en las tres** ✓. (El `stats_kmb2.py` del reporte solo carga swap42 y P1-col; la fila-mayor la cargué yo mismo — como hizo el Brujo — ver D-P1-2.)

## 3. Matriz 6×7 — VERIFICADA (módulo importado + prueba aislada re-corrida)

Re-corrido por mí (`test_kmul42_p1.py` con el intérprete kickmix + chequeos propios sobre `dqi_kmul42` importado de `p1/src`):

- `PLAN42` len 42, **distintos 42** (0 fusiones) ✓.
- `PLAN42_MATRIX` **6 filas × 7 columnas**, `EMIT_ORDER = "col"` ✓.
- Aplanar por columnas == `PLAN42`: **True**; por filas == `PLAN42`: **False** ✓.
- `PLAN42[6*col + row] == PLAN42_MATRIX[row][col]`: **42/42** ✓.
- `list(_iter_plan()) == PLAN42`: **True** ✓.
- Prueba aislada (3 registros × 12 qubits): `toffoli_like = 42`, `num_qubits = 39` (36 + 3 transitorios) — **"P1 aislado: 42 ANDs, 3 transitorios, OK"** ✓.

## 4. Generador — VERIFICADO (la agrupación no es asumida)

`diseno_toom4.py`, `build_plan`: bucle externo `for i, w in enumerate(PTS)` (**7 puntos**), interno `for (fx3, fy3, m5) in kar3_plan()` (**6 ANDs** Karatsuba por producto GF(8)) ✓. El plan plano es columna-mayor sobre la matriz (6 ANDs por punto, paso 6 — no 7; la primera versión de la matriz usó el paso 7 y la aserción estructural lo habría rechazado, como dice el reporte §3).

## 5. Gold de swap42 — LEÍDO EN DIRECTO (cubre a P1 por identidad de bytes)

`verify_swap42_gold.log` (copia local del Gold de la Kali, 14 nov 11:23–11:30 CST):

| Campo | Valor |
|---|---|
| status | PASS |
| score | 2,993,914,799,696.024 |
| verified_shots | 102,400 |
| value_errors / phase_errors | 5 / 0 |
| empirical_error_rate | 4.8828125e-05 |
| repetition_factor (R) | 1.2131052140444296 |
| mean_error_weight | 31.046737331746634 |
| toffoli_count (T) | 710,312 |
| reaction_depth | 19,501 |
| num_ops | 74,182,884 |
| num_qubits / num_bits | 1,864 / 198,813 |
| circuit_sha256 | `746271d9…` |
| exit_gold | 0 |

**Score recomputado por Datos:** R × Q² × T = 1.2131052140444296 × 1,864² × 710,312 = **2,993,914,799,696.024** ✓ (exacto al Gold).

## 6. Aritmética del multiplicador — VERIFICADA

- 5,385 llamadas × 42 ANDs = **226,170 T** = 31.84% del T DQI ✓.
- 774,932 − 710,312 = **64,620** = 5,385 × 12 (Karatsuba 54 → Toom-4 42) ✓.
- 3 transitorios (`tx, ty, t`) una vez por llamada; la prueba aislada da 39 qubits (36 + 3), no 42×3 ✓.

## 7. Diff — VERIFICADO (solo `dqi_kmul42.py` difiere)

Comparación `.py` por `.py` entre `p1/src/` y el fuente swap42 (`~/workspace/qcc-data/dqi-perfil/swap42/`, archivos planos, sin subdirectorio `src/`): entre los archivos presentes en ambos lados, **solo `dqi_kmul42.py` difiere** (p1 md5 `ae03f5375642af01f258404bead8734d`; swap42 md5 `eb412bd7a187e6d6feecb38fe685086b`) ✓. `construir_dqi_p1.py` es nuevo (el script de build de P1, no un archivo modificado de swap42); el resto de `.py` son byte-idénticos. El cuerpo del AND no cambia: la única línea cambiada en el cuerpo es `for fx, fy, tm in PLAN42:` → `for fx, fy, tm in _iter_plan():` (verificado en el diff leído por el Brujo; concurro).

## 8. Build logs — LEÍDOS EN DIRECTO

- `build_control.log`: `TOTAL P1-CONTROL Q=1864 T=710312 en 119s`, `live_frontera` 1794/1794/1794/1794/1724, sha `746271d9…` ✓.
- `build_p1.log`: `TOTAL P1 Q=1864 T=710312 en 136s`, mismo `live_frontera`, sha `746271d9…` ✓.
- `build_p1_rowmajor.log`: `TOTAL P1 Q=1864 T=710312 en 160s`, sha `192ae5d4…` ✓.
- Los tres imprimen `PRODUCCION (omega/Karatsuba): Q=1864 T=774932`, `Delta Q=0 Delta T=-64620` ✓.

## 9. Sonda fila-mayor + limitación `reaction_depth` — VERIFICADO

- Sonda fila-mayor (`EMIT_ORDER = "row"`): Q/T/bits/instrucciones **idénticos** a swap42 por mi propia carga (§2) ✓. El `.kmb` difiere solo en el orden de las puertas (mismo tamaño). **El orden de emisión no cambia ninguna métrica de coste medida** ✓. La sonda NO es entregable (sin Gold) — correcto no correrle Gold.
- `reaction_depth` de la sonda queda **sin medir** en esta caja: por construcción (42 ANDs secuenciales por el transitorio `t` compartido) se espera idéntico, pero es inferencia, no número — el reporte lo dice explícito y el Brujo concurre ✓. Yo tampoco lo intenté (ver D-P1-3).
- Para P1 no importa: byte-idéntico → `reaction_depth` 19,501 del Gold de swap42 ✓.

## 10. Precisiones

**D-P1-1 (del Brujo, CONCURRO — verificada exacta):** los números 8.16189x y 3.52162x del §5 son estimados del script de build, no los valores medidos por Gold. Verificado por mí: el script (`construir_dqi_p1.py`) calcula `ratio_dqi = 7.48129 * (774932 / t)` y `g_calc = (5.32 * ratio_dqi * 1.00583) ** (1/3)`; el ancla 7.48129 está desactualizada (el ratio omega/Karatsuba medido por Gold es **7.55517814** = 2.4439e13 / 3,234,735,110,839.3457) y `g_calc` usa 5.32 redondeado en vez de 5.32499. Valores verdaderos por cómputo propio: **ratio DQI = 8.162890942147493** (2.4439e13 / 2,993,914,799,696.024), **geomean = 3.522859936910316**. Los valores del script re-derivados por mí: ratio 8.16189368, geomean 3.52161912 — coinciden con lo impreso. La afirmación "(idénticos a swap42)" es **cierta para los valores impresos**: `build_swap42.log` imprime los mismos 8.16189x / 3.52162x (verificado por grep). Y `g_esc = 3.42920 * (774932/710312)^(1/3)` = 3.53018633 → imprime 3.53019, que coincide con el score real de Kaggle (3.53019) a 5 decimales — coincidencia del estimador, no una medición, como dice el Brujo. **No cambia nada del circuito**: byte-idéntico a swap42, sus métricas verdaderas son las de swap42 (8.16289 / 3.52286). Impacto en score de P1: 0.

**D-P1-2 (del Brujo, CONCURRO — reforzada por mí):** la fila-mayor — estadísticas medidas por el Brujo, no por el script del reporte. Ahora también medidas por mí (§2, carga directa de los 3 .kmb): Q/T/bits/instrucciones idénticos. La afirmación del §6 es cierta, con evidencia mía además de la del Brujo.

**D-P1-3 (del Brujo, CONCURRO — verificada por mí):** el intento de `reaction_depth` murió como se reporta. Leído por mí `stats_kmb.log` (155 B): carga swap42 (Q=1864 T=710312 num_bits=198813) y el log termina en `[swap42] reaction_depth ...` — muere en el cálculo, sin OOM en dmesg (el reporte §9). Limitación medida, no asumida. Yo no lo re-intenté (no hacía falta: el log ya lo documenta y P1 es byte-idéntico).

**D-P1-4 (mía, menor — la hora del encabezado del reporte):** el reporte dice "construcción ~18:08–18:22 CST". Esas son horas **UTC** etiquetadas como CST: los mtimes en CST son `build_control.log` 12:10:39, `dqi_p1.kmb` 12:14:58, `build_p1_rowmajor.log` 12:21:20 — la ventana real es **~12:08–12:22 CST** (18:08–18:22 UTC). Misma clase de trampa que la lección de tiempos: verificar contra mtimes, no contra lo etiquetado. No cambia ningún número del reporte.

## 11. Criterio FASE 2 §P1 — CUMPLIDO

- Matriz 6×7 explícita: ✓ (verificado en módulo y generador).
- Exactamente 42 ANDs por llamada: ✓ (prueba aislada 42 T).
- 3 transitorios reutilizados: ✓ (39 qubits aislados).
- Q = 1,864 y T = 710,312 sin cambio: ✓ (build + carga de .kmb).
- Circuito byte-idéntico a swap42: ✓ (sha256 + `cmp`).
- Gold: ✓ por identidad de bytes (PASS, 102,400 tiros, 5 valor / 0 fase).
- Sonda fila-mayor: el orden de emisión no cambia ninguna métrica de coste medida (Q/T/bits/instrucciones idénticos por carga directa mía); `reaction_depth` sin medir (inferencia declarada).

## 12. Veredicto y cadena

**CONCURRO (PASA)** — P1 pasa: matriz 6×7 explícita verificada en módulo y generador, 42 ANDs por llamada, 3 transitorios, Q/T sin cambio, circuito byte-idéntico a swap42 con Gold PASS por identidad. Precisiones: D-P1-1 (valores del script vs Gold — concurro, verificada exacta), D-P1-2 (fila-mayor medida por mí también), D-P1-3 (`reaction_depth` muere como se reporta — concurro), D-P1-4 (hora del encabezado: UTC etiquetada como CST). Ninguna cambia el veredicto.

**Cadena:** Programación (construye) → **Datos ✓ (esta supervisión)** → Brujo ✓ (verifica) → Auditor (revisa) → Elán (decide).

**Contexto (no es supervisión, es estado):** Fase 2 — P2 verificado por el Brujo (CONCURRO PASA, 12:37) y pasado a Datos para supervisión; P3 en construcción. Fase 1 completa (R1 adoptado, confirmado por Elán 12:16:35 "Deja R1"; R2c cadena completa; R5 supervisado por Datos y verificado por el Brujo, pasado al Auditor 12:40).
