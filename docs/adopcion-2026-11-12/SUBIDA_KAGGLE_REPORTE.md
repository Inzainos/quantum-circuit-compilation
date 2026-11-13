# SUBIDA DEL ZIP ADOPTADO A KAGGLE — REPORTE

**Fecha:** 2026-11-12 (subida 15:34:22 UTC / 09:34:22 CST, America/Mexico_City)
**Orden de Elán (2026-11-12 ~09:31, palabras exactas, relayada por el Coordinador):** "Subanlo".
**Alcance:** SOLO subir el ZIP y reportar el geomean autoritativo cuando el scoring termine. NO se marca la selección final (0 de 2, solo Elán). NO se publica el notebook.
**Regla 0:** cada número viene de un log citado; lo no medido se dice, no se asume.

## VEREDICTO FINAL — PUNTAJE AUTORITATIVO MEDIDO: 3.33544 (nuevo personal best)

**El envío quedó registrado en Kaggle: ref 58277509, 2026-11-12T15:34:22.297Z, 66,225,789 B, file_name `submission.zip`, submitted_by `elnzainoscorona`, team_name `Frantal Core`.** **El scoring terminó: public_score = "3.33544", status = "COMPLETE"** (chequeo 7 del poller, 16:10:20Z; confirmado por lectura independiente con `get_competition_submission` a las 16:16:06Z: ref 58277509, public_score 3.33544, status COMPLETE). El scoring tomó ~36 min (subida 15:34:22Z → puntaje 16:10:20Z), no ~45 min.

**Comparación (medido):**
- **Nuevo personal best: 3.33544** (antes 3.31949, ref 58113636 "v8", 2026-11-08). Mejora +0.01595 (+0.48%).
- **Geomean calculado 3.3289x → medido 3.33544** (+0.0065, +0.20% arriba del calculado). La diferencia es por las referencias exactas de Kaggle (el cálculo usó los ratios documentados 6.77x / 1.00583x / 2,070,563, con redondeo).
- **Rank: 2520 de 2917 equipos** (`get_competition`: user_rank 2520, team_count 2917). Contexto del leaderboard público (top 10, medido 16:16:06Z): 1. Entangled Team 29.90871, 2. Schrödinger's cat lived 29.76123, 3. yicheng guang 29.02209, 4. taiseiu 28.68861, 5. Some Joint 28.65116, 6. yu4u 28.14827, 7. Breaking1800 27.99617, 8. CroDoc & Pavel 27.78422, 9. Diana 27.66022, 10. trust the transpiler 27.52478. Nuestro 3.33544 está lejos de los líderes (27–30x).

**La selección final (0 de 2) NO está marcada** (solo Elán puede hacerlo). El notebook NO se publicó en este trabajo.

## 1. El ZIP subido (verificado por sha256 antes de subir)

- Archivo: `~/workspace/qcc-data/valid_submission_fb4e95b.zip`
- sha256: `171d5a81c4ca47b17573d4876acb3b63386b7048a5f7b1f77fae4e4a60a7f87e` ✓ (medido por `sha256sum` antes de subir; coincide con el reporte de adopción)
- Tamaño: 66,225,789 B (63.2 MB), 13 archivos, íntegro (`testzip` None, adopción)
- Contenido: invsqrt logshift2 (Q=139, score 390,005.06) + DQI fusionado+E1d (Q=1,934, T=785,012, geomean 3.3259x) + dfthcsos lbfgs (score 3,336,160,975). Geomean calculado 3.3289x.
- DQI gold-verificado: PASA verificador oficial a 102,400 tiros, 2 errores de valor, 0 de fase, eps_plus 0.000949, R 1.2014.

## 2. Acceso y competición (verificados)

- Acceso probado con `get_user_profile`: user_id 34340170, display_name "Elán Zainos Corona", user_name `elnzainoscorona`, `can_edit` true. (Log: llamada MCP, 2026-11-12.)
- Competición verificada con `get_competition`: slug `google-verifiable-quantum-circuit-compilation`, título "Google Quantum AI - Verifiable Quantum Circuit Compilation", categoría Featured, deadline 2027-01-20T23:59:00Z. (Fuente del slug: `~/workspace/qcc-dqi/README.md` línea 233, citación oficial.)

## 3. Flujo de subida (primera vez por este conector)

- `submit_to_competition` sube por blob file tokens; el esquema se leyó con `list-tools` (76 tools). `start_competition_submission_upload` NO estaba en `ALLOWED_TOOLS` de `client.py` — se añadió después de leer su esquema de entrada (competitionName, hasCompetitionName, contentLength, lastModifiedEpochSeconds, fileName), como indica el conector.
- Script nuevo: `~/workspace/qcc-data/kaggle-subida/submit_competition.py` (modelo de `create_dataset_version.py`): pide sesión de subida → PUT de los bytes al GCS firmado → `submit_to_competition` con el token. Nunca imprime el token ni la URL firmada; el token se guarda 0600 en `blob_token_qcc.json`.
- **Primer intento FALLÓ (medido, no asumido):** `submit_to_competition` devolvió `isError: true` — "Submission not allowed: Submission files must be named \"submission.zip\" for this Competition." (Log: `submit.log`.) La sesión de subida se había creado con fileName `valid_submission_fb4e95b.zip`; ese token quedó inutilizable para esta competición.
- **Corrección:** se copió el ZIP (mismos bytes) a `submission.zip` en el scratch (sha256 verificado `171d5a81…` ✓) y se repitió el flujo con ese nombre.
- **Segundo intento: ÉXITO.** Upload HTTP 200 (66,225,789 B). `submit_to_competition` devolvió `{"message": "Successfully submitted to Google Quantum AI - Verifiable Quantum Circuit Compilation", "ref": 58277509}`. (Log: `submit2.log`; respuesta guardada en `submit_response.json`.)

## 4. Verificación del registro en Kaggle

- `get_competition_submission` (ref 58277509): ref 58277509, total_bytes "66225789", date "2026-11-12T15:34:22.297Z", description (la puesta en el envío), file_name "submission.zip", submitted_by "elnzainoscorona", team_name "Frantal Core", url "/submissions/58277509/58277509.raw". Sin `public_score` ni `status` todavía (scoring en curso).
- `search_competition_submissions` (Date, pageSize 10): el envío nuevo es el más reciente (ref 58277509, sin score). El mejor anterior es ref 58113636 ("v8", 2026-11-08T03:44:52Z): public_score "3.31949", status "COMPLETE" — coincide con el personal best documentado (3.31949). El campo del puntaje es `public_score` (string) y el estado es `status` ("COMPLETE" al terminar).

## 5. Scoring (terminado — puntaje medido 3.33544)

- Poller: `~/workspace/qcc-data/kaggle-subida/poll_score.py` (chequeo cada 300 s por `search_competition_submissions`, máx 20 polls ~100 min; log `poll.log`). Lanzado 15:35:18Z; primer intento falló por un bug (`AttributeError` al parsear la respuesta como lista — la respuesta es un dict con clave `submissions`), corregido y relanzado 15:35:59Z. Un reinicio del runtime mató el poller (~15:40Z); se relanzó 15:40:09Z. Chequeos: poll 1 (15:36:01Z) pending, poll 1 (15:40:11Z) pending, poll 2 (15:45:12Z) pending, poll 3 (15:50:14Z) pending, poll 4 (15:55:15Z) pending, poll 5 (16:00:17Z) pending, poll 6 (16:05:19Z) pending, **poll 7 (16:10:20Z): SCORED public_score=3.33544 status=COMPLETE**. El poller terminó (exit 0) al encontrar el puntaje.
- Duración del scoring: subida 15:34:22Z → puntaje 16:10:20Z = ~36 min (la estimación de ~45 min era aproximada).
- Confirmación independiente: `get_competition_submission` (ref 58277509) a las 16:16:06Z: public_score 3.33544, status COMPLETE. `get_competition`: user_rank 2520, team_count 2917, user_has_entered True, max_daily_submissions 5.

## 6. Lo que NO se hizo

- NO se marcó la selección final (0 de 2, solo Elán).
- NO se publicó el notebook.
- NO se tocó main ni el ZIP (el ZIP de la entrega sigue en `~/workspace/qcc-data/valid_submission_fb4e95b.zip`, sha `171d5a81…`).

## 7. Archivos

Scratch: `~/workspace/qcc-data/kaggle-subida/`
- `SUBIDA_KAGGLE_REPORTE.md` — este reporte.
- `submit_competition.py` — script de subida (reutilizable).
- `submit.log`, `submit2.log` — logs de los dos intentos (el primero falló por el nombre del archivo; el segundo tuvo éxito).
- `submit_response.json` — respuesta de `submit_to_competition` (ref 58277509).
- `blob_token_qcc.json` — token del blob (0600, nunca impreso).
- `submission.zip` — copia del ZIP con el nombre requerido (mismos bytes, sha `171d5a81…`).
- `list_tools.json` — 76 tools del MCP server.
- `search1.json` — primer `search_competition_submissions` (el envío nuevo sin score; el mejor anterior 3.31949).
- `poll_score.py`, `poll.log`, `poll_run.log`, `poll_run2.log` — poller del scoring.
- `score.json`, `search_final.json` — se crean cuando salga el puntaje.
