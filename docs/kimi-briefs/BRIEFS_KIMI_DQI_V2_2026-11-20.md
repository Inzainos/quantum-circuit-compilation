# Briefs para Kimi (Kiwi) — Optimización del DQI — V2 (CORREGIDA)

**Fecha:** 2026-11-20 ~11:10 CST (v2; v1: 2026-11-20 ~08:10 CST).
**Origen:** v1 (`BRIEFS_KIMI_DQI_2026-11-20.md`, 131 l. / md5 `a0fe453f…`) + anexo de correcciones del Brujo (`ANEXO_CORRECCIONES_BRIEFS_KIMI_2026-11-20.md`, 103 l. / md5 `1cb7d086…`), aplicado por GO de Elán (2026-11-20 ~11:00 CST).
**Cadena de la corrección (COMPLETA):** Brujo (anexo ✓) → Datos supervisa (`SUPERVISION_DATOS_ANEXO_BRIEFS_KIMI_2026-11-20.md`, 123 l. / md5 `2f1285af…`, CONCURRO PASA con 2 precisiones menores D-KB-1/D-KB-2) → Auditor revisa (`REVISION_AUDITOR_ANEXO_BRIEFS_KIMI_2026-11-20.md`, CONCURRO PASA, sin correcciones) → Elán decide (GO 11:00 CST: aplicar las correcciones y hacer el nuevo modelo).
**⚠️ EL PATCH NO ESTÁ EN DISCO:** `p15_main64d4cec.patch` (el plan de 15 AND para GF(64), medido por Elán) NO existe en `~/workspace` ni en `/home/hatch` (verificado por el Brujo, por Datos y por el Auditor). **Elán debe re-enviarlo.** Sin el patch, Kimi no puede partir de la base corregida. Los números de la base nueva (670,307 / 8.7154 / 4.9876 / 248,312 / 57,540 / 364,455 / 66 T) son **medidos por Elán en su build** (Gold PASS, seed fija, 102,400 tiros, 5 errores de valor, 0 de fase, R=1.2131) — no re-medidos por el Brujo, Datos ni el Auditor. La aritmética sobre ellos está verificada por los tres.
**Decisión de Elán (08:07, por widget, vía Coordinador):** DQI con Kimi — tercer nivel de escalamiento (refuerzo externo por encima de Claude). Elán es el puente (le pasa los archivos y las tareas a Kimi); el Brujo prepara los briefs y los archivos; el Coordinador coordina. Las respuestas de Kimi vuelven por Elán y pasan por verificación del Brujo → Datos → Auditor → Elán decide.
**Orden de Elán (07:20):** DQI primero; invsqrt en pausa.
**Nada a Kaggle sin GO nuevo. Nada a main.**

## 0. Estado del DQI (base, no repetir trabajo)

**Adoptado (QF + 15 AND):** Q=1,857, T=670,307, factor DQI 8.7154, geomean local 4.9876, Kaggle v5 4.90803 (ref 58594222, selección final marcada por Elán). Gold PASS (102,400 tiros, 5 errores de valor, 0 de fase, R=1.2131052140444296, mean_error_weight 31.046737331746634, seed fijo `52642227205936912575373656611044064096114070193057152544535209180255000077827`).
**Base anterior (QF sin parche, para comparar):** Q=1,857, T=710,312, factor DQI 8.22455, geomean local 4.89215. El parche de 15 AND baja la inversión por torre de 75 T a **66 T** y el total de 710,312 a 670,307 (−40,005 T). **Kimi parte del patch `p15_main64d4cec.patch`, no de 710,312.** Si no, sus ahorros salen sobreestimados (todo ahorro que proponga se mediría contra una base que ya no existe).

**Score:** DQI cost = R·Q²·T (R depende de los errores del Gold). **Un qubit vale 2·T/Q ≈ 722 Toffoli con la base nueva** (765 con la QF) — NO ~20× como decía la v1. Regla de break-even: T_nuevo/T_viejo < (Q_viejo/Q_nuevo)². Geomean = (invsqrt × DQI × dfthcsos)^(1/3) con ratios 5.33517 (invsqrt R1+R5), 8.7154 (DQI QF+15AND), 2.6684 (dfthcsos seg100@brot13).

**Decodificador QF (3 etapas):** `build_decoder` = BM → omega → scan → omega⁻¹ → BM⁻¹. El scan (Chien) ES el barrido. NO hay etapa "Decoder" separada.

**Mapa de fricción (QF + 15 AND, medido por Elán en su build, suma exacta 670,307 T):**
| Bloque | T | % |
|---|---|---|
| Barrido (scan_pos, 4,095 pos × 89 T) | 364,455 | 54.4% |
| BM fwd+rev | 248,312 | 37.0% |
| Omega fwd+rev | 57,540 | 8.6% |

Desglose del barrido: inversión por torre por posición 66 T × 4,095 = **270,270 T** (74.16% del barrido); cadena f 11 T + ANDs de fase 12 T = 23 T/pos. Desglose BM: bm_update 117,432 + bm_disc 55,818 + bm_swap 33,552 + bm_alpha 22,260 + bm_dclear 13,860 + bm_d 2,100 + bm_x 1,680 + bm_flags 1,610 = 248,312. (bm_alpha y bm_dclear bajan 1,260 T c/u vs la QF: 140 ValueInv c/u × 9 T.) Desglose omega: gf_mul 26,460 + ValueInv 2,310 por dirección (57,540 total). Evaluaciones lineales sigma(r)/omega(r)/sigma'(r): 0 T (solo CX).

**En curso (no tocar, no duplicar):**
- Tests A y C (Programación): Test A — ¿los 5 fallos del Gold son señal (concentrados) o ruido (repartidos)? Hipótesis de Elán: repartidos. Test C — tasa de fallo vs peso del error (pesos 10/20/31/40/50).
- Hoisting de delta en omega (construcción en Programación, Gold decide): delta = sigma_0⁻¹ se calcula 35×/dirección. Con 66 T el ahorro es 34×66×2 = **4,488 T** (no 5,100, que usa 75 T), T → ~665,819 (**PROYECCIÓN, no medición**). La construcción verificada (Q=1,857, T=705,212) usa el ValueInv de 75 T; su Gold sigue pendiente (Kali reinicia).

**CERRADO CON NÚMERO (no proponer de nuevo):**
- Filtro por f=1 (saltar posiciones sin error): **BLOQUEADO por la API de kickmix** (HMR mide en base X y no lee f; `push_condition` y `bit_store` rechazan un qubit; probado en simulador: 130/256 en f=|1⟩ y 130/256 en f=|0⟩, aleatorio). No hay forma de condicionar por f. (Cierre equivalente de Elán por otra ruta: condicionar cada posición por `E[p]` da 670,218 contra 670,307, o sea ruido, porque `mbuc` es aleatorio — medición de Elán.)
- Multiplicador GF(2¹²): **42 ANDs es el piso** (barrido de 435,456 casos, todos exactamente 42; 7 productos GF(8) × 6 ANDs). No existe <42.
- Inversión por torre (TowerInv/ValueInv): **66 T con el parche de 15 AND** (era 75 T; el "75 T es el piso" de la v1 es FALSO). No hay inversión más barata que 66 T.
- Inversión por lotes (Montgomery) para el barrido: **2.45–2.86× PEOR con la base nueva** (12,282 muls + 1 inv = 773,841 T a 63 T/mul, 663,303 T a 54 T/mul, vs 270,270 T actuales; +49,128 qubits persistentes). Razón: 3 muls (189 T) > 1 inv (66 T). (Con la base QF era 2.16–2.52× vs 307,125 T.)
- Barrido por traza, Parte B: **FUNCIONA** (Q=2,285, T=400,037 con la base nueva; barrido 94,185 T = 4,095 × 23; factor 9.6453, geomean 5.159 — recomputado por Datos desde los números verificados) — pero exige un Psi GRATIS que no existe. Ver Tarea 1.
- EEA para Psi (división): **NETO-NEGATIVO** (T_E ≥ 66,063 T + ~1,384 Q; break-even T_E < 42,679 Y ΔQ_E < 119 con la base nueva; el EEA división excede ambos; Stein binario ~3.92–6.04×, tampoco cabe). Q es la restricción vinculante, no T. Ver Tarea 1.
- Walsh-Hadamard: **NO-GO** (69.4× peor que V34). No proponer transformadas tipo WHT/QFT como circuito nuevo (BM ya concentra el síndrome; la QFT es lente de diagnóstico, no diseño).
- Regla de paridad (Elán): invsqrt y dfthcsos IMPARES; DQI PAR (bloques de seis, matrices 6×7).
- kickmix: Z_POW ángulos fijos en compilación; `init_and` sobrescribe (no autoinverso; deshacer = `del_and`, 0 T, MBU); `init_lookup` = 2ⁿ−2 exacto; el simulador da FALSOS POSITIVOS con HMR — siempre verificar con el verificador oficial; la profundidad NO entra en el score.

**Reglas para Kimi:**
- Proponer DISEÑOS con números (Q, T, factor, geomean proyectado), no construir circuitos. La construcción la hace Programación; la verificación es el Gold (102,400 tiros, seed fijo); Datos supervisa; el Auditor revisa; Elán decide.
- Cada propuesta debe decir: qué cambia, cuánto cuesta (Q y T, con el desglose), cuánto ahorra, y qué presupuesto cumple (break-even explícito). Si no cabe en el presupuesto, decirlo con número (no esconderlo).
- No proponer nada ya cerrado arriba. Si una vía cerrada tiene una variante nueva, decir explícitamente qué cambia respecto a lo medido.
- Citar los archivos que leyó y los números que usó. No inventar números: todo número viene de un archivo, un log o un cálculo explícito.
- **Partir del patch `p15_main64d4cec.patch` (base Q=1,857, T=670,307), no de 710,312.** Un qubit vale ~722 Toffoli (base nueva) — usar 722 o la regla de break-even, no el 20× de la v1.

---

## Tarea 1 — Desbloquear el barrido por traza: conseguir Psi dentro del presupuesto (ALTA PRIORIDAD)

**Por qué:** la Parte B del barrido por traza YA está medida y funciona (Q=2,285, T=400,037 con la base nueva; barrido 94,185 T; factor DQI 9.6453, geomean 5.159 — vs base nueva 8.7154 / 4.9876). El único bloqueo es Psi = (sigma')⁻¹ mod sigma: la Parte B lo necesita como registro (420 qubits) y el EEA para calcularlo no cabe. Si Psi se consigue dentro del presupuesto, el DQI salta a ~9.65× (geomean ~5.16×). Es la palanca más grande que queda.

**Presupuesto (break-even, medido desde la Parte B, base nueva 670,307):** T_E < 42,679 T **Y** ΔQ_E < 119 qubits (con T_E=0). A T_E=16,331 → ΔQ máx 71; a 30,000 → 33; a 50,000 → −19 (ya no hay margen de Q); a 42,679 → 0. El EEA de división medido da T_E ≥ 66,063 T (peor caso L=35: 1,026 multiplicaciones + 19 inversiones; promedio 250 muls + 7.5 invs, T_E ≥ 16,331) y ~1,384 qubits nuevos (864 conjunto de trabajo + cociente ~420 + contadores/controles ~100) — excede AMBOS. Q es la restricción vinculante.

**Pregunta:** ¿hay una forma de obtener Psi (o un equivalente que haga funcionar `build_scan` sin la inversión por posición) dentro del presupuesto (T_E < 42,679 Y ΔQ_E < 119)?

**Vías a explorar (en orden de promesa):**
1. **EEA empaquetado/sincronizado estilo v11:** el BM v11 es un motor sincronizado (sin arrays grandes). ¿Se puede empaquetar el EEA igual — reutilizando registros, sincronizando las iteraciones — para bajar los ~1,384 qubits a <119? ¿Cuánto costaría en T?
2. **BM extendido que produzca Psi como subproducto:** el BM ya calcula sigma y sigma'. ¿Se puede extender el BM para que, al mismo tiempo, produzca (sigma')⁻¹ mod sigma (o los coeficientes de Bézout que lo dan) sin una etapa EEA separada? ¿Cuánto Q y T extra costaría?
3. **Otra formulación del barrido por traza que no necesite el Psi completo:** ¿se puede calcular la fase por traza con una cantidad menor (p. ej., Psi parcial, o Psi calculado incrementalmente por posición con costo amortizado)? ¿O una fórmula que use sigma' directamente sin invertir?
4. **Si ninguna vía cabe:** demostrarlo con número (el costo mínimo de cada vía y por qué excede el presupuesto). Un "no cabe" con número también es un resultado.

**Archivos que leer:**
- `~/workspace/qcc-data/test-dev/espiral-prototipo/scan-traza-v1/REPORTE_CONSTRUCCION_BARRIDO_TRAZA_DQI_2026-11-20.md` — Parte B medida, EEA medido, break-even, direcciones futuras.
- `~/workspace/qcc-data/test-dev/espiral-prototipo/scan-traza-v1/eea_psi_referencia.py` — referencia clásica del EEA (48/48 verificada contra pinvmod; peor caso L=35: 18 iter, 72 coefs vivos, 1,026 muls + 19 invs).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/DISENO_REDISENO_BARRIDO_TRAZA_DQI_2026-11-20.md` — diseño original (Parte A: EEA; Parte B: build_scan).
- `~/workspace/qcc-dqi/src/dqi_bma_v11.py` — el motor sincronizado v11 (modelo de empaquetado); `_synchronized_eea` es el punto de partida (motor sincronizado SIN coeficientes de Bézout — adaptarlo exige +1–2 arrays).
- `~/workspace/qcc-dqi/src/dqi_decoder_v1.py` — `build_decoder`, `build_scan_inv` (actual), `build_omega_tmp`.
- `~/workspace/qcc-dqi/src/dqi_scan_stage.py` — `build_scan` (23 T/pos; fase (-1)^{Σ_r Tr(μ(M_p)·ω(r)·ψ(r))} verificada en `tools/dqi_phase_model.py`).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/scan-traza-v1/test_psi_tau.py` — hipótesis τ∝Psi FALSA (8/56 casos; tau NO se puede reusar para Psi).

**Entregable:** diseño concreto de la vía propuesta (o demostración de que ninguna cabe), con Q y T desglosados, comparación contra el presupuesto (T_E < 42,679 Y ΔQ_E < 119), y factor/geomean proyectado. Si propone construir algo, decir exactamente qué archivos cambian y qué mide el Gold.

---

## Tarea 2 — Bajar el costo del BM (248,312 T, 37.0% del T)

**Por qué:** el BM es el segundo bloque más grande (248,312 T, 37.0% del T total), después del barrido. El multiplicador ya está en su piso (42 ANDs), así que la palanca NO es el multiplicador — es el NÚMERO y la ESTRUCTURA de las multiplicaciones y conversiones del BM.

**Desglose (QF + 15 AND, medido por Elán en su build):** bm_update 117,432 + bm_disc 55,818 + bm_swap 33,552 + bm_alpha 22,260 + bm_dclear 13,860 + bm_d 2,100 + bm_x 1,680 + bm_flags 1,610 = 248,312 T. El bm_update solo es 117,432 T (47.3% del BM, 17.5% del T total).

**Pregunta:** ¿se puede reestructurar el BM para usar menos multiplicaciones de campo (o conversiones) sin cambiar el resultado? ¿O hay una variante del BM más eficiente para este caso (síndrome de 70 elementos, grado ≤35)?

**Vías a explorar:**
1. **bm_update (117,432 T):** ¿qué hace exactamente y por qué cuesta tanto? ¿Se puede fusionar con bm_disc/bm_swap, o evitar multiplicaciones redundantes (p. ej., multiplicar por 0 o por 1, o por el mismo valor varias veces)?
2. **Variante del BM:** ¿un BM linealizado, un BM que trabaje directamente sobre el síndrome sin conversiones intermedias, o un BM que aproveche la estructura del síndrome (70 elementos, grado ≤35, L≤35)? ¿Cuántas multiplicaciones necesitaría cada variante?
3. **¿Se puede reducir el número de rondas del BM?** (L ≤ 35; ¿el BM siempre necesita las 35 rondas, o se puede terminar antes cuando el síndrome ya está resuelto?)
4. **Trade-off T vs Q:** ¿una variante que use más Q pero menos T (o viceversa) mejora el score R·Q²·T? (Q está al cuadrado — un aumento de Q tiene que compensarse con una bajada grande de T. Un qubit vale ~722 Toffoli.)

**Preguntas nuevas (agregadas por la corrección):**
- **A. Ventana de coeficientes no nulos de σ y tau por ronda.** `bm_update` son 117,432 T = 2,796 multiplicaciones de 42 T (1,398 por dirección). La cota `bu(r)` es de peor caso (bu(r) = min(35, r//2+2) — crece con r hasta 35). **¿Cuál es la ventana de coeficientes no nulos de σ y tau por ronda?** Si en la práctica solo una ventana angosta de σ y tau es no nula por ronda, las multiplicaciones reales son menos que 2,796 y hay un ahorro medible. Medir la ventana por ronda (no asumirla).
- **B. Cuánto error de decodificación tolera el score.** Pasar de 5 errores a 0 solo mueve R de 1.2131 a ≈1.191, o sea **~1.8% del DQI**. Eso acota lo que vale recortar casos raros: **ninguna optimización que solo reduzca los errores de decodificación puede ganar más de ~1.8% del DQI.** Si se propone recortar casos raros (p. ej. pesos altos), demostrar que el ahorro en T o Q supera ese techo — si no, no vale la pena.

**Archivos que leer:**
- `~/workspace/qcc-dqi/src/dqi_bm_stage_v1.py` — la etapa BM (P2 vive aquí, no en dqi_decoder_v1.py).
- `~/workspace/qcc-dqi/src/dqi_decoder_v1.py` — `build_decoder`, cómo se llama al BM.
- `~/workspace/qcc-data/dqi-perfil/REPORTE_PERFIL_DQI.md` — perfil del 1949 (BM 185,034 + 113,198 = 298,232 T en el 1949; el QF es 250,832 T por el swap 63→42 ANDs; el QF+15AND es 248,312 T).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/p1p2p3-qf/verify_p1p2p3_qf_gold.log` — Gold del QF (Q, T, R, k).
- El multiplicador GF(2¹²) en `~/workspace/qcc-dqi/src/` (42 ANDs, piso medido — no proponer cambiarlo).

**Entregable:** diseño concreto de la reestructuración propuesta, con el número de multiplicaciones antes/después, Q y T desglosados, y factor/geomean proyectado. Si la respuesta es "el BM ya está en su piso para esta arquitectura", demostrarlo con número (contar las multiplicaciones mínimas que el algoritmo exige).

---

## Tarea 3 — ¿Existe un BM sin tau? (NO asumir 1.698×)

**Por qué (CORREGIDO):** Q está al cuadrado en el score (R·Q²·T) — bajar Q es la palanca más amplificada. El registro tau (~432 qubits, ~23% de Q) **NO es "frío" durante el barrido**: tau es estado del propio BM, porque `σ ← σ + α·x·τ` lo usa en las 70 rondas (`bm_update` lo lee en cada ronda, `bm_swap` también). El pico global de 1,857 ocurre dentro del BM, con tau vivo (el pico del barrido es 1,837 en medición de Elán). Soltar tau solo durante el barrido no baja el máximo. **Qué haría falta: un BM sin tau.** Recomputarlo después tampoco cabe, porque ya probaron que τ∝Psi es falso y tau no sale de σ y S.

**El 1.698× de la v1 es aritmética correcta con premisa falsa:** (1,857/1,425)² = 1.698 (1,857−432 = 1,425), pero el 1,425 no es alcanzable soltando tau solo durante el barrido — presupone que tau se puede soltar sin costo y que el pico bajaría; ambas premisas son falsas.

**Pregunta (REFORMULADA):** ¿existe un BM sin tau (que no guarde el registro tau), y cuánto costaría en T y Q? ¿O se puede achicar tau (p. ej., guardar solo parte, o comprimirlo)?

**Vías a explorar:**
1. **BM sin tau:** ¿se puede rediseñar el BM para no necesitar el registro tau (p. ej., recomputando lo necesario en el reverso, o con una formulación que no guarde el historial)? ¿Cuánto T extra costaría y cuál es el neto en R·Q²·T?
2. **Achicar tau:** ¿tau necesita los 432 qubits (36 coefs × 12 bits), o se puede guardar solo los coeficientes no nulos / solo hasta el grado actual? ¿Cuánto Q se ahorraría y cuánto T costaría?
3. **¿Tau se puede reusar para otra cosa?** (Ya medido: NO se puede reusar para Psi — la hipótesis τ∝Psi es FALSA, 8/56 casos. No proponerlo de nuevo. ¿Se puede reusar para otra cosa, p. ej., como scratch del barrido o de omega?)
4. **Trade-off general:** dado que Q está al cuadrado, ¿cuánto T extra vale la pena pagar por cada qubit ahorrado? (El break-even: ahorrar ΔQ qubits vale la pena si T_nuevo/T_viejo < (Q_viejo/Q_nuevo)². Un qubit vale ~722 Toffoli con la base nueva.)

**Archivos que leer:**
- `~/workspace/qcc-dqi/src/dqi_bm_stage_v1.py` — cómo se usa tau en el BM (forward y reverse). `bm_update` lee tau en las 70 rondas (`forward_round` l.248, `bm_update` l.263–265 en la copia QF).
- `~/workspace/qcc-dqi/src/dqi_decoder_v1.py` — `build_decoder`, `bm.reverse()`, tamaños de registros.
- `~/workspace/qcc-data/test-dev/espiral-prototipo/p1p2p3-qf/build_p1p2p3_qf.log` — live_frontera por etapa (bm_forward 1,794; omega_fwd 1,794; scan 1,794; omega_rev 1,794; bm_reverse 1,724; pico global 1,857 intra-etapa).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/scan-traza-v1/test_psi_tau.py` — τ∝Psi FALSA (no proponer reusar tau para Psi).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/scan-traza-v1/REPORTE_CONSTRUCCION_BARRIDO_TRAZA_DQI_2026-11-20.md` — Q por etapa (bm_forward 1,794 → omega_fwd 1,794 → psi_alloc 2,214 → scan 2,214 → omega_rev 1,794 → bm_reverse 1,724).

**Entregable:** diseño concreto (BM sin tau / achicar / reusar tau), con Q y T antes/después, el trade-off en R·Q²·T (factor y geomean proyectado), y el break-even (cuánto T extra se puede pagar por cada qubit ahorrado). Si no vale la pena, demostrarlo con número.

---

## Resumen de entregables (para Elán)

| Tarea | Palanca | Techo (si funciona) |
|---|---|---|
| 1. Psi (barrido por traza) | Desbloquea 9.65× DQI | DQI 8.72× → ~9.65×; geomean 4.99× → ~5.16× |
| 2. BM más barato | 37.0% del T | Depende del diseño (bm_update 117,432 T es el blanco; ventana de no nulos y techo de errores ~1.8% son las preguntas nuevas) |
| 3. BM sin tau | Q² (432 Q, ~23%) | Solo si existe un BM sin tau; el 1.698× de la v1 NO es alcanzable soltando tau solo durante el barrido |

**Orden sugerido:** Tarea 1 primero (techo más alto), luego Tarea 3 (palanca Q²), luego Tarea 2 (optimización incremental). Las tres son independientes — se pueden hacer en paralelo.

---

## Cambios de la v1 a la v2 (para el registro)

| # | Corrección | v1 (erróneo) | v2 (correcto) |
|---|---|---|---|
| 1 | Base | Q=1,857, T=710,312; factor 8.22455; geomean 4.89215; inversión por torre 75 T ("piso") | Q=1,857, T=670,307; factor 8.7154; geomean 4.9876; inversión por torre **66 T** (parche 15 AND) |
| 2 | Tarea 3 | Tau "frío" durante el barrido; Q→1,425; ×1.698 | Tau vivo en las 70 rondas del BM; la tarea pide "demuestra si existe un BM sin tau"; el 1.698× es aritmética correcta con premisa falsa |
| 3 | Presupuesto Tarea 1 | T_E < 66,063; ΔQ máx 180/131/93/40 | T_E < 42,679; ΔQ máx **119/71/33/−19** (base 670,307; Parte B T=400,037) |
| 4 | Valor de un qubit | ~20× un Toffoli | **~722 Toffoli** (2·T/Q, base nueva; 765 con la QF) |
| A | Tarea 2 (agregado) | — | Preguntar por la ventana de coeficientes no nulos de σ y tau por ronda (bm_update = 2,796 muls × 42 T) |
| B | Tarea 2 (agregado) | — | Techo por recortar errores ~1.8% del DQI (R 1.2131 → 1.191) |

**Números recomputados por Datos para la v2 (desde los números verificados del anexo):** desglose BM (bm_alpha 22,260; bm_dclear 13,860; total 248,312); desglose omega (ValueInv 2,310/dirección; total 57,540); barrido (270,270 + 94,185 = 364,455); Montgomery 2.45–2.86× vs la base nueva; Parte B factor 9.6453 / geomean 5.159. **Números medidos por Elán (no re-medidos):** 670,307, 8.7154, 4.9876, 248,312, 57,540, 364,455, 66 T, 1,837 (pico del barrido), 670,218 (condicionar por E[p]). **El patch `p15_main64d4cec.patch` NO está en disco — Elán debe re-enviarlo.**
