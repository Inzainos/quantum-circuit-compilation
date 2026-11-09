# Perfilado del DQI por etapa — 2026-11-08

Decodificador BM v1 (`src/dqi_decoder_v1.py`), commit `a741cc7`. Trabajo tomado de
Claude (se quedó sin tokens al iniciar el perfilado). Invsqrt cerrado con
logshift2 (390,005); el esfuerzo pasa al DQI.

## 1. Reproducción del build — DISCREPANCIA ENCONTRADA Y RESUELTA

El build desde el HEAD local (`local/invsqrt-opt-v1`, commit `8382d3f`) **NO**
reproduce el sha vigente:

| Build | Q | Toffoli | sha256 |
|---|---|---|---|
| HEAD local `8382d3f` | 2,016 | 784,172 | `2b9eb49f…` (el sha viejo de la zip 2026-11-07) |
| Commit `a741cc7` (worktree) | **1,949** | **784,172** | **`6108f5c3…` ✓** |

Causa: el fix Q=1,949 vive en el commit `a741cc7` ("dqi: torre de inversión
sin copias + barrido sin t/u (Q 2009→1949, mismos 784,172 Toffoli)"), en la
rama remota `fix/zip-final-2026-11-07` (mergeada en PR #24). La rama local
`local/invsqrt-opt-v1` no lo contiene. Se construyó desde un worktree
desacoplado en `~/workspace/qcc-worktrees/dqi-1949` (sin tocar main ni el ZIP):

- `dqi-1949.kmb`: **Q=1,949, Toffoli=784,172, sha256
  `6108f5c344b995221f3cf57cd357a1742051031cc89929d0ae055a7bb5233dfb`** —
  reproduce el sha vigente exacto.
- El HEAD local da el mismo T (784,172) pero Q=2,016 y sha `2b9eb49f…`.

## 2. Perfil por etapa (medido, un solo build con foto por frontera)

Método: `perfil_dqi_etapas.py` reproduce `build_decoder()` paso a paso y llama
`finish_circuit()` en cada frontera (verificado que el doble-finish no altera
el resultado: BM-forward solo da Q=1,949/T=185,034 idéntico en un build con un
solo finish y en uno con finish intermedio). Q = `num_qubits` del prefijo
(= pico de qubits vivos en ese prefijo); T(etapa) = diferencia de
`num_toffoli_like` acumulado.

| Etapa | Q pico | T etapa | % de T | T acumulado | vivos al final |
|---|---|---|---|---|---|
| bm_forward (70 rondas) | 1,949 | 185,034 | 23.6% | 185,034 | 1,864 |
| omega_fwd | 1,949 | 42,315 | 5.4% | 227,349 | 1,864 |
| scan (4,095 posiciones) | 1,949 | 401,310 | 51.2% | 628,659 | 1,864 |
| omega_rev | 1,949 | 42,315 | 5.4% | 670,974 | 1,864 |
| bm_reverse (70 rondas) | 1,949 | 113,198 | 14.4% | 784,172 | 1,724 |
| **TOTAL** | **1,949** | **784,172** | 100% | — | — |

Verificación: el total reproduce Q=1,949 / T=784,172 del build. El Q pico
(1,949) ya está fijado al final de `bm_forward` y ninguna etapa posterior lo
supera. Los vivos al final del circuito son 1,724 (S 840 + sigma 432 + tau 432
+ d 8 + H 12); las 140 banderas p/t ya se liberaron en la vuelta.

## 3. Desglose fino por etiqueta (perfil estático, `tools/kmx_profile.py`)

Sobre `dqi-1949.kmb`, profundidad 1 (todas incondicionales, 0 condicionadas):

| Etiqueta | T | % |
|---|---|---|
| scan_pos | 401,310 | 51.2% |
| bm_update | 150,984 | 19.3% |
| bm_disc | 71,766 | 9.2% |
| omega_fwd | 42,315 | 5.4% |
| omega_rev | 42,315 | 5.4% |
| bm_swap | 33,552 | 4.3% |
| bm_alpha | 22,680 | 2.9% |
| bm_dclear | 13,860 | 1.8% |
| bm_d | 2,100 | 0.3% |
| bm_x | 1,680 | 0.2% |
| bm_flags | 1,610 | 0.2% |
| **TOTAL** | **784,172** | 100% |

Profundidad 2: `omega_fwd/gf_mul` 39,690 + resto 2,625 (igual en `omega_rev`);
`bm_alpha` 13,860 + `bm_alpha/gf_mul` 8,820. Scan = **98.0 Toffoli/posición**
exacto (401,310 / 4,095).

## 4. Dónde se fija el pico Q=1,949 (medido por ronda)

- Vivos durante `bm_forward`: ronda 0 → 1,726; **+2 por ronda** (las banderas
  p,t que cada ronda guarda para la vuelta); ronda 69 → **1,864** (máximo).
- Pico Q=1,949 = 1,864 vivos + **85 transitorios** en el momento pico dentro
  de la última ronda (D 12 + X 12 + alpha 12 + P 12 + Pinv 12 + andamiaje de
  la inversión ≈ 25).
- Composición de los 1,864 vivos: **S 840 + sigma 432 + tau 432 + d 8 + H 12
  + banderas p/t 140 = 1,864**.
- `bm_reverse`: vivos bajan de 1,862 (tras ronda 69) a 1,724 (tras ronda 0),
  −2 por ronda (las banderas se liberan). El scan y omega no mueven el pico.

## 5. Asimetría BM forward vs reverse (verificada)

`bm_forward` (185,034) − `bm_reverse` (113,198) = **71,836**. Desglose medido
con un circuito solo-BM-forward (`bm_forward.kmb`, Q=1,949, T=185,034):

| Etiqueta | forward | reverse |
|---|---|---|
| bm_update | 75,492 | 75,492 |
| bm_disc | 71,766 | 0 |
| bm_swap | 16,776 | 16,776 |
| bm_alpha | 11,340 | 11,340 |
| bm_dclear | 6,930 | 6,930 |
| bm_d | 1,050 | 1,050 |
| bm_x | 840 | 840 |
| bm_flags | 840 | 770 |

La vuelta es más barata porque **la discrepancia D no se recomputa en la
vuelta**: en forward se calcula con `_disc` (71,766 Toffoli, incluye una
inversión), en reverse se limpia con `_disc_clear` por MBU (0 Toffoli).
Los otros 70 son las banderas (840 forward vs 770 reverse, 1 por ronda).

## 6. Dónde está el margen — BM in-place (Q manda, va al cuadrado)

Costo DQI = R·Q²·T. Actual (R≈1.20, baseline ≈2.42e13, ambos de la
recalibración 2026-11-07): costo ≈ 3.5745e12, **ratio ≈ 6.77x**,
geomean (5.32 × 6.77 × 1.00583)^(1/3) ≈ **3.31x** (Kaggle real 3.31949).

El margen está en **Q, no en T**: sigma + tau = **864 qubits (44% de Q)**.
El rediseño BM in-place elimina los polinomios sigma/tau como registros
separados (operar sobre S + poco trabajo), como el circuito frontera público
(Q≈889 = 840 de entrada + ≈52). Proyecciones (T igual salvo que se diga):

| Escenario | Q | T | ratio DQI | geomean |
|---|---|---|---|---|
| Actual | 1,949 | 784,172 | 6.77x | 3.31x |
| **BM in-place Q≈1,150** | 1,150 | 784,172 | **19.45x** | **4.70x** |
| Banderas p/t recomputadas (no guardarlas) | 1,809 | 784,172 | 7.86x | 3.48x |
| Scan MBU −23/posición (test cero + fase) | 1,949 | 689,987 | 7.69x | 3.45x |
| BM in-place + scan MBU | 1,150 | 689,987 | 22.10x | 4.91x |
| Frontera pública Q≈889 (T igual) | 889 | 784,172 | 32.54x | 5.58x |

Notas:
- Las banderas p/t (140) son el ahorro de Q más barato y seguro: recomputar
  en vez de guardarlas (−140 Q, geomean 3.31x → 3.48x). No se midió el costo
  del recómputo; es la primera palanca a medir.
- El scan MBU (−11 test cero + −12 fase por posición, docs
  `OPTIMIZACION_DQI_SCAN.md`) es una optimización de T documentada pero **no
  medida** en este perfilado; la cifra −23/posición es teórica.
- BM in-place es el único camino al orden de magnitud: Q≈1,150 → 4.70x.
  Requiere rediseñar la etapa BM (no una variante del EEA/BM actual: el
  doc `DQI_estado_e_ideas.md` ya descartó BM con historia, Q→2,700, efecto
  neto ≈1.0x; el in-place tiene que evitar la historia).
- El verificador DQI completo no corre en esta caja (8 GB, `reaction_depth`
  → bad_alloc); las cifras de R y baseline son las registradas, no medidas
  aquí. Cualquier cambio de circuito debe validarse con el verificador
  oficial antes de afirmar mejora.

## 7. Archivos

- `dqi-1949.kmb` — build reproducido (sha `6108f5c3…`, Q=1,949, T=784,172)
- `dqi.kmb` — build del HEAD local (Q=2,016, sha `2b9eb49f…`, NO vigente)
- `perfil_dqi_etapas.py` — script del perfil por etapa
- `perfil_dqi_etapas.json` — números del perfil (etapas + vivos por ronda)
- `bm_forward.kmb` — circuito solo-BM-forward (Q=1,949, T=185,034)
- `bm_forward_only.py` — script que lo genera
- `REPORTE_PERFIL_DQI.md` — este archivo
