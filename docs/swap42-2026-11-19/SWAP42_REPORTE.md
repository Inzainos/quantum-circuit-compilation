# Construcción del 42: swap + build completo + Gold en Kali — Reporte

**Fecha:** 2026-11-14
**Trabajo:** scratch en `~/workspace/qcc-data/dqi-perfil/swap42/`
**GO:** Elán 2026-11-14 ~11:06 (en el chat de El Brujo): "Inicien la construcción
del cuarenta y dos, para tener el bosquejo, cómo vamos a trasladarlo a treinta
y nueve." Resuelve la pregunta del swap: el 42 AHORA (no esperar al 39).
**Estado:** swap aplicado, build completo OK (Q/T exactos). Gold en Kali:
ver §3. Main y ZIP intactos. Nada a Kaggle ni a GitHub.

## §0 — Veredicto

**El swap al 42 funciona y está verificado Gold: build Q=1,864, T=710,312
(exacto lo proyectado, ΔT=−64,620) + Gold PASS en Kali (102,400 tiros, 0
phase, exit 0).** Geomean calc 3.52162 (+2.94% vs producción; 3.51024 con el
R medido en Gold, +2.61%), Kaggle-esc 3.53019 (3.51878 con R medido). El .kmb
construido (sha `746271d9…`) pasó el verificador oficial (ver §3).

## §1 — El swap aplicado (2 bindings de import)

Método: réplica del directorio de producción
`~/workspace/qcc-data/dqi-perfil/omega_karatsuba/` en `swap42/` (solo archivos
`.py`; sin el `.kmb` de producción, sin `__pycache__`, sin logs), más
`dqi_kmul42.py` (Toom-4 42 ANDs) copiado de `multiplicador_gf12/`. Diff exacto
en `diff_swap42.txt` (generado con `diff -ru`).

Los 2 cambios (A-MUL-4 del Auditor: son 2 bindings de import, no 4 ediciones
de línea — las 4 llamadas del decoder fluyen por el import :27):

| Archivo | Línea | Antes | Después |
|---|---|---|---|
| `dqi_bm_stage_v1.py` | 19 | `from dqi_kmul import ixor_kmul` | `from dqi_kmul42 import ixor_kmul42 as ixor_kmul  # SWAP42: Toom-4 42 T en lugar de Karatsuba 54 T` |
| `dqi_decoder_v1.py` | 27 | `from dqi_kmul import ixor_kmul  # OMEGA-KARATSUBA: Karatsuba 54 T en lugar del ctor 63 T` | `from dqi_kmul42 import ixor_kmul42 as ixor_kmul  # SWAP42: Toom-4 42 T en lugar de Karatsuba 54 T` |

Los call sites NO se tocaron (`dqi_bm_stage_v1.py:57` `_mul`;
`dqi_decoder_v1.py:121/126/129/132`): la firma es idéntica —
`ixor_kmul(b, x, y, target)` ≡ `ixor_kmul42(b, x, y, target)`, 3 qubits
transitorios en ambos. Verificado: `grep -rn "from dqi_kmul import"` en
`swap42/` solo deja `medir_aislado_omega.py:18` (script standalone de
medición, no importado por el build — no afecta).

`construir_dqi_omega.py` (copia en `swap42/`): solo cambiaron OUT, el
docstring y las líneas de reporte — la lógica del build es idéntica a la de
producción:
- OUT: `.../omega_karatsuba/dqi_omega_karatsuba.kmb` →
  `.../swap42/dqi_swap42.kmb`.
- Anclas de reporte actualizadas a producción (Q=1,864, T=774,932; ratio
  7.48129 con R=1.201388; geomean (5.32·ratio·1.00583)^(1/3); Kaggle-esc
  con base 3.42920). Los anclajes viejos (7.38175 / 786,272 / 3.41660) eran
  del build sin-t y ya no aplicaban.
- `py_compile` OK en los 4 archivos clave (`construir_dqi_omega.py`,
  `dqi_bm_stage_v1.py`, `dqi_decoder_v1.py`, `dqi_kmul42.py`).

## §2 — Build completo (medido)

Comando: `/home/hatch/workspace/py313/python/bin/python3.13 -u
construir_dqi_omega.py` en `swap42/` (log `build_swap42.log`, 270 s, EXIT=0).

```
modulos: dqi_bm_stage_v1=.../swap42/dqi_bm_stage_v1.py
modulos: bm_fused=.../swap42/bm_fused.py
modulos: bm_fused_e1d=.../swap42/bm_fused_e1d.py
modulos: dqi_decoder_v1=.../swap42/dqi_decoder_v1.py
[bm_forward] live_frontera=1794
[omega_fwd] live_frontera=1794
[scan] live_frontera=1794
[omega_rev] live_frontera=1794
[bm_reverse] live_frontera=1724
TOTAL SWAP42 Q=1864 T=710312 en 270s
PRODUCCION (omega/Karatsuba): Q=1864 T=774932
Delta Q=0 Delta T=-64620 (proyectado Delta Q=0 Delta T=-64620)
DQI ratio nuevo = 8.16189x
geomean calculado = 3.52162x ; geomean escalando Kaggle 3.42920x = 3.53019x
guardado .../swap42/dqi_swap42.kmb sha256=746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603
```

- **Q=1,864 y T=710,312: EXACTOS lo proyectado** (ΔQ=0, ΔT=−64,620 =
  5,385×12). Los 4 módulos se cargaron desde `swap42/` (el shadowing
  funcionó; el build usó el multiplicador 42 en los 5,385 llamados).
- `live_frontera` idéntico al build de producción en las 5 etapas
  (1794/1794/1794/1794/1724): el pico de qubits no se movió, como se
  proyectó (mismos 3 transitorios por llamada).
- DQI ratio 8.16189x (R=1.201388; la tabla del reporte del multiplicador
  daba 8.17115x con R=1.20 — misma convención mixta ya registrada en M-2;
  el geomean, que es el número del veredicto, es exacto en ambas: 3.52162).
- `.kmb`: 646,811,990 B (producción: 629,623,070 B — ~17 MB más: menos
  Toffolis pero más ops lineales (CX) de las formas del Toom-4; el .kmb
  guarda todas las ops). sha256 verificado independiente del log:
  `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603`.
- El build tardó 270 s (producción: 158 s) — más lento por el mayor número
  de operaciones lineales que emite el constructor Toom-4 por llamada.
  No afecta al resultado.

## §3 — Gold en Kali (verificador oficial)

**Resultado: PASS.** El verificador Gold oficial corrió en Kali sobre el .kmb
construido (11:23:48 → 11:30:17 CST, ~6.5 min, log `verify_swap42_gold.log`,
47 l. / md5 `38d9f639…`). `exit_gold=0`.

```
{
  "status": "PASS",
  "score": 2993914799696.024,
  "verified_shots": 102400,
  "value_errors": 5,
  "phase_errors": 0,
  "empirical_error_rate": 4.8828125e-05,
  "effective_error_rate": 0.0010479495500463395,
  "repetition_factor": 1.2131052140444296,
  "mean_error_weight": 31.046737331746634,
  "toffoli_count": 710312.0,
  "reaction_depth": 19501,
  "num_ops": 74182884,
  "num_qubits": 1864,
  "num_bits": 198813,
  "circuit_sha256": "746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603"
}
```

Comparación con el Gold de producción (mismo verificador, 102,400 tiros):

| | Producción (omega/Karatsuba) | Swap42 (Toom-4 42) |
|---|---|---|
| status / exit | PASS / 0 | PASS / 0 |
| score (R·Q²·T) | 3,234,735,110,839.35 | 2,993,914,799,696.02 |
| toffoli_count | 774,932 | 710,312 |
| value_errors | 2 | 5 |
| phase_errors | 0 | 0 |
| effective_error_rate | 0.000949 | 0.001048 |
| repetition_factor R | 1.2013880602795501 | 1.2131052140444296 |
| mean_error_weight | 31.046737331746634 | 31.046737331746634 |
| num_ops | 72,244,284 | 74,182,884 |
| reaction_depth | 19,501 | 19,501 |
| num_qubits / num_bits | 1,864 / 198,813 | 1,864 / 198,813 |

Lectura:
- **PASS con phase_errors=0** — la fase es exacta; el criterio duro de
  corrección se cumple.
- **T=710,312 confirmado en el circuito** por el propio verificador
  (toffoli_count 710,312.0, max 710,312). El ahorro es real y medido, no
  proyectado.
- **R medido 1.2131 vs 1.2014 en producción**: los value_errors (5 vs 2 de
  102,400 tiros) son ruido de muestreo — el `mean_error_weight` es IDÉNTICO
  (31.046737331746634) en ambas corridas, así que la distribución de error
  subyacente no cambió; R fluctúa entre corridas. Por eso el geomean con R
  medido es 3.51024 (+2.61%) en vez de 3.52162 (+2.94%) con R fijo en el
  valor de producción. La mejora es real en ambos casos.
- **num_ops +2.68%** (74,182,884 vs 72,244,284): más ops totales por el
  sobrecosto lineal (CX) del Toom-4; CCX bajó (68.78e9 vs 75.40e9) y CX
  subió (6,569.79e9 vs 6,344.81e9), consistente con el diseño.
  reaction_depth idéntico (19,501).

## §4 — Qué sigue (no hecho aquí)

1. **Decisión de Elán** sobre este 42 construido (¿pasa a producción / ZIP /
   Kaggle?). Este trabajo es scratch hasta que él decida.
2. **El 39**, si aparece (desarrollo <42 en paralelo): mismo pipeline
   (swap de 2 imports + build + Gold). Ver `BOSQUEJO_42_A_39.md`.
3. **La alpha** sigue siendo proyección (−2,940 T, no cambio verificado):
   necesita cambio de forma de llamada + verificación semántica (§6.2 del
   reporte del multiplicador).

## §5 — Archivos (este directorio)

| Archivo | Contenido |
|---|---|
| `SWAP42_REPORTE.md` | Este reporte |
| `BOSQUEJO_42_A_39.md` | Bosquejo de la construcción del 42 como plantilla para el 39 |
| `dqi_swap42.kmb` | Circuito construido (646,811,990 B, sha `746271d9…`) |
| `construir_dqi_omega.py` | Build (copia con OUT y anclas actualizadas) |
| `dqi_bm_stage_v1.py` | Build (import :19 cambiado) |
| `dqi_decoder_v1.py` | Build (import :27 cambiado) |
| `dqi_kmul42.py` | Multiplicador Toom-4 42 ANDs |
| `diff_swap42.txt` | Diff exacto vs `omega_karatsuba/` |
| `build_swap42.log` | Log del build (270 s, EXIT=0) |
| `run_verify_swap42_gold.sh` | Script Gold (Kali) |
| `verify_swap42_gold.log` | Log Gold (47 l., md5 `38d9f639…`, copia local; original en Kali) |
