# RECOMENDACIÓN CONJUNTA — MEJOR CAMINO DE ADOPCIÓN
## Datos + Auditor · Prototipo espiral + QF: qué adoptar, en qué orden, qué construir

**Fecha:** 2026-11-19 ~13:29 CST
**Pedido:** Elán (vía Brujo, vía Coordinador, ~13:26): "lo de los datos hay
que verlo con el analista de datos y la auditoría para elegir el mejor
camino."
**Autores:** Datos (Analista de datos) + Auditor Interno — recomendación
conjunta. Borradores reconciliados: Datos
(`RECOMENDACION_CONJUNTA_ADOPCION_BORRADOR_2026-11-19.md`, 147 l. / md5
`032289cd…`) y Auditor
(`~/workspace/auditoria/BORRADOR_RECOMENDACION_ADOPCION_AUDITOR_2026-11-19.md`,
95 l. / md5 `7f504602…`). Ambos borradores coinciden en todos los puntos
sustanciales; las diferencias eran de orden y de análisis (el techo
R1+R2c del Auditor, el criterio §9 de Datos) y quedan incorporadas aquí.
**Destino:** se entrega al Brujo, que se la lleva a Elán.
**Fuera de alcance:** la selección final ref 58570485 (3.53019) — solo
Elán la marca. El dfthcsos no cambia: el lbfgs sigue hasta que un
entrenamiento pase el Gold oficial Y score < 3,336,160,975.
**Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.**

## 0. Base de hechos (todo medido, cadenas completas)

### invsqrt (referencia adoptada: R1, score 389,261.01)

| Variante | Score | T | Q | n_rot | Peor error | Margen | Estado |
|---|---|---|---|---|---|---|---|
| Baseline logshift2 | 390,005.06 | 2,561 | 139 | 35 | 0.792 | 20.80% | Referencia original |
| B (skip_low) | 389,261.01 | 2,561 | 139 | 34 | 0.8375 | 16.25% | Medido |
| C (filtro dead) | 389,848.82 | 2,557 | 139 | 35 | 0.8823 | 11.77% | Medido |
| B+C | 390,098.06 | — | 139 | — | 0.9624 | — | PEOR (+93.00), NO adoptado |
| **R1 (= B)** | **389,261.01** | **2,561** | **139** | **34** | **0.8375** | **16.25%** | **ADOPTADO por Elán (12:01, "Deja R1" 12:16:35)** |
| R2c | 389,823.73 | 2,557 | 139 | 35 | 0.8551 | — | Cadena completa; NO supera a R1 ni a B |
| R5 (= baseline) | 390,005.06 | 2,561 | 139 | 35 | 0.792 | 20.80% | Cadena completa; limpieza, 0 T/Q |
| R1+R5 | — | — | — | — | — | — | SIN CONSTRUIR |
| R1+R2c | — | — | — | — | — | — | SIN CONSTRUIR, SIN MEDIR |

- R1 y B empatan EXACTO en todo lo que el score mide (Δscore = 0.0);
  únicas diferencias: num_ops −2 y tamaño −18 B (R1).
- R2c vs C: ΔC = −0.1805 exacto (C_R2c = 2,804.4872484048065 vs
  C_C = 2,804.667769784173), todo por r (ΔT = 0) → mejora de score
  **25.09 puntos** (139 × 0.1805 = 25.0895; verificado por Datos en su
  supervisión R2: "R2c vs C: 25.0918 → −25.09 ✓"). R2c NO supera a R1
  (Δ = +562.72) ni a B. (Precisión de lectura: son 25.09 puntos de
  SCORE vía ΔC = −0.1805, no ΔC = 25.09.)
- R5 es byte-idéntico al baseline (limpieza: la fase `copy_c0` sale de
  la lista y su copia CX se pliega en `DesnormLog`; geomean 0% exacto).
- Diseño invsqrt (cadena completa): TODO-2 (Horner con ventanas de 4
  bits) **+4.8–7.1% [ESTIMADO]** (D-DI-1, break-even Q ≈ 160–171);
  TODO-4 (rediseño del lookup) **+2.0–3.5% [ESTIMADO]** (techo +7.6%).
  Medición especificada por Datos (§9): medir UN paso windowed aislado
  primero; criterio: el ventaneado es el núcleo SI el (Q,T) proyectado
  cae bajo la curva Q_break(T) = 390,005.06 / C(T); si T_paso ≥ 4×T_bit
  o Q_paso empuja el Q total sobre el break-even, se DESCARTA con número.

### DQI Fase 2 (referencia: swap42, Q=1,864, T=710,312, Gold PASS, Kaggle 3.53019)

| Variante | Q | T | sha256 | Score | Estado |
|---|---|---|---|---|---|
| swap42 (referencia) | 1,864 | 710,312 | 746271d9… | 2,993,914,799,696.024 | Adoptado; Kaggle 3.53019 |
| P1 (matriz 6×7) | 1,864 | 710,312 | 746271d9… | = swap42 | PASA, byte-idéntico |
| P2 (bloque 6×1) | 1,864 | 710,312 | 746271d9… | = swap42 | PASA, byte-idéntico |
| P3 (90 bloques de 7) | 1,864 | 710,312 | 746271d9… | = swap42 | PASA, byte-idéntico |
| P1+P2+P3 | — | — | — | — | SIN CONSTRUIR |
| P4 | — | — | — | — | INVALIDADO (A-F2-1) |

- Las tres son organizacionales (0 T, 0 Q, impacto en score 0). Su valor
  es la estructura explícita para el trabajo futuro, no el score.
- P5 (interfaz de paridad) sin construir.

### QF (parche de Claude, −7 qubits)

- Revisión del Brujo: CONCURRO (estática + Q/T). Build independiente en
  scratch (main 64d4cec): **Q=1,857, T=710,312** (Delta Q=−7, T=0).
  Circuito `dqi_qf.kmb` sha256 `38b9cbf0…` (628,685,675 B).
- **Build de la Kali BYTE-IDÉNTICO al control del Brujo** (13:28):
  `dqi_qf.kmb` (628,685,675 B, 12:55) sha256 `38b9cbf0…`, todos los
  módulos desde `/home/deamon/quantum-circuit-compilation-qf/src/`
  (copia parcheada), **sin mezcla** (el aviso D-QF-1 sirvió). TOTAL QF
  Q=1857 T=710312 en 136 s; Delta Q=−7, T=0.
- **Gold control CORRIENDO** (PID 1275, desde 13:19:55, swap42 con
  `--seed` explícito
  `52642227205936912575373656611044064096114070193057152544535209180255000077827`)
  — debe reproducir exacto el Gold publicado (R=1.2131, score
  2,993,914,799,696.024, 5 valor / 0 fase) para validar el seed.
  **Gold QF pendiente** (corre después del control, ~7 min cada uno).
- Números esperados, misma R [ESTIMADO]: score 2,971,470,537,625.300,
  ratio 8.22455 (vs 8.16289), geomean 3.53171 (Kaggle-escala 3.53906).
  Ganancia DQI +0.75%, geomean +0.25%. El ruido de R entre seeds
  (1.19–1.21, ~1.68%) es MAYOR que la ganancia real (0.75%) — sin seed
  fijo la comparación no vale.
- El QF toca los mismos módulos que P1/P2/P3: `bm_fused`,
  `dqi_decoder_v1`, `dqi_kmul42`, torre.

## 1. Recomendación conjunta

### 1.1 invsqrt — R1 se queda; R2c fuera del set; R5 solo vía R1+R5; TODO-2 primero

1. **R1 se queda adoptado.** Elán ya decidió ("Deja R1", 12:16:35). No
   se revisita.
2. **R2c NO entra al set de adopción.** R2c (389,823.73) es peor que R1
   (389,261.01) por 562.72 puntos. Su mecanismo (truncar solo c[2] +
   conservar el filtro dead para c[2]) mejora a C en 25.09 puntos de
   score, pero eso es vs C, no vs R1. La composición R1+R2c está sin
   medir; el techo plausible si el ΔC se transfiriera exacto sería
   ~139 × 0.1805 ≈ 25 puntos de score (~0.006% en el factor invsqrt) —
   **dos órdenes de magnitud por debajo de TODO-2 (+4.8–7.1%)**. No vale
   un build + Gold + cadena por eso. R2c queda documentada como variante
   medida (cadena completa), por si la base de R1 cambia algún día.
   (Matiz de Datos, verificado: el techo asume transferencia exacta del
   ΔC, que no está probada — y aun el techo generoso es despreciable:
   TODO-2 son ~51,569–72,197 puntos de score invsqrt (13.2%–18.5%; el
   +4.8–7.1% es mejora de geomean); el techo R1+R2c son ~25.)
   [Corrección del Auditor, A-RC-6: el rango 18,685–27,638 aplicaba el %
   de geomean al score invsqrt. Verificado por cómputo propio: D-DI-1,
   390,005.06 → 338,436.06 (25%) = 51,569 puntos y → 317,808.46 (35%) =
   72,197 puntos.]
3. **R5 se adopta SOLO vía la combinación R1+R5.** R5 sola = baseline
   (390,005.06), peor que R1 — adoptarla sola sería una regresión de
   score. Su valor es arquitectónico (menos fases, `fold_copy`, mínima
   fricción — el principio de Elán). **Construir R1+R5, verificar con
   Gold, y si el score es = R1 (389,261.01) con la estructura R5,
   adoptar la combinación como la nueva referencia invsqrt.** Esperado:
   exactamente el score de R1 (R5 no cambia la secuencia de puertas;
   los mecanismos tocan partes distintas — R1 el camino skip_low/copia,
   R5 el plegado de `copy_c0` en `DesnormLog`). **Pero la composición NO
   está probada hasta medirla: el build + Gold es obligatorio.** (Matiz
   de Datos: no es un merge mecánico — la truncación de R1 vive en
   `CopiaC0` y R5 elimina esa fase del orquestador; el constructor debe
   colocar la truncación correctamente en la copia plegada. El Gold lo
   verifica.)
4. **TODO-2 es la siguiente prioridad de construcción (antes que
   TODO-4).** TODO-2 ofrece +4.8–7.1% [ESTIMADO]; TODO-4 +2.0–3.5%
   [ESTIMADO] (techo +7.6%). Ambas son estimadas; TODO-2 tiene el rango
   mayor y el techo mayor. **Primer paso: medir UN paso windowed
   aislado** (criterio de Datos §9: bajo la curva Q_break(T) =
   390,005.06 / C(T) o se descarta con número). Si el paso aislado pasa
   el criterio, construir el Horner windowed completo sobre la base
   adoptada (R1+R5 si se adoptó). TODO-4 después de TODO-2.

### 1.2 DQI Fase 2 — adoptar P1+P2+P3 COMBINADAS, en UNA sola construcción, sobre la base que quede tras el QF

1. **Adoptar las tres juntas, no por separado.** P1, P2 y P3 son
   organizacionales (impacto 0). Adoptarlas por separado son tres
   cambios de código, tres cadenas y tres chances de deriva. **Una sola
   construcción combinada (P1+P2+P3), verificada byte-idéntica al
   circuito base, es la única adopción que tiene sentido:** da la
   estructura explícita completa en un solo paso, con un solo criterio
   de aceptación (byte-identidad → score sin cambio por construcción).
2. **NO construir P1+P2+P3 todavía — esperar el Gold del QF.** El QF
   toca los mismos módulos (bm_fused, dqi_decoder_v1, dqi_kmul42,
   torre). Si el QF pasa y Elán lo adopta, la base cambia a Q=1,857 y
   P1/P2/P3 habría que re-basificarlas sobre el código QF — el trabajo
   sobre swap42 se tiraría. El costo real no es el build (~2–3 min por
   variante) sino la cadena (Brujo → Datos → Auditor); construir dos
   veces (swap42 y luego QF) duplica la cadena. El Gold del QF es el
   ítem que bloquea: el build de la Kali ya es byte-idéntico al control
   del Brujo (13:28) y el Gold control corre ahora mismo (PID 1275,
   desde 13:19:55), con el Gold QF después (~7 min cada uno).
   **Esperar cuesta menos de una hora; construir dos veces cuesta una
   cadena entera.**
3. **Escenario QF adoptado:** construir P1+P2+P3 sobre el código QF.
   Criterio de aceptación: el circuito combinado byte-idéntico al
   circuito QF (sha `38b9cbf0…`). Los mecanismos son plausiblemente
   ortogonales (el QF quita ancillas, mueve el update de `d` y reordena
   el andamio de la torre; P1 expone la matriz Toom-4, P2 la escalera,
   P3 los bloques de Omega) — pero la ortogonalidad se verifica
   construyendo, no se asume.
4. **Escenario QF no adoptado** (Gold falla o Elán decide no adoptarlo):
   construir P1+P2+P3 sobre swap42. Criterio de aceptación:
   byte-idéntico a swap42 (sha `746271d9…`).

### 1.3 QF — adoptar si el Gold pasa con seed fijo y el score casa con lo esperado

- **Criterio de aceptación del Gold:** mismo `--seed` fijo que el Gold
  de swap42; `phase_errors = 0`; `value_errors` en el rango de swap42
  (5, ruido de muestreo); score dentro del ruido de R del valor
  esperado [ESTIMADO] 2,971,470,537,625.300. (Matiz de Datos: el PASS
  del verificador es el criterio duro; los conteos de errores son el
  rango de ruido alrededor de lo medido en swap42.)
- **Si pasa:** se recomienda adoptarlo. Es una reducción real de Q (−7
  qubits, T sin cambio) — exactamente la palanca que Elán priorizó ("Q
  primero, después T, después R"). Ganancia DQI +0.75%, geomean +0.25%
  [ESTIMADO]. La base DQI cambia a Q=1,857 y P1/P2/P3 se re-basifican
  sobre el código QF (§1.2.3). Además: el build de Programación debe
  salir byte-idéntico al control del Brujo (sha `38b9cbf0…`); si no,
  DETENERSE antes del Gold (D-QF-1, bug de mezcla).
- **Si no pasa:** la base DQI se queda en swap42 y P1+P2+P3 se
  construye sobre swap42 (§1.2.4).

## 2. Orden de trabajo recomendado

| # | Trabajo | Dependencia | Quién |
|---|---|---|---|
| 1a | Construir R1+R5 + Gold | Ninguna | Programación → Brujo → Datos → Auditor |
| 1b | Medir UN paso windowed aislado (TODO-2, criterio §9 de Datos) | Ninguna (en paralelo con 1a) | Brujo / Datos |
| 2 | Gold del QF (en curso) | — | Programación (Kali, seed fijo) |
| 3 | Decisión de Elán sobre el QF (si el Gold pasa) | 2 | Elán |
| 4 | Construir P1+P2+P3 sobre la base que quede (QF si se adopta, swap42 si no) + cadena | 3 | Programación → Brujo → Datos → Auditor |
| 5 | Si el paso aislado TODO-2 pasa el criterio: construir el Horner windowed completo sobre la base adoptada (R1+R5) | 1a, 1b | Programación → Brujo → Datos → Auditor |
| 6 | TODO-4 (rediseño del lookup) | Después de 5 | Programación → Brujo → Datos → Auditor |
| — | R2c: NO se adopta, NO se construye R1+R2c | — | Queda documentada |

**Lo que NO se hace:** adoptar R5 sola (regresión de score); adoptar
R2c como reemplazo de R1 (peor score); construir P1+P2+P3 sobre swap42
antes del Gold del QF (trabajo que se tiraría si el QF se adopta);
construir R1+R2c (techo ~25 puntos, dos órdenes por debajo de TODO-2).

## 3. Respuestas de Datos a las 5 preguntas del Auditor (reconciliación)

1. **R2c fuera del set; no construir R1+R2c — SÍ, concurro.** Verifiqué
   tu techo por cómputo propio: ΔC = −0.1805 exacto (R2c vs C) →
   139 × 0.1805 = 25.0895 ≈ 25.09 puntos; R2c − R1 = 562.72. Aun con
   transferencia exacta (no probada), ~0.006% frente a TODO-2
   (~51,569–72,197 puntos de score invsqrt; ver corrección A-RC-6 en
   §1.1.2). No vale build + Gold + cadena.
2. **R1+R5 como único camino de R5; criterio score = R1 (389,261.01)
   — SÍ, concurro,** con el matiz de §1.1.3: el constructor debe
   colocar la truncación de R1 correctamente en la copia plegada; el
   Gold lo verifica.
3. **Esperar el Gold del QF antes de P1+P2+P3; re-basificar sobre el
   código QF si se adopta — SÍ, concurro.** Criterio byte-idéntico al
   circuito QF (sha `38b9cbf0…`); si no, swap42 (sha `746271d9…`).
4. **TODO-2 antes que TODO-4, paso aislado primero (criterio §9) — SÍ,
   concurro.**
5. **Correcciones a tus números — ninguna de sustancia.** Verifiqué
   ΔC, el techo, R2c − R1, y los rangos TODO-2/TODO-4. Dos precisiones
   menores: (a) "mejora a C en 25.09" se lee como 25.09 puntos de SCORE
   vía ΔC = −0.1805 (aclarado en §0); (b) tu orden de trabajo (1a/1b en
   paralelo con el Gold QF) es mejor que mi borrador serializado — lo
   adopto (§2). Tu criterio QF (phase_errors = 0, value_errors en
   rango) — concurro, con el matiz del PASS como criterio duro (§1.3).

**Datos — concurro con esta recomendación conjunta. Auditor — concurrencia
pendiente en esta versión; al concurrir, se entrega al Brujo.**
