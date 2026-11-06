# Logs por dentro y por fuera + primer modelo surrogate (2026-11-06)

Rama `local/logs-modelo-v1` (sobre `local/integracion-v1`, commit
4146c18). Idea de Elán: cada archivo/script lleva logs; cada fase se
documenta desde dentro por los scripts y desde fuera por el modelo que
entrena/verifica, que también reporta cómo está trabajando. Con la
radiografía completa se ven los puntos para optimizar. Eso es lo que
aquí significan los "logs de entrada y salida".

## 1. Esquema de logs (`tools/qcc_log.py`, solo stdlib)

Una línea JSON por evento, en `~/workspace/qcc-data/logs/qcc.jsonl`
(env `QCC_LOG_PATH` lo cambia; `QCC_LOG_OFF=1` desactiva el archivo):

```json
{"ts": "2026-11-06T23:16:11.990320+00:00", "run_id": "4c732e25f5cf",
 "script": "invsqrt_logshift2", "phase": "build", "status": "ok",
 "inputs": {"deg": 2, "j": 8, "wc": 28, "dd": 13, "sesgo": 1},
 "outputs": {"Q": 139, "T": 2561}, "duration_s": 0.032}
```

- `run_id`: uno por proceso (env `QCC_RUN_ID` lo fija; los drivers
  lo propagan a los hijos para agrupar una corrida).
- `status`: `start` | `ok` | `error`. Los eventos también se ecoan
  por `logging` para que aparezcan en los logs de texto existentes.
- Escribir el log nunca rompe el pipeline (errores de E/S se tragan
  con un warning).

## 2. Inventario de logs que ya existían

| Fuente | Qué cubre (entradas → salidas) | Huecos |
|---|---|---|
| `qcc-data/dfthcsos_sweep_official/optimization_results.json` | Barrido brot×J (20 puntos) contra datos oficiales: solo 2 PASS (brot12/J4, brot12/J8). Entradas brot/J; salidas score/λ_eff/T/Q o el motivo de ERROR/FAIL. Sin Lambda/E_gap por punto. | No guarda los circuitos ni los tiempos por punto. |
| `qcc-data/dfthcsos-refit/*.log` | 4 corridas de refit (LBFGS ep30/ep100/ep300-muerto, Adam diag 20ep): checkpoints por época (eps, λ_eff, Λ, gap, E_SOS, ms/it) + DONE final. | El ep300 no guardó .npz (el driver solo guarda al final); el pilot de 1000 épocas no dejó salida por buffering. |
| `qcc-data/dfthcsos-refit/candidates/lbfgs_ep100_rho1e-4/` | Candidato: `summary.json` (costos por circuito, métricas), `verify_official.log` (PASS 3,336,160,975), `check_factorization.log`, `encode.log`, `build_circuits.log`. | Un solo candidato: no hay serie de candidatos para entrenar. |
| `logs/invsqrt_sweep_0.csv`, `invsqrt_sweep_1.csv` | Barrido (deg,j,wc,dd,sesgo) → max_err/Q/T, 24 filas únicas. | Sin scores (solo Q/T); sin tiempos; sin el sha del circuito por fila. |
| `logs/dqi_*.log`, `logs/dqi_bm_forecast.json` | Pruebas del decodificador BM (build, simulación, PASA), forecast de pesos de error por peso (14–35). | Sin serie de decodificadores alternativos (solo v10 y BM v1); sin muestreos por variante salvo el n_iters. |
| `qcc-data/agent-proposals/` + `scratch/` | Análisis del motor, 3 propuestas, logs de verificación de proposal-01 y de dqi v10. | Los logs de scratch son texto libre, sin esquema. |
| `qcc-data/local_metric/` | Réplica local del evaluador (`local_score.py`) + `score_valid.log`. | La corrida completa murió por OOM en la verificación dqi; no hay un JSON de scores por split. |
| `qcc-data/review-feat/dqi_harness_102400.log` | Muestreo BM v1: 102,400 tiros, 0 fallos, 286 s. | Un solo muestreo a ese N; sin fallos por peso. |
| `qcc-data/integracion/*.log` | Rebuild del ZIP integrado + verificación de sus 3 componentes. | Los logs de verificación del ZIP están separados del rebuild. |

## 3. Scripts instrumentados (desde dentro)

Solo se añadió logging; ninguna línea de construcción de circuitos
ni ningún número cambió.

| Script | Fases logueadas |
|---|---|
| `src/invsqrt_logshift2.py` | `build` (params → Q, T, duración), `write` (sha256, bytes). Regresión verificada: regenera sha `7e842bbf…3faf79`. |
| `src/dqi_decoder_v1.py` | `build` (toffoli, qubits, duración), `write` (sha256, bytes). Smoke test 16 posiciones: toffoli=384,430, Q=2016, igual que antes. |
| `submission/rebuild_valid_zip.py` | `start` (salida, dfthcsos-zip/commit, TMPDIR), `invsqrt_build`, `dqi_build`, `zip_write` (sha256 del ZIP + shas de cada `dfthcsos/`). Rebuild completo re-ejecutado: reproduce invsqrt `7e842bbf…`, dqi `b555beda…` y los `dfthcsos/*.kmx` byte a byte (el sha del ZIP cambia solo por los timestamps del formato ZIP). |
| `tools/dfthcsos_refit.py` | Copia instrumentada de `refit.py`: `start` (todos los args), `seed_eval` (eps/Λ/λ_eff/gap), `train` (wall + valores finales), `save` (sha256 del .npz). No se re-ejecutó un refit completo (2,562 s el de 100 épocas); validado con `--help` y `py_compile`. |
| `tools/dfthcsos_build_candidate.py` | Driver con logs de las 4 fases de `build_candidate.sh`: `check_factorization`, `encode`, `build_circuits`, `verify` (parsea el JSON del verificador: status, score, λ_eff, error_2, E_gap, sha). No re-ejecutado de punta a punta (reutiliza los logs del candidato existente). |

Notas de entorno que el logging deja registradas: el rebuild usa
`tempfile` → hay que poner `TMPDIR` en disco (`/tmp` es un tmpfs de
512 MB y el .kmb de dqi pesa 631 MB); los hijos del rebuild necesitan
`kickmix.so` visible (`src/kickmix.so` symlink temporal, gitignored).

## 4. Observador externo (`tools/qcc_observe.py`)

Verifica un ZIP desde fuera y loguea cada entrada/salida:

```bash
PYTHONPATH=$HOME/workspace/qcc/kickmix:$PWD/src python tools/qcc_observe.py \
    ~/workspace/qcc-data/integracion/submission.zip --shots 2560 --seed 1
```

- Extrae a `~/workspace/qcc-data/observe/<zip-stem>/` (nunca `/tmp`).
- invsqrt: verificador oficial, dominio completo, 1 tiro/x.
- dfthcsos: verificador oficial sobre el `dfthcsos/` extraído (usa
  la copia de verificadores con el .fcidump, `qcc-data/verifiers/`).
- dqi: muestreo con las funciones del propio verificador
  (`tools/dqi_harness.py`), con `reaction_depth` parcheado a -1:
  el verificador completo no corre en esta caja (bad_alloc). El score
  dqi que reporta es una ESTIMACIÓN (`R × Q² × mean_toffoli`, R de la
  fórmula del verificador), y depende del N de tiros: a 2,560 tiros
  R=4.94 (score ≈1.57e13); a 102,400 tiros R≈1.19 (score ≈3.80e12).
  El N de referencia es 102,400.

Corrida sobre el ZIP integrado (2026-11-06): invsqrt PASS 390,005.06;
dfthcsos PASS 3,336,160,975; dqi 2,560 tiros, 0 fallos, R=4.9417
(ver `qcc-data/logs-modelo/observe.log`).

## 5. Primer modelo surrogate (`tools/qcc_model.py`, `tools/qcc_model.json`)

9,728 bytes. Solo mediciones reales, cero datos sintéticos.
Entrenado por `tools/qcc_model_train.py` (dataset regenerable en
`qcc-data/logs/qcc_dataset.csv`, 55 filas).

| Benchmark | Modelo | Datos | Validación (honesta) |
|---|---|---|---|
| invsqrt | Ridge (numpy) (j,wc,dd,sesgo) → Q, T, max_err; score = Q·T·1.0933 (media medida de toffoli_equiv/T en 3 circuitos verificados) | 24 filas del barrido | 80/20: MAE Q=0.22, T=68, max_err=0.035. Leave-one-group-out: Q=0.53, T=134 (~5%), max_err=0.047. En el punto verificado (139/2561/390,005): Q≈139.5, T≈2666, score≈406,513 (+4.2%). |
| dfthcsos | Ridge (log10 rho, eps, época, solver) → λ_eff, log(eps), gap; score = λ_eff_enc·T(brot,J)·Q(brot,J) con tabla determinista y offsets de encode medidos (n=1) | 21 puntos LBFGS (3 corridas) | Leave-one-run-out: MAE λ_eff=0.47, eps=0.67 mHa, gap=0.076 (máx. gap 0.32, en la corrida rho=1e-3). En el candidato: score≈3,345,481,176 vs 3,336,160,975 medido (+0.28%). |
| dqi | Sin regresor ajustado: la fórmula exacta del verificador (Clopper-Pearson 1-2^-128 + repetition_overhead) | 2 decodificadores + tabla n_iters | Reproduce el score registrado de v10 con error relativo 3e-8. BM v1: 3.797e12 (0 fallos) / 3.829e12 (2 fallos) a 102,400 tiros. No predice T/Q de un decodificador nuevo. |

Reglas del modelo: todo lo que imprime es ESTIMACIÓN. Adam está
rechazado explícitamente (el CLI sale con código 2 y explica que
Adam lr=1e-4 destruye la semilla, medido en `diag_20ep.log`); el
modelo de trayectoria cubre solo fine-tuning LBFGS. El modelo de forma
(R,B,C) es un ajuste de 2 parámetros sobre 3 puntos colineales: solo
sirve para ordenar, no para predecir.

```bash
python tools/qcc_model.py predict --benchmark invsqrt --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1
python tools/qcc_model.py predict --benchmark dfthcsos --rho 1e-4 --eps 0.017 --epochs 100 --brot 12 --J 8
python tools/qcc_model.py predict --benchmark dqi --T 784172 --Q 2016 --shots 102400 --failures 0
python tools/qcc_model.py validate
python tools/qcc_model.py info
```

## 6. Lo que falta (qué logs mejorarían más el modelo)

1. **Serie de candidatos dfthcsos.** Hoy hay un solo candidato PASS.
   Cada refit futuro que pase por `tools/dfthcsos_refit.py` +
   `tools/dfthcsos_build_candidate.py` dejará sus puntos en
   `qcc.jsonl` automáticamente; con 5–10 candidatos el modelo de
   score dejaría de depender de un solo offset de encode (n=1).
2. **Muestreos dqi por variante.** Solo hay 2 decodificadores y un
   muestreo grande (BM v1, 102,400 tiros). Un muestreo por cada
   variante de decodificador (aunque sea 2,560 tiros) es lo único que
   permitiría predecir fallos/T/Q en vez de solo convertirlos en score.
3. **Barrido invsqrt con sha y tiempo por fila.** El CSV actual no
   guarda ni el sha del circuito ni la duración; con eso el modelo
   podría predecir costo de cómputo además de Q/T.
4. **Corrida completa del evaluador local.** Sigue bloqueada por OOM
   en dqi; sin ella no hay scores por split medidos para entrenar la
   media geométrica directamente (hoy es aritmética de 3 scores).
5. **Logs por época del refit en JSON.** Hoy los checkpoints viven
   en texto libre; el entrenador del kit los imprime y el parser de
   `qcc_model_train.py` los extrae con regex. Si el driver emitiera
   un evento por época, el dataset sería exacto en vez de parseado.
