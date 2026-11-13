# scripts/ — código generador de la entrega adoptada 2026-11-12

Código generador del DQI fusionado+E1d (Q=1,934, T=785,012), del notebook
público y de la subida a Kaggle, adoptado el 2026-11-12 (geomean medido 3.33544
en Kaggle, ref 58277509). Los módulos importables viven en `src/`; estos son
los scripts que los usan.

## Módulos generadores (en `src/`)

- `src/bm_fused.py` — `BMStageFused`: fusión mul+inv (inversión directa en
  alpha + selección CSWAP; ahorra Pinv, 12 qubits). Q 1,949→1,937, T idéntico.
- `src/tower_inv3r.py` — torre de inversión rediseñada (base R).
- `src/tower_inv3_e1d.py` — cambio E1d: N' libre (3 bits) tras calcular r,
  antes de los productos en rc (0 T, `mulN_del` con N), recompute en el undo
  (6 T/inversión). Q 1,937→1,934, T 784,172→785,012.
- `src/bm_fused_e1d.py` — `BMStageFused` con E1d (variante adoptada).
- `src/bm_fused_r.py` — `BMStageFused` con R (variante de comparación).

## Scripts (en `scripts/`)

- `construir_dqi_e1d.py` — construye el DQI fusionado+E1d (el .kmb de
  624,877,910 B, sha `16e06d61…3664`).
- `verificar_e1d.py`, `verificar_fusion.py` — verificación (sim n=6 + oficial
  Kali 2,560 tiros, 0 errores).
- `medir_fusion.py`, `medir_dqi_fusionado.py`, `medir_andamios.py`,
  `medir_pico_fino_torre.py` — medición de la fusión.
- `medir_dqi_e1d.py`, `medir_dqi_r.py`, `medir_torre_e1d.py`,
  `medir_torre_r.py`, `medir_itoh_builtin.py`, `medir_norma_cubica.py`,
  `medir_scan_pico.py`, `probar_frob.py` — medición del rediseño (E1/E2/E1d,
  Itoh-Tsujii, norma cúbica, pico del scan, Frobenius).
- `build_notebook.py` — construye el notebook público
  `qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` (17 celdas, 0 errores).
- `submit_competition.py`, `poll_score.py` — subida del ZIP a Kaggle y sondeo
  del puntaje (ref 58277509, 3.33544).
- `refit.py` — entrenamiento/refit del factor dfthcsos (candidato lbfgs
  rho=1e-4, eps=0.017, 100 épocas). El generador del circuito dfthcsos es el
  planner (clduab11, Apache 2.0, NO nuestro; postura C14/B7 abierta).

## Cómo correr (rutas relativas al repo)

Rama `local/rutas-relativas-v1` (2026-11-12, refrescada sobre `origin/main`
`181419ec`, Adopted v3): las rutas ya son relativas al
repo. Cada archivo resuelve la raíz desde `__file__` (`_ROOT`) y añade
`<repo>/src` y `<repo>/kickmix` a `sys.path`. **No hace falta `PYTHONPATH`.**
Solo la lógica de rutas cambió; la lógica de los circuitos, los números y
los SHAs no se tocaron (ver el diff contra `origin/main`: solo líneas de ruta).

```bash
# Desde la raíz del repo, con Python 3.13 (kickmix.so solo carga en 3.13):
python3.13 scripts/medir_fusion.py
python3.13 -u scripts/verificar_fusion.py
python3.13 -u scripts/construir_dqi_e1d.py   # escribe outputs/dqi_fusionado_e1d.kmb
```

Dependencias: `kickmix` (**vendida en `kickmix/kickmix.so`** en esta rama;
ver `kickmix/README.md` — solo CPython 3.13, Linux x86-64), `numpy`, y para
`refit.py` el starter kit de la competición + `jax`/`optax`.

Salidas: los scripts que escriben archivos lo hacen en `outputs/` del repo
(`*.kmb`, `*.npz` e `*.ipynb`; los binarios siguen ignorados por `.gitignore`
según las reglas del repo). Cada salida acepta override por variable de
entorno: `QCC_DQI_FUSIONADO_OUT`, `QCC_DQI_E1D_OUT`, `QCC_NOTEBOOK_OUT`,
`QCC_REFIT_OUT_DIR`.

Dependencias externas que NO están en el repo (defaults originales, con
override por entorno):

- `refit.py` — starter kit de la competición (`QCC_STARTER_KIT`, default
  `~/workspace/qcc-data/starter-kit/starter_kit`): trae `dfthc` y
  `starter.task1_factorization` + los datos FeMoCo.
- `submit_competition.py`, `poll_score.py` — conector Kaggle de la máquina
  (`QCC_KAGGLE_BIN`, `QCC_KAGGLE_CALLS`, `QCC_KAGGLE_SCRATCH`).
- `build_notebook.py` — el ZIP de envío (`valid_submission_fb4e95b.zip`):
  lo busca en `/kaggle/input/qcc-submission/` o en el CWD; sin él, la
  celda §4 del notebook lo dice y no falla el resto.

Los módulos de `src/` que estos scripts importan (`dqi_bm_stage_v1`,
`dqi_tower_inv`, `dqi_tower_inv2`, `dqi_tower_inv3`, `dqi_decoder_v1`,
`dqi_bm_model`) ya están en `src/` del repo.
