# SUPERVISIÓN DE DATOS — Score público del ZIP v5 en Kaggle (ref 58594222)

**Fecha:** 2026-11-19 ~22:50 CST
**Cadena:** Programación → Datos (esta supervisión) → Brujo (ya verificó: CONCURRO PASA) → Auditor (revisa) → Elán
**Regla 0:** cada número de esta supervisión viene de una lectura directa de Kaggle o de un cálculo propio; lo [ESTIMADO] se marca.

## 0. Veredicto

**CONCURRO (PASA).** Verifiqué directo en Kaggle con el conector (dos llamadas). **El ZIP v5 ya calificó: ref 58594222, public_score 4.90803, status COMPLETE. Nuevo mejor personal por mucho: era v4.1 3.54317, ahora 4.90803 (+38.52%); por arriba de lo esperado 4.89215 (+0.32%).** Las comparaciones del Brujo se reproducen exacto. Una precisión mía (D-SC5-1, menor): el "local 3.53396" de su paréntesis no es el local del v4.1 — con el local correcto, la escala Kaggle-local del v4.1 es +0.3245%, la misma que la del v5 (+0.3246%).

**Archivos supervisados (medidos por mí):**

| Archivo | Tamaño / líneas | Hash |
|---|---|---|
| `candidato-v5-2026-11-19/VERIFICACION_BRUJO_SCORE_V5_2026-11-19.md` | 42 l. | md5 `97df01cddd07d9e505544933a118880a` |

## 1. Verificación directa en Kaggle (por mí, dos llamadas)

### 1.1 `get_competition_submission` (ref 58594222)

```json
{
  "ref": 58594222,
  "total_bytes": "60104444",
  "date": "2026-11-20T04:12:53.993Z",
  "description": "v5: P1P2P3-QF DQI (Q=1857, T=710312) + R1R5 invsqrt (Q=139) + seg100@brot13 dfthcsos; expected geomean 4.89215",
  "file_name": "submission.zip",
  "public_score": "4.90803",
  "status": "COMPLETE",
  "submitted_by": "elnzainoscorona",
  "submitted_by_ref": "elnzainoscorona",
  "team_name": "Frantal Core",
  "url": "/submissions/58594222/58594222.raw"
}
```

- **public_score "4.90803", status "COMPLETE"** — el v5 ya calificó ✓
- ref, total_bytes "60104444" (exacto al ZIP local sha256 `d1392960…`), fecha, descripción con 4.89215, file_name, submitted_by, team — todos coinciden con la subida verificada ✓

### 1.2 `search_competition_submissions` (10 más recientes, por fecha)

El v5 es la primera (la más reciente), public_score 4.90803, COMPLETE; seguida por v4.1 (3.54317, COMPLETE) y swap42 (3.53019, COMPLETE). **El v5 es el mejor por score público entre las 10** ✓.

## 2. Comparaciones — recomputadas por mí ✓

| Comparación | Cálculo | Resultado |
|---|---|---|
| v5 vs v4.1 | 4.90803/3.54317−1 | **+38.5209% → +38.52%** |
| v5 vs esperado | 4.90803/4.89215−1 | **+0.3246% → +0.32%** |
| v5 vs adoptado | 4.90803/3.53171−1 | **+38.9704% → +38.97%** |
| v5 vs g2 | 4.90803/3.55185−1 | **+38.1824% → +38.18%** |
| v5 vs swap42 | 4.90803/3.53019−1 | +39.03% |

Todas coinciden con las del Brujo. **La coincidencia se verifica:** el +38.52% vs v4.1 (38.5209%) y el +38.52% del geomean corregido vs adoptado (4.89215/3.53171−1 = 38.5207%) son comparaciones distintas con el mismo número redondeado (difieren en 0.0002 puntos porcentuales).

## 3. Precisión

- **D-SC5-1 (mía, menor):** el paréntesis del Brujo dice "la escala Kaggle-local, como en v4.1: local 3.53396 vs Kaggle 3.54317, +0.26%". **El 3.53396 no es el local del v4.1** — es el geomean del adoptado R1+R5-based de A-V5-1 (5.33517 × 8.22455 × 1.00583)^(1/3) = 3.53396. El local del v4.1 es **3.53171** (logshift2 + QF + lbfgs, recomputado por mí: (5.32499245 × 8.22455 × 1.00583)^(1/3) = 3.53171). Con el local correcto, la escala Kaggle-local del v4.1 es **3.54317/3.53171−1 = +0.3245%** (no +0.26%) — **y es la misma que la del v5 (+0.3246%), a 4 decimales**. El +0.32% del v5 por arriba de lo esperado no es solo "consistente con" la escala del v4.1: es el mismo factor. (Respaldo: el swap42, Kaggle/esperado 3.53019/3.51878−1 = +0.3244%, el mismo factor.) No cambia el veredicto — las comparaciones principales del Brujo son todas correctas.

## 4. Selección final — el v5 es el mejor por score, pero NO está marcado como final

Elán ya lo sabe ("Ya subio", 22:48). La selección final ya está marcada por Elán (las 2 mejores: **v4.1 y swap42**, marcadas a las 22:12, antes de que el v5 calificara) — no se toca. **El v5 (4.90803) es ahora el mejor por score público, pero marcarlo como final es decisión solo de Elán, aparte.** Si Elán lo marca, la selección pasaría a ser v5 + v4.1 (las 2 mejores por score público).

## 5. Veredicto y cadena

**CONCURRO (PASA).** El v5 calificó en Kaggle con **4.90803** — nuevo mejor personal (+38.52% vs v4.1), por arriba del esperado 4.89215 (+0.32%).

Cadena: Programación ✓ → **Datos ✓ (esta supervisión)** → Brujo ✓ (ya verificó) → Auditor (revisa) → **Elán decide si marca el v5 como final**.

## 6. Adenda — revisión del Auditor: CONCURRO (PASA)

**Revisión del Auditor:** `~/workspace/auditoria/REVISION_AUDITOR_SCORE_V5_2026-11-19.md` — 65 l. / md5 `6745b1cae4c0f8d5788c081d1b395246` (verificado por mí en disco). Veredicto del Auditor: **CONCURRO (PASA)**.

El Auditor verificó por sí mismo directo en Kaggle con el conector, dos llamadas: `get_competition_submission` (ref 58594222, public_score "4.90803", status "COMPLETE", total_bytes "60104444", descripción con 4.89215) y `search_competition_submissions` (el v5 es la primera, 4.90803, COMPLETE; seguida por v4.1 3.54317 y swap42 3.53019; **verificado computacionalmente por él: el v5 es el mejor por public_score entre las 10**). Comparaciones recomputadas por él: vs v4.1 +38.5209% → +38.52%; vs esperado +0.3246% → +0.32%; vs adoptado +38.9704% → +38.97%; vs g2 +38.1824% → +38.18%; vs swap42 +39.03%. Todas coinciden con las mías y con las del Brujo. La coincidencia se verifica (38.5209% vs 38.5207%, difieren en 0.0002 puntos porcentuales).

**D-SC5-1 — concurre (verificada por él):** el 3.53396 no es el local del v4.1 — es el adoptado R1+R5-based (recomputado por él: 3.53396); el local del v4.1 es 3.53171 (recomputado por él: 3.53171). Con el local correcto, la escala Kaggle-local del v4.1 es +0.3245% — la misma que la del v5 (+0.3246%).

**A-SC5-1 (nota de redondeo del Auditor, trivial — concurro, verificada por mí):** mi respaldo swap42 dice "+0.3244%", pero con el esperado redondeado 3.51878 da **+0.324260% → +0.3243%** (verificado por mí); con el esperado sin redondear (3.518775) da **+0.324403% → +0.3244%** (mi valor). La diferencia es 0.0001 puntos porcentuales y se explica por el redondeo del esperado. No afecta nada: las tres escalas son +0.32% a 2 decimales — el mismo factor.

**Cadena COMPLETA: Programación ✓ → Datos ✓ → Brujo ✓ → Auditor ✓ → Elán decide si marca el v5 como final.** El v5 calificó con 4.90803 — nuevo mejor personal. La selección final (v4.1 + swap42) no se toca; marcar el v5 como final es decisión solo de Elán.
