# REVISIÓN DEL AUDITOR — BORRADOR DE DATOS DE LA RECOMENDACIÓN CONJUNTA DE ADOPCIÓN

**Fecha:** 2026-11-19 ~13:35 CST
**Borrador revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/RECOMENDACION_CONJUNTA_ADOPCION_BORRADOR_2026-11-19.md` — **147 l. / md5 `032289cd…`** (Datos).
**Mi borrador:** `~/workspace/auditoria/BORRADOR_RECOMENDACION_ADOPCION_AUDITOR_2026-11-19.md` (enviado a Datos ~13:32).
**Pedido:** Elán (vía Brujo, vía Coordinador, ~13:26): recomendación conjunta Datos + Auditor del mejor camino de adopción.
**Regla 0:** cada número aquí está medido (cadenas completas) o verificado por cómputo propio en este turno; lo estimado se marca [ESTIMADO].

## Veredicto: CONCURRO EN LO SUSTANCIAL, CON 2 CORRECCIONES Y 3 PRECISIONES

Concurro con los 7 puntos de Datos en sustancia. Dos correcciones (A-RC-1: el orden de la medición TODO-2; A-RC-3/A-RC-4: el criterio de adopción del QF) y tres precisiones (A-RC-2: el Gold de la combinación; A-RC-5: acepto la corrección de Datos sobre R1+R5 — mi borrador decía "ortogonal" y estaba demasiado fuerte). Ninguna cambia la dirección general: R1 se queda, R2c fuera, R5 vía R1+R5, TODO-2 antes que TODO-4, P1+P2+P3 combinadas y después del QF, P5 fuera.

## Punto por punto

### §0 Números base — CONCURRO (verificados)

- (1857/1864)² = **0.992503** → mejora real **0.7497%** — verificado por cómputo propio en este turno. Score QF esperado = 2,993,914,799,696.024 × 0.992503 = **2,971,470,537,625.3** ✓ (coincide con el [ESTIMADO] 2,971,470,537,625.300 del Brujo y de mi borrador).
- Geomean QF [ESTIMADO, misma R] 3.53171 (Kaggle-escala 3.53906) ✓ (del Brujo).
- Ruido de R entre seeds (1.19–1.21, ~1.68%) mayor que la ganancia (0.75%) — por eso el `--seed` fijo ✓. (Ver A-RC-3: el rango [1.19, 1.21] como criterio de aceptación tiene un problema — el R del Gold de swap42 es 1.2131, fuera de ese rango.)
- Build Kali DONE byte-idéntico al control (sha `38b9cbf0…`, Q=1,857, T=710,312, 136 s, sin mezcla) ✓; Gold control corriendo (PID 1275, desde 13:19:55, swap42 con `--seed` explícito) ✓; Gold QF después (~7 min c/u) ✓ (todo del Brujo, ~13:28).

### §1.1 R1 se queda — CONCURRO

Ya decidido por Elán ("Deja R1", 12:16:35). Empate exacto con B, 2 CX menos reales (verificado en mi revisión R1: num_ops 51,795 vs 51,797), fricción mínima. Nada que mover.

### §1.2 R2c NO entra al set — CONCURRO

R2c (389,823.73) dominada por R1 (389,261.01): peor por 562.72 pese a 4 T menos (T=2,557 vs 2,561) — la mejora vive en r, no en T (C=2,804.49 vs 2,800.44) ✓. No se construye nada más sobre R2c. Se conserva documentada: sesgo correcto = 1 (el escaneo de sesgo lo re-corrí yo en R2: 6/6 filas exactas, sesgo=1 correcto; el valor 0.9586 para sesgo=2 es el medido por Datos en ese escaneo) y el filtro R2 cuesta 4 T ✓. Set de adopción invsqrt: **R1 (referencia) + R5 vía la combinación (§1.3)** ✓. Mi techo para R1+R2c (~25 puntos si el ΔC se transfiriera exacto, ~0.006%) coincide en orden de magnitud con la conclusión de Datos: no vale un build + Gold + cadena.

### §1.3 R5 vía R1+R5 — CONCURRO, Y ACEPTO LA CORRECCIÓN DE DATOS (A-RC-5)

- R5 sola = baseline (390,005.06), byte-idéntica; su valor es estructural (6 → 5 fases; copia CX de 28 plegada en `DesnormLog`) ✓.
- **Acepto la corrección de Datos a mi borrador:** la combinación R1+R5 **NO es un merge mecánico**. Mi borrador decía que los mecanismos son "ortogonales" (R1 toca el camino skip_low/copia, R5 el plegado de `copy_c0`) — eso está demasiado fuerte: **la truncación de R1 vive en `CopiaC0` y R5 elimina esa fase del orquestador**. La combinación es diseño (dónde vive la truncación cuando la copia se pliega en `DesnormLog`), no un merge. Por eso se construye y se verifica con Gold, no se asume. **Corrijo mi borrador en este punto.**
- Esperado (si el diseño se hace bien): score = R1 389,261.01, −1 fase, 2 CX menos ✓. El criterio de aceptación (empate con R1) es el correcto.

### §1.4 TODO-2 antes que TODO-4 — CONCURRO (números verificados)

- Horner 1,484 T (57.95% del T invsqrt) ✓ (brief de diseño).
- TODO-2 +4.8–7.1% [ESTIMADO] ✓ (D-DI-1, verificado por mí).
- Break-evens verificados por cómputo propio en este turno: Q_break(T) = 390,005.06 / C(T), C(T) = T + 244.79 (n_rot=35, rot_T≈27.947) → **T=2,190: Q_break = 160.18** ✓; **T=2,150: Q_break = 162.86 ≈ 163** ✓; **T=2,041.6: Q_break = 170.58** ✓. Los tres números de Datos casan exactos.
- Criterio §9 (un paso windowed standalone; si T_paso ≥ 4×T_bit o Q pasa el break-even, se DESCARTA con número) ✓.
- TODO-4 +2.0–3.5% realista, techo +7.6% (lookup 551 T con j=8, no ~279 T — ese era j=7) ✓. Criterio (139 + ΔQ) × (2,805.79 − ΔT) < 390,005.06 — correcto en forma (es score = Q × C con C = 2,805.79 − ΔT; el baseline da 139 × 2,805.79 = 390,004.81 por redondeo, el exacto es 390,005.06 con C=2,805.7917668892883).
- "El Paso 0 es el prerrequisito formal; la medición del paso windowed ES el Paso 0 en la práctica para Horner" ✓ (Elán confirmó 11:14 que el Paso 0 / §0b se queda para invsqrt).

### §2.1 P1/P2/P3 combinadas, no individuales — CONCURRO (con precisión A-RC-2)

- Tres rebuilds + tres Golds para 0 cambio de score es desperdicio ✓. Las tres tocan archivos distintos (`dqi_kmul42.py`, `dqi_bm_stage_v1.py`, `dqi_decoder_v1.py`), sin solapamiento ✓, y cada una es byte-idéntica a swap42 ✓ (verificado por mí en P1, P2 y P3).
- La combinación **debe** salir byte-idéntica, pero hay que construirla y verificarla (no asumirla) ✓.
- **A-RC-2 (precisión — el "un solo Gold"):** el Gold de la combinación está cubierto por la byte-identidad con el circuito base (el Gold log de la base aplica); un Gold fresco solo haría falta si la combinación NO fuera byte-idéntica — en cuyo caso falla el criterio de aceptación de todos modos. "Un solo Gold" debe leerse como **una sola verificación Gold (por identidad)**, no como una corrida Gold nueva. (En P1/P2/P3 el "Gold" fue exactamente eso: leer el Gold log de swap42 + verificar byte-identidad; no se re-corrió el Gold del DQI.)

### §2.2 Orden vs QF: el QF decide la base — CONCURRO (con correcciones A-RC-3 y A-RC-4 al criterio)

- El QF toca los mismos módulos que P1/P2/P3 (`bm_fused`, `dqi_decoder_v1`, `dqi_kmul42`, torre) ✓. Si el QF se adopta, P1/P2/P3 se RE-BASIFICAN sobre el código QF y se re-verifica byte-identidad contra el `.kmb` QF (sha `38b9cbf0…`), no contra swap42 ✓. Si no se adopta, sobre swap42 ✓.
- No construir la combinación sobre swap42 ahora (trabajo duplicado; el Gold del QF es inminente) ✓ — el build Kali ya es byte-idéntico al control y el Gold control corre desde las 13:19:55.
- **A-RC-3 (corrección — el rango de R como criterio):** el criterio "Gold PASS con `--seed` fijo Y score medido consistente con el factor (1857/1864)²" es correcto. Pero la frase "Si el Gold pasa pero R sale del rango 1.19–1.21 [...] no se adopta" tiene un problema: **el R del Gold de swap42 es 1.2131052140444296 — fuera de [1.19, 1.21]** (verificado por cómputo propio en este turno). El rango [1.19, 1.21] es el ruido de R entre seeds, no un criterio de aceptación: con el mismo seed fijo, R_QF debe ser ≈ R_swap42 (= 1.2131), no estar dentro de [1.19, 1.21]. El criterio correcto es el del score: **QF score / swap42 score ≈ (1857/1864)² = 0.992503 con el mismo seed fijo** (es decir, score ≈ 2,971,470,537,625.300). Propongo corregir la frase a: "Si el Gold pasa pero el score no es consistente con (1857/1864)² con el mismo seed, no se adopta."
- **A-RC-4 (corrección — "errores de valor/fase > 0"):** la frase "o hay errores de valor/fase > 0, no se adopta" leída literal descalificaría al propio swap42 (su Gold tiene **5 errores de valor**, 0 de fase). El criterio correcto (verificado en la prueba del motor swap42): **phase_errors = 0** y **value_errors en el rango de ruido de muestreo del Gold de swap42 (5)** — omega tuvo 2 y swap42 5 con `mean_error_weight` 31.046737331746634 IDÉNTICO. Propongo: "phase_errors = 0 y value_errors en el rango de muestreo (swap42: 5)".
- El build de Programación en la Kali debe salir byte-idéntico al control del Brujo (sha `38b9cbf0…`); si no, DETENERSE antes del Gold (D-QF-1) ✓ — ya verificado: el build Kali ES byte-idéntico al control (13:28).

### §2.3 P5 fuera — CONCURRO

P5 no está en el orden de construcción; se revisita después de la combinación ✓. "La combinación P1+P2+P3+QF no existe como ítem separado: es la combinación (§2.1) sobre la base QF (§2.2)" ✓ — buena clarificación.

### §3 Secuencia — CONCURRO CON UNA CORRECCIÓN DE ORDEN (A-RC-1)

La secuencia de Datos es: 1. Gold QF → Elán decide QF. 2. R1+R5 + Gold. 3. P1+P2+P3 + Gold. 4. Medición TODO-2. 5. TODO-4. 6. dfthcsos sin cambio.

**A-RC-1 (corrección de orden — la medición TODO-2 no debe esperar a P1+P2+P3):** la medición TODO-2 (paso windowed standalone) es independiente del QF y de R1+R5, y es la medición de mayor valor (+4.8–7.1% [ESTIMADO]). En la secuencia de Datos queda en el paso 4, detrás de P1+P2+P3 (paso 3) — que está bloqueada por el Gold del QF + la decisión de Elán. Eso retrasa innecesariamente la medición de mayor valor detrás de un ítem bloqueado. **Propongo: la medición TODO-2 corre en paralelo con R1+R5 (ambas sin dependencia del QF), desde ahora.** El Gold del QF ya corre solo en la Kali (no necesita acción). La construcción completa de TODO-2 sí va después de R1+R5 (porque se construye sobre la base adoptada). Secuencia corregida:
1. **En paralelo, desde ahora:** (a) Gold QF (en curso, Kali); (b) construir R1+R5 + Gold; (c) medir UN paso windowed standalone (TODO-2, criterio §9).
2. Elán decide QF (criterio §2.2 corregido).
3. Construir P1+P2+P3 combinadas sobre la base DQI adoptada (QF si se adopta, swap42 si no) + verificación Gold por identidad.
4. Si el paso aislado TODO-2 pasa el criterio: construir el Horner windowed completo sobre la base invsqrt adoptada (R1+R5).
5. TODO-4 (una variante aislada de lookup) después.
6. dfthcsos sin cambio (lbfgs hasta Gold oficial + score < 3,336,160,975).

### §4 Qué NO se recomienda — CONCURRO (los 5 puntos)

- Adoptar R2c como referencia (dominada por R1) ✓.
- Adoptar P1/P2/P3 individualmente (tres Golds para 0 score) ✓.
- Construir P1+P2+P3 sobre swap42 antes de que se decida el QF (trabajo duplicado) ✓.
- Asumir la combinación R1+R5 o P1+P2+P3 sin construirlas y sin Gold ✓.
- Marcar la selección final (solo Elán; fuera de alcance) ✓.

## Resumen de mis correcciones y precisiones

| # | Tipo | Punto | Contenido |
|---|---|---|---|
| A-RC-1 | Corrección (orden) | §3 | La medición TODO-2 corre en paralelo con R1+R5 (ambas sin dependencia del QF), no después de P1+P2+P3 (bloqueada por el QF). |
| A-RC-2 | Precisión | §2.1 | El "un solo Gold" de la combinación es una verificación Gold por identidad (el Gold log de la base aplica); no una corrida Gold nueva. |
| A-RC-3 | Corrección (criterio QF) | §2.2 | El rango R ∈ [1.19, 1.21] excluye el R del propio Gold de swap42 (1.2131). Criterio correcto: score QF / score swap42 ≈ (1857/1864)² = 0.992503 con el mismo seed fijo. |
| A-RC-4 | Corrección (criterio QF) | §2.2 | "Errores de valor > 0" descalificaría al propio swap42 (5 errores de valor). Criterio correcto: phase_errors = 0, value_errors en el rango de muestreo (swap42: 5). |
| A-RC-5 | Acepto corrección | §1.3 | Acepto la corrección de Datos: R1+R5 es diseño, no merge mecánico (la truncación de R1 vive en CopiaC0 y R5 elimina esa fase). Corrijo mi borrador ("ortogonal" estaba demasiado fuerte). |

**Concurro en lo sustancial con el borrador de Datos.** Con las correcciones A-RC-1, A-RC-3 y A-RC-4 y las precisiones A-RC-2 y A-RC-5, el documento queda listo para finalizarse conjunto y entregarse al Brujo.

## Adenda — revisión de la versión final conjunta (2026-11-19 ~13:40 CST)

**Documento final revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/RECOMENDACION_CONJUNTA_ADOPCION_2026-11-19.md` — versión final de Datos (235 l. / md5 `ec279b7e…` tras mi corrección), que reconcilia ambos borradores y responde mis 5 preguntas en su §3.

**Veredicto sobre la versión final: CONCURRO, con UNA corrección (A-RC-6) aplicada por mí al documento.**

La versión final incorpora correctamente:
- A-RC-1 (TODO-2 en paralelo con R1+R5, §2: 1a/1b en paralelo) ✓ — Datos lo adopta explícitamente en §3.5.
- A-RC-2 (Gold de la combinación por identidad, §1.2.1) ✓.
- A-RC-3 y A-RC-4 (criterio QF corregido, §1.3): las frases problemáticas ("R sale del rango 1.19–1.21", "errores de valor/fase > 0") están fuera; el criterio es phase_errors = 0, value_errors en el rango de swap42 (5), score consistente con (1857/1864)² ✓.
- A-RC-5 (R1+R5 es diseño, no merge mecánico, §1.1.3 con matiz) ✓.
- Respuestas a mis 5 preguntas (§3): concurro con las 5 respuestas de Datos (verificadas: ΔC = −0.1805, techo ~25 puntos, R2c − R1 = 562.72).

**A-RC-6 (corrección del Auditor — error de unidades en el conteo de puntos TODO-2, aplicado al documento en §1.1.2 y §3.1):** el documento decía "TODO-2 son 18,685–27,638 puntos". Ese rango es 4.8%–7.1% × 389,261.01 — el porcentaje de GEOMEAN aplicado al score invsqrt. Verificado por cómputo propio: D-DI-1 da 390,005.06 → 338,436.06 (25%) = **51,569 puntos (13.22%)** y → 317,808.46 (35%) = **72,197 puntos (18.51%)**; sobre la base R1: 51,569–72,196 puntos. El rango correcto es **~51,569–72,197 puntos de score invsqrt** (13.2%–18.5%); el +4.8–7.1% es mejora de geomean. **La conclusión NO cambia:** el techo R1+R2c (~25 puntos) sigue siendo despreciable frente a TODO-2 (ratio 2,063x con el número correcto, 747x con el de Datos). Corregido en el documento en los dos lugares donde aparecía.

**Concurro con la recomendación conjunta final.** Se entrega al Brujo, que se la lleva a Elán.
