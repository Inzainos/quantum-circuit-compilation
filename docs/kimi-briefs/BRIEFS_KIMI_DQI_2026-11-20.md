# Briefs para Kimi (Kiwi) — Optimización del DQI

**Fecha:** 2026-11-20 ~08:10 CST
**Decisión de Elán (08:07, por widget, vía Coordinador):** DQI con Kimi — tercer nivel de escalamiento (refuerzo externo por encima de Claude). Elán es el puente (le pasa los archivos y las tareas a Kimi); el Brujo prepara los briefs y los archivos; el Coordinador coordina. Las respuestas de Kimi vuelven por Elán y pasan por verificación del Brujo → Datos → Auditor → Elán decide.
**Orden de Elán (07:20):** DQI primero; invsqrt en pausa.
**Nada a Kaggle sin GO nuevo. Nada a main.**

## 0. Estado del DQI (base, no repetir trabajo)

**Adoptado (QF):** Q=1,857, T=710,312, factor DQI 8.22455, geomean local 4.89215, Kaggle v5 4.90803 (ref 58594222, selección final marcada por Elán). Gold PASS (102,400 tiros, 5 errores de valor, 0 de fase, R=1.2131052140444296, mean_error_weight 31.046737331746634, seed fijo `52642227205936912575373656611044064096114070193057152544535209180255000077827`).

**Score:** DQI cost = R·Q²·T (R depende de los errores del Gold; Q está al cuadrado — un qubit vale ~20× un Toffoli). Geomean = (invsqrt × DQI × dfthcsos)^(1/3) con ratios 5.33517 (invsqrt R1+R5), 8.22455 (DQI QF), 2.6684 (dfthcsos seg100@brot13).

**Decodificador QF (3 etapas):** `build_decoder` = BM → omega → scan → omega⁻¹ → BM⁻¹. El scan (Chien) ES el barrido. NO hay etapa "Decoder" separada.

**Mapa de fricción (QF, medido por perfilador, suma exacta 710,312 T):**
| Bloque | T | % |
|---|---|---|
| Barrido (scan_pos, 4,095 pos × 98 T) | 401,310 | 56.5% |
| BM fwd+rev | 250,832 | 35.31% |
| Omega fwd+rev | 58,170 | 8.19% |

Desglose del barrido: inversión por torre por posición 75 T × 4,095 = **307,125 T** (76.53% del barrido); cadena f 11 T + ANDs de fase 12 T = 23 T/pos. Desglose BM: bm_update 117,432 + bm_disc 55,818 + bm_swap 33,552 + bm_alpha 23,520 + bm_dclear 15,120 + bm_d 2,100 + bm_x 1,680 + bm_flags 1,610 = 250,832. Desglose omega: gf_mul 26,460 + ValueInv 2,625 por dirección (58,170 total). Evaluaciones lineales sigma(r)/omega(r)/sigma'(r): 0 T (solo CX).

**En curso (no tocar, no duplicar):**
- Tests A y C (Programación): Test A — ¿los 5 fallos del Gold son señal (concentrados) o ruido (repartidos)? Hipótesis de Elán: repartidos. Test C — tasa de fallo vs peso del error (pesos 10/20/31/40/50).
- Hoisting de delta en omega (construcción en Programación, Gold decide): delta = sigma_0⁻¹ se calcula 35×/dirección (5,250 T); calcularlo 1× y reusarlo ahorra 5,100 T (T → 705,212; factor DQI → 8.2840; geomean → 4.90392). PROYECCIÓN — el Gold decide.

**CERRADO CON NÚMERO (no proponer de nuevo):**
- Filtro por f=1 (saltar posiciones sin error): **BLOQUEADO por la API de kickmix** (HMR mide en base X y no lee f; `push_condition` y `bit_store` rechazan un qubit; probado en simulador: 130/256 en f=|1⟩ y 130/256 en f=|0⟩, aleatorio). No hay forma de condicionar por f.
- Multiplicador GF(2¹²): **42 ANDs es el piso** (barrido de 435,456 casos, todos exactamente 42; 7 productos GF(8) × 6 ANDs). No existe <42.
- Inversión por torre (TowerInv/ValueInv): **75 T es el piso** (scaffold 315 T). No hay inversión más barata.
- Inversión por lotes (Montgomery) para el barrido: **2.16–2.52× PEOR** (12,282 muls + 1 inv = 773,841 T a 63 T/mul, 663,303 T a 54 T/mul, vs 307,125 T actuales; +49,128 qubits persistentes). Razón: 3 muls (189 T) > 1 inv (75 T).
- Barrido por traza, Parte B: **FUNCIONA** (Q=2,285, T=403,187; barrido 94,185 T = 4,095 × 23; factor 9.5699, geomean 5.1456) — pero exige un Psi GRATIS que no existe. Ver Tarea 1.
- EEA para Psi (división): **NETO-NEGATIVO** (T_E ≥ 66,063 T + ~1,384 Q; break-even T_E < 66,063 Y ΔQ_E < 180; el EEA división excede ambos; Stein binario ~3.92–6.04×, tampoco cabe). Q es la restricción vinculante, no T. Ver Tarea 1.
- Walsh-Hadamard: **NO-GO** (69.4× peor que V34). No proponer transformadas tipo WHT/QFT como circuito nuevo (BM ya concentra el síndrome; la QFT es lente de diagnóstico, no diseño).
- Regla de paridad (Elán): invsqrt y dfthcsos IMPARES; DQI PAR (bloques de seis, matrices 6×7).
- kickmix: Z_POW ángulos fijos en compilación; `init_and` sobrescribe (no autoinverso; deshacer = `del_and`, 0 T, MBU); `init_lookup` = 2ⁿ−2 exacto; el simulador da FALSOS POSITIVOS con HMR — siempre verificar con el verificador oficial; la profundidad NO entra en el score.

**Reglas para Kimi:**
- Proponer DISEÑOS con números (Q, T, factor, geomean proyectado), no construir circuitos. La construcción la hace Programación; la verificación es el Gold (102,400 tiros, seed fijo); Datos supervisa; el Auditor revisa; Elán decide.
- Cada propuesta debe decir: qué cambia, cuánto cuesta (Q y T, con el desglose), cuánto ahorra, y qué presupuesto cumple (break-even explícito). Si no cabe en el presupuesto, decirlo con número (no esconderlo).
- No proponer nada ya cerrado arriba. Si una vía cerrada tiene una variante nueva, decir explícitamente qué cambia respecto a lo medido.
- Citar los archivos que leyó y los números que usó. No inventar números: todo número viene de un archivo, un log o un cálculo explícito.

---

## Tarea 1 — Desbloquear el barrido por traza: conseguir Psi dentro del presupuesto (ALTA PRIORIDAD)

**Por qué:** la Parte B del barrido por traza YA está medida y funciona (Q=2,285, T=403,187; barrido 94,185 T; factor DQI 9.5699, geomean 5.1456 — vs QF 8.22455 / 4.89215). El único bloqueo es Psi = (sigma')⁻¹ mod sigma: la Parte B lo necesita como registro (420 qubits) y el EEA para calcularlo no cabe. Si Psi se consigue dentro del presupuesto, el DQI salta a ~9.57× (geomean ~5.15×). Es la palanca más grande que queda.

**Presupuesto (break-even, medido desde la Parte B):** T_E < 66,063 T **Y** ΔQ_E < 180 qubits (con T_E=0). A T_E=16,331 → ΔQ máx 131; a 30,000 → 93; a 50,000 → 40; a 66,063 → 0. El EEA de división medido da T_E ≥ 66,063 T (peor caso L=35: 1,026 multiplicaciones + 19 inversiones; promedio 250 muls + 7.5 invs, T_E ≥ 16,331) y ~1,384 qubits nuevos (864 conjunto de trabajo + cociente ~420 + contadores/controles ~100) — excede AMBOS. Q es la restricción vinculante.

**Pregunta:** ¿hay una forma de obtener Psi (o un equivalente que haga funcionar `build_scan` sin la inversión por posición) dentro del presupuesto (T_E < 66,063 Y ΔQ_E < 180)?

**Vías a explorar (en orden de promesa):**
1. **EEA empaquetado/sincronizado estilo v11:** el BM v11 es un motor sincronizado (sin arrays grandes). ¿Se puede empaquetar el EEA igual — reutilizando registros, sincronizando las iteraciones — para bajar los ~1,384 qubits a <180? ¿Cuánto costaría en T?
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

**Entregable:** diseño concreto de la vía propuesta (o demostración de que ninguna cabe), con Q y T desglosados, comparación contra el presupuesto (T_E < 66,063 Y ΔQ_E < 180), y factor/geomean proyectado. Si propone construir algo, decir exactamente qué archivos cambian y qué mide el Gold.

---

## Tarea 2 — Bajar el costo del BM (250,832 T, 35.31% del T)

**Por qué:** el BM es el segundo bloque más grande (250,832 T, 35.31% del T total), después del barrido. El multiplicador ya está en su piso (42 ANDs), así que la palanca NO es el multiplicador — es el NÚMERO y la ESTRUCTURA de las multiplicaciones y conversiones del BM.

**Desglose (QF, medido por perfilador):** bm_update 117,432 + bm_disc 55,818 + bm_swap 33,552 + bm_alpha 23,520 + bm_dclear 15,120 + bm_d 2,100 + bm_x 1,680 + bm_flags 1,610 = 250,832 T. El bm_update solo es 117,432 T (46.8% del BM, 16.5% del T total).

**Pregunta:** ¿se puede reestructurar el BM para usar menos multiplicaciones de campo (o conversiones) sin cambiar el resultado? ¿O hay una variante del BM más eficiente para este caso (síndrome de 70 elementos, grado ≤35)?

**Vías a explorar:**
1. **bm_update (117,432 T):** ¿qué hace exactamente y por qué cuesta tanto? ¿Se puede fusionar con bm_disc/bm_swap, o evitar multiplicaciones redundantes (p. ej., multiplicar por 0 o por 1, o por el mismo valor varias veces)?
2. **Variante del BM:** ¿un BM linealizado, un BM que trabaje directamente sobre el síndrome sin conversiones intermedias, o un BM que aproveche la estructura del síndrome (70 elementos, grado ≤35, L≤35)? ¿Cuántas multiplicaciones necesitaría cada variante?
3. **¿Se puede reducir el número de rondas del BM?** (L ≤ 35; ¿el BM siempre necesita las 35 rondas, o se puede terminar antes cuando el síndrome ya está resuelto?)
4. **Trade-off T vs Q:** ¿una variante que use más Q pero menos T (o viceversa) mejora el score R·Q²·T? (Q está al cuadrado — un aumento de Q tiene que compensarse con una bajada grande de T.)

**Archivos que leer:**
- `~/workspace/qcc-dqi/src/dqi_bm_stage_v1.py` — la etapa BM (P2 vive aquí, no en dqi_decoder_v1.py).
- `~/workspace/qcc-dqi/src/dqi_decoder_v1.py` — `build_decoder`, cómo se llama al BM.
- `~/workspace/qcc-data/dqi-perfil/REPORTE_PERFIL_DQI.md` — perfil del 1949 (BM 185,034 + 113,198 = 298,232 T en el 1949; el QF es 250,832 T por el swap 63→42 ANDs).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/p1p2p3-qf/verify_p1p2p3_qf_gold.log` — Gold del QF (Q, T, R, k).
- El multiplicador GF(2¹²) en `~/workspace/qcc-dqi/src/` (42 ANDs, piso medido — no proponer cambiarlo).

**Entregable:** diseño concreto de la reestructuración propuesta, con el número de multiplicaciones antes/después, Q y T desglosados, y factor/geomean proyectado. Si la respuesta es "el BM ya está en su piso para esta arquitectura", demostrarlo con número (contar las multiplicaciones mínimas que el algoritmo exige).

---

## Tarea 3 — Eliminar o achicar el registro tau (~432 Q, ~23% de Q)

**Por qué:** Q está al cuadrado en el score (R·Q²·T) — bajar Q es la palanca más amplificada. El registro tau (~432 qubits, ~23% de Q) es "frío" durante el barrido y solo lo necesita `bm.reverse()` (para deshacer el BM). Si tau se elimina (recomputar en vez de guardar), Q bajaría de 1,857 a ~1,425, y el factor DQI subiría por (1,857/1,425)² = **1.698×** — SI el costo en T de recomputar no lo come. Es la palanca de Q más grande que queda.

**Pregunta:** ¿se puede eliminar el registro tau recomputándolo durante `bm.reverse()` (en vez de guardarlo), y cuál es el trade-off T vs Q? ¿O se puede achicar tau (p. ej., guardar solo parte, o comprimirlo)?

**Vías a explorar:**
1. **Recomputar tau en el reverso:** `bm.reverse()` deshace las actualizaciones del BM usando tau. ¿Se puede recomputar tau hacia adelante (re-ejecutar el BM) durante el reverso, en vez de guardarlo? ¿Cuánto T extra costaría (re-ejecutar el BM = ~185,034 T fwd, o menos si solo se recomputa lo necesario)? ¿Cuál es el neto en R·Q²·T?
2. **Achicar tau:** ¿tau necesita los 432 qubits (36 coefs × 12 bits), o se puede guardar solo los coeficientes no nulos / solo hasta el grado actual? ¿Cuánto Q se ahorraría y cuánto T costaría?
3. **¿Tau se puede reusar para otra cosa?** (Ya medido: NO se puede reusar para Psi — la hipótesis τ∝Psi es FALSA, 8/56 casos. No proponerlo de nuevo. ¿Se puede reusar para otra cosa, p. ej., como scratch del barrido o de omega?)
4. **Trade-off general:** dado que Q está al cuadrado, ¿cuánto T extra vale la pena pagar por cada qubit ahorrado? (El break-even: ahorrar ΔQ qubits vale la pena si T_nuevo/T_viejo < (Q_viejo/Q_nuevo)².)

**Archivos que leer:**
- `~/workspace/qcc-dqi/src/dqi_bm_stage_v1.py` — cómo se usa tau en el BM (forward y reverse).
- `~/workspace/qcc-dqi/src/dqi_decoder_v1.py` — `build_decoder`, `bm.reverse()`, tamaños de registros.
- `~/workspace/qcc-data/test-dev/espiral-prototipo/p1p2p3-qf/build_p1p2p3_qf.log` — live_frontera por etapa (bm_forward 1,794; omega_fwd 1,794; scan 1,794; omega_rev 1,794; bm_reverse 1,724; pico global 1,857 intra-etapa).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/scan-traza-v1/test_psi_tau.py` — τ∝Psi FALSA (no proponer reusar tau para Psi).
- `~/workspace/qcc-data/test-dev/espiral-prototipo/scan-traza-v1/REPORTE_CONSTRUCCION_BARRIDO_TRAZA_DQI_2026-11-20.md` — Q por etapa (bm_forward 1,794 → omega_fwd 1,794 → psi_alloc 2,214 → scan 2,214 → omega_rev 1,794 → bm_reverse 1,724).

**Entregable:** diseño concreto (recomputar / achicar / reusar tau), con Q y T antes/después, el trade-off en R·Q²·T (factor y geomean proyectado), y el break-even (cuánto T extra se puede pagar por cada qubit ahorrado). Si no vale la pena, demostrarlo con número.

---

## Resumen de entregables (para Elán)

| Tarea | Palanca | Techo (si funciona) |
|---|---|---|
| 1. Psi (barrido por traza) | Desbloquea 9.57× DQI | DQI 8.22× → ~9.57×; geomean 4.89× → ~5.15× |
| 2. BM más barato | 35.31% del T | Depende del diseño (bm_update 117,432 T es el blanco) |
| 3. Eliminar tau | Q² (432 Q, ~23%) | DQI ×1.698 si T no sube; neto según trade-off |

**Orden sugerido:** Tarea 1 primero (techo más alto), luego Tarea 3 (palanca Q²), luego Tarea 2 (optimización incremental). Las tres son independientes — se pueden hacer en paralelo.
