# src — Optimizadores

La construcción y verificación de circuitos usa la biblioteca **kickmix**
(`pip install kickmix`, paquete de los desarrolladores de Qualtran).
Los verificadores de referencia están en `verifiers/`.

## Scripts canónicos

- `optimize_invsqrt.py` / `optimize_invsqrt_prec.py`: barrido de `Precision(...)`
  validado con el modelo de punto fijo sobre todo el dominio.
- `dbhexa_invsqrt_final.py`: genera el circuito invsqrt con 27/27/27 bits
  (Q=254, Toffoli=7405).
- `dfthcsos_optimizer.py`: barrido de `brot` y `batch_size` con el verificador.

## Experimentales / históricos (no usar para envío)

`dbhexa_invsqrt.py`, `_v2`, `_debug`, `_debug_v2`, `_n_intervals`, `_param`,
`_pool`, `_pool_final`, `_practical`, `_ref_based`, `_temporal`: iteraciones de
exploración. Varias usan `result_bits=28`, que NO pasa el verificador.

## Incompletos

- `dqi_from_zero.py`: esqueleto sin decodificador real. Se niega a escribir
  circuitos salvo con `--allow-skeleton`.
- `dqi_optimizer.py`: no optimiza; reexporta el baseline.
- `qubit_temporal_manager.py`: contabilidad lógica, sin efecto en los circuitos.
