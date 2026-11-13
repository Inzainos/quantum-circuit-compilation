# PUBLICAR EL NOTEBOOK EN KAGGLE — REPORTE

**Fecha:** 2026-11-12 (11:52–12:00 CST aprox., America/Mexico_City)
**Decisión de Elán (2026-11-12 ~11:52, vía el widget, palabras exactas, relayada por el Coordinador):** "Sí, publiquen el notebook".
**Alcance:** SOLO publicar el notebook (y verificar que quedó publicado y que corre en Kaggle). NO se marca la selección final (0 de 2, solo Elán).
**Regla 0:** cada número viene de un log citado; lo no medido se dice, no se asume.

## VEREDICTO: EL NOTEBOOK QUEDÓ PUBLICADO EN KAGGLE (PÚBLICO) Y CORRE CON 0 ERRORES

- **URL pública:** https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation
- **Kernel ID:** 144639626
- **Ref / slug:** `elnzainoscorona/verifiable-quantum-circuit-compilation`
- **Título en Kaggle:** "Verifiable Quantum Circuit Compilation" (38 caracteres; ver §3 — el título del borrador excede el límite de 50)
- **Versión actual:** 2 (la v1 se publicó pero su ejecución falló por el kernelspec; la v2 corrige solo el kernelspec — ver §4)
- **Privacidad:** **PÚBLICA** (`is_private: false`, confirmado por `get_notebook_info` en v1 y v2)
- **Ejecución en Kaggle:** sesión **COMPLETE**, 0 errores, 40 entradas de log, 0 con Traceback/Error; las 5 celdas de código produjeron las salidas documentadas (ver §5)

## 1. Acceso probado

`get_user_profile` (log `get_user_profile` — llamada directa, sin archivo de log guardado): Elán Zainos Corona, user name `elnzainoscorona`, user id 34340170, `can_edit: true`. País México, región/ciudad Tlaxcala. `total_kernels: 1` antes de esta publicación (el notebook CASMI).

## 2. Revisión del notebook antes de publicar

Notebook: `~/workspace/qcc-data/notebook/qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` — 17 celdas (12 markdown, 5 código), sha256 `ad0033be84e0071acc08075ce2605de50b37c51e2c5d4dd44267ba52573b2b97`, 40,894 B.
Título en metadata: "Verifiable Quantum Circuit Compilation — logshift2 + fused DQI (Q=1,934) + lbfgs chemistry".
Kernelspec original: `{'display_name': 'Python 3.13 (py313)', 'language': 'python', 'name': 'py313'}` (local; ver §4 — es lo que rompió la v1).

Las 5 celdas de código revisadas (fuente leída completa):
- Celda 2 (§0 geomean): puro cálculo (`math`), sin rutas.
- Celda 4 (§1 invsqrt): puro cálculo, sin rutas.
- Celda 7 (§2 DQI): puro cálculo, sin rutas.
- Celda 10 (§3 dfthcsos): puro cálculo, sin rutas.
- Celda 12 (§4 ZIP): **defensiva** — prueba `/kaggle/input/qcc-submission/valid_submission_fb4e95b.zip` y `/home/hatch/workspace/qcc-data/valid_submission_fb4e95b.zip`; si ninguno existe imprime "Submission ZIP not attached in this environment." + el sha esperado + "Attach valid_submission_fb4e95b.zip as a dataset and re-run this cell." **No falla si el ZIP no está adjunto** (confirmado en la ejecución en Kaggle, §5).
- Ninguna celda depende de rutas locales de forma que rompa la ejecución. No se reescribió ninguna celda. No se cambió ningún número, ninguna atribución ni ninguna declaración.

## 3. Primer intento (v1) — el título excede el límite de Kaggle

`save_notebook` con `newTitle` = título de metadata (89 caracteres) devolvió `isError: true`: "The title cannot exceed 50 characters." (log `save_notebook.log`, EXIT=1).
Corrección: `newTitle` = "Verifiable Quantum Circuit Compilation" (38 caracteres) — el nombre de la competición. **Solo cambió el título de Kaggle; el texto del notebook no cambió.**
Segundo intento: `save_notebook` EXIT=0, `isError: false` (log `save_notebook2.log`):
```json
{"ref": "/code/elnzainoscorona/verifiable-quantum-circuit-compilation",
 "url": "https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation",
 "version_number": 1, "kernel_id": 144639626}
```
Argumentos usados (archivo `save_notebook_qcc.json`): `newTitle` + `text` (el .ipynb completo, 40,894 B) + `language: python` + `kernelType: notebook` + `isPrivate: false` (**PÚBLICO**) + `enableGpu/enableTpu/enableInternet: false` + `kernelExecutionType: SaveAndRunAll` (corre de arriba a abajo).
`get_notebook_info` v1 confirmó: id 144639626, ref `elnzainoscorona/verifiable-quantum-circuit-compilation`, title "Verifiable Quantum Circuit Compilation", author "Elán Zainos Corona", `is_private: false`, language python, kernel_type notebook, current_version_number 1, y el blob `source` empieza con la primera celda del borrador ("# Verifiable Quantum Circuit Compilation — measured submission...").

## 4. La ejecución v1 falló — causa raíz: el kernelspec local `py313`

`get_notebook_session_status` v1: primero `RUNNING`, luego `ERROR` (log `get_notebook_session_status` — llamada directa).
`list_notebook_session_output` v1 (log `list_notebook_session_output2.log`, 68 entradas): la causa raíz es la última línea del traceback:
```
jupyter_client.kernelspec.NoSuchKernel: No such kernel named py313
```
Kaggle ejecuta con papermill (`pm.execute_notebook("__notebook__.ipynb", ...)`) y papermill busca el kernel por el `kernelspec.name` del notebook. El borrador trae `name: "py313"` (kernelspec local registrado en `~/.local/share/jupyter/kernels/py313`); ese kernel no existe en la imagen de Kaggle (`gcr.io/kaggle-images/python@sha256:0717e81990be591f8c5f98f033d29ab23e9ffde057e5b3a6bd4371f93969e962`). El contenido del notebook no es el problema — solo el metadata de ejecución.

**Arreglo (trivial, documentado):** copia de publicación en `~/workspace/qcc-data/kaggle-notebook/qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` (sha256 `8d721babe5e21a2b4134a930bc1c6a6ec96390ee1cfcea6cded45e6fce0c3080`) con el ÚNICO cambio:
- `metadata.kernelspec`: `{'display_name': 'Python 3.13 (py313)', 'language': 'python', 'name': 'py313'}` → `{'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}`
Verificado por diff: **celdas idénticas, metadata (excl. kernelspec) idéntica, nbformat idéntico**. El borrador original (`~/workspace/qcc-data/notebook/qcc_submission_logshift2_fused_dqi_lbfgs.ipynb`, sha `ad0033be…`) quedó intacto; la copia de publicación es la que se subió. Ningún número, atribución ni declaración cambió.

**Re-publicación como actualización (v2):** `save_notebook` con `id: 144639626, hasId: true, slug: verifiable-quantum-circuit-compilation, hasSlug: true` + el texto de la copia + los mismos flags (`isPrivate: false`, GPU/TPU/Internet false, `kernelExecutionType: SaveAndRunAll`). Log `save_notebook_v2.log`, EXIT=0, `isError: false`:
```json
{"ref": "/code/elnzainoscorona/verifiable-quantum-circuit-compilation",
 "url": "https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation",
 "version_number": 2, "kernel_id": 144639626}
```
Misma URL, versión 2, mismo kernel ID.

## 5. Verificación: publicado (PÚBLICO) y corre con 0 errores en Kaggle

`get_notebook_session_status` v2 (tras ~90 s): `{"status": "COMPLETE"}`.
`list_notebook_session_output` v2 (log `list_notebook_session_output_v2.log`): 40 entradas, **0 con Traceback/Error**. Salidas stdout medidas en Kaggle (todas coinciden con los números documentados):
- §0 geomean: invsqrt ratio 5.30907; DQI ratio 6.86807; dfthcsos ratio 1.01169; producto 36.88930; **geomean 3.32890x (CALCULATED, not Kaggle-measured)**; composición anterior 3.30657x; mejora +0.0223x.
- §1 invsqrt: score 139 × 2805.7918 = 390,005.06; ratio 5.30907; PASS oficial dominio completo (200,540,928 tiros), peor error 0.7920 tol en x=2,764,799.
- §2 DQI: baseline Q=1949 ratio 6.77000; fused F1b Q=1937 ratio 6.85414; fused+E1d Q=1934 T=785012 ratio 6.86807; cadena 3.31x → 3.3237x → 3.3259x; E1d +0.0022x.
- §3 dfthcsos: lbfgs score 3,336,160,975 (sample 3,355,599,588, −0.58%); ratio 1.01169; error₁ 3.340 mHa, error₂ 19.371 mHa, λ_eff 49.0158; PASS oficial 254,464 tiros.
- §4 ZIP: "Submission ZIP not attached in this environment." + "Expected ZIP sha256: 171d5a81c4ca47b17573d4876acb3b63386b7048a5f7b1f77fae4e4a60a7f87e" + "Attach valid_submission_fb4e95b.zip as a dataset and re-run this cell." — la rama defensiva funcionó como fue diseñada (el ZIP no está adjunto como dataset al notebook).

`get_notebook_info` v2 (log `get_notebook_info_v2.log`, `isError: false`): id 144639626, ref `elnzainoscorona/verifiable-quantum-circuit-compilation`, title "Verifiable Quantum Circuit Compilation", author "Elán Zainos Corona", slug `verifiable-quantum-circuit-compilation`, language python, kernel_type notebook, **`is_private: false` (PÚBLICO)**, enable_gpu/enable_internet/enable_tpu false, **current_version_number 2**, docker_image `gcr.io/kaggle-images/python@sha256:0717e81990be591f8c5f98f033d29ab23e9ffde057e5b3a6bd4371f93969e962`, machine_shape None. El blob `source` trae kernelspec `{'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}`, 17 celdas, primera celda "# Verifiable Quantum Circuit Compilation — measured submission".

Anomalía anotada (no afecta el veredicto): el campo `last_run_time` de `get_notebook_info` muestra `2026-11-09T17:58:13.663592700Z` (y en v1 mostraba `2026-11-09T17:54:07.200972300Z`) — una fecha anterior a la creación del kernel (2026-11-12). El campo parece desactualizado o de otro origen en la respuesta del servidor. La evidencia directa de la ejecución es la sesión (`COMPLETE`) y el log de salida (40 entradas, 0 errores, salidas correctas), que son inequívocos.

## 6. Lo que NO se hizo / decisiones abiertas

- **NO se marca la selección final (0 de 2, solo Elán).**
- **La postura C14/B7 del planner sigue ABIERTA** (junta, sin resolver); el notebook NO lo incluye como pieza de la entrega y lo dice explícitamente (§6) — no se añadió al publicar.
- **El notebook publicado dice 3.3289x (calculado), no el medido en Kaggle 3.33544 (ref 58277509, status COMPLETE).** El notebook ya declara 3.3289x como calculado (portada, §0, §5) y dice "Best Kaggle score so far: 3.31949" (ahora 3.33544). NO se cambió ningún número al publicar (Elán aprobó este borrador). Es candidato para una actualización v3 del notebook (publicar el 3.33544 medido).
- **El notebook dice "Gold-standard 102,400 tiros NO corrido" (§2.2–2.3, §8).** Eso ya no es cierto: el gold-standard corrió después del borrador — **PASA a 102,400 tiros, 2 errores de valor, 0 de fase, eps_plus 0.000949, R 1.2014** (reporte `dqi-perfil/verificacion_gold/VERIFICACION_GOLD_REPORTE.md`). NO se cambió al publicar. También es candidato para la v3.
- La historia interna del ZIP viejo (piecewise → logshift2) NO está en el notebook público (solo en el reporte de adopción), como estaba planeado.

## 7. Archivos

Scratch: `~/workspace/qcc-data/kaggle-notebook/`
- `PUBLICAR_NOTEBOOK_REPORTE.md` — este reporte.
- `qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` — copia de publicación (kernelspec `python3`; sha256 `8d721babe5e21a2b4134a930bc1c6a6ec96390ee1cfcea6cded45e6fce0c3080`).
- `save_notebook_qcc.json` — argumentos de la v1 (título largo, falló por >50 caracteres).
- `save_notebook.log` / `save_notebook.err` — v1, error "The title cannot exceed 50 characters."
- `save_notebook2.log` / `save_notebook2.err` — v1 reintentada (título corto), éxito, versión 1.
- `save_notebook_qcc_v2.json` — argumentos de la v2 (actualización, id+slug).
- `save_notebook_v2.log` / `save_notebook_v2.err` — v2, éxito, versión 2.
- `get_notebook_info_qcc.json`, `get_notebook_info.log`, `get_notebook_info_v2.log` — verificación de publicación.
- `get_notebook_session_status_qcc.json`, `get_notebook_session_status.log` (v1: RUNNING → ERROR).
- `list_notebook_session_output_qcc.json`, `list_notebook_session_output.log` (v1: vacío), `list_notebook_session_output2.log` (v1: ERROR, `NoSuchKernel: py313`), `list_notebook_session_output_v2.log` (v2: COMPLETE, 0 errores).
- `list_tools.json` — esquemas del servidor MCP (76 tools).

Borrador original intacto: `~/workspace/qcc-data/notebook/qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` (sha256 `ad0033be84e0071acc08075ce2605de50b37c51e2c5d4dd44267ba52573b2b97`). Main y ZIP intactos. Nada descargado. No se pidió ninguna credencial en chat; el conector resolvió la credencial por su flujo seguro.
