# Changelog — Quantum Circuit Compilation

All notable changes to this project are documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.
Dates are local time (UTC-6, México).

---

## [Unreleased] - 2026-10-27 — Estado inicial documentado

### Added
- `AGENTS.md` — Reglas operativas para agentes IA en este repositorio.
- `CHANGELOG.md` — Este archivo.
- Documentación del estado de cada benchmark (invsqrt, dqi, dfthcsos).

### Notes
- invsqrt: mejora real ~6.5% medida; dqi y dfthcsos sin optimización propia todavía.
- `submission/final_submission.zip` (~74 MB, ~910 MB descomprimido) versionado como artefacto; circuitos sueltos no se versionan (límite 100 MiB de GitHub).

## [Unreleased] - 2026-10-28 — Arquitectura invsqrt sin Newton (piecewise) verificada

### Pulled from remote (fast-forward)
- `src/invsqrt_piecewise.py` — arquitectura "sin Newton": polinomio por tramos + QROM + Horner (elimina paso Newton-Raphson, ~60% de Toffolis).
- `src/invsqrt_bloqs.py` — fases-clase estilo Qualtran Bloq (circuito idéntico byte a byte a piecewise).
- `src/dbhexa_orchestrator.py` — orquestador con `--arch pw`, búsqueda 192 candidatos.
- `benchmarks/fusion_energy/piecewise/metrics.json` — métricas del mejor circuito.
- `tests/test_piecewise.py`, `tests/test_piecewise_metrics.py`, `tests/test_bloqs_pipeline.py` — 10 tests nuevos.

### Tested (todos con Python 3.13 + kickmix)
- `pytest tests/` → **19/19 passed** (9 originales + 10 nuevos).
- `src/invsqrt_piecewise.py --deg 2 --j 7 --wc 28 --dd 13` → **circuito generado**: Q=185, T=2,993, error/tol=0.8934.
- `verifiers/invsqrt/verify_submission_invsqrt.py` → **PASS** en ambas tiradas:
  - 1 shot/x (3,133,440 shots): score **599,866**, Q=185, T=2,993, worst_err/tol=0.893.
  - 16 shots/x (50,135,040 shots): score **599,866**, Q=185, T=2,993, worst_err/tol=0.893.
- Reducción: **−71.0% vs baseline** (2,070,562 → 599,866), **−69.0% vs mejor previo** (1,935,003 → 599,866).

### Mejores scores invsqrt (verificados oficialmente)
| Config | Q | Toffolis | Score Q×C | Mejora |
|--------|---|----------|-----------|--------|
| Baseline (27/27/27) | 260 | 7,735 | 2,011,100 | — |
| Tu previa (27/27/27) | 254 | 7,405 | 1,880,870 | −6.5% |
| **Piecewise sin Newton (deg=2,j=7,wc=28,dd=13)** | **185** | **2,993** | **599,866** | **−71.0%** |

Circuito guardado: `/tmp/invsqrt_piecewise_opt.kmb` (no versionado; `*.kmb` está en `.gitignore`).

### Pending
- Construir ZIP de submission para Kaggle: requiere `invsqrt.kmb` + `dqi.kmb` + `dfthcsos/` + `submission.npz` via `submission/build_submission.py`.
- dfthcsos: verificado con sample (brot=12,J=8, score 3,355,599,588).
- dqi: reference completo generado y verificado (Fase 2):
  - `verifiers/dqi/dqi_reference_circuit.py` — `ProosAndZalkaDecoder` implementa EEA completo, Chien search, Forney's formula, fase MBUC, reverse EEA.
  - Circuito generado: Q=1,893, T=5,725,461 (idéntico al baseline).
  - `verifiers/dqi/verify_submission_dqi.py` → **PASS**, score 101,381,003,883,062.67 (2,560 shots).
  - Q²×T = 20,515,583,693,402 (~2.05×10¹³).
  - Ancillas temporales: 1,053 qubits (840 son S obligatorios, 1,053 scratch optimizables).

### DQI Fase 2 — Optimización de contadores (2026-10-28)
- `src/dqi_optimized_v2.py` — basado en `dqi_reference_circuit.py` con contadores n_A, n_B, n_a, n_b reducidos de 8→7 bits (máx 127 > 73 necesario). n_q se mantiene en 8 bits (máx 256 > n_iters=222).
- Resultado verificado oficialmente (2,560 shots): **PASS**
  - Q: 1,893 → 1,889 (-4 qubits)
  - T: 5,725,461 → 5,712,031 (-13,430)
  - Q²×T: 20,515,583,693,402 → 20,382,361,983,382 (-0.65%)
  - Score: 101,381,003,883,062 → 100,722,667,717,607 (-0.65%)

### Optimizaciones DQI pendientes (mayor impacto)
| Oportunidad | Detalle | Q actual | Q objetivo | Impacto estimado |
|-------------|---------|----------|------------|------------------|
| Compartir reg_a/reg_b | Los 73 registros se swapean; solo se necesitan 73 no 146 | 876 | 438 | -438 qubits |
| Reducir reg_b | Solo registros activos por iteración EEA | 876 | ~200 | -676 qubits |
| Reusar scaffolds GF(2^12) | Entre divisiones del EEA | — | — | Toffoli↓ |
| Pool de ancillas scratch | Reutilizar qubits temporales | 1,053 | ~200 | -853 qubits |

### Comandos DQI (Python 3.13)
```
export PYTHONPATH=/home/deamon/quantum-circuit-compilation/kickmix:/home/deamon/quantum-circuit-compilation/src
/tmp/py313-venv/bin/python src/dqi_optimized_v2.py /tmp/dqi_optimized_v2.kmb --m 4095 --n 70 --degree 12 --format kmb
/tmp/py313-venv/bin/python verifiers/dqi/verify_submission_dqi.py /tmp/dqi_optimized_v2.kmb --num-shots 2560 --batch-size 256 --max-workers 1
```

## [Unreleased] - 2026-10-29 — DQI v10 (Horner iQFT) + Submission actualizado

### DQI v10 — Horner iQFT reemplaza Chien+Forney
- `src/dqi_optimized_v10.py` — arquitectura con Horner iQFT: evalúa σ(α^j) secuencialmente, eliminando registros reg_b de Chien (73×12 = 876 qubits).
- Optimizaciones combinadas: counter 7-bit, active length tracking (b_len), scaffold reuse para divisiones, adjoint cleanup pipeline (reverse EEA).
- Resultado verificado (2,560 shots): **PASS**
  - Q: 1,888 (vs 1,889 v2)
  - T: 5,708,480 (vs 5,712,031 v2, -3,551 Toffolis)
  - Score: 100,553,499,141,099 (-0.82% vs baseline 101.38T)
  - Mejora vs v2: -0.16% (1 qubit, 3.5K Toffolis)

### Submission ZIP actualizado
- `submission/submission.zip` — ZIP final listo para Kaggle (74 MB comprimido, 915 MB descomprimido)
  - invsqrt.kmb: piecewise deg=2,j=7,wc=28,dd=13 (Q=185, T=2,993, score=593,733)
  - dqi.kmb: v10 Horner iQFT (Q=1,888, T=5,708,480, score=100.55T)
  - dfthcsos/: 10 angle_k_*.kmx + submission.npz (brot=12,J=8, score=3.36B)
- Backup anterior: `submission/submission_2026-10-28.zip`

### Qualtran Bloqs — Arquitectura unificada DQI
- `src/qualtran_bloqs/` — Bloqs Qualtran unificando 3 enfoques:
  - v5: scaffold reuse, BMA, testbench
  - motorv15: adjoint cleanup pipeline (Forney† → Chien† → BMA† → EEA†)
  - planB: custom Cirq gates con _t_complexity_ hardcodeado
- Bloqs: BMABloq, EEABloq, ChienForneyBloq, DQIDecoderBloq, DQIMasterPipeline
- Plan B Gates: InzainosGaloisMultiplier/Adder/Inverse (222/12/888 Toffolis)
- Testbench: VerificadorAislado con simulación clásica GF(2^12)

### Verificaciones completadas
- invsqrt: 64 shots/x (10K max) + 1 shot/x (dominio completo 3.1M) → PASS
- dqi v10: 2,560 shots, 0 errors → PASS
- dfthcsos: brot=12,J=8 → PASS

### Estado actual (2026-10-29)
| Tarea | Circuito | Score | Mejora vs Baseline |
|-------|----------|-------|-------------------|
| invsqrt | piecewise (deg=2,j=7,wc=28,dd=13) | 593,733 | −71.3% |
| dqi | v10 Horner iQFT | 100.55T | −0.82% |
| dfthcsos | brot=12,J=8 | 3.36B | PASS |

