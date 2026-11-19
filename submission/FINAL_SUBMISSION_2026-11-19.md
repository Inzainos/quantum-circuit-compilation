# Final Submission — Google Quantum AI Verifiable Quantum Circuit Compilation

**Fecha:** 2026-11-19
**Rama:** `local/swap42-2026-11-19`
**Autor:** Elán Zainos Corona (Fractal Core Research)

---

## Resumen Ejecutivo

Entrega para la competición **Google Quantum AI - Verifiable Quantum Circuit Compilation** (Kaggle 2026). Tres benchmarks verificados con el **verificador oficial kickmix** (gold standard). El único cambio respecto al Adopted v3 es el DQI: el swap42 (multiplicador Toom-4 de 42 ANDs en lugar de Karatsuba de 54).

| Benchmark | Circuito | Métricas | Verificación Oficial |
|-----------|----------|----------|---------------------|
| **invsqrt** (Fusión) | `logshift2` (deg=2, j=8, wc=28, dd=13) | Q=139, T=2,561, Score=390,005.06 | ✅ **PASS** (200,540,928 shots) |
| **DQI** (Optimización) | `swap42` (Toom-4 42 ANDs, sin t, fusión + E1d) | Q=1,864, T=710,312, Score=2.994×10¹² | ✅ **PASS** (102,400 tiros, gold) |
| **dfthcsos** (Química) | `lbfgs` (65,60,60, brot=12, J=8) | Q=730, T=93,237, Score=3.336×10⁹ | ✅ **PASS** (254,464 tiros) |

**Geomean calculado:** 3.51878 (esperado); 3.52286 (medido directo)
**Kaggle medido (ref 58570485):** **3.53019** (nuevo personal best, +2.945% vs Adopted v3, 3.42920)

---

## Archivo de Entrega

**ZIP:** `submission/final_submission.zip`
**SHA256:** `44781dea76353a015f33ace06d50f45bc894da5041ed8c3522db1f1d11b4f4de`
**Tamaño:** 67,007,440 bytes (63.9 MB comprimido; 676,376,535 bytes / 645 MB sin comprimir)
**Estructura:** 13 archivos

```
final_submission.zip
├── invsqrt.kmb                    (437 KB)   — logshift2
├── dqi.kmb                        (647 MB)   — swap42 (Toom-4 42)
└── dfthcsos/
    ├── angle_k_0.kmx .. angle_k_9.kmx  (10 circuitos)
    └── submission.npz            (4.5 MB)  — factorización lbfgs
```

---

## El cambio: swap42 (DQI)

El multiplicador GF(2¹²) pasa de Karatsuba (54 ANDs) a Toom-4 sobre GF(8) (42 ANDs, el mínimo explícito medido: el barrido de la etapa C, 435,456 casos, dio exactamente 42 en todos). El cambio en el código son **2 bindings de import** (A-MUL-4 del Auditor) más el archivo nuevo `src/dqi_kmul42.py`:

| Archivo | Línea | Antes | Después |
|---|---|---|---|
| `src/dqi_bm_stage_v1.py` | 19 | `from dqi_kmul import ixor_kmul` | `from dqi_kmul42 import ixor_kmul42 as ixor_kmul` |
| `src/dqi_decoder_v1.py` | 27 | `from dqi_kmul import ixor_kmul` | `from dqi_kmul42 import ixor_kmul42 as ixor_kmul` |

Los call sites no se tocaron (la firma es idéntica: `ixor_kmul(b, x, y, target)` ≡ `ixor_kmul42(b, x, y, target)`, 3 qubits transitorios en ambos). Detalle completo en `docs/swap42-2026-11-19/SWAP42_REPORTE.md`.

**Efecto medido:** T=774,932 → 710,312 (ΔT=−64,620 = 5,385 llamadas × 12 T), Q=1,864 intacto. El .kmb pesa 17,188,920 B más (+2.73%) pese a bajar T (CX extra del Toom-4).

---

## Verificaciones Oficiales (Gold Standard)

### invsqrt — Fusion Energy
- **Circuito:** `logshift2` (PipelineLog2, deg=2, j=8, wc=28, dd=13, sesgo=1)
- **SHA256:** `7e842bbfba8fb40d32c05b3b195073cf368981a92de77197ed22bd3a3f3faf79`
- **Verificador:** `verifiers.invsqrt.verify_submission_invsqrt`
- **Shots:** 200,540,928 (dominio completo n_p=10, β=1, 64 shots/x)
- **Resultado:** **PASS**
  - Score: 390,005.06
  - Q=139, T=2,561, Toffoli-equiv=2,805.79
  - Peor error/tol: 0.7920 (x=2,764,799)
  - Circuit SHA256 match: ✅ byte-idéntico

### DQI — Combinatorial Optimization
- **Circuito:** `swap42` (Toom-4 42 ANDs, sin t, fusión mul+inv, E1d)
- **SHA256:** `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603`
- **Verificador:** `verifiers.dqi.verify_submission_dqi`
- **Shots:** 102,400 (gold standard, m=4095, n=70, degree=12, r=2016)
- **Resultado:** **PASS**
  - Score: 2,993,914,799,696
  - Q=1,864, T=710,312, Toffoli-equiv=710,312
  - Value errors: 5, Phase errors: 0
  - R: 1.2131
  - Circuit SHA256 match: ✅ byte-idéntico
  - Nota: los 5 errores de valor vs 2 del omega/Karatsuba son ruido de muestreo — el `mean_error_weight` es idéntico (31.046737331746634) en ambos logs Gold.

### dfthcsos — Quantum Chemistry (FeMoCo)
- **Circuito:** `lbfgs` (65,60,60, brot=12, J=8, batch=8)
- **Factorización:** `submission.npz` (U, W, H2_I, H1_I, Hsym_lower + tree_edges)
- **SHA256 submission:** `d89772be6b4b8484cc090ea065baf61c0f8cedc2ad0e6689106c44ef87b7fa4d`
- **MD5 submission:** `521d53c6d8948720cdb9913f7885bdc9`
- **Verificador:** `verifiers.dfthcsos.verify`
- **Shots:** 254,464 (verificación completa)
- **Resultado:** **PASS**
  - Score: 3,336,160,975
  - Q=730, T=93,237
  - error_1: 3.340 mHa (< 20 mHa ✅)
  - error_2: 19.371 mHa (< 20 mHa ✅)
  - Lambda: 308.361, lambda_eff: 49.0158

---

## Métricas Agregadas

| Métrica | invsqrt | DQI | dfthcsos | Geomean |
|---------|---------|-----|----------|---------|
| **Q** | 139 | 1,864 | 730 | — |
| **T** | 2,561 | 710,312 | 93,237 | — |
| **Score** | 390,005 | 2.994×10¹² | 3.336×10⁹ | — |
| **Ratio vs baseline** | 5.32499× | 8.16289× | 1.005827× | **3.52286×** |
| **Kaggle score** | — | — | — | **3.53019** |

**Kaggle (ref 58570485):** 3.53019, COMPLETE, 2026-11-19T16:43:47Z. +0.10099 (+2.945%) vs Adopted v3 (3.42920). Kaggle puntuó por arriba del geomean medido directo (3.52286, +0.208%) y del esperado (3.51878, +0.324%); sin explicación medida — reportado tal cual.

---

## Historial de Cambios (Esta Rama)

### Circuitos Adoptados
- **invsqrt:** `logshift2` — sin cambio vs Adopted v3 (Q=139, T=2,561, score 390,005.06)
- **DQI:** `swap42` — Toom-4 42 ANDs reemplaza Karatsuba 54 ANDs (2 bindings de import + `src/dqi_kmul42.py` nuevo) → Q=1,864, T=710,312 (vs 774,932 del omega/Karatsuba)
- **dfthcsos:** `lbfgs` — sin cambio vs Adopted v3 (Q=730, T=93,237, score 3,336,160,975)

### Verificaciones Completadas
1. **invsqrt:** Verificación exhaustiva dominio completo (3.13M x) + oficial 200M shots
2. **DQI:** Gold standard 102,400 tiros (Kali) + oficial 102,400 shots + Kaggle 3.53019
3. **dfthcsos:** Verificación completa 254,464 tiros

---

## Archivos en el Commit

| Archivo | Descripción |
|---------|-------------|
| `submission/final_submission.zip` | **Entrega (67,007,440 B)** — 13 archivos, SHA `44781dea...` |
| `submission/FINAL_SUBMISSION_2026-11-19.md` | Este documento |
| `src/dqi_kmul42.py` | **Nuevo** — multiplicador GF(2¹²) Toom-4 de 42 ANDs (128 l.) |
| `src/dqi_bm_stage_v1.py` | 1 línea — import swap a `dqi_kmul42` |
| `src/dqi_decoder_v1.py` | 1 línea — import swap a `dqi_kmul42` |
| `docs/swap42-2026-11-19/SWAP42_REPORTE.md` | Reporte de construcción + Gold del swap42 |

---

## Cómo Reproducir las Verificaciones

```bash
cd /home/deamon/quantum-circuit-compilation

# invsqrt (200M shots, ~45 min)
.venv/bin/python -m verifiers.invsqrt.verify_submission_invsqrt \
  submission/final_submission.zip --n-p 10 --beta 1 --shots-per-x 64

# DQI (102,400 shots, gold, ~10 min)
.venv/bin/python -m verifiers.dqi.verify_submission_dqi \
  submission/final_submission.zip --m 4095 --n 70 --degree 12 --r 2016 --num-shots 102400

# dfthcsos (254k shots, ~5 min)
.venv/bin/python -m verifiers.dfthcsos.verify \
  submission/final_submission.zip
```

---

## Estado Kaggle

- **Último envío:** ref 58570485 (2026-11-19T16:43:47Z)
- **Score público:** 3.53019 (nuevo personal best)
- **Selección final:** NO marcada (solo Elán la marca). Actuales: Adopted v3 (58289295, 3.42920) + v4 (58329687, 3.42257, lleva el sample).

---

## Próximos Pasos

1. [ ] Marcar selección final en Kaggle (ref 58570485) — solo Elán
2. [x] Push a GitHub (`git push origin local/swap42-2026-11-19`)
3. [ ] PR a `main` (solo con GO de Elán)

---

**Firmado:** Elán Zainos Corona — Fractal Core Research
**Fecha:** 2026-11-19

*GO de Elán (2026-11-19 ~11:35:24, vía Coordinador): "Sí. Sí, de una vez." — actualizar en GitHub el candidato swap42. Actualización del GATE original 09:24:36, pendiente hasta que saliera el score — salió 3.53019.*
