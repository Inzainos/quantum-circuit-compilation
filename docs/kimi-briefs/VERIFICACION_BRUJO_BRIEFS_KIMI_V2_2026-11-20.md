# Verificación del Brujo — Briefs Kimi DQI v2 (2026-11-20)

**Fecha:** 2026-11-20 ~11:05 CST
**Verificado:** `BRIEFS_KIMI_DQI_V2_2026-11-20.md` (157 l. / md5 `f8446fee…`) — producidos por Datos por GO de Elán (11:00 CST: "aplíquenlas y hagan el nuevo modelo").
**Base:** mi anexo `ANEXO_CORRECCIONES_BRIEFS_KIMI_2026-11-20.md` (103 l. / md5 `67e7ca5c…`, con D-KB-1/D-KB-2 aplicadas) + briefs v1 (131 l. / md5 `a0fe453f…`).

## Veredicto: CONCURRO (PASA) — la v2 aplica las 4 correcciones + los 2 agregados del anexo, con los números recomputados verificados

## 1. Integridad de archivos
- **v2:** 157 l. / md5 `f8446fee…` ✓ (lo que Datos reportó).
- **v1 intacta:** 131 l. / md5 `a0fe453f…` ✓ (sin tocar — la v1 queda como referencia).
- **Supervisión de Datos (actualizada):** 131 l. / md5 `148cba4b…` ✓ (incluye la revisión del Auditor y la nota de md5 de mi edición del anexo a las 10:43, `1cb7d086…` → `67e7ca5c…` — correcto, esa edición fue aplicar D-KB-1/D-KB-2; la sustancia no cambia).

## 2. Las 4 correcciones están aplicadas (verificado en disco, línea por línea)
- **Corrección 1 (base nueva):** v2 l.13 "Adoptado (QF + 15 AND): Q=1,857, T=670,307, factor DQI 8.7154, geomean local 4.9876" ✓; l.14 "Base anterior (QF sin parche): Q=1,857, T=710,312, factor 8.22455, geomean 4.89215. El parche de 15 AND baja la inversión por torre de 75 T a 66 T y el total de 710,312 a 670,307 (−40,005 T)" ✓; l.6 aviso del patch (ver §5) ✓.
- **Corrección 2 (Tarea 3):** v2 l.109 "Tarea 3 — ¿Existe un BM sin tau? (NO asumir 1.698×)" ✓; l.111 "Por qué (CORREGIDO)" con tau NO frío (se usa en las 70 rondas, pico 1,857 dentro del BM, pico del barrido 1,837 en medición de Elán) ✓; l.115 "Pregunta (REFORMULADA): ¿existe un BM sin tau…?" ✓.
- **Corrección 3 (presupuesto):** v2 l.57 "T_E < 42,679 T Y ΔQ_E < 119 qubits (con T_E=0). A T_E=16,331 → ΔQ máx 71; a 30,000 → 33; a 50,000 → −19 (ya no hay margen de Q); a 42,679 → 0" ✓; l.152 tabla resumen (119/71/33/−19) ✓.
- **Corrección 4 (valor del qubit):** v2 l.16 "Un qubit vale 2·T/Q ≈ 722 Toffoli con la base nueva (765 con la QF) — NO ~20× como decía la v1. Regla de break-even: T_nuevo/T_viejo < (Q_viejo/Q_nuevo)²" ✓; l.153 tabla resumen ✓.

## 3. Los 2 agregados a la Tarea 2 están aplicados
- **A. Ventana:** v2 l.95 "A. Ventana de coeficientes no nulos de σ y tau por ronda. `bm_update` son 117,432 T = 2,796 multiplicaciones de 42 T (1,398 por dirección). La cota `bu(r)` es de peor caso… ¿Cuál es la ventana de coeficientes no nulos de σ y tau por ronda?" ✓
- **B. Techo de errores:** v2 l.96 "B. Cuánto error de decodificación tolera el score. Pasar de 5 errores a 0 solo mueve R de 1.2131 a ≈1.191, o sea ~1.8% del DQI… ninguna optimización que solo reduzca los errores de decodificación puede ganar más de ~1.8% del DQI" ✓

## 4. Números recomputados por Datos — verificados por el Brujo (recomputados, no re-medidos)
- **BM:** 117,432 + 55,818 + 33,552 + 22,260 + 13,860 + 2,100 + 1,680 + 1,610 = **248,312** ✓. bm_alpha 23,520 → 22,260 (−1,260 = 140×9) ✓; bm_dclear 15,120 → 13,860 (−1,260 = 140×9) ✓ (las cifras QF 23,520 y 15,120 son del reporte del arco — verificado en disco: "bm_alpha 23,520 + bm_dclear 15,120"). Baja total del BM 2,520 = 280×9 ✓.
- **Omega:** ValueInv 35×66 = **2,310**/dirección (QF 35×75 = 2,625) ✓; omega/dirección 26,460 + 2,310 = 28,770; total 2×28,770 = **57,540** ✓; baja/dirección 315 = 35×9 ✓.
- **Barrido:** 4,095×66 = **270,270**; 4,095×23 = **94,185**; suma **364,455** ✓.
- **Montgomery:** 773,841/270,270 = **2.863**; 663,303/270,270 = **2.454** → **2.45–2.86×** vs la base nueva ✓ (vs la QF eran 2.52/2.16 — verificado: 773,841/307,125 = 2.520; 663,303/307,125 = 2.160).
- **Parte B:** costo = R × 2,285² × 400,037 = 2,533,792,462,604.685; factor = 2.4439e13 / costo = **9.64523 → 9.6452** ✓ (precisión A-V2-2 del Auditor, aplicada: el redondeo a 4 decimales es 9.6452, no 9.6453 — 9.64522563 redondea hacia abajo; el error era mío, no de Datos); geomean = (5.33517 × 9.64523 × 2.6684)^(1/3) = **5.15906 → 5.159** ✓ (con el ratio químico exacto 2.66832953 → 5.15901, mismo redondeo; el geomean no cambia).
- **Chequeo de consistencia:** factor QF = 8.22455 ✓; factor base nueva = 8.7154 ✓ (recomputados por mí con R=1.2131052140444296).

## 5. Precisiones del Auditor (A-V2-1 a A-V2-3, aplicadas donde me tocan)
- **A-V2-1:** la cabecera de la v2 cita los md5 viejos del anexo (`1cb7d086…`, actual `67e7ca5c…`) y de la supervisión (`2f1285af…`/123 l., actual `148cba4b…`/131 l.) — es documento de Datos (v2 l.4–l.5), sustancia intacta; no lo edito (es suyo).
- **A-V2-2:** el factor de la Parte B es 9.6452, no 9.6453 (ver §4) — aparece también en la v2 (l.38, l.55, l.157) y en la adenda de Datos (l.131); esos son documentos de Datos.
- **A-V2-3:** la cita de D-KB-1 para la copia del repo estaba corrida por una línea: el `_mul` de `forward_round` está en **l.174**, no l.173; el bloque `bm_update` es **l.172–174**, no l.170–173 (verificado por el Auditor con grep -n y por mí: l.172 `with b.mark('bm_update')`, l.173 `for i in range(self.bu(r) + 1)`, l.174 `self._mul(...)`). Corregido en el anexo (D-KB-1). Las citas de la copia QF (l.248, l.263–265) sí son correctas.

## 6. El patch sigue sin estar en disco
- v2 l.6: "⚠️ EL PATCH NO ESTÁ EN DISCO: `p15_main64d4cec.patch`… NO existe en `~/workspace` ni en `/home/hatch` (verificado por el Brujo, por Datos y por el Auditor). **Elán debe re-enviarlo.**" ✓ — la advertencia está en la v2, en su lugar. Datos lo verificó de nuevo ~11:00: sigue sin estar. **Elán es quien le pasa los briefs corregidos a Kimi** — y sin el patch, Kimi no puede partir de la base corregida.

## 6. Alcance
- Los números medidos por Elán (670,307, 8.7154, 4.9876, 248,312, 57,540, 364,455, 66 T, 1,837, 670,218) se citan en la v2 como medidos por Elán (l.6, l.157) — no re-medidos por el Brujo, Datos ni el Auditor. La aritmética sobre ellos está verificada por los tres.
- Nada a Kaggle sin GO nuevo. Nada a main. Nada al repo. Cadena: Datos (v2) → Brujo verifica → Auditor revisa → Elán decide (y es él quien le pasa los briefs corregidos a Kimi).
