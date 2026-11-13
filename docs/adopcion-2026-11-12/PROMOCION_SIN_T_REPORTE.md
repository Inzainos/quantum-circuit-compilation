# PROMOCIÓN DEL DQI SIN t A PRODUCCIÓN — REPORTE

**Fecha:** 2026-11-12 (16:47–~17:30 CST, America/Mexico_City)
**Decisión de Elán (2026-11-12 ~16:47, palabras exactas):** "Promovemos de inmediato dqi_sin_t.kmb (Q = 1,864, T = 786,272) a producción."
**Alcance:** integrar los 3 .py sin-t en GitHub, reconstruir el ZIP con dqi_sin_t.kmb, subirlo a Kaggle, publicar el notebook v3, actualizar los docs de estado. NO se marca la selección final (0 de 2, solo Elán). NO se abre la rama omega/Karatsuba (siguiente paso, otro agente). NO se toca main.
**Regla 0:** cada número viene de un log citado; lo no medido se dice, no se asume.

## VEREDICTO: LA PROMOCIÓN QUEDÓ — DQI SIN t ADOPTADO, EN KAGGLE Y EN EL NOTEBOOK v3

| Pieza | Estado | Verificación |
|---|---|---|
| 3 .py sin-t en GitHub | Commit `c0fb9a57…` en `fix/zip-final-2026-11-07` | 3/3 por blob SHA; pytest 34 passed con los módulos sin-t |
| ZIP nuevo | `valid_submission_fb4e95b.zip`, sha `ba222d1c…`, 66,288,156 B, 13 archivos | `testzip` None; 12/12 miembros idénticos al ZIP anterior salvo dqi.kmb (sin-t, sha `8dd3e6a3…`) |
| Kaggle | Ref **58286822**, 2026-11-12T22:52:49Z, 66,288,156 B | **PUNTUADO: 3.41660, status COMPLETE** (~40 min; ver §3) |
| Notebook público | **v3, PUBLICADO**, URL https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation | Ejecución COMPLETE, 42 entradas, 0 Traceback (ver §4) |
| Docs en GitHub | 3 archivos en `fix/zip-final-2026-11-07` (ver §5) | Verificados por blob SHA (ver §5) |

**Geomean calculado: 3.40990x** (DQI ratio 7.38175x; invsqrt 5.30907; dfthcsos 1.01169; producto 39.64834). **Geomean medido en Kaggle: 3.41660** (ref 58286822, status COMPLETE) — nuevo personal best (antes 3.33544, +0.08116, +2.43%); el calculado quedó 0.0067 abajo del medido (+0.20%, mismo patrón que la subida anterior: referencias exactas de Kaggle vs redondeadas).

## 1. GitHub — los 3 .py sin-t integrados (commit c0fb9a57)

Procedimiento: `SUBIR_PY_REPORTE.md` + `references/snapshot-push.md` (push_files del conector, rama `fix/zip-final-2026-11-07`, NUNCA main; `get_file_contents` con `ref`, NO `branch`; verificación por blob SHA).

- Head remoto antes del push (verificado por `git ls-remote`): `fcc7d9c976e625004b6d5e80fb9dbb6d7d4d6847` — sin divergencia. Conector GitHub: `status` = connected, `authenticated: true`, `push_files` disponible.
- Base de sincronización verificada ANTES del push (los 3 paths ya existían en el remoto, sin divergencia):
  - `src/dqi_bm_stage_v1.py` remoto `049df911…` = versión del clon (a40a82f).
  - `src/bm_fused.py` remoto `a4967cc7…` = versión fcc7d9c.
  - `src/bm_fused_e1d.py` remoto `e8d0b60f…` = versión fcc7d9c.
- Archivos pusheados (byte por byte, sin reescribir; 20,302 B total):

| Archivo en el repo | Tamaño | Blob SHA | Origen | Qué cambia vs la versión anterior |
|---|---|---|---|---|
| `src/dqi_bm_stage_v1.py` | 14,207 B | `cd433e16…` | `dqi-perfil/rama_t_eliminada/dqi_bm_stage_v1.py` | `_flags` sin t (solo p); `_t_recon` + `_t_recon_del` nuevos (9 T, 11 ancillas); `_dclear` sin t (control = w reconstruido); `forward_round`/`reverse_round` con solo p |
| `src/bm_fused.py` | 4,209 B | `d94968c1…` | `dqi-perfil/rama_t_eliminada/bm_fused.py` | `forward_round`/`reverse_round` con solo p; insert scratch-first (`__file__`) |
| `src/bm_fused_e1d.py` | 1,886 B | `42d24321…` | `dqi-perfil/rama_t_eliminada/bm_fused_e1d.py` | `_dclear` sin t con la torre ORIGINAL (E1d solo vive en alpha); insert scratch-first |

- **Verificación byte por byte / por blob SHA: 3/3 OK** (log `verificar_sin_t.log`): el blob SHA local (`git hash-object` del staging) coincide con el SHA remoto (`get_file_contents` con `ref: refs/heads/fix/zip-final-2026-11-07`) en los 3 archivos.
- **Commit nuevo:** `c0fb9a57e6d99977fb102676343dc7c05139c851` — "dqi: eliminar bandera t (Q 1,934->1,864, T 786,272, Gold PASS 102,400 tiros; geomean calculado 3.40990x)". Head confirmado por `git ls-remote` después del push. URL: https://github.com/Inzainos/quantum-circuit-compilation/commit/c0fb9a57e6d99977fb102676343dc7c05139c851
- Registro de sincronización actualizado: `staging.muse-github-snapshot-sync.json` (3 entradas: `cc79814` + `fcc7d9c` + `c0fb9a57`).
- **pytest tests/ (AGENTS.md regla 5): 34 passed en 4.27 s** con los módulos sin-t haciendo sombra a `src/` (PYTHONPATH = rama_t_eliminada : clon/src : kickmix). Ningún test importa `dqi_bm_stage_v1` ni `bm_fused` (verificado por grep); la verificación cerrada del cambio es el simulador n=6 (6 semillas) + el Gold oficial a 102,400 tiros (PASS, §0 del reporte de la rama).
- Advertencia (igual que en el push anterior, no reescrita): `bm_fused.py` y `bm_fused_e1d.py` llevan `sys.path` absolutos de esta máquina; el insert scratch-first (`__file__`) es relativo y en el repo apunta a `src/` (inocuo). kickmix sigue sin estar en el repo (solo `LICENSE.txt`).

## 2. ZIP reconstruido con dqi_sin_t.kmb (sha ba222d1c…)

Procedimiento: `ADOPCION_REPORTE.md` + `submission/build_submission.py` (el mismo script de la adopción), sustituyendo `dqi.kmb` por `dqi_sin_t.kmb`. Las demás piezas son las mismas del ZIP adoptado, verificadas por sha256 contra los miembros del ZIP actual antes de construir.

- **Backup del ZIP adoptado anterior:** `adopcion-sin-t/backup/valid_submission_fb4e95b.zip.OLD` — sha `171d5a81c4ca47b17573d4876acb3b63386b7048a5f7b1f77fae4e4a60a7f87e` (66,225,789 B, verificado idéntico al ZIP en entrega antes del reemplazo). El `.kmb` adoptado viejo (`dqi_fusionado_e1d.kmb`, sha `16e06d61…`) queda intacto como respaldo en `dqi-perfil/verificacion_e1d/`.
- Piezas (log `miembros_zip_actual.log` + `verificar_zip.log`):
  - invsqrt logshift2: `7e842bbf…faf79` (437,575 B) — IGUAL que el ZIP anterior.
  - dqi sin-t: `8dd3e6a30aa0f87f71249aa5ec2b465e1e9817172aee1fb3120ccdc2bb3aa6bf` (624,960,230 B) — CAMBIO (antes E1d `16e06d61…`, 624,877,910 B).
  - dfthcsos lbfgs: 10 angle_k_*.kmx (shas `adf19022…`, `6104ef8f…`, etc.) + npz `d89772be…7fa4d` — IGUALES.
- **Verificación del ZIP nuevo:** `testzip` = None (íntegro), 13 archivos, **12/12 miembros idénticos al ZIP anterior salvo dqi.kmb** (el cambio esperado).
- **ZIP nuevo en entrega:** `~/workspace/qcc-data/valid_submission_fb4e95b.zip` — sha256 `ba222d1c130acec71406b1b5473e78140ce87f4af8041db5907dc4ff8b9e0703`, 66,288,156 B (63.2 MB), re-verificado en su ubicación final (log `verificar_final.log`): mismo sha, testzip None, 13 archivos, dqi.kmb dentro es el sin-t.
- **Geomean calculado** (mismas referencias que la adopción): invsqrt 5.30907; DQI 6.86807 × (1934/1864)² × (785012/786272) = **7.38175**; dfthcsos 1.01169; producto 39.64834 → **3.40990x** (+0.0810x vs 3.32890x). Escalando el medido en Kaggle anterior (3.33544x): **3.41660x** esperado.

## 3. Kaggle — envío ref 58286822, PUNTUADO 3.41660

Procedimiento: `SUBIDA_KAGGLE_REPORTE.md` + scripts `kaggle-subida/submit_competition.py` y `poll_score_sin_t.py` (copia de `poll_score.py` con el ref nuevo).

- Acceso probado con `get_user_profile` (misma cuenta que el envío anterior): `elnzainoscorona`, user_id 34340170.
- El archivo se copió a `submission.zip` en el scratch (mismos bytes, sha `ba222d1c…` verificado) — el nombre es obligatorio para esta competición (el primer intento de la subida anterior falló por eso).
- **Envío registrado: ref 58286822, 2026-11-12T22:52:49.910Z, 66,288,156 B, file_name `submission.zip`, submitted_by `elnzainoscorona`, team_name `Frantal Core`** (confirmado por `get_competition_submission`, log `get_sub_sin_t.log`). Descripción: "Adopted v2: logshift2 invsqrt (Q=139) + DQI without t (Q=1864, T=786272) + lbfgs dfthcsos; calc geomean 3.40990x; DQI gold-verified 102400 shots PASS (2 value errors, 0 phase)".
- Poller: `poll_score_sin_t.py` (chequeo cada 300 s, máx 20 polls ~100 min; log `poll_sin_t.log`). Poll 1 (22:53:01Z) → poll 8 (23:28:14Z): pending; **poll 9 (23:33:16Z): SCORED public_score=3.41660 status=COMPLETE** (log `poll_sin_t.log`, `score_sin_t.json`).
- **Geomean medido: 3.41660** (confirmado por lectura independiente con `get_competition_submission`, log `get_sub_sin_t_final.log`: ref 58286822, total_bytes 66288156, status COMPLETE, public_score 3.41660). **Nuevo personal best** (antes 3.33544, ref 58277509): +0.08116 (+2.43%). Calculado 3.40990x → medido 3.41660 (+0.0067, +0.20%).
- **Scoring: ~40 min** (subida 22:52:49Z → puntaje 23:33:16Z). **Rank: 2538 de 2936 equipos** (`get_competition`: user_rank 2538, team_count 2936; el conteo subió de 2917 a 2936 — entraron más equipos).

## 4. Notebook público v3 — PUBLICADO, versión 3, ejecución COMPLETE 0 errores

Procedimiento: `PUBLICAR_NOTEBOOK_REPORTE.md`. Generador: `notebook/build_notebook_v3.py` (transformación verificada de `build_notebook.py`: 34 sustituciones exactas, cada una ocurre exactamente 1 vez, log `transformar_v3.log`).

- Cambios vs v2: DQI Q=1,864, T=786,272; geomean calculado 3.40990x; Gold PASS a 102,400 tiros (2 value, 0 phase, eps_plus 0.000949, R 1.2014) para el DQI sin t y para el E1d; la sección §2.2 reescrita (el "gold-standard NOT run" ya no es cierto); §4 ZIP con el sha nuevo `ba222d1c…`; §5 con el medido en Kaggle (3.41660, ref 58286822); §8 con la palanca omega/Karatsuba como siguiente paso; el "DRAFT" de la honesty box corregido (el notebook está publicado desde v2).
- El borrador v2 quedó respaldado como `notebook/qcc_submission_logshift2_fused_dqi_lbfgs_v2.ipynb` (sha `ad0033be…`).
- Ejecución local (nbconvert, kernel py313): **0 errores**. Salidas verificadas: §0 geomean 3.40990x (DQI ratio 7.38175; composición anterior 3.32890x; mejora +0.0810x); §2 cadena DQI completa (baseline 6.77000 → F1b 6.85414 → E1d 6.86807 → sin-t 7.38175); §4 ZIP sha match True (`ba222d1c…`).
- Quedan solo referencias históricas a 1,934 / 785,012 / `171d5a81` / `16e06d61` (tabla ladder, build anterior, backup) — verificado por grep, ninguna como número vigente.
- Publicación (copia con kernelspec `python3`, NO `py313`; título ≤50 caracteres: "Verifiable Quantum Circuit Compilation"): `save_notebook` con id 144639626 + slug (log `save_notebook_v3.log`, EXIT=0, `isError: false`) → **versión 3**, misma URL, mismo kernel ID. Copia de publicación sha256 `84d0cfed4e48be5da130d185e7bb13eeeaa58af3a200ef17e011c0e616a8a21c`; diff verificado: celdas idénticas, metadata idéntica salvo kernelspec, nbformat idéntico.
- Verificación: `get_notebook_info` (v3, `is_private: false` **PÚBLICO**, title "Verifiable Quantum Circuit Compilation"; el blob publicado trae kernelspec `python3`, 17 celdas, título sin-t, 3.41660 ×5, 1,864 ×13, `ba222d1c` ×4). `get_notebook_session_status`: **COMPLETE**. `list_notebook_session_output`: **42 entradas, 0 con Traceback**; las salidas coinciden con los números documentados (geomean 3.40990x calculado, DQI ratio 7.38175, composición anterior 3.32890x, mejora +0.0810x, t elim. Q=1864 T=786272 ratio 7.38175, ZIP sha `ba222d1c…` en la rama defensiva — el ZIP no está adjunto como dataset, como fue diseñado).
- Nota: el primer intento de `get_notebook_info` con id+slug devolvió `Permission 'kernels.get' was denied`; con la forma usada en v2 (userName + kernelSlug) funcionó. La v1/v2 usaron esa forma.

## 5. GitHub — docs de estado

- 3 archivos pusheados a la rama `fix/zip-final-2026-11-07` (mismo procedimiento del §1; verificación por blob SHA; log `push_docs_sin_t.log`):
  - `docs/adopcion-2026-11-12/PROMOCION_SIN_T_REPORTE.md` — copia de este reporte (sin el SHA de este commit, que no existe antes del push).
  - `docs/adopcion-2026-11-12/ESTADO_ADOPCION_SIN_T_2026-11-12.md` — estado de la entrega adoptada v2.
  - `scripts/build_notebook_v3.py` — generador del notebook v3 (34 sustituciones exactas verificadas).
- El SHA del commit de este push quedó registrado en el log `push_docs_sin_t.log`, en `verificar_docs_sin_t.log` y en el registro de sincronización (`staging.muse-github-snapshot-sync.json`, 4ª entrada).

## 6. Lo que NO se hizo

- **NO se marcó la selección final en Kaggle (0 de 2).** Solo Elán puede hacerlo, a mano en su cuenta. El envío a marcar es el ref **58286822 (3.41660)**. Antes tenía marcado el 3.31949 (ref 58113636); confirmar cuáles quedan seleccionados y marcar el nuevo antes del cierre.
- NO se tocó main (no existe rama main visible; el trabajo es todo en `fix/zip-final-2026-11-07`).
- NO se tocó `final_submission.zip` (2c3018f8) ni `integracion/submission.zip` (ce1d12a6) — siguen con el BM v7 Q=2,016; Elán decide si se actualizan con el DQI sin-t.
- NO se abrió la rama omega/Karatsuba — siguiente paso, otro agente, después de asegurar esto en Kaggle.
- NO se pusheó el ZIP (63 MB) ni el .kmb (596 MB) a GitHub por el conector (solo texto ≤16 MiB); el ZIP va por push git desde la máquina de Elán o por Release, como en el reporte de adopción.

## 7. Archivos

Scratch: `~/workspace/qcc-data/adopcion-sin-t/`
- `PROMOCION_SIN_T_REPORTE.md` — este reporte.
- `backup/valid_submission_fb4e95b.zip.OLD` — backup del ZIP adoptado anterior (sha `171d5a81…`).
- `nueva_entrega/` — piezas del ZIP nuevo (invsqrt logshift2, dqi sin-t, dfthcsos lbfgs).
- `nuevo_zip/submission_sin_t_2026-11-12.zip` — el ZIP construido (sha `ba222d1c…`, idéntico al de la entrega).
- `construir_zip.log`, `miembros_zip_actual.log`, `verificar_zip.log`, `verificar_final.log` — logs de construcción y verificación del ZIP.
- `transformar_notebook_v3.py`, `transformar_v3.log`, `medida_kaggle.json` — transformación del notebook v3.
- `NOTEBOOK_V3_EJECUCION` — ejecución local del notebook v3 (log `notebook/ejecucion_v3.log`, 0 errores).

Scratch Kaggle: `~/workspace/qcc-data/kaggle-subida/`
- `submit_sin_t.log`, `submit_response.json` (ref 58286822), `get_sub_sin_t.log`, `poll_score_sin_t.py`, `poll_sin_t.log`, `poll_run_sin_t.log`, `score_sin_t.json` (cuando puntúe).
- Respaldos del envío anterior: `submit_response_58277509.json`, `score_58277509.json`, `search_final_58277509.json`, `poll.log_58277509.json`.

Scratch GitHub: `~/workspace/qcc-data/github/`
- `push_sin_t.log` (commit `c0fb9a57…`), `verificar_sin_t.py` / `verificar_sin_t.log` (3/3 OK), `paths-sin-t.txt`, `staging.muse-github-snapshot-sync.json` (3 entradas).
- `notebook/build_notebook_v3.py` — generador del notebook v3.
- `notebook/qcc_submission_logshift2_fused_dqi_lbfgs_v2.ipynb` — respaldo del borrador v2.
