# SUPERVISIÓN DE DATOS — Subida del ZIP v5 a Kaggle (ref 58594222)

**Fecha:** 2026-11-19 ~22:14 CST
**Cadena:** Programación → Datos (esta supervisión) → Brujo (ya verificó: CONCURRO PASA) → Auditor (revisa) → Elán
**Regla 0:** cada número de esta supervisión viene de una lectura directa de Kaggle o de un cálculo propio; lo [ESTIMADO] se marca.

## 0. Veredicto

**CONCURRO (PASA).** Verifiqué directo en Kaggle con el conector (dos llamadas independientes). **La subida del v5 está en Kaggle: ref 58594222, total_bytes 60,104,444 exacto al ZIP local, fecha 2026-11-19 22:12:53 CST, descripción con el geomean corregido 4.89215 (A-V5-1 aplicada). Sin public_score aún — en calificación.** No hay nada que corregir en la subida.

**Archivos supervisados (medidos por mí):**

| Archivo | Tamaño / líneas | Hash |
|---|---|---|
| `candidato-v5-2026-11-19/VERIFICACION_BRUJO_SUBIDA_V5_2026-11-19.md` | 35 l. | md5 `9aed7f13eddcb199456e8cfae5f58687` |
| `candidato-v5-2026-11-19/candidato-v5-2026-11-19.zip` (local) | 60,104,444 B | sha256 `d1392960b0e64bf4a40ec1f2019cfd10bdc71118b801655cfb633f261ab6407a` |

## 1. Verificación directa en Kaggle (por mí, dos llamadas)

### 1.1 `get_competition_submission` (ref 58594222)

```json
{
  "ref": 58594222,
  "total_bytes": "60104444",
  "date": "2026-11-20T04:12:53.993Z",
  "description": "v5: P1P2P3-QF DQI (Q=1857, T=710312) + R1R5 invsqrt (Q=139) + seg100@brot13 dfthcsos; expected geomean 4.89215",
  "file_name": "submission.zip",
  "submitted_by": "elnzainoscorona",
  "submitted_by_ref": "elnzainoscorona",
  "team_name": "Frantal Core",
  "url": "/submissions/58594222/58594222.raw"
}
```

- **ref 58594222** — coincide con lo reportado por Programación y por el Brujo ✓
- **total_bytes "60104444"** — exacto al ZIP local (60,104,444 B, sha256 `d1392960…`) ✓
- **fecha 2026-11-20T04:12:53.993Z = 2026-11-19 22:12:53 CST** — verificado por mí con `date -d` ✓
- **descripción con geomean 4.89215** — corrección A-V5-1 aplicada ✓
- **file_name submission.zip, submitted_by elnzainoscorona, team "Frantal Core"** ✓
- **Sin public_score** — la respuesta no trae el campo (tampoco `status`); en calificación ✓

### 1.2 `search_competition_submissions` (10 más recientes, por fecha)

El v5 es la primera (la más reciente), con los mismos campos que en §1.1 — **tampoco trae public_score ni status** ✓. Las 9 siguientes, todas COMPLETE con public_score:

| ref | Descripción | public_score | status |
|---|---|---|---|
| 58579331 | v4.1 | 3.54317 | COMPLETE |
| 58570485 | swap42 | 3.53019 | COMPLETE |
| 58329687 | v4 | 3.42257 | COMPLETE |
| 58289295 | Adopted v3 | 3.42920 | COMPLETE |
| 58286822 | Adopted v2 | 3.41660 | COMPLETE |
| 58277509 | Adopted | 3.33544 | COMPLETE |
| 58113636 | v8 | 3.31949 | COMPLETE |
| 58074943 | v7 | 3.23829 | COMPLETE |
| 58004240 | v6.6.6 | 1.61459 | COMPLETE |

## 2. Selección final — no verificable por API, descansa en la palabra de Elán

Elán confirmó en Programación (22:12): "Ya están marcados las últimas 2 mejores versiones". Por score público las 2 mejores son **v4.1 (3.54317, ref 58579331)** y **swap42 (3.53019, ref 58570485)** — consistente con su declaración. La selección anterior era Adopted v3 (3.42920) + v4 (3.42257).

**Verificado por mí: ninguna de las 10 respuestas (ni `get_competition_submission` ni `search_competition_submissions`) trae un campo de selección/final.** La API de Kaggle NO expone el indicador de selección, así que el marcado mismo no es verificable por API y descansa en la palabra de Elán. **No se toca la selección** (solo Elán la marca).

Nota: Kaggle tampoco expone el hash del archivo subido, así que la verificación del contenido subido descansa en total_bytes (60,104,444 exacto) + descripción + fecha + ref. El ZIP local verificado es sha256 `d1392960…`.

## 3. Pendiente

**El score público del v5 aún no sale** — en calificación al momento de esta supervisión (22:14 CST). Cuando salga, se verifica contra el esperado (geomean 4.89215; referencia v4.1 en Kaggle 3.54317) y se reporta a Elán. El subagente de subida aún no reporta su handoff (pendiente, según el Brujo); la ref la verificó Programación y la re-verifiqué yo directo en Kaggle.

## 4. Veredicto y cadena

**CONCURRO (PASA).** La subida del v5 está verificada en Kaggle (ref 58594222, bytes exactos, descripción con 4.89215). Falta el score público — en calificación.

Cadena: Programación ✓ → **Datos ✓ (esta supervisión)** → Brujo ✓ (ya verificó) → Auditor (revisa) → **Elán**.

## 5. Adenda — revisión del Auditor: CONCURRO (PASA)

**Revisión del Auditor:** `~/workspace/auditoria/REVISION_AUDITOR_SUBIDA_V5_2026-11-19.md` — 71 l. / md5 `efcfca60d54ba423ddddc972ea4277a4` (verificado por mí en disco). Veredicto del Auditor: **CONCURRO (PASA)**.

El Auditor verificó por sí mismo directo en Kaggle con el conector, dos llamadas independientes: `get_competition_submission` (ref 58594222, total_bytes "60104444" exacto al ZIP local sha256 `d1392960…`, fecha 2026-11-20T04:12:53.993Z = 2026-11-19 22:12:53 CST verificado con `date -d`, descripción con geomean 4.89215, file_name submission.zip, submitted_by elnzainoscorona, team "Frantal Core", sin public_score ni status) y `search_competition_submissions` (el v5 es la primera, sin public_score ni status; las 9 siguientes todas COMPLETE con public_score, idénticas a mi tabla del §1.2).

**Corroboración del Auditor (verificada por mí):** el v4.1 trae total_bytes "62985968" en la respuesta de búsqueda — el ZIP local v4.1 mide **62,985,968 B** (verificado por mí con `stat`). El campo total_bytes sí refleja el tamaño del archivo subido, lo que refuerza la verificación de bytes del v5 (60,104,444 exacto).

**Selección final:** las 2 mejores por score público son v4.1 (3.54317) y swap42 (3.53019), consistente con lo que confirmó Elán. Verificado por el Auditor (y por mí en §2): ninguna de las 10 respuestas trae un campo de selección/final — el marcado descansa en la palabra de Elán. No se toca la selección.

**Cadena COMPLETA: Programación ✓ → Datos ✓ → Brujo ✓ → Auditor ✓ → Elán.** La subida del v5 está verificada en Kaggle; falta el score público — en calificación.
