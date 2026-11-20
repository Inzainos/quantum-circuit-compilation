# VERIFICACIÓN DEL BRUJO — P1 (Fase 2, DQI): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~12:26 CST
**Reporte verificado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p1/REPORTE_P1_2026-11-19.md` (175 l. / md5 `6340d78f…`)
**Constructor:** Programación (subagente constructor P1)
**Diseño:** `FASE2_DQI_2026-11-19.md` §1 y §P1
**Cadena:** Programación ✓ → **Datos (supervisión pendiente)** → **Brujo ✓ (este informe)** → Auditor → Elán
**Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.**

## Veredicto: CONCURRO (PASA)

P1 cumple el criterio de FASE 2 §P1: el multiplicador Toom-4 emite su plan
de 42 ANDs como matriz 6×7 explícita, con exactamente 42 `init_and` por
llamada, los 3 transitorios reutilizados, Q = 1,864 y T = 710,312 sin cambio,
y el circuito resultante es **byte-idéntico a swap42** (equivalencia probada
por hash; el Gold de swap42 lo cubre). Impacto en score: 0, como estima el
diseño.

## Verificado por cómputo propio

### 1. Circuito byte-idéntico a swap42 (la equivalencia central)
- `dqi_p1.kmb` sha256 calculado por mí: `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` (646,811,990 B).
- `dqi_swap42.kmb` sha256 calculado por mí: `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` — **idéntico**.
- `dqi_p1_control.kmb` sha256: `746271d9…` (mismo) — la ruta de build es reproducible en esta caja.
- `dqi_p1_rowmajor.kmb` sha256: `192ae5d4df5f7801c6d498d91807f731dc7691ba9563d777daf196530f346d8c` — coincide con el reporte.

### 2. Estadísticas leídas por mí de los 3 .kmb (carga directa con `km.Circuit.from_file`)
| Variante | Q | T | num_bits | num_instructions |
|---|---|---|---|---|
| swap42 | 1,864 | 710,312 | 198,813 | 74,182,884 |
| P1 (col-mayor) | 1,864 | 710,312 | 198,813 | 74,182,884 |
| P1 sonda (fila-mayor) | 1,864 | 710,312 | 198,813 | 74,182,884 |

Idénticos en las tres. (Nota: el `stats_kmb2.py` del reporte solo carga
swap42 y P1-col; la fila-mayor la cargué yo mismo — ver §Precisiones.)

### 3. Matriz 6×7 — verificada en el módulo importado (no solo citada)
- `PLAN42` len 42, distintos 42.
- `PLAN42_MATRIX` 6 filas × 7 columnas, `EMIT_ORDER = "col"`.
- Aplanar por columnas == `PLAN42`: **True**; por filas == `PLAN42`: **False**.
- `PLAN42[6*col + row] == PLAN42_MATRIX[row][col]`: **True** (42/42).
- `list(_iter_plan()) == PLAN42`: **True**.
- Prueba aislada re-corrida por mí (`test_kmul42_p1.py`): matriz 6×7 OK,
  aplanado por columnas == PLAN42, `toffoli_like = 42`, `num_qubits = 39`
  (36 + 3 transitorios). Reproduce exacto lo que dice el reporte.

### 4. Mecanismo confirmado en el código (diff leído)
- `diff -rq` p1/src vs swap42: entre los `.py` **solo `dqi_kmul42.py`
  difiere** (los `.pyc` son bytecode regenerado; el resto de "Only in" son
  docs/logs/scripts de build, no fuentes). md5 `dqi_kmul42.py`:
  `ae03f5375642af01f258404bead8734d` — coincide con el reporte y con el
  archivo `dqi_kmul42_P1_col.md5`.
- El diff muestra exactamente: docstring ampliado + bloque matriz
  (`N_ROWS = 6`, `N_COLS = 7`, `PLAN42_MATRIX` con paso `N_ROWS`,
  3 aserciones estructurales, `EMIT_ORDER = "col"`, `_iter_plan()`) +
  una sola línea cambiada en el cuerpo: `for fx, fy, tm in PLAN42:` →
  `for fx, fy, tm in _iter_plan():`. **El cuerpo del AND no cambia.**
- Agrupación verificada en el generador: `diseno_toom4.py`, `build_plan`
  (líneas 304–329): bucle externo `for i, w in enumerate(PTS)` (7 puntos),
  interno `for (fx3, fy3, m5) in kar3_plan()` (6 ANDs Karatsuba por
  producto GF(8)). 0 fusiones, 0 nulos (42 pares distintos).

### 5. Build logs leídos en directo
- `build_control.log`: `TOTAL P1-CONTROL Q=1864 T=710312 en 119s`,
  `live_frontera` 1794/1794/1794/1794/1724, sha `746271d9…`.
- `build_p1.log`: `TOTAL P1 Q=1864 T=710312 en 136s`, mismo
  `live_frontera`, sha `746271d9…`.
- `build_p1_rowmajor.log`: `TOTAL P1 Q=1864 T=710312 en 160s`,
  sha `192ae5d4…`.
- Los tres imprimen `PRODUCCION (omega/Karatsuba): Q=1864 T=774932`,
  `Delta Q=0 Delta T=-64620`.

### 6. Gold de swap42 leído en directo (cubre a P1 por identidad de bytes)
- `verify_swap42_gold.log`: `status: PASS`, `score: 2993914799696.024`,
  `verified_shots: 102400`, `value_errors: 5`, `phase_errors: 0`,
  `reaction_depth: 19501`, `num_ops: 74182884`,
  `circuit_sha256: 746271d9…`, `exit_gold=0`. Coincide con el reporte §6.

### 7. Aritmética del multiplicador
- 5,385 llamadas × 42 ANDs = 226,170 T = 31.8% del T DQI. Verificado:
  774,932 − 710,312 = 64,620 = 5,385 × 12 (Karatsuba 54 → Toom-4 42).
- 3 transitorios (`tx, ty, t`) una vez por llamada; la prueba aislada da
  39 qubits (36 + 3), no 42×3.

## Precisiones

### D-P1-1 (presentación, NO afecta el veredicto): los números 8.16189x y 3.52162x del §5 son estimados del script de build, no los valores medidos por Gold
- El script (`construir_dqi_p1.py`, líneas 52–55) calcula:
  `ratio_dqi = 7.48129 * (774932 / t)` y `g_calc = (5.32 * ratio_dqi * 1.00583) ** (1/3)`.
- El ancla 7.48129 está desactualizada: el ratio omega/Karatsuba medido
  por Gold es **7.55517814** (2.4439e13 / 3,234,735,110,839.3457), no
  7.48129. Y `g_calc` usa 5.32 redondeado en vez de 5.32499.
- Valores verdaderos por cómputo propio (ratios exactos desde los scores
  Gold): **ratio DQI = 8.16289094** (2.4439e13 / 2,993,914,799,696.024),
  **geomean = 3.52285992** — los del reporte swap42, no los del script.
- La afirmación "(idénticos a swap42)" del §5 es **cierta para los valores
  impresos por el script**: `build_swap42.log` imprime los mismos
  8.16189x / 3.52162x (el script swap42 tiene la misma fórmula). Pero el
  reporte debería citar los valores Gold como autoritativos.
- El `g_esc = 3.42920 * (774932/t)^(1/3)` = 3.53018633 → imprime 3.53019:
  es el estimado por escalado de T, que coincide con el score real de
  Kaggle (3.53019) a 5 decimales — coincidencia del estimador, no una
  medición.
- **No cambia nada del circuito**: es byte-idéntico a swap42, así que sus
  métricas verdaderas son las de swap42 (8.16289 / 3.52286). Impacto en
  score de P1: 0, como estima el diseño.

### D-P1-2 (menor): la fila-mayor — estadísticas medidas por mí, no por el script del reporte
- El `stats_kmb2.py` del reporte solo carga swap42 y P1-col. La fila-mayor
  la cargué yo mismo (§2): Q/T/bits/instrucciones idénticos. La afirmación
  del §6 es **cierta**, con evidencia mía.
- `reaction_depth` de la fila-mayor queda **sin medir** en esta caja (el
  reporte lo dice explícito: inferencia, no número). Para P1 no importa
  (byte-idéntico → 19,501 del Gold de swap42). La sonda no es entregable
  (sin Gold) — correcto no correrle Gold.

### D-P1-3 (menor): el intento de `reaction_depth` murió como se reporta
- `stats_kmb.log` muestra la carga de swap42 (Q=1864 T=710312
  num_bits=198813) y muere en el cálculo de `reaction_depth`, sin OOM en
  dmesg — consistente con el reporte §9. Limitación medida, no asumida.

## Lo que NO se tocó (verificado)
- Fuente swap42 local: el `.kmb` sigue en sha `746271d9…`; el diff muestra
  solo el cambio P1 en la copia test-dev.
- Candidato swap42 (ZIP), ZIP Adopted v3, docs de diseño, árboles R1/R2/R5:
  sin cambios en esta tarea.
- Entrenamiento SomeJoint en la Kali: ni mirado (el reporte lo registra;
  el driver PID 183966 seguía vivo en mi último chequeo, seg20 DONE
  12:19:56).

## Criterio FASE 2 §P1 — cumplido
- Matriz 6×7 explícita: ✓ (verificado en módulo y generador).
- Exactamente 42 `init_and` por llamada: ✓ (prueba aislada 42 T).
- 3 transitorios reutilizados: ✓ (39 qubits aislados).
- Q = 1,864 y T = 710,312 sin cambio: ✓ (build + carga de .kmb).
- Circuito byte-idéntico a swap42: ✓ (sha256).
- Gold: ✓ por identidad de bytes (PASS, 102,400 tiros, 5 valor / 0 fase).
- Sonda fila-mayor: el orden de emisión no cambia ninguna métrica de
  coste medida (Q/T/bits/instrucciones idénticos por carga directa mía);
  `reaction_depth` sin medir (inferencia declarada).

**P1 PASA. Siguiente: Datos (supervisión) → Auditor → Elán.**
