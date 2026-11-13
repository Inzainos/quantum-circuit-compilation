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

## Cómo correr (advertencia: rutas de máquina)

Estos archivos son copias byte por byte de los scripts de trabajo; **no se
reescribieron**. Sus `sys.path.insert` apuntan a rutas absolutas de la máquina
de trabajo (`/home/hatch/workspace/qcc-dqi/src`,
`/home/hatch/workspace/qcc-data/kickmix`,
`/home/hatch/workspace/qcc-data/dqi-perfil/...`) y varios escriben salidas a
`/home/hatch/workspace/qcc-data/...`. En un clon fresco hay que ajustar esas
rutas (o usar `PYTHONPATH=<repo>/src:<kickmix>` y correr desde el directorio
adecuado). Dependencias: `kickmix` (copia vendida en `qcc-data/kickmix`; en
este repo solo está `kickmix/LICENSE.txt`, la librería no está versionada),
`numpy`, y para `refit.py` el starter kit de la competición + `jax`/`optax`.

Los módulos de `src/` que estos scripts importan (`dqi_bm_stage_v1`,
`dqi_tower_inv`, `dqi_tower_inv2`, `dqi_tower_inv3`, `dqi_decoder_v1`,
`dqi_bm_model`) ya están en `src/` del repo.
