# PROMOCIÓN DEL DQI OMEGA/KARATSUBA A PRODUCCIÓN — REPORTE

**Fecha:** 2026-11-12/13 (18:11–~01:00 CST, America/Mexico_City)
**Decisión de Elán (2026-11-12 ~18:11, palabras exactas):** "promovemos de inmediato dqi_omega_karatsuba.kmb (Q = 1,864, T = 774,932) a producción y subimos a Kaggle."
**Orden final de despliegue (Elán, 4 pasos):** (1) integrar `dqi_decoder_v1.py` con ixor_kmul al repo junto con los archivos sin-t; (2) reconstruir submission.zip reemplazando dqi_sin_t.kmb por dqi_omega_karatsuba.kmb, subir a Kaggle y esperar el score oficial; (3) publicar el notebook v4 y actualizar main en GitHub con los tres circuitos definitivos; (4) Elán marca la selección final en Kaggle cuando se confirme el score — ESE PASO NO SE HACE AQUÍ (solo Elán, a mano).
**Descripción canónica (Elán, 2026-11-12 ~18:47, vía Coordinador) — VERBATIM:** "Adopted v3: logshift2 invsqrt (Q=139) + DQI omega/Karatsuba without t (Q=1864, T=774932) + lbfgs dfthcsos; calc geomean 3.42645x; DQI gold-verified 102400 shots PASS (2 value errors, 0 phase)"
**Alcance:** integrar el decoder omega en GitHub, reconstruir el ZIP con dqi_omega_karatsuba.kmb, subirlo a Kaggle, publicar el notebook v4, actualizar los docs de estado. NO se marca la selección final (0 de 2, solo Elán). NO se toca main sin verificar su estado primero. NO se tocan `final_submission.zip` ni `integracion/submission.zip`. NO se toca el scratch del motor clásico.
**Regla 0:** cada número viene de un log citado; lo no medido se dice, no se asume.

## VEREDICTO: LA PROMOCIÓN QUEDÓ — DQI OMEGA/KARATSUBA ADOPTADO, EN KAGGLE Y EN EL NOTEBOOK v4

| Pieza | Estado | Verificación |
|---|---|---|
| `dqi_decoder_v1.py` omega en GitHub | Commit `4d1ba483…` en `fix/zip-final-2026-11-07` | 1/1 por blob SHA; pytest 34 passed (ver §1) |
| ZIP nuevo | `valid_submission_fb4e95b.zip`, sha `83b0c756…`, 66,674,933 B, 13 archivos | `testzip` None; 12/12 miembros idénticos al ZIP anterior salvo dqi.kmb (omega, sha `209d53e2…`) (ver §2) |
| Kaggle | Ref **58289295**, 2026-11-13T00:17:18Z, 66,674,933 B | **PUNTUADO: 3.42920, status COMPLETE** (~30 min; ver §3) |
| Notebook público | **v4, PUBLICADO**, URL https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation | Ejecución COMPLETE, 42 entradas, 0 Traceback (ver §4) |
| Docs en GitHub | 3 archivos en `fix/zip-final-2026-11-07` (ver §5) | Verificados por blob SHA (ver §5) |
| Main | **NO actualizada por el conector** — el repo NO tiene rama `main` | Merge probado en local: LIMPIO, 40 archivos, +4,693/−18; pasos exactos para Elán (ver §6) |

**Geomean calculado: 3.42645x** (DQI ratio 7.48977x; invsqrt 5.30907; dfthcsos 1.01169; producto 40.22853). **Geomean medido en Kaggle: 3.42920** (ref 58289295, status COMPLETE) — nuevo personal best (antes 3.41660, +0.01260, +0.37%); el calculado quedó 0.00275 abajo del medido (+0.08%, mismo patrón que las subidas anteriores: referencias exactas de Kaggle vs redondeadas). El escalado previo (~3.43319×) era una estimación aritmética, no una medición; el medido quedó 0.00399 por debajo de esa estimación.

## 1. GitHub — `dqi_decoder_v1.py` omega integrado (commit 4d1ba483)

Procedimiento: `SUBIR_PY_REPORTE.md` + `references/snapshot-push.md` (push_files del conector, rama `fix/zip-final-2026-11-07`, NUNCA main; `get_file_contents` con `ref`, NO `branch`; verificación por blob SHA).

- Head remoto antes del push (verificado por `git ls-remote`): `ad809537a0fb9667d5d7547978a6f3eaa65def2c` — sin divergencia. Conector GitHub: `status` = connected, `authenticated: true`, `push_files` disponible.
- Base de sincronización verificada ANTES del push: `src/dqi_decoder_v1.py` remoto `410eaecb…` = versión del clon (a40a82f), sin divergencia. El archivo omega (8,912 B, UTF-8 válido) difiere del clon solo en el cambio omega: import `from dqi_kmul import ixor_kmul` + 4 sitios de llamada en `build_omega_tmp` (diff verificado). `dqi_kmul.py` YA está en el repo (remoto `bd1738b8…`, trackeado en el clon) — el import del decoder resuelve dentro del repo.
- Archivo pusheado (byte por byte, sin reescribir):

| Archivo en el repo | Tamaño | Blob SHA | Origen | Qué cambia vs la versión anterior |
|---|---|---|---|---|
| `src/dqi_decoder_v1.py` | 8,912 B | `839f4bce…` | `dqi-perfil/omega_karatsuba/dqi_decoder_v1.py` | `build_omega_tmp` usa `ixor_kmul` (Karatsuba 54 T) en lugar del constructor `ixor_gf2_mul` (63 T) en 630 gf_mul/dirección; los 2 `del_gf2_mul` quedan intactos (0 T) |

- **Verificación byte por byte / por blob SHA: 1/1 OK** (log `verificar_omega.log`): el blob SHA local (`git hash-object` del staging) coincide con el SHA remoto (`get_file_contents` con `ref: refs/heads/fix/zip-final-2026-11-07`).
- **Commit nuevo:** `4d1ba4839d45a1245ec64397e17e4ae2bf7fd2c0` — "dqi: Karatsuba en build_omega_tmp (Q 1,864 intacto, T 774,932, Gold PASS 102,400 tiros; geomean calculado 3.42645x)". Head confirmado por `git ls-remote` después del push y por `git fetch` + `git show` en el clon (el archivo en ese commit hashea `839f4bce…`; el commit toca 1 archivo, 7 inserciones, 4 borrados). URL: https://github.com/Inzainos/quantum-circuit-compilation/commit/4d1ba4839d45a1245ec64397e17e4ae2bf7fd2c0
- Registro de sincronización actualizado: `staging.muse-github-snapshot-sync.json` (5 entradas: `cc79814` + `fcc7d9c` + `c0fb9a57` + `ad809537` + `4d1ba483`).
- **pytest tests/ (AGENTS.md regla 5): 34 passed en 4.48 s** con los módulos omega haciendo sombra a `src/` (PYTHONPATH = omega_karatsuba : clon/src : kickmix). Ningún test importa `dqi_decoder_v1` (verificado por grep); la verificación cerrada del cambio es el mini-omega (hash vivo idéntico, fase 0) + el Gold oficial a 102,400 tiros (PASS, §0 del reporte de la rama).
- Advertencia (igual que en los pushes anteriores, no reescrita): los .py llevan `sys.path` absolutos de esta máquina; kickmix sigue sin estar en el repo (solo `LICENSE.txt`).

## 2. ZIP reconstruido con dqi_omega_karatsuba.kmb (sha 83b0c756…)

Procedimiento: `ADOPCION_REPORTE.md` + `submission/build_submission.py` (el script del clon, `~/workspace/qcc-dqi/submission/build_submission.py`; verificado idéntico al de `entrega-2026-11-04/qcc-local/submission/`), sustituyendo `dqi.kmb` por `dqi_omega_karatsuba.kmb`. Las demás piezas son las mismas del ZIP adoptado, verificadas por sha256 contra los miembros del ZIP actual antes de construir.

- **Backup del ZIP adoptado anterior:** `adopcion-omega/backup/valid_submission_fb4e95b.zip.OLD` — sha `ba222d1c130acec71406b1b5473e78140ce87f4af8041db5907dc4ff8b9e0703` (66,288,156 B, verificado idéntico al ZIP en entrega antes del reemplazo). El `.kmb` adoptado viejo (`dqi_sin_t.kmb`, sha `8dd3e6a3…`) queda intacto como respaldo en `dqi-perfil/rama_t_eliminada/`.
- Piezas (log `verificar_zip.log`):
  - invsqrt logshift2: `7e842bbf…faf79` (437,575 B) — IGUAL que el ZIP anterior.
  - dqi omega: `209d53e2da4e815797a8f420fd91372f84c256ad9a2374f67dbbbcb0a1a5c884` (629,623,070 B) — CAMBIO (antes sin-t `8dd3e6a3…`, 624,960,230 B).
  - dfthcsos lbfgs: 10 angle_k_*.kmx (shas `adf19022…`, `6104ef8f…`, etc.) + npz `d89772be…7fa4d` — IGUALES.
- **Verificación del ZIP nuevo:** `testzip` = None (íntegro), 13 archivos, **12/12 miembros idénticos al ZIP anterior salvo dqi.kmb** (el cambio esperado).
- **ZIP nuevo en entrega:** `~/workspace/qcc-data/valid_submission_fb4e95b.zip` — sha256 `83b0c75615274769a36d3822da2f8f5c63470dc59f6820bee516a0952c7b1c4d`, 66,674,933 B (63.6 MB), re-verificado en su ubicación final (log `verificar_final.log`): mismo sha, testzip None, 13 archivos, dqi.kmb dentro es el omega.
- **Geomean calculado** (mismas referencias que la adopción): invsqrt 5.30907; DQI 6.77 × (1949/1864)² × (784172/774932) = **7.48977**; dfthcsos 1.01169; producto 40.22853 → **3.42645x** (+0.01655x vs 3.40990x). Escalando el medido en Kaggle anterior (3.41660x): **~3.43319x** esperado (estimación).

## 3. Kaggle — envío ref 58289295, PUNTUADO 3.42920

Procedimiento: `SUBIDA_KAGGLE_REPORTE.md` + scripts `kaggle-subida/submit_competition.py` y `poll_score_omega.py` (copia de `poll_score_sin_t.py` con el ref nuevo).

- Acceso probado con `get_user_profile` (misma cuenta que el envío anterior): `elnzainoscorona`, user_id 34340170, Elán Zainos Corona.
- El archivo se copió a `submission.zip` en el scratch (mismos bytes, sha `83b0c756…` verificado) — el nombre es obligatorio para esta competición.
- **Envío registrado: ref 58289295, 2026-11-13T00:17:18.593Z, 66,674,933 B, file_name `submission.zip`, submitted_by `elnzainoscorona`, team_name `Frantal Core`** (confirmado por `get_competition_submission`, log `get_sub_omega.log`). Descripción: "Adopted v3: logshift2 invsqrt (Q=139) + DQI omega/Karatsuba without t (Q=1864, T=774932) + lbfgs dfthcsos; calc geomean 3.42645x; DQI gold-verified 102400 shots PASS (2 value errors, 0 phase)" — **idéntica, carácter por carácter, a la descripción canónica de Elán** (verificado por comparación programática contra `get_sub_omega_final.log`).
- Poller: `poll_score_omega.py` (chequeo cada 300 s, máx 20 polls ~100 min; log `poll_omega.log`). Poll 1 (00:17:30Z) → poll 6 (00:42:40Z): pending; **poll 7 (00:47:43Z): SCORED public_score=3.42920 status=COMPLETE** (log `poll_omega.log`, `score_omega.json`).
- **Geomean medido: 3.42920** (confirmado por lectura independiente con `get_competition_submission`, log `get_sub_omega_final.log`: ref 58289295, total_bytes 66674933, status COMPLETE, public_score 3.42920). **Nuevo personal best** (antes 3.41660, ref 58286822): +0.01260 (+0.37%). Calculado 3.42645x → medido 3.42920 (+0.00275, +0.08%).
- **Scoring: ~30 min** (subida 00:17:18Z → puntaje 00:47:43Z). **Rank: 2,545 de 2,940 equipos** (`get_competition`: user_rank 2545, team_count 2940; antes 2,538/2,936 — entraron 4 equipos más).

## 4. Notebook público v4 — PUBLICADO, versión 4, ejecución COMPLETE 0 errores

Procedimiento: `PUBLICAR_NOTEBOOK_REPORTE.md`. Generador: `notebook/build_notebook_v4.py` (transformación verificada de `build_notebook_v3.py`: 36 sustituciones exactas, cada una ocurre exactamente 1 vez, log `transformar_v4.log`).

- Cambios vs v3: DQI T = 774,932 (Q = 1,864 igual), geomean calculado 3.42645x, DQI ratio 7.48977x; párrafo omega/Karatsuba nuevo en §2.1 (conteo 630/dirección, mini-omega, Gold); ladder con la fila omega como adoptada; §2.2 Gold omega (2 value, 0 phase, eps_plus 0.000949, R 1.2014; DQI score 3,234,735,110,839; ratio 7.38175 → 7.48977); §4 ZIP con el sha nuevo `83b0c756…`; §5 con el medido en Kaggle (3.42920, ref 58289295); §8 con omega marcado DONE y el siguiente lever (<54-AND, no medido); **descripción canónica Adopted v3 incluida VERBATIM en la portada** (instrucción de Elán 2026-11-12 ~18:47); pie actualizado a versión 4.
- El borrador v3 quedó respaldado como `notebook/qcc_submission_logshift2_fused_dqi_lbfgs_v3.ipynb` (sha `b624155a…`).
- Ejecución local (nbconvert, kernel py313): **0 errores**, 17 celdas. Salidas verificadas: §0 geomean 3.42645x (DQI ratio 7.48977; composición anterior 3.40990x; mejora +0.0166x); §2 cadena DQI completa (baseline 6.77000 → F1b 6.85414 → E1d 6.86807 → t elim. + omega 7.48977); §4 ZIP sha match True (`83b0c756…`).
- Quedan solo referencias históricas a 786,272 / 3.4099 / `ba222d1c` / `58286822` / `3.41660` / `8dd3e6a3` (ladder previa, backup, previous best, build anterior) — verificado por grep, ninguna como número vigente.
- Publicación (copia con kernelspec `python3`, NO `py313`; título ≤50 caracteres: "Verifiable Quantum Circuit Compilation"): `save_notebook` con id 144639626 + slug (log `save_notebook_v4.log`, EXIT=0, `isError: false`) → **versión 4**, misma URL, mismo kernel ID. Copia de publicación sha256 `2637c7c2dd823a290b72b3a59ed12b0f5c6bb7045f23d135ebd185d14cfe3aae`; diff verificado: celdas idénticas, metadata idéntica salvo kernelspec, nbformat idéntico. (Nota: el primer intento de `save_notebook` falló solo por una ruta de archivo de argumentos inexistente — error local `No such file or directory`, sin envío; el reintento con la ruta correcta tuvo éxito.)
- Verificación: `get_notebook_info` (v4, `is_private: false` **PÚBLICO**, title "Verifiable Quantum Circuit Compilation"; el blob publicado trae kernelspec `python3`, 17 celdas, descripción canónica ×1, 3.42920 ×5, 774,932 ×10, `83b0c756` ×3). `get_notebook_session_status`: **COMPLETE**. `list_notebook_session_output`: **42 entradas, 0 con Traceback**; las salidas coinciden con los números documentados (geomean 3.42645x calculado, DQI ratio 7.48977, cadena DQI, ZIP sha `83b0c756…` en la rama defensiva — el ZIP no está adjunto como dataset, como fue diseñado). (Nota: las primeras lecturas de `list_notebook_session_output` reportaron 0 entradas por un error de parsing propio — la respuesta trae las entradas bajo la clave `log`, no `entries`; con el parser corregido son 42, igual que en v3.)

## 5. GitHub — docs de estado

- 3 archivos pusheados a la rama `fix/zip-final-2026-11-07` (mismo procedimiento del §1; verificación por blob SHA; log `push_docs_omega.log`):
  - `docs/adopcion-2026-11-12/PROMOCION_OMEGA_REPORTE.md` — copia de este reporte (sin el SHA de este commit, que no existe antes del push).
  - `docs/adopcion-2026-11-12/ESTADO_ADOPCION_OMEGA_2026-11-12.md` — estado de la entrega adoptada v3 (incluye la descripción canónica verbatim).
  - `scripts/build_notebook_v4.py` — generador del notebook v4 (36 sustituciones exactas verificadas).
- El SHA del commit de este push quedó registrado en el log `push_docs_omega.log`, en `verificar_docs_omega.log` y en el registro de sincronización (`staging.muse-github-snapshot-sync.json`, 6ª entrada).
- **Commit de este push (añadido tras el push): `PENDIENTE_SHA_DOCS`** — "docs: promocion DQI omega/Karatsuba a produccion (Kaggle 3.42920, ref 58289295; notebook v4; geomean calculado 3.42645x)". Verificado 3/3 por blob SHA. (La copia de este reporte pusheada en ese mismo commit no incluye esta línea, porque el SHA no existe antes del push.)

## 6. Main en GitHub — estado exacto y pasos para Elán

**El repo NO tiene ninguna rama llamada `main`.** Verificado por `git ls-remote`:
- `refs/heads/main` — NO EXISTE.
- La rama por defecto (HEAD simbólico) es **`main/quantum-circuit-compilation-v0.1.0`**, en `3dc0c58c5aa303ec8319433aded257aa757d14db` (Merge PR #28, docs V34 invsqrt).
- La rama de trabajo `fix/zip-final-2026-11-07` está en `4d1ba483…` (este push). Su merge-base con la rama por defecto es `a40a82f`: la rama fix se bifurcó de a40a82f y la rama por defecto avanzó con los PRs #27 y #28 (docs V34). Un merge es necesario (no es fast-forward) y **el conector push_files no puede hacerlo** (snapshot-only: escribe archivos, no hace merges, no trae historia). Por eso NO se forzó ninguna "actualización de main" desde el conector — hacerlo habría creado un snapshot divergente, no un merge.

**Prueba de merge (solo local, sin tocar el remoto):** en un worktree temporal del clon, `git merge origin/fix/zip-final-2026-11-07` sobre `main/quantum-circuit-compilation-v0.1.0` terminó **LIMPIO, sin conflictos** (commit de prueba `c8d71e2`, solo local; worktree eliminado después): 40 archivos cambiados, +4,693/−18. El merge es seguro de hacer desde la máquina de Elán.

**Pasos exactos para Elán (desde su máquina, con el clon actualizado):**
```
git fetch origin
git checkout main/quantum-circuit-compilation-v0.1.0
git pull
git merge origin/fix/zip-final-2026-11-07 -m "merge: adopt omega/Karatsuba DQI (Q=1,864, T=774,932; Kaggle 3.42920, ref 58289295)"
git push origin main/quantum-circuit-compilation-v0.1.0
```
Alternativa (si prefiere una rama llamada `main` literalmente):
```
git fetch origin
git checkout -b main origin/fix/zip-final-2026-11-07
git push -u origin main
# y luego cambiar la rama por defecto a `main` en la configuración del repo en github.com
```

## 7. Lo que NO se hizo

- **NO se marcó la selección final en Kaggle (0 de 2).** Solo Elán puede hacerlo, a mano en su cuenta. El envío a marcar es el ref **58289295 (3.42920)**.
- NO se tocó main (no existe rama `main`; ver §6).
- NO se tocó `final_submission.zip` (2c3018f8) ni `integracion/submission.zip` (ce1d12a6) — siguen con el BM v7 Q=2,016; Elán decide si se actualizan con el DQI omega.
- NO se tocó el scratch del motor clásico (`dfthcsos-refit/motor_clasico/`) — corre en paralelo.
- NO se pusheó el ZIP (63.6 MB) ni el .kmb (596 MB) a GitHub por el conector (solo texto ≤16 MiB); el ZIP va por push git desde la máquina de Elán o por Release, como en el reporte de adopción.

## 8. Archivos

Scratch: `~/workspace/qcc-data/adopcion-omega/`
- `PROMOCION_OMEGA_REPORTE.md` — este reporte.
- `ESTADO_ADOPCION_OMEGA_2026-11-12.md` — estado de la entrega adoptada v3.
- `backup/valid_submission_fb4e95b.zip.OLD` — backup del ZIP adoptado anterior (sha `ba222d1c…`).
- `nueva_entrega/` — piezas del ZIP nuevo (invsqrt logshift2, dqi omega, dfthcsos lbfgs).
- `nuevo_zip/submission_omega_2026-11-12.zip` — el ZIP construido (sha `83b0c756…`, idéntico al de la entrega).
- `construir_zip.log`, `verificar_zip.log`, `verificar_final.log` — logs de construcción y verificación del ZIP.
- `push_omega.log` / `push_omega.err`, `verificar_omega.py` / `verificar_omega.log` — push del decoder + verificación blob SHA.
- `transformar_notebook_v4.py`, `transformar_v4.log`, `medida_kaggle_omega.json` — transformación del notebook v4.
- `NOTEBOOK_V4_EJECUCION.ipynb` + `ejecucion_v4.log` / `ejecucion_v4_final.log` — ejecución local del notebook v4 (0 errores).
- `publicar_v4.log` — copia de publicación (kernelspec python3) y su verificación por diff.
- `submit_omega.log` / `submit_omega.err`, `get_sub_omega.log`, `get_sub_omega_final.log`, `get_comp_omega.log` — envío y verificación en Kaggle.
- `poll_score_omega.py`, `poll_omega.log`, `poll_run_omega.log`, `score_omega.json` — sondeo del puntaje (poll 7: SCORED 3.42920).
- `merge_test.log` — prueba de merge local (limpio).

Scratch Kaggle: `~/workspace/qcc-data/kaggle-subida/`
- `submit_response.json` (ref 58289295), `submit_response_58286822.json` (respaldo del envío anterior), `score_omega.json`, `search_final_omega.json`, `poll_score_omega.py`, `poll_omega.log` (en adopcion-omega), `submission.zip` (sha `83b0c756…`).
- Respaldos de envíos anteriores: `submit_response_58277509.json`, `score_58277509.json`, `score_sin_t.json`, `search_final_sin_t.json`.

Scratch GitHub: `~/workspace/qcc-data/github/`
- `push_omega.log` (commit `4d1ba483…`), `verificar_omega.py` / `verificar_omega.log` (1/1 OK), `paths-omega.txt`, `staging.muse-github-snapshot-sync.json` (5 entradas; la 6ª tras el push de docs).
- `notebook/build_notebook_v4.py` — generador del notebook v4.
- `notebook/qcc_submission_logshift2_fused_dqi_lbfgs_v3.ipynb` — respaldo del borrador v3.

Scratch notebook: `~/workspace/qcc-data/kaggle-notebook/`
- `save_notebook_qcc_v4.json`, `save_notebook_v4.log` / `save_notebook_v4.err` — publicación v4 (versión 4).
- `qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` — copia de publicación v4 (sha `2637c7c2…`).
- `qcc_submission_logshift2_fused_dqi_lbfgs_v3.ipynb` — respaldo de la copia de publicación v3 (sha `84d0cfed…`).
- `get_notebook_info_v4.log`, `get_notebook_session_status_v4.log`, `list_notebook_session_output_v4.log` — verificación (v4, PÚBLICO, COMPLETE, 42 entradas, 0 Traceback).
