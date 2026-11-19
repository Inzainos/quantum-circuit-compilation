# VERIFICACIÓN DEL BRUJO — Medición TODO-2 (paso windowed aislado)

**Fecha:** 2026-11-19 ~15:19 CST
**Verificador:** El Brujo (chat El brujo)
**Reporte verificado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/todo2-paso/REPORTE_TODO2_PASO_2026-11-19.md` (232 l., 15,582 B)
**Orden:** Elán (2026-11-19 ~15:00 CST, vía el Brujo). Medición standalone, NO el TODO-2 completo.
**Cadena:** Programación → Datos → Brujo → Auditor → Elán.

## Veredicto

**CONCURRO (PASA).** La medición es correcta y el veredicto se sostiene: **TODO-2 (ventaneado del Horner) SE DESCARTA — NO PASA el criterio §9.**

Verifiqué con cómputo propio (archivos leídos directamente, shas y aritmética recalculada). Una precisión menor (D-T2-1) que NO afecta el veredicto.

## Lo que verifiqué

### 1. Archivos y shas (leídos directamente)

| Archivo | Verificado |
|---|---|
| `control_baseline.kmb` (437,575 B) | sha256 `7e842bbfba8fb40d32c05b3b195073cf…` — **byte-idéntico al baseline logshift2** ✓ |
| `medida_paso.py` (8,670 B) | md5 `d20ab7e167666f6833fceaada25323e2` — coincide con el reporte ✓ |
| `resultados_paso.json` (4,977 B) | md5 `3ae578087ec9ae6932182870d2b4857a` — coincide con el reporte ✓ |
| `proyeccion.py` (2,579 B), `sonda_costos.py`, `sonda_fase.py`, `sonda_reuse.py` | presentes ✓ |
| `logs/` (9 logs), `tree/` (copia fresca del árbol B/C) | presentes ✓ |

### 2. T/Q por ventana (del JSON, coinciden exacto con la tabla del reporte)

| Ventana | bit4 T/Q | acc_keep T/Q | acc_seq T/Q | narrow T/Q |
|---|---|---|---|---|
| fila 0 m=1 (n=18) | 174 / 105 | **209 / 146** | 257 / 105 | 208 / 97 |
| fila 0 m=5 (n=14) | 158 / 105 | **173 / 130** | 209 / 94 | 208 / 93 |
| fila 0 m=9 (n=10) | 142 / 105 | **137 / 114** | 161 / 90 | 208 / 89 |
| fila 0 m=13 (n=6) | 33 / 105 | 51 / 86 | 51 / 86 | 52 / 85 |
| fila 1 m=1 (n=10) | 106 / 79 | **119 / 88** | 143 / 64 | 136 / 63 |
| fila 1 m=5 (n=6) | 90 / 79 | **83 / 72** | 95 / 60 | 136 / 59 |
| fila 1 m=9 (n=2) | 39 / 79 | **38 / 57** | 39 / 56 | 68 / 55 |

Totales de ida (Σ ventanas, recalculados por mí): bit4 = 742; acc_keep = **810** (209+173+137+51+119+83+38+0); acc_seq = 955; narrow = 1,016. Horner total (ida+vuelta): bit4 = 1,484; acc_keep = 1,620. ✓

Incrementos de Q acc_keep vs bit4 (recalculados): fila 0 m=1 **+41**, m=5 +25, m=9 +9, m=13 −19; fila 1 m=1 +9, m=5 −7, m=9 −22. Máximo +41 → Q_proy = 139+41 = **180**. ✓

### 3. Horner 1,484 T por dos vías

- Suma de pasos bit a bit: ida 742 × 2 = **1,484 T**. ✓
- Perfilador: 422 ANDs + 531 iadd + 531 isub = **1,484 T**. ✓
- Coinciden exacto.

### 4. Proyecciones §9.3 (recalculadas por mí con la fórmula oficial)

C = T + (1.0 + n_rot × rot_T)/4; rot_T = 27.947630501632958; n_rot = 35; C_base = 2,805.791767; score_base = 390,005.06. Q_break(T) = 390,005.06 / C(T).

| Caso | T | Q | C (recalc.) | score (recalc.) | Q_break (recalc.) | Veredicto |
|---|---|---|---|---|---|---|
| Baseline | 2,561 | 139 | 2,805.79 | 390,005.06 | — | referencia |
| acc_keep FULL | 2,697 | 180 | 2,941.79 | **529,522.52** | **132.57** | **NO PASA** (+35.77%) |
| acc_seq FULL | 2,987 | 139 | 3,231.79 | 449,219.06 | 120.68 | NO PASA (+15.18%) |
| narrow FULL | 3,109 | 139 | 3,353.79 | 466,177.06 | 116.29 | NO PASA (+19.53%) |
| acc_keep cherry-pick | 2,535 | 148 | 2,779.79 | 411,409.18 | 140.30 | NO PASA (+5.49%) |
| acc_keep fila 1 m=5,m=9 | 2,545 | 139 | 2,789.79 | 387,781.06 | 139.80 | PASA* (−0.57%) |

Todos los scores y Q_break coinciden con el reporte (diferencias ≤ 0.01 por redondeo). ✓

- acc_keep FULL: 180 × 2,941.7918 = 529,522.52. ✓ Q_break = 390,005.06 / 2,941.7918 = 132.57. ✓
- Cherry-pick: 148 × 2,779.7918 = 411,409.18. ✓ Q_break = 140.30 < 148 → NO PASA. ✓
- Micro-opt: 139 × 2,789.7918 = 387,781.06. ✓ Q_break = 139.80 > 139 → PASA. ✓

### 5. Condiciones de descarte §9.4 (ambas se cumplen)

- T_paso (209) ≥ 4 × T_bit (4 × 45 = 180). 209 ≥ 180. ✓
- Q (180) > break-even (132.57). ✓

### 6. Corrección 64/64 (del JSON, leído directamente)

16 combinaciones (4 ventanas × 4 construcciones), cada una ok=64, total=64, bad=[]. **64/64 en las 16.** ✓ El scratch vuelve a |0⟩. La nota del reporte sobre el primer intento de lectura (16/64 por leer `read_across_shots` como entero por qubit) es transparente y correcta: el error fue de lectura, no del circuito.

### 7. Fase / eps

num_z_pow = 0, fase del tiro 0, eps sin cambio (6.694e-13). Consistente: el paso windowed no introduce rotaciones. ✓

## Precisión

### D-T2-1 (menor, NO afecta el veredicto)

La fórmula `acc_keep = 9n+2W−9 por ventana` que el reporte dice "verificado exacto contra todos los valores medidos" **coincide en 5 de 6 ventanas, pero NO en fila 1 m=9 (n=2, W=19)**: la fórmula da 9×2+2×19−9 = **47**, el medido es **38**.

Causa (verificada por mí): la fórmula asume 4 productos parciales (3 iadd + 1 isub + descomputo). Con n=2 solo existen 2 productos parciales (P_0, P_1), así que la fórmula no aplica en ese borde. Las 5 ventanas con n≥6 sí coinciden exacto (209, 173, 137, 119, 83).

**Impacto: ninguno.** Las proyecciones §9.3 usan los T MEDIDOS por ventana (no la fórmula), y el veredicto lo dominan la ventana fila 0 m=1 (209 T, n=18, donde la fórmula sí coincide) y los totales medidos. El descarte del TODO-2 se sostiene.

## Límites (los del reporte, confirmados)

- NO se construyó el TODO-2 completo (solo la medición aislada, como pedía la tarea).
- NO se corrió Gold en la Kali (el §9 no lo exige para el paso aislado; la corrección por simulación exhaustiva + fase 0 es lo que pide el §9).
- NO se tocó: árbol B/C original, árboles R1/R2/R5/P1/P2/P3, producción, ZIP Adopted v3, candidato swap42, entrenamiento SomeJoint.

## Hallazgo menor (del reporte, lo suscribo)

Ventanear solo fila 1 m=5,m=9 con acc_keep ahorra 16 T (2,561 → 2,545) con Q=139, score 387,781.06 (−0.57%). Es una micro-optimización de 2 ventanas, NO el TODO-2. Queda a decisión de Elán si vale la pena (Programación no lo adopta: cambio de constructor por 16 T). Yo tampoco lo adopto como parte del TODO-2 — es decisión separada de Elán.

## Siguiente paso

Esta verificación va a Datos para supervisión (cadena: Programación → Datos → Brujo → Auditor → Elán). El Auditor revisa después de Datos. Elán decide (incluido si la micro-optimización fila 1 m=5,m=9 vale la pena).
