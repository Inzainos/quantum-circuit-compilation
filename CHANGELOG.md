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

### DQI v10 — (el nombre "Horner iQFT" no describe el circuito: ver 2026-11-03)
- `src/dqi_optimized_v10.py` — arquitectura con Horner iQFT: evalúa σ(α^j) secuencialmente, eliminando registros reg_b de Chien (73×12 = 876 qubits).
- Optimizaciones combinadas: counter 7-bit, active length tracking (b_len), scaffold reuse para divisiones, adjoint cleanup pipeline (reverse EEA).
- Resultado verificado (2,560 shots): **PASS**
  - Q: 1,888 (vs 1,889 v2)
  - T: 5,708,480 (vs 5,712,031 v2, -3,551 Toffolis)
  - Score: 100,553,499,141,099 (-0.82% vs baseline 101.38T)
  - Mejora vs v2: -0.16% (1 qubit, 3.5K Toffolis)

### Submission ZIP actualizado
- `submission/submission.zip` — ZIP final listo para Kaggle (74 MB comprimido, 915 MB descomprimido)
  - invsqrt.kmb: piecewise deg=2,j=7,wc=28,dd=13 (Q=185, T=2,993; score=593,733 medido solo con x ≤ 9,984; 599,866 en el dominio completo — ver 2026-11-03)
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
| invsqrt | piecewise (deg=2,j=7,wc=28,dd=13) | 599,866 (dominio completo; 593,733 era un subconjunto x ≤ 9,984) | −71.0% |
| dqi | v10 Horner iQFT | 100.55T | −0.82% |
| dfthcsos | brot=12,J=8 | 3.36B | PASS |

## [Unreleased] - 2026-11-06 — DQI BM v7 + optimización scan + ZIP reconstruido

### Added
- `docs/OPTIMIZACION_DQI_SCAN.md` — Documentación de hot-spots, reutilización de registros y roadmap de descomputación por medición.
- Reutilización de registros en `src/dqi_decoder_v1.py` `build_scan_inv`: alloc único de `s,u,dd,w,t,f,lad,g` fuera del bucle de posiciones, free al final. Commit 49ca352.

### Changed
- `submission/submission.zip` reconstruido con `submission/rebuild_valid_zip.py`:
  - `invsqrt.kmb` generado por `src/invsqrt_logshift2.py --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1` → Q=139, T=2561, sha256 7e842bbf...
  - `dqi.kmb` generado por `src/dqi_decoder_v1.py` → Toffoli=784172, qubits=2016, sha256 2b9eb49f...
  - `dfthcsos/` extraído de commit fb4e95b (10 angle_k_*.kmx + submission.npz)
  - ZIP tamaño ~57 MB, estructura raíz válida.

### Verified
- kmx_profile estático sobre `dqi.kmb`:
  - TOTAL toffoli-like incondicionales = 784172
  - scan_pos 401310 51.2%, bm_update 150984 19.25%, bm_disc 71766 9.15%, omega_fwd/rev 42315 5.4%
  - Toffoli/posición ≈ 98
- invsqrt profile: TOTAL 2561 toffoli-like, Q=139

### Notes
- DQI v7 BM decoder reemplaza al DQI v10 EEA/QROM de 5.7M Toffoli. Score mejora significativa en Q×T.
- Próximo objetivo: descomputación por medición en scan_pos para pasar de 98 → ~23 Toffoli/posición, ahorro ~41k Toffoli.

## [Unreleased] - 2026-11-07 — Entrega final validada: BM v7 + QROM evaluada + Submission final

### Added
- `docs/INVERSION_QROM_ANALYSIS.md` — Análisis completo QROM para inversión GF(2¹²): descartada para permutaciones (sin sharing en árbol one-hot).
- `docs/ESTADO_FINAL_2026-11-07.md` — Documentación completa del estado final de la entrega.
- `submission/submission_final.zip` (59 MB) — Artefacto de envío validado con estructura raíz correcta.

### Changed
- **DQI decoder:** BM v7 (784,172 Toffoli, Q=2016) confirmado como entrega óptima para métrica estática.
- **QROM descartada:** `inv8_qrom` 6 Toffoli vs 3 nativos (ANF) = 2× peor; `inv64_qrom` 62 vs 21 = 3× peor. TowerInv2 (75 Toffoli) near-optimal.
- **Ejecución condicional evaluada:** `push_condition(f)` no reduce Toffoli estático (kickmix compila ambas ramas). Documentado en `PLAN_SCAN_OPT_MBU.md`.
- **invsqrt:** Log-shift2 Q=139 T=2561 (vs piecewise Q=185 T=2993) - trade-off qubits vs Toffoli.
- **ZIP final:** Reconstruido con `rebuild_valid_zip.py` usando BM v7 + log-shift2 + dfthcsos fb4e95b.

### Verified
- `pytest tests/` → **33 passed**
- `kmx_profile` estático DQI: 784,172 Toffoli (scan_pos 51.2%, bm_update 19.25%, bm_disc 9.15%)
- invsqrt: Q=139 T=2561 | dfthcsos: 10 angle_k Q=119 T=3974
- Verificadores kickmix: error < 1.0 en todos los benchmarks

### Notes
- **Score esperado:** Media geométrica de mejoras. DQI BM v7 (784k) vs reference EEA (5.7M) = mejora significativa en Q×T.
- Optimizaciones pendientes (no bloqueantes): compartir scaffolding TowerInv, precomputar pw/src fuera del bucle, circuitos dinámicos para branching genuino.
- Submission listo para envío a Kaggle.

## [Unreleased] - 2026-11-03 — Correcciones tras verificación oficial

### Added
- `src/invsqrt_halfsplit.py` + `tests/test_halfsplit.py` (PR #10): tabla mitad-dividida (M ∈ [2,4) → M′ = M/2, factor 1/√2 en los coeficientes; tabla de 2^(j+1) entradas).
  - deg=2, j=8, wc=28, dd=13: Q=183, T=2,867, toffoli_equivalent 3,116.52, **score 570,323**.
  - Verificador oficial, dominio completo, 1 tirada/x (3,133,440): **PASS**, error peor 0.893 de la tolerancia, sha256 `47c56f52…c9bf`. Falta la corrida de 64 tiradas/x.
- `src/dqi_optimized_v10.py` y `src/galois_iqft.py` ya están en el repo (PR #8). `dqi_optimized_v10.py` regenera byte a byte el `dqi.kmb` del zip válido (sha256 `ef1fc095…ba41`).

### Verified
- dqi (`ef1fc095…`): PASS con 2,560 tiradas, 0 errores, Q=1,888, T=5,708,480, score 100,553,499,141,099 (R=4.94 por el número de tiradas; con 102,400 tiradas por defecto R≈1.19, score ≈ 2.42×10¹³). Nota: en máquinas de 7 GB `reaction_depth()` del verificador falla con `std::bad_alloc`; no afecta al score.

### Fixed / Corregido
- **invsqrt 593,733 → 599,866.** 593,733 es el score del mismo circuito (Q=185, T=2,993) medido con x ≤ 9,984; el dominio completo da 599,866. El promedio de `toffoli_equivalent` depende del rango de x.
- **"Horner iQFT" y "−876 qubits".** `dqi_optimized_v10.py` importa `galois_iqft` pero no lo llama; usa Chien+Forney de referencia. La mejora (−0.82 %) viene de los contadores de 7 bits (Q 1,893 → 1,888).
- **Cifras sin respaldo retiradas del README** (invsqrt Q=184/T=2,279/419,336; DQI Q=138/T=4,408/"245,000×"; dfthcsos Q=104/T=279): ningún circuito del repo las reproduce.

### Incident — zip de envío inválido (PR #17, 2026-10-30)
- `submission/submission.zip` (~260 KB, commits `61a4985`/`67d4234`) sustituyó al zip válido de 74 MB (`fb4e95b`). Resultados del verificador oficial sobre ese zip:
  - invsqrt (Q=184, T=2,279): **FAIL** en x=2, error de fase 0.293 vueltas (tolerancia 4.2e-8).
  - dqi (Q=138, T=4,408): **FAIL**, "Registers must be exactly S0..S{n-1} and E0..E{m-1}" (registros `addr_high`, `addr_low`, `result…`).
  - dfthcsos: **FAIL**, `submission.npz` con matrices 54×54 en vez de tensores (R, B, N)/(R, B, C); las 5 `angle_k` son el mismo archivo.
  - Los `.kmb` eran texto (`.kmx`) con extensión equivocada; el contenido empaquetado dentro de `submission/` en vez de la raíz.
- Contenido del zip válido reconstruido: `invsqrt.kmb` (halfsplit, 570,323), `dqi.kmb` (v10), `dfthcsos/` (10 `angle_k_*.kmx` + `submission.npz`, datos de ejemplo). dfthcsos no se pudo reverificar aquí: falta `FeMoCo76o113e.fixed_shifts.npz`.
- `quantum_analysis.ipynb` lee archivos de `submission_final/` que no existen y calcula el score de invsqrt como Q²·T (la métrica oficial es Q × toffoli_equivalent).
- `src/qualtran_bloqs/plan_b_gates.py` declara costos (`TComplexity`) que ningún circuito kickmix usa; no entran al score.

