# REVISIÓN DEL AUDITOR — Verificación del Brujo a los briefs Kimi DQI v2

**Fecha:** 2026-11-20 ~11:20 CST
**Revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/VERIFICACION_BRUJO_BRIEFS_KIMI_V2_2026-11-20.md` (37 l. / md5 `63a73f70…`).
**Briefs v2:** `~/workspace/qcc-data/test-dev/espiral-prototipo/BRIEFS_KIMI_DQI_V2_2026-11-20.md` (157 l. / md5 `f8446fee…`, producidos por Datos por GO de Elán 11:00).
**Base:** briefs v1 intactos (131 l. / md5 `a0fe453f…`); anexo `ANEXO_CORRECCIONES_BRIEFS_KIMI_2026-11-20.md` (103 l. / md5 `67e7ca5c…`, con D-KB-1/D-KB-2 aplicadas — era `1cb7d086…`); supervisión de Datos `SUPERVISION_DATOS_ANEXO_BRIEFS_KIMI_2026-11-20.md` (131 l. / md5 `148cba4b…`, CONCURRO PASA con D-KB-1/D-KB-2).
**Método:** verificación independiente por mi cuenta: leí los 3 documentos completos; verifiqué las líneas citadas de la v2 en disco con awk; recomputé toda la aritmética (BM, omega, barrido, Montgomery, Parte B con R y referencia); verifiqué las citas de línea del código BM en ambas copias con grep -n; verifiqué que el anexo actual conserva todos los números; busqué el patch.
**Cadena:** Datos (v2) → Brujo verifica → Auditor revisa → Elán decide (y es él quien le pasa los briefs corregidos a Kimi). Nada a Kaggle sin GO nuevo. Nada a main. Nada al repo.

## VEREDICTO: CONCURRO (PASA) — LA V2 APLICA LAS 4 CORRECCIONES Y LOS 2 AGREGADOS, CON 3 PRECISIONES TRIVIALES (A-V2-1 A A-V2-3)

Ninguna precisión cambia ningún veredicto ni ningún número que Kimi usaría para diseñar (el factor 9.6452 vs 9.6453 no mueve el geomean 5.159).

---

## 1. LAS 4 CORRECCIONES ESTÁN APLICADAS (VERIFICADO LÍNEA POR LÍNEA EN LA V2)

- **Corrección 1 (base nueva):** v2 l.13 "Adoptado (QF + 15 AND): Q=1,857, T=670,307, factor DQI 8.7154, geomean local 4.9876" ✓; l.14 "Base anterior (QF sin parche…): Q=1,857, T=710,312, factor DQI 8.22455, geomean local 4.89215. El parche de 15 AND baja la inversión por torre de 75 T a 66 T y el total de 710,312 a 670,307 (−40,005 T)" ✓; l.6 aviso del patch (ver §4) ✓.
- **Corrección 2 (Tarea 3):** v2 l.109 "Tarea 3 — ¿Existe un BM sin tau? (NO asumir 1.698×)" ✓; l.111 "Por qué (CORREGIDO)" con tau NO frío (se usa en las 70 rondas, pico 1,857 dentro del BM, pico del barrido 1,837 en medición de Elán) ✓; l.115 "Pregunta (REFORMULADA): ¿existe un BM sin tau…?" ✓. La v2 l.124 cita el código correctamente: "`forward_round` l.248, `bm_update` l.263–265 en la copia QF" (verificado por mí con grep -n en la copia QF: l.248 `def forward_round`, l.263 `with b.mark('bm_update')`, l.265 `self._mul(...)`) ✓ — la v2 incorpora la sustancia de D-KB-1.
- **Corrección 3 (presupuesto):** v2 l.57 "T_E < 42,679 T Y ΔQ_E < 119 qubits (con T_E=0). A T_E=16,331 → ΔQ máx 71; a 30,000 → 33; a 50,000 → −19 (ya no hay margen de Q); a 42,679 → 0" ✓; l.152 tabla resumen (119/71/33/−19) ✓.
- **Corrección 4 (valor del qubit):** v2 l.16 "Un qubit vale 2·T/Q ≈ 722 Toffoli con la base nueva (765 con la QF) — NO ~20× como decía la v1. Regla de break-even: T_nuevo/T_viejo < (Q_viejo/Q_nuevo)²" ✓; l.153 tabla resumen ✓.

## 2. LOS 2 AGREGADOS ESTÁN APLICADOS

- **A. Ventana:** v2 l.95 "A. Ventana de coeficientes no nulos de σ y tau por ronda. `bm_update` son 117,432 T = 2,796 multiplicaciones de 42 T (1,398 por dirección). La cota `bu(r)` es de peor caso… ¿Cuál es la ventana de coeficientes no nulos de σ y tau por ronda?" ✓
- **B. Techo de errores:** v2 l.96 "B. Cuánto error de decodificación tolera el score. Pasar de 5 errores a 0 solo mueve R de 1.2131 a ≈1.191, o sea ~1.8% del DQI… ninguna optimización que solo reduzca los errores de decodificación puede ganar más de ~1.8% del DQI" ✓

## 3. NÚMEROS RECOMPUTADOS POR DATOS — VERIFICADOS POR MÍ (TODOS EXACTOS, SALVO A-V2-2)

- **BM:** 117,432 + 55,818 + 33,552 + 22,260 + 13,860 + 2,100 + 1,680 + 1,610 = **248,312** ✓. bm_alpha 23,520 → 22,260 (−1,260 = 140×9) ✓; bm_dclear 15,120 → 13,860 (−1,260 = 140×9) ✓; baja total 2,520 = 280×9 ✓. Las cifras QF 23,520/15,120 son del reporte del arco — verificado en disco (`LENTE_ARCO_COMPLETO…` l.42; `ANALISIS_TEST_E…` l.22; reporte del hoist l.163; supervisión del arco l.66 y l.73: suma QF 250,832 exacta) ✓. El 140 por bloque es 1 inversión por ronda × 140 rondas (70 fwd + 70 rev) — `bm_alpha` invierte en `_inv_init` por ronda (verificado en la copia del repo, l.167 `scaf = self._inv_init(P, Pinv)` dentro del mark `bm_alpha`); Datos contó 280 en el código (2 por ronda: `_dclear` 1 + `bm_alpha` 1) ✓.
- **Omega:** ValueInv 35×66 = **2,310**/dirección (QF 35×75 = 2,625) ✓; 26,460 + 2,310 = 28,770/dirección; total 2×28,770 = **57,540** ✓ (QF 58,170); baja 630 = 70×9 ✓.
- **Barrido:** 4,095×66 = **270,270**; 4,095×23 = **94,185**; suma **364,455** ✓.
- **Montgomery:** 773,841/270,270 = 2.8632 → **2.863** ✓; 663,303/270,270 = 2.4542 → **2.454** ✓; vs QF 773,841/307,125 = 2.5196 → 2.520 y 663,303/307,125 = 2.1597 → 2.160 ✓; 12,282×63+75 = 773,841 y 12,282×54+75 = 663,303 ✓. La v2 l.37 (2.45–2.86×, +49,128 Q, 3 muls 189 T > 1 inv 66 T) ✓.
- **Parte B:** costo = R × 2,285² × 400,037 = **2,533,792,462,604.685** (exacto al del Brujo) ✓; Parte B T = 248,312 + 57,540 + 94,185 = **400,037** ✓; geomean = (5.33517 × factor × 2.6684)^(1/3) = **5.159** ✓ (5.15906 con factor 9.64523; 5.15901 con ratio químico exacto 2.66832953 — mismo redondeo). **Factor: ver A-V2-2 (9.6452, no 9.6453).**
- **Chequeo de consistencia:** factor QF = 2.4439e13/(R×1,857²×710,312) = 8.2245473 → 8.22455 a 5 decimales ✓; factor base nueva = 8.7154015 → **8.7154** ✓; referencia desde el Gold QF: 8.22455 × 2,971,470,537,625.3 = 24,439,008,010,226.16 (≈2.4439e13) ✓.
- **Hoisting (v2 l.31):** 34×66×2 = **4,488** ✓; T → ~665,819 como **PROYECCIÓN, no medición** ✓; construcción verificada T=705,212 con ValueInv 75 T, Gold pendiente ✓.

## 4. EL PATCH — LA ADVERTENCIA ESTÁ EN SU LUGAR Y ES CLARA

v2 l.6: "⚠️ EL PATCH NO ESTÁ EN DISCO: `p15_main64d4cec.patch`… NO existe en `~/workspace` ni en `/home/hatch` (verificado por el Brujo, por Datos y por el Auditor). **Elán debe re-enviarlo.** Sin el patch, Kimi no puede partir de la base corregida." ✓ — prominente, al inicio, antes de cualquier número de la base nueva. Reforzada en l.14 ("Kimi parte del patch `p15_main64d4cec.patch`, no de 710,312") y l.157 ("El patch `p15_main64d4cec.patch` NO está en disco — Elán debe re-enviarlo") ✓. Yo verifiqué la ausencia en mi revisión del anexo (find vacío para `*p15_main64d4cec*`); Datos lo verificó de nuevo ~11:00 (supervisión §8) ✓.

## 5. ALCANCE — LAS CONCLUSIONES NO EXCEDEN LO VERIFICADO

La v2 l.157 lista los números medidos por Elán como no re-medidos (670,307, 8.7154, 4.9876, 248,312, 57,540, 364,455, 66 T, 1,837, 670,218) ✓; l.6 dice explícito que la aritmética sobre ellos está verificada por los tres ✓. El 1,837 aparece solo como medición de Elán ✓. El hoisting 665,819 se marca PROYECCIÓN ✓. Nada a Kaggle, nada a main, nada al repo ✓.

## 6. ADENDA A MI REVISIÓN DEL ANEXO — SUPERVISIÓN DE DATOS (LLEGÓ; LA REVISO AQUÍ)

La supervisión de Datos del anexo llegó después de mi revisión (`SUPERVISION_DATOS_ANEXO_BRIEFS_KIMI_2026-11-20.md`, 131 l. / md5 `148cba4b…`). **CONCURRO (PASA) con ella, con D-KB-1/D-KB-2**, con la salvedad de A-V2-3 (abajo). Verificado por mí: las 4 líneas del brief (mismas que yo verifiqué); la aritmética (mismos valores que yo recomputé: 364,455; 670,307; 8.7154; 4.9876; tablas 180/131/93/40/65,951 y 119/71/33/−19/42,679; 765/722/36.1; 2,796×42=117,432; R(k=0)=1.191260 → +1.83%); el conteo estructural de inversiones (BM 280, omega 70, barrido 4,095, total 4,445×9 = 40,005 — coincide con mi chequeo de consistencia de la revisión del anexo); el patch ausente (find vacío, mismos archivos no relacionados que yo encontré). **D-KB-2 fortalece la Corrección 3** (el supuesto T=400,037 queda confirmado estructuralmente, no solo por reproducir los 5 números de Elán) ✓. La adenda de la supervisión registra mi revisión y la nota de md5 del anexo (1cb7d086… → 67e7ca5c…, edición del Brujo 10:43:04) — verifiqué que la edición no cambia la sustancia: todos los números que Datos listó siguen presentes y correctos en el anexo actual (364,455: 6×; 670,307: 11×; 248,312: 6×; 57,540: 6×; 117,432: 1×; 8.7154: 5×; 4.9876: 4×; 42,679: 4×; 765: 4×; 722: 6×; 4,488: 2×; 2,796: 3×; 1.191260: 1×; 65,951: 3×; 66,063: 3×; 119: 5×) ✓.

## 7. PRECISIONES TRIVIALES

### A-V2-1 — La cabecera de la v2 cita los md5 viejos del anexo y de la supervisión
La v2 l.3–4 cita el anexo como "103 l. / md5 `1cb7d086…`" y la supervisión como "123 l. / md5 `2f1285af…`". Los actuales son anexo **67e7ca5c…** (editado por el Brujo 10:43, antes de producir la v2 ~11:10) y supervisión **148cba4b…** (131 l., con la adenda). La sustancia no cambia — el contenido de la v2 refleja el anexo actual (l.124 nombra la copia QF, sustancia de D-KB-1) — pero la cabecera cita las versiones previas a la edición y a la adenda. Para higiene de cadena, la cabecera debería citar `67e7ca5c…` y `148cba4b…`.

### A-V2-2 — El factor de la Parte B es 9.6452, no 9.6453
2.4439e13 / 2,533,792,462,604.685 = **9.64522563 → 9.6452** (con la referencia exacta del Gold, 24,439,008,010,226.16 / costo = 9.64522879 → también 9.6452). El "9.64523 → 9.6453" del Brujo (§4) redondea mal hacia arriba (el 5º decimal es 2). Aparece como 9.6453 en la v2 (l.38, l.55, l.157), en la verificación del Brujo (l.29) y en la adenda de Datos (l.131) — en los tres debería ser **9.6452**. El geomean **5.159 no cambia** (5.159055 con 9.6452 vs 5.159073 con 9.6453; ambos → 5.159) y el "~9.65×" de la tabla resumen sigue correcto. Diferencia de 0.0001, sin efecto.

### A-V2-3 — La cita de línea de D-KB-1 para la copia del repo está corrida por una línea
El anexo (l.33) y Datos (D-KB-1, §9) dicen que en la copia del repo `bm_update` está en l.170–173 y que `self._mul(alpha, self.tau[i], self.sigma[i])` está en l.173. Verificado por mí con `grep -n`: `def forward_round` l.157 ✓, `with b.mark('bm_update')` l.172 ✓, pero `self._mul(...)` está en **l.174**, no l.173. El bloque `bm_update` es l.172–174, no l.170–173 (l.170 es el loop de `bm_swap`). El archivo no ha cambiado desde el 9 nov (mtime 9 nov 02:57, último commit a741cc7), así que no es deriva — la cita nació corrida por una. Las citas de la copia QF (l.248, l.263–265) sí son correctas (verificado: l.248 `def forward_round`, l.263 mark, l.265 `_mul`). No cambia ningún veredicto: la lógica es idéntica y tau se lee en las 70 rondas en ambas copias (en la del repo, `reverse_round` l.187 también usa tau: mark l.200, `_mul` l.202).

## 8. CONCLUSIÓN

**CONCURRO (PASA) con la verificación del Brujo a los briefs Kimi DQI v2: las 4 correcciones y los 2 agregados están aplicados, los números recomputados por Datos están verificados, la advertencia del patch está en su lugar, y las conclusiones no exceden lo verificado.** Precisiones triviales A-V2-1 (md5 viejos en la cabecera de la v2), A-V2-2 (factor Parte B 9.6452, no 9.6453) y A-V2-3 (cita de línea del repo l.174, no l.173). Elán decide (y es él quien le pasa los briefs corregidos a Kimi). Nada a Kaggle sin GO nuevo. Nada a main. Nada al repo.
