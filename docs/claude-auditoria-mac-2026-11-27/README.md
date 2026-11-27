# Auditoría del plan invsqrt "meseta MAC / Horner por tramos" — 2026-11-27

Procedencia: archivo `9d6c28be-attachment.txt` entregado por Capitán (texto de un agente
externo, estilo "Frente 1/2/3" + script `invsqrt_mac_bench.py`). El script se guarda **sin
modificar** en `scripts/invsqrt_mac_bench_original.py` (sha256 que empieza con `3bc029c1a2f520c9`).
Esta carpeta NO toca `main`, el zip de envío ni Kaggle. Es material de medición para el equipo.

## 1. Qué se verificó ejecutando el script (logs/original_run.log, logs/sweep_seg_bits.log)

| Afirmación del plan | Estado | Evidencia |
|---|---|---|
| Error máximo del Horner grado 2 truncado (9 bits de segmento, 34 frac.) ≈ 9.25e-10 sobre [1,2) | **Reproducido** | `logs/original_run.log` |
| "Límite 3.76e-9" | **Límite equivocado**: el verificador usa tolerancia relativa `2^-24` ≈ 5.96e-8 (`TOL = 2.0 ** -24`) | ver `src/dbhexa_invsqrt.py` (`Tolerancia: 2^-24`) |
| Q = 110 | **No medido**: es `38 + 34 + (34+4)` escrito a mano en `audit_piecewise_invsqrt` | código original, líneas "Cálculo de Recursos" |
| C = 1858 | **No medido**: constantes inventadas (180, 420 = "3×140", factor 1.45 por bit activo, ×1.15 final) y solo cuenta el sentido directo | idem |
| Q·C = 204,380 | **Derivado de lo anterior; no usar** | idem |
| "Multiplicar acc por Δx in-place" | **No reversible** (si Δx=0 toda `acc` colapsa a 0). Solo `acc += a·b` hacia otro registro es reversible | análisis |
| Primitiva QASM `mac_trunc_inplace` | **No es un circuito**: `cx tmp_and, acc[k]` es XOR sin acarreo; corta a 12 operaciones con "[resto truncado]"; fila j=0 vacía; no es `.kmb` | `logs/original_run.log` (salida emitida) |
| Baseline "261 q / 4,467" y "Q·C ≈ 1.31M" | **Desactualizado e inconsistente**: 261×4467 = 1,165,887 (la propia tabla lo dice y luego escribe ~1.31M). Nuestro estado adoptado es Q=139, T=2561 | `docs/claude-optimizacion-2026-11-20/README.md` (rama `local/hoist-delta-omega-2026-11-20`) |
| "Meta logshift2: 390,005" | Equivale a lo que ya tenemos (139 × ≈2800 ≈ 389k) | idem |

## 2. Hallazgo útil (medido con el código del propio plan)

Barrido de bits de segmento y bits fraccionarios contra `2^-24` (error relativo máximo, 40,000
muestras en [1,2); columna `x(2^-24)` = error / tolerancia):

| seg_bits | frac 28 | frac 30 | frac 34 |
|---|---|---|---|
| 4 | 37.43 | 36.92 | 36.92 |
| 5 | 5.68 | 5.00 | 4.80 |
| 6 | 1.32 | 0.79 | 0.62 |
| 7 | 1.09 | 0.31 | 0.09 |
| 8 | 1.03 | 0.29 | 0.02 |
| 9 | 1.03 | 0.27 | 0.02 |

Lecturas: (a) 28 bits fraccionarios NO alcanzan (piso de cuantización ≈ 6.15e-8 ≥ 2^-24);
(b) con ≥30 bits fraccionarios, 6–7 bits de segmento ya pasan con margen; 8→9 casi no mejora.
Esto es solo el error numérico de **esta** familia (Horner grado 2 por tramos). No dice nada de
costo en Toffoli.

## 3. Estimación de costo (NO medida; rangos míos, para que se contrasten)

Con los componentes del propio plan (normalización 180, QROM 420, 2 MAC ≈ 1015 forward):
forward ≈ 1,615; sumando el sentido inverso (compute + uncompute) C ≈ 2,700–3,200.
Q realista ≥ 125–140 (x 38 + c2/acc 34 + registro de la 2.ª etapa 34 + ancillas), no 110.
Q·C ≈ 340k–450k, es decir, **empata con lo nuestro (≈389k), no lo supera**. Hipótesis a medir.
Referencia de la meseta pública (Family C): 37 q, costo 60,955 → ratio ≈ 34.07× vs nuestro 5.335×.

## 4. Protocolo de medición propuesto (Muse / Datos / Auditor)

1. Construir con nuestro constructor kickmix (no QASM) la familia "Horner grado 2 por tramos":
   normalización, lookup c2/c1/c0 (anotar si es una QROM de ancho 3×w o tres), dos etapas
   `r1 = c1 + Δx·c2` y `r0 = c0 + Δx·r1` con registros distintos, fase por bits, inversa exacta.
2. Reportar por bloque (`builder.mark`): Q pico y T (Toffoli por tiros, como el verificador).
3. Verificar con el verificador (semilla fija de nuestra práctica) en x ∈ [1,2) **y** [2,4)
   (el script original solo mide [1,2)).
4. Comparar contra Q=139 / T=2561 (C≈2800.4). Solo si el Q·C medido < 389k tiene sentido seguir.
5. Cualquier adopción cumple C14: re-derivar con nuestro constructor, con cita/declaración; no
   copiar circuitos públicos literalmente.

## 5. Archivos

- `scripts/invsqrt_mac_bench_original.py` — script del plan, sin tocar.
- `scripts/sweep_seg_bits.py` — barrido contra 2^-24 (con logging; `python3 -I sweep_seg_bits.py`).
- `logs/original_run.log`, `logs/sweep_seg_bits.log` — corridas de esta auditoría.
