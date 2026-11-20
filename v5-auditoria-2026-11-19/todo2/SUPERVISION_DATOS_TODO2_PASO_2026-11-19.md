# SUPERVISIÓN DE DATOS — Medición TODO-2 (paso windowed aislado): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~15:20 CST
**Supervisor:** Datos (Analista de datos)
**Cadena:** Programación (mide) → Brujo ✓ → **Datos (este documento)** →
Auditor → Elán (decide).
**Veredicto: CONCURRO (PASA).** La medición es correcta y el veredicto se
sostiene: **TODO-2 (ventaneado del Horner) SE DESCARTA con número — NO
PASA el criterio §9.**
**Nota de orden:** el Brujo verificó antes que yo — la cadena está completa
en cualquier orden (igual que en P1/P2/P3 y en el QF). Mi supervisión es
por cómputo propio sobre el JSON y los logs leídos directamente, no por
confianza en el reporte ni en la verificación.

## 1. Archivos verificados en disco por mí (medidos, no citados de oídas)

| Archivo | Medido por mí | Reportado | ¿Coincide? |
|---|---|---|---|
| `REPORTE_TODO2_PASO_2026-11-19.md` | 232 l. / 15,582 B / md5 `cf3b0e20…` | 232 l. | ✓ |
| `VERIFICACION_BRUJO_TODO2_PASO_2026-11-19.md` | 103 l. / md5 `b6a839a0…` | 103 l. / md5 `b6a839a0…` | ✓ |
| `medida_paso.py` | md5 `d20ab7e1…` | md5 `d20ab7e1…` | ✓ |
| `resultados_paso.json` | 4,977 B / md5 `3ae57808…` | md5 `3ae57808…` | ✓ |
| `control_baseline.kmb` | 437,575 B / sha256 `7e842bbf…` | mismo sha | ✓ |
| `logs/` (9 logs), `tree/` (copia del árbol B/C) | presentes | presentes | ✓ |

## 2. Baseline reproducido — verificado por mí cargando el circuito

`control_baseline.kmb` es **byte-idéntico al baseline logshift2 de
producción** (sha256 `7e842bbfba8fb40d32c05b3b195073cf368981a92de77197ed22bd3a3f3faf79`).
Cargado por mí con kickmix: **Q = 139, T = 2,561, num_ops = 51,798,
nbits = 513** — Q/T exactos; num_ops 51,798 coincide con el baseline de
la cadena R5. Score 390,005.06 (verificado en §5).

## 3. Horner 1,484 T por dos vías independientes (coinciden exacto)

- Suma de mis pasos bit a bit standalone (JSON): ida 742 × 2 = **1,484 T** ✓
- Perfilador (`logs/kmx_profile_control.log`): horner 422 (ANDs) +
  horner/iadd 531 + horner/isub 531 = **1,484 T** ✓
- El perfilador además confirma la tabla de etapas del diseño:
  normalize 224 (48+88+88), giro 42 (21+21), lookup 551 (510+41),
  denorm 260 (130+130). ✓

## 4. T/Q por ventana — del JSON leído directamente (coinciden exacto con la tabla del reporte)

| Ventana | n | bit4 T/Q | acc_keep T/Q | acc_seq T/Q | narrow T/Q |
|---|---|---|---|---|---|
| fila 0 m=1 | 18 | 174 / 105 | **209 / 146** | 257 / 105 | 208 / 97 |
| fila 0 m=5 | 14 | 158 / 105 | **173 / 130** | 209 / 94 | 208 / 93 |
| fila 0 m=9 | 10 | 142 / 105 | **137 / 114** | 161 / 90 | 208 / 89 |
| fila 0 m=13 | 6 | 33 / 105 | 51 / 86 | 51 / 86 | 52 / 85 |
| fila 1 m=1 | 10 | 106 / 79 | **119 / 88** | 143 / 64 | 136 / 63 |
| fila 1 m=5 | 6 | 90 / 79 | **83 / 72** | 95 / 60 | 136 / 59 |
| fila 1 m=9 | 2 | 39 / 79 | **38 / 57** | 39 / 56 | 68 / 55 |

Totales de ida (Σ ventanas, recalculados por mí): bit4 = **742**;
acc_keep = **810** (+68); acc_seq = **955** (+213); narrow = **1,016**
(+274). Horner total (ida+vuelta): bit4 = 1,484; acc_keep = 1,620;
acc_seq = 1,910; narrow = 2,032. ✓

Incrementos de Q acc_keep vs bit4 (recalculados): fila 0 m=1 **+41**,
m=5 +25, m=9 +9, m=13 −19; fila 1 m=1 +9, m=5 −7, m=9 −22. Máximo
**+41** → Q_proy = 139+41 = **180**. ✓ El windowed solo gana en las
ventanas tardías (fila 0 m=9 −5 T, fila 1 m=5 −7 T, fila 1 m=9 −1 T) y
pierde en las tempranas que dominan el T (fila 0 m=1 +35 T, m=5 +15 T,
fila 1 m=1 +13 T). El neto es negativo.

## 5. Proyecciones §9.3 — recalculadas por mí con la fórmula oficial

C = T + (1.0 + n_rot × rot_T)/4; rot_T = 0.56·log2(1/eps) + 5.3 =
**27.947630501632958** (recalculado de eps = 6.6939970219409e-13 ✓);
C_base = 2,805.791767; score_base = 390,005.06. Q_break(T) =
390,005.06 / C(T).

| Caso | T | Q | C (recalc.) | score (recalc.) | Q_break (recalc.) | Veredicto |
|---|---|---|---|---|---|---|
| Baseline | 2,561 | 139 | 2,805.79 | 390,005.06 | — | referencia |
| acc_keep FULL | 2,697 | 180 | 2,941.79 | **529,522.52** | **132.57** | **NO PASA** (+35.77%) |
| acc_seq FULL | 2,987 | 139 | 3,231.79 | 449,219.06 | 120.68 | NO PASA (+15.18%) |
| narrow FULL | 3,109 | 139 | 3,353.79 | 466,177.06 | 116.29 | NO PASA (+19.53%) |
| acc_keep cherry-pick | 2,535 | 148 | 2,779.79 | 411,409.18 | 140.30 | NO PASA (+5.49%) |
| acc_keep solo fila 1 m=5,m=9 | 2,545 | 139 | 2,789.79 | 387,781.06 | 139.80 | PASA* (−0.57%) |

Verificación de las T proyectadas (regla §9.3: T = 2,561 − 1,484 +
2 × Σ T_ventana): acc_keep 2,561−1,484+2×810 = **2,697** ✓; acc_seq
2,561−1,484+2×955 = **2,987** ✓; narrow 2,561−1,484+2×1,016 = **3,109** ✓.
Cherry-pick (mejor por ventana): ida 174+158+137+33+106+83+38 = **729** →
T = 2,561−1,484+2×729 = **2,535** ✓; Q: máx incremento entre las
ventanas elegidas (+9 en fila 0 m=9) → **148** ✓. Micro-opt: ida
742−7−1 = **734** → T = **2,545** ✓; incrementos −7 y −22 → Q = **139** ✓.
Todos los scores, Q_break y deltas coinciden con el reporte (≤ 0.01 por
redondeo). El TODO-2 necesitaría T ≈ 2,041–2,190 con Q ≤ 160–171; lo
medido es T = 2,697 con Q = 180 — fuera del rango por ambos ejes.

## 6. Condiciones de descarte §9.4 — ambas se cumplen

- T_paso (209) ≥ 4 × T_bit (4 × 45 = 180). 209 ≥ 180. ✓
- Q (180) > break-even (132.57). ✓

## 7. Corrección 64/64 — del JSON leído directamente

16 combinaciones (4 ventanas × 4 construcciones), cada una ok=64,
total=64, bad=[]. **64/64 en las 16.** ✓ El scratch vuelve a |0⟩. La
nota del reporte sobre el primer intento de lectura (16/64 por leer
`read_across_shots` como entero por qubit) es transparente y correcta:
el error fue de lectura, no del circuito.

## 8. Fase / eps

`num_z_pow = 0` en las 4 construcciones; fase del tiro 0 medias vueltas
(bit4 y acc_keep, u=0b1111); **eps = 6.6939970219409e-13 sin cambio,
rot_T = 27.947630501632958, n_rot = 35**. El paso windowed NO introduce
rotaciones ni cambia eps — el costo de síntesis no cambia. ✓ La lección
B+C no aplica aquí (no hay peor error nuevo que sintetizar).

## 9. Precisiones

### D-T2-1 (del Brujo — fórmula acc_keep) — CONCURRO
La fórmula `acc_keep = 9n+2W−9` coincide en 5/6 ventanas pero da **47**
(no 38) en fila 1 m=9 (n=2, W=19): 9×2+2×19−9 = 47. Verificado por mí.
Causa: con n=2 solo hay 2 productos parciales, no 4. **Impacto: ninguno**
— las proyecciones §9.3 usan los T MEDIDOS, no la fórmula.

### D-T2-2 (mía — la fórmula bit4 tiene el mismo borde)
La fórmula `bit4 = 4n+4W−10` da 174, 158, 142, 106, 90 en 5/6 ventanas, pero **74** (no 39) en fila 1 m=9 (n=2, W=19):
4×2+4×19−10 = 74. Misma causa que D-T2-1: el modelo supone 4 pasos
completos y la ventana parcial tiene solo 2 términos. **Impacto: ninguno**
— mismo motivo que D-T2-1. (La ventana fila 0 m=13, de 1 bit, tampoco
entra en los modelos de 4 pasos; el reporte no la reclama.)

### D-T2-3 (mía — procedencia de T_bit = 45)
El T_bit = 45 T del §9.4 viene de la hipótesis del diseño (proyección:
"paso windowed ~3× paso bit = 135 T" → 135/3 = 45), no de una medición
directa de un paso aislado. Los costos medidos por paso son 43.5 T
promedio en ventana (174/4) o 52 T standalone (`_add_row` sonda, fila 0).
Bajo CUALQUIERA de estas lecturas, 4 × T_bit ≤ 208 < 209, así que la
condición 1 del §9.4 se cumple de todos modos — y la condición 2 se
cumple por margen amplio. El veredicto no depende del valor de T_bit.

### Costos de primitivas (verificados — regla max())
`isub(a,W) = iadd(a,W) = max(W−1, 2W−a−4)`: verificado exacto en los 7
pares de `sonda_costos.log` y los 7 de `sonda_iadd_fino.log` ((17,19)=18,
(16,19)=18, (15,19)=19, (19,28)=33, (18,28)=34, (14,19)=20, (10,19)=24).
init_and = 1 T/producto; del_and = 0 T. El sumador estrecho nunca cuesta
menos que el de ancho completo — es el "impuesto del isub estrecho" que
mata el ahorro (§7.1 del reporte, medido).

## 10. Hallazgo menor — micro-optimización fila 1 m=5,m=9 (NO es el TODO-2)

Verificado: ventanear solo esas dos ventanas con acc_keep ahorra 16 T
(2,561 → 2,545) con Q = 139, score **387,781.06 (−0.57%)**,
Q_break **139.80** > 139 → PASA el criterio §9 como cambio de 2
ventanas. Es una micro-optimización, NO el TODO-2 del diseño, y su
ganancia (0.57%) está muy por debajo del rango +4.8–7.1% [ESTIMADO] del
diseño. Queda a decisión de Elán si vale la pena. Yo tampoco lo adopto
como parte del TODO-2 — es decisión separada de Elán (igual que
Programación y el Brujo).

## 11. Robustez del veredicto (sensibilidad §10 del reporte — verificada)

Si el workspace real del Horner fuera 45 bits (no 28), el incremento de
acc_keep sería +24 en vez de +41 y Q_proy = 163 — que TAMPOCO pasa:
score 163 × 2,941.79 = **479,512.06**, Q_break 132.57. Verificado por mí.
El veredicto no depende de esa contabilidad. (El análisis teórico del §7
— carry-save, lookup, mux — está marcado "no medido" en el reporte; no
lo verifico: el descarte descansa en las mediciones, no en esa teoría.)

## 12. Veredicto: CONCURRO (PASA)

La medición es correcta y **TODO-2 SE DESCARTA con número**: el paso
windowed mejor cuesta 209 T (4.64× un paso de bit, 1.201× los 4 pasos bit
a bit que reemplaza); su mejor proyección da score 529,522.52 (+35.77%)
y hasta el cherry-pick (411,409.18, +5.49%) queda fuera del break-even
(Q=148 > Q_break 140.30). La hipótesis del diseño ("cada paso ~3× un
paso de bit", 25–35% de ahorro) queda **refutada por medición**.
Precisiones: concurro D-T2-1; mías D-T2-2 y D-T2-3 (menores, sin impacto).

**Cadena: Programación ✓ → Brujo ✓ → Datos ✓ (este documento) →
Auditor ✓ → Elán decide.** Consecuencia según la recomendación conjunta
(Datos + Auditor): con TODO-2 descartado, el siguiente candidato de
construcción invsqrt es **TODO-4** (una variante aislada de lookup, con
su criterio) — pendiente de la decisión de Elán (incluida la
micro-optimización fila 1 m=5,m=9 y la adopción del QF). R1+R5 sigue en
construcción en paralelo.

## 13. Adenda — revisión del Auditor (2026-11-19 ~15:24 CST)

Revisión del Auditor: `~/workspace/auditoria/REVISION_AUDITOR_TODO2_PASO_2026-11-19.md`
(106 l. / md5 `202ce11d…`, verificado en disco por mí) — **CONCURRO
(PASA)**. El Auditor verificó por cómputo propio lo mismo que yo
(baseline byte-idéntico y cargado con kickmix, Horner 1,484 T por dos
vías, proyecciones §9.3, §9.4, corrección 64/64, fase 0) y **concurrió
con D-T2-1, D-T2-2 y D-T2-3**.

**A-T2-1 (del Auditor, menor) — CONCURRO:** la frase del reporte §7.2
("verificado exacto contra todos los valores medidos") es inexacta —
es 5 de 6, no 6 de 6. Es la misma imprecisión que D-T2-1/D-T2-2 ya
establecen para las fórmulas; la corrección es de redacción, sin
impacto en ningún número ni en el veredicto.

**Cadena TODO-2 COMPLETA: Programación ✓ → Brujo ✓ → Datos ✓ →
Auditor ✓ → Elán decide.**
