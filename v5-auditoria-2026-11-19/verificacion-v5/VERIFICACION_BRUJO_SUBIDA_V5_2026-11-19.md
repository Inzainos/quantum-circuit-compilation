# Verificación del Brujo — Subida del ZIP v5 a Kaggle (ref 58594222)

**Fecha:** 2026-11-19 ~22:14 CST
**Veredicto: CONCURRO (PASA) — la subida está verificada en Kaggle.**

## Verificación directa en Kaggle (por mí, `get_competition_submission`, ref 58594222)

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

- **ref 58594222** — coincide con lo reportado por Programación ✓
- **total_bytes 60,104,444** — exacto al ZIP local (60,104,444 B, sha256 `d1392960…`) ✓
- **fecha 2026-11-20T04:12:53Z (22:12:53 CST)** — coincide ✓
- **descripción con geomean 4.89215** — corrección A-V5-1 aplicada ✓
- **file_name submission.zip, submitted_by elnzainoscorona, team Frantal Core** ✓
- **Sin public_score aún** — la respuesta no trae el campo; en calificación (Programación reporta lo mismo). El score se verifica cuando salga.

## Selección final

Elán confirmó en Programación (22:12): "Ya están marcados las últimas 2 mejores versiones". Por score público las 2 mejores son v4.1 (3.54317, ref 58579331) y swap42 (3.53019, ref 58570485); la selección anterior era Adopted v3 (3.42920) + v4 (3.42257). La API de Kaggle NO expone el indicador de selección (verificado por Programación: ni `search_competition_submissions` ni `get_competition_submission` traen el campo), así que el marcado mismo descansa en la palabra de Elán. **No se toca la selección.**

## Consecuencia

La subida del v5 está verificada en Kaggle (ref 58594222, bytes exactos, descripción con 4.89215). Falta el score público — en calificación. Cuando salga, se reporta a Elán.
