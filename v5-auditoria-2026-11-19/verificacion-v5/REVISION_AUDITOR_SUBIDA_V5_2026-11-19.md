# REVISIÓN DEL AUDITOR — Subida del ZIP v5 a Kaggle (ref 58594222)

**Fecha:** 2026-11-19 ~22:15 CST
**Auditor:** Auditor Interno
**Documento revisado (Brujo):** `~/workspace/qcc-data/candidato-v5-2026-11-19/VERIFICACION_BRUJO_SUBIDA_V5_2026-11-19.md` (35 l. / md5 `9aed7f13…`, verificado en disco por mí)
**Documento revisado (Datos):** `SUPERVISION_DATOS_SUBIDA_V5_2026-11-19.md` (75 l. / md5 `1b57bdda…`, verificado en disco por mí)
**Cadena:** Programación (sube y reporta la ref) → Datos ✓ → Brujo ✓ → Auditor (este documento) → Elán.
**Veredicto: CONCURRO (PASA) — la subida está verificada en Kaggle.**

---

## 1. Verificación directa en Kaggle (por mí, con el conector, dos llamadas independientes)

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

- **ref 58594222** — coincide con lo reportado por Programación, Datos y el Brujo ✓
- **total_bytes "60104444"** — exacto al ZIP local (60,104,444 B, sha256 `d1392960…`, verificado por mí de nuevo: el archivo local sigue igual) ✓
- **fecha 2026-11-20T04:12:53.993Z = 2026-11-19 22:12:53 CST** — verificado por mí con `TZ='America/Mexico_City' date -d` ✓
- **descripción con geomean 4.89215** — corrección A-V5-1 aplicada ✓
- **file_name submission.zip, submitted_by elnzainoscorona, team "Frantal Core"** ✓
- **Sin public_score** — la respuesta no trae el campo (tampoco `status`); en calificación ✓

### 1.2 `search_competition_submissions` (10 más recientes, por fecha)

El v5 es la primera (la más reciente), con los mismos campos que en §1.1 — **tampoco trae public_score ni status** ✓. Las 9 siguientes, todas COMPLETE con public_score (verificadas por mí, idénticas a la tabla de Datos):

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

Corroboración adicional de que total_bytes es un chequeo de contenido fiable: el v4.1 trae total_bytes "62985968", que es el tamaño exacto del ZIP local v4.1 (62,985,968 B) que ya verifiqué en su momento.

## 2. Selección final — no verificable por API, descansa en la palabra de Elán

Elán confirmó en Programación (22:12): "Ya están marcados las últimas 2 mejores versiones". Por score público las 2 mejores son **v4.1 (3.54317, ref 58579331)** y **swap42 (3.53019, ref 58570485)** — consistente con su declaración (la selección anterior era Adopted v3 3.42920 + v4 3.42257, que ahora son 3ª y 4ª por score).

**Verificado por mí: ninguna de las 10 respuestas (ni `get_competition_submission` ni `search_competition_submissions`) trae un campo de selección/final.** Los campos presentes son ref, total_bytes, date, description, file_name, public_score (9 de 10), status (9 de 10), submitted_by, submitted_by_ref, team_name y url. La API de Kaggle NO expone el indicador de selección, así que el marcado mismo no es verificable por API y descansa en la palabra de Elán. **No se toca la selección** (solo Elán la marca).

Nota: Kaggle tampoco expone el hash del archivo subido, así que la verificación del contenido subido descansa en total_bytes (60,104,444 exacto) + descripción + fecha + ref. El ZIP local verificado es sha256 `d1392960…`.

## 3. Pendiente

**El score público del v5 aún no sale** — en calificación al momento de esta revisión (22:15 CST). Cuando salga, se verifica contra el esperado (geomean 4.89215; referencia v4.1 en Kaggle 3.54317) y se reporta a Elán. El subagente de subida aún no reporta su handoff (pendiente, según el Brujo); la ref la verificó Programación y la re-verifiqué yo directo en Kaggle con dos llamadas independientes.

## 4. Veredicto: CONCURRO (PASA)

La subida del v5 está verificada en Kaggle (ref 58594222, bytes exactos, descripción con 4.89215). Falta el score público — en calificación.

**Cadena: Programación ✓ → Datos ✓ → Brujo ✓ → Auditor ✓ (este documento) → Elán.**
