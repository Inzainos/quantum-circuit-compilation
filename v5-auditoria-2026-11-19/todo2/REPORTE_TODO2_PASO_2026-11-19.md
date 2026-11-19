# REPORTE — Medición TODO-2: UN paso windowed aislado (invsqrt)

**Fecha:** 2026-11-19 ~15:17 CST (21:17 UTC)
**Orden:** Elán (2026-11-19 ~15:00 CST, vía el Brujo). Medición standalone, NO el TODO-2 completo.
**Workspace:** `~/workspace/qcc-data/test-dev/espiral-prototipo/todo2-paso/`
**Árbol usado:** copia fresca del árbol B/C en `todo2-paso/tree/` (el árbol B/C original NO se tocó).
**Base de comparación:** logshift2 (baseline adoptada), NO R1 — el diseño TODO-2 se mide contra la
baseline logshift2, como pide la tarea.

## 0. Veredicto (resumen)

**TODO-2 (ventaneado del Horner) SE DESCARTA con número — NO PASA el criterio §9.**

El paso windowed aislado cuesta MÁS Toffolis que los 4 pasos bit a bit que reemplaza en las
ventanas que dominan el Horner, y su proyección de score es PEOR que el baseline en las tres
construcciones medidas. La hipótesis del diseño ("cada paso ~3× un paso de bit", 25–35% de
ahorro) queda **refutada por medición**: el paso windowed mejor (acumulador) cuesta 209 T
en la ventana fila 0 m=1, es decir **4.64× un paso de bit (45 T) y 1.201× los 4 pasos bit a bit
(174 T)** — no 3×.

| Construcción (ventaneado FULL, 8 ventanas) | T nuevo | Q proy. | C | score proy. | Q_break | Δ score | §9 |
|---|---|---|---|---|---|---|---|
| **acc_keep** (acumulador, P_j vivos) | 2,697 | 180 | 2,941.79 | 529,522.52 | 132.57 | **+35.77%** | NO PASA |
| **acc_seq** (acumulador, un P_j a la vez) | 2,987 | 139 | 3,231.79 | 449,219.06 | 120.68 | **+15.18%** | NO PASA |
| **narrow** (4 isub estrechos directos) | 3,109 | 139 | 3,353.79 | 466,177.06 | 116.29 | **+19.53%** | NO PASA |
| acc_keep mejor-por-ventana (cherry-pick) | 2,535 | 148 | 2,779.79 | 411,409.18 | 140.30 | **+5.49%** | NO PASA |
| acc_keep solo fila 1 m=5,m=9 (micro-opt) | 2,545 | 139 | 2,789.79 | 387,781.06 | 139.80 | −0.57% | PASA* |

Baseline logshift2: Q=139, T=2,561, C=2,805.791767, **score 390,005.06**.

\* El único caso que pasa NO es el TODO-2: es ventanear solo 2 ventanas tardías de la fila 1
(ahorro 16 T, 0.57%). Se reporta como hallazgo menor, no como adopción del TODO-2.

Se cumplen las DOS condiciones de descarte del §9.4: T_paso (209) ≥ 4 × T_bit (4×45 = 180)
y Q_paso empuja el Q total (180) por encima del break-even (132.57).

## 1. Qué paso medí (definición)

El diseño no define "un paso windowed" con una fórmula cerrada. Mi interpretación, declarada
antes de medir: **un grupo de 4 pasos de bit consecutivos dentro de una fila del Horner** —
ventana que empieza en m, que computa restar S = Σ_j u_j·(A>>j) de c[i], donde A = c[i+1]>>m
y u_j son los 4 bits de control de la ventana. Fundamento: §9.3 del diseño dice que el Horner
tiene dd=13 pasos de bit por fila → 4 pasos de ventana (4+4+4+1 bits). Ventanas por fila:
m = 1, 5, 9, 13 (la 4ª es de 1 bit en fila 0 y está vacía en fila 1, porque dd=13 y w[2]=11).

Estructura del Horner (leída en código, `tree/src/invsqrt_halfsplit.py` l.169 `HornerMitad`,
l.186 `u_ctl`; `tree/verifiers/invsqrt/nr_reference_circuit.py` l.150 `_add_row`):
- El baseline usa `HornerMitad` con el `_add_row` del verificador (NO `_add_row_estrecha`).
- Cada paso de bit es `_add_row(b, inverse, ctl, terms, c[i], scratch, subtract=True)` con
  terms = [(c[i+1][t], t−m) for t in range(m, w[i+1])]. Orden ida: i=1 luego i=0; m=1..13.
- El Horner corre ida Y vuelta: T_Horner = 2 × T_ida.
- Anchos: w = [28, 19, 11] (c0, c1, c2); scratch compartido = max(w) = 28 bits.

**Control baseline reproducido:** `python3.13 -m src.invsqrt_logshift2 --sesgo 1 --out
control_baseline.kmb` → Q=139, T=2,561, sha256 `7e842bbfba8fb40d32c05b3b195073cf368981a92de77197ed22bd3a3f3faf79`
(byte-idéntico al baseline de producción). `control_baseline.kmb`, 437,575 B.

**Horner medido por dos vías independientes (coinciden exacto):**
- Suma de mis pasos bit a bit standalone: ida 742 → **1,484 T**.
- Perfilador `kmx_profile.py` sobre el control: horner 422 (ANDs) + horner/iadd 531 +
  horner/isub 531 = **1,484 T** (`logs/kmx_profile_control.log`). Los ANDs de ida son 211
  (156 fila 0 + 55 fila 1) y los isub de ida 531 (351 + 180) — exactos.

## 2. Construcciones windowed medidas (archivo `medida_paso.py`, md5 `d20ab7e1…`)

Las tres computan lo mismo que los 4 pasos bit a bit: restar S = Σ_j u_j·(A>>j) del destino
(mod 2^W). El acumulador es de n+1 bits (no n): S < 1.875·2^n necesita n+1 bits.

- **bit4 (control):** 4 `_add_row` consecutivos del verificador, scratch compartido de 28 bits.
- **acc_keep:** productos parciales P_j = u_j AND (A>>j) en scratch; P_0 en el acumulador
  (n+1 bits); 3 iadd (P_j → acc); 1 isub (acc → destino); descomputo: 3 isub inversos
  + del_and (gratis). P_1,P_2,P_3 vivos hasta el descomputo.
- **acc_seq:** igual, pero un P_j a la vez (del_and inmediato; recomputo de P_j para
  descomputar el acumulador). Menos scratch, más T.
- **narrow:** sin acumulador: 4 isub estrechos directos al destino, un P_j a la vez.
- **Overhead §9.3 = 0:** no hay tabla de ventana que inicializar ni mux de selección —
  los bits de control son los bits de x, ya disponibles. La proyección es OPTIMISTA para
  el lado windowed (cualquier overhead real solo empeoraría el número).

Costos kickmix medidos antes (`sonda_costos.py`, `logs/sonda_costos.log`,
`logs/sonda_iadd_fino.log`): init_and = 1 T/producto; del_and = 0 T;
isub(a,W) = iadd(a,W) = **max(W−1, 2W−a−4)** — el sumador estrecho nunca cuesta menos
que el de ancho completo (W−1). Medido: (17,19) = 18, no 17; (16,19) = 18; (15,19) = 19;
(19,28) = 33; (18,28) = 34; (10,19) = 24. (La regla max() explica el +2 sistemático
de acc_keep sobre mi fórmula inicial 9n+2W−11: el iadd(P_1,acc) de (n−1)x(n+1) cuesta
n, no n−1, y su inverso otro tanto.)

## 3. Resultados medidos por ventana (T, Q) — `logs/medida_paso.log`, `resultados_paso.json`

T = `operation_statistics().num_toffoli_like`; Q = `num_qubits` (pico de qubits vivos —
el builder reutiliza qubits liberados, verificado en `logs/sonda_reuse.log`).

| Ventana | n | bit4 T/Q | acc_keep T/Q | acc_seq T/Q | narrow T/Q |
|---|---|---|---|---|---|
| fila 0 m=1 | 18 | 174 / 105 | **209 / 146** | 257 / 105 | 208 / 97 |
| fila 0 m=5 | 14 | 158 / 105 | **173 / 130** | 209 / 94 | 208 / 93 |
| fila 0 m=9 | 10 | 142 / 105 | **137 / 114** | 161 / 90 | 208 / 89 |
| fila 0 m=13 | 6 | 33 / 105 | 51 / 86 | 51 / 86 | 52 / 85 |
| fila 1 m=1 | 10 | 106 / 79 | **119 / 88** | 143 / 64 | 136 / 63 |
| fila 1 m=5 | 6 | 90 / 79 | **83 / 72** | 95 / 60 | 136 / 59 |
| fila 1 m=9 | 2 | 39 / 79 | **38 / 57** | 39 / 56 | 68 / 55 |
| fila 1 m=13 | — | 0 | 0 | 0 | 0 |

Totales de ida (Σ ventanas): bit4 = **742**; acc_keep = **810** (+68); acc_seq = **955**
(+213); narrow = **1,016** (+274). El Horner total (ida+vuelta): bit4 = 1,484;
acc_keep = 1,620; acc_seq = 1,910; narrow = 2,032.

Lectura: el windowed solo gana en las ventanas TARDÍAS (n pequeño): fila 0 m=9 (−5 T),
fila 1 m=5 (−7 T), fila 1 m=9 (−1 T). Pierde en las ventanas TEMPRANAS, que dominan el
T: fila 0 m=1 (+35 T), fila 0 m=5 (+15 T), fila 1 m=1 (+13 T). El neto es negativo.

**Q (incremento vs bit4, misma ventana):** acc_keep: fila 0 m=1 **+41**, m=5 +25, m=9 +9,
m=13 −19; fila 1 m=1 +9, m=5 −7, m=9 −22. Máximo +41 → Q_proy = 180. acc_seq y narrow
NO aumentan Q (máximo 0 y negativo, resp.) — su problema es solo T. El scratch de acc_keep
es 4n−5 bits (acumulador n+1 + P_1+P_2+P_3 = 3n−6); fila 0 m=1: 67 bits vs 28 del
scratch compartido → +39 de scratch (+2 de ancillas internas del sumador = +41 medido).

## 4. Corrección (16 valores) — `logs/medida_paso.log`

Simulación exhaustiva con `km.Simulator` (patrón del verificador oficial:
`write_across_shots` / `do` / `read_across_shots`): 16 valores de ventana u (0..15) ×
4 pares (src, tgt) = **64 casos por (fila, m, construcción)**, en (fila 0, m=1), (fila 1, m=1),
(fila 0, m=5), (fila 1, m=5). **64/64 correctos en las 16 combinaciones** (bit4, acc_keep,
acc_seq, narrow coinciden entre sí y con el valor clásico de referencia; el scratch vuelve
a |0> en todos los casos). Los circuitos son clásico-reversibles (sin H ni rotaciones), así
que la simulación es exacta para valores. (Nota: un primer intento leyó `read_across_shots(..., out=int)`
— que devuelve un entero POR QUBIT, no por tiro — y dio 16/64; corregido a lectura bool
(width, batch) y reconstrucción del entero: 64/64. El error fue de mi lectura, no del circuito.)

## 5. Fase / eps — `logs/sonda_fase.log`, `logs/sonda_zpow.log`

- `num_z_pow = 0` en las 4 construcciones (bit4, acc_keep, acc_seq, narrow).
- Fase del tiro medida con el Simulator: **0 medias vueltas** (bit4 y acc_keep, u=0b1111).
- El paso windowed NO introduce rotaciones ni cambia eps: **eps = 6.6939970219409e-13 sin
  cambio, rot_T = 27.947630501632958, n_rot = 35**. El costo de síntesis no cambia.
  (Lección B+C no aplica aquí: no hay peor error nuevo que sintetizar.)

## 6. Proyección §9.3 y criterio §9 — `logs/proyeccion.log`, `proyeccion.py`

Fórmula oficial: score = Q × C; C = T + (1.0 + n_rot × rot_T)/4; rot_T(eps) =
0.56·log2(1/eps) + 5.3 = 27.947630501632958; C_base = 2,805.791767; score_base = 390,005.06.
Regla §9.3: T_Horner_proyectado = Σ T_ventana (medido por ventana, ida) × 2 (ida+vuelta);
Q_proyectado = 139 + máx incremento de Q standalone vs bit4. Q_break(T) = 390,005.06 / C(T).

| Caso | T | Q | C | score | Q_break | Veredicto |
|---|---|---|---|---|---|---|
| Baseline | 2,561 | 139 | 2,805.79 | 390,005.06 | — | referencia |
| acc_keep FULL | 2,697 | 180 | 2,941.79 | 529,522.52 | 132.57 | **NO PASA** (+35.77%) |
| acc_seq FULL | 2,987 | 139 | 3,231.79 | 449,219.06 | 120.68 | **NO PASA** (+15.18%) |
| narrow FULL | 3,109 | 139 | 3,353.79 | 466,177.06 | 116.29 | **NO PASA** (+19.53%) |
| acc_keep mejor-por-ventana | 2,535 | 148 | 2,779.79 | 411,409.18 | 140.30 | **NO PASA** (+5.49%) |
| acc_keep solo fila 1 m=5,m=9 | 2,545 | 139 | 2,789.79 | 387,781.06 | 139.80 | PASA* (−0.57%) |

Comparación con el break-even del diseño (Q ≈ 160–171 a 25–35% de ahorro): el TODO-2
necesitaría T ≈ 2,041–2,190 con Q ≤ 160–171. Lo medido es T = 2,697 con Q = 180
(acc_keep FULL) — fuera del rango por ambos ejes. Incluso el mejor caso cherry-pick
(T=2,535, Q=148) queda fuera (Q_break 140.30 < 148).

## 7. Por qué pierde el ventaneado (causa estructural, medida)

1. **El isub bit a bit es barato porque es de ancho completo.** `_add_row` coloca los
   productos en el scratch alineados con el destino y hace UN isub de ancho completo:
   costo W−1 (27 T en fila 0, 18 T en fila 1). Cualquier versión windowed hace su isub
   con un sumando ESTRECHO (n+1 bits en un destino de W bits): costo 2W−(n+1)−4
   (45 T en fila 0 m=1). El "impuesto del isub estrecho" es +18 T por ventana, y se paga
   una sola vez por ventana — pero es lo que mata el ahorro. Prueba: hasta una ventana
   de 1 bit (fila 0 m=13) pierde: 51 T windowed vs 33 T bit a bit.
2. **La red sumadora se paga dos veces.** Formar S desde 4 productos parciales cuesta
   ~3n T (3 iadd) y descomputar el acumulador cuesta otros ~3n T (el scratch debe volver
   a |0> al final de la ida). El bit a bit descomputa GRATIS (del_and, por medición).
   El costo total de acc_keep es **9n+2W−9 por ventana** (verificado exacto contra todos
   los valores medidos: 209, 173, 137, 119, 83, 38) vs 4n+4W−10 bit a bit: gana solo
   si n < (2W−1)/5 — fila 0: n < 11; fila 1: n < 7.4. Solo las ventanas tardías cumplen.
3. **El Q es el eje que domina.** acc_keep ahorra T solo en 3 ventanas (−13 T de ida en
   el mejor cherry-pick) pero su scratch (4n−5 bits) sube Q +41 en la ventana dominante
   (fila 0 m=1). 1 qubit ≈ 20 Toffolis en esta métrica: +41 Q ≈ +820 T equivalentes.
   acc_seq evita el Q (+0) pero paga +213 T de ida en recomputo. No hay punto del
   tradeoff que caiga bajo la curva de break-even.

**Análisis teórico (no medido, para no repetirlo):** carry-save con compresores MAJ
tampoco salva el diseño — el MAJ de 1 Toffoli corrompe sus entradas (a,b → a⊕c,b⊕c),
así que la versión limpia necesita 3 T por bit de carry (≈17n+2W−12 por ventana, peor
que acc_keep) y su scratch es ~8n bits (peor Q). Un lookup de los 16 múltiplos no
funciona: el multiplicando es cuántico (c[i+1] es registro cuántico; dirección
segmento+ventana = 13 bits → 8,190 T). Un mux de 16 entradas es peor (~22n+W).
acc_keep está esencialmente en el piso teórico de la familia "formar S y restar" (su
red de 3 iadd ≈ el árbol carry-save mínimo), y aun así pierde — por eso el descarte
es robusto y no depende de no haber probado otra construcción.

## 8. Hallazgo menor (no es el TODO-2)

Ventanear SOLO las dos ventanas tardías de la fila 1 (m=5: 83 vs 90 T; m=9: 38 vs 39 T)
con acc_keep ahorra 16 T totales (2,561 → 2,545) con Q = 139 (sus incrementos de Q son
negativos: −7 y −22), score 387,781.06 (−0.57%, Q_break 139.80 > 139). Es una
micro-optimización de 2 ventanas, no el TODO-2 del diseño, y su ganancia (0.57%) está
muy por debajo del rango +4.8–7.1% [ESTIMADO] del diseño. Queda a decisión de Elán si
vale la pena (yo no lo adopto: es un cambio de constructor por 16 T).

## 9. Archivos y logs (todo en `todo2-paso/`)

| Archivo | Tamaño | Contenido |
|---|---|---|
| `REPORTE_TODO2_PASO_2026-11-19.md` | este reporte | veredicto + números |
| `medida_paso.py` (md5 `d20ab7e1…`) | 8,670 B | constructores bit4/acc_keep/acc_seq/narrow + simulación |
| `proyeccion.py` | 2,579 B | proyección §9.3 exacta |
| `resultados_paso.json` (md5 `3ae57808…`) | 4,977 B | T/Q por ventana + corrección 64/64 |
| `control_baseline.kmb` (sha `7e842bbf…`) | 437,575 B | baseline reproducido byte-idéntico |
| `sonda_costos.py` | 2,611 B | costos init_and/del_and/isub/iadd |
| `sonda_fase.py`, `sonda_reuse.py` | 1,156 / 683 B | fase 0; builder reutiliza qubits liberados |
| `tree/` | copia del árbol B/C | NO se modificó el árbol original |
| `logs/medida_paso.log` | 2,311 B | T/Q por ventana + corrección 64/64 |
| `logs/proyeccion.log` | 792 B | proyecciones §9.3 exactas |
| `logs/kmx_profile_control.log` | 3,321 B | Horner = 422+531+531 = 1,484 T |
| `logs/sonda_costos.log` | 2,592 B | costos de primitivas |
| `logs/sonda_fase.log` / `logs/sonda_zpow.log` | 297 / 225 B | fase 0; num_z_pow = 0 |
| `logs/sonda_iadd_fino.log` | 413 B | isub/iadd = max(W−1, 2W−a−4) |
| `logs/sonda_reuse.log` | 129 B | num_qubits = pico de vivos |
| `logs/live_probe.log` | 495 B | línea de tiempo de qubits vivos del baseline |

## 10. Qué NO hice (límites)

- NO construí el TODO-2 completo (solo la medición aislada de UN paso por ventana, como
  pedía la tarea). NO corrí Gold en la Kali (el §9 no lo exige para el paso aislado; la
  corrección por simulación exhaustiva sobre 16 valores + fase 0 es lo que pide el §9).
- NO toqué: árbol B/C original, árboles R1/R2/R5/P1/P2/P3, producción, ZIP Adopted v3,
  candidato swap42, entrenamiento SomeJoint en la Kali.
- La proyección §9.3 usa la regla declarada (Σ T_ventana × 2 + overhead 0) y la versión
  refinada por fila (3 ventanas completas + 1 de un bit por fila). El Q proyectado usa el
  máximo incremento standalone vs bit4 (conservador: el scratch compartido es 28 bits;
  si el workspace real del Horner fuera 45 bits, el incremento de acc_keep sería +24
  en vez de +41 y Q_proy = 163 — que TAMPOCO pasa: score 163 × 2,941.79 = 479,512.06,
  Q_break 132.57. El veredicto no depende de esa contabilidad).
