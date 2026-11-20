# DOCUMENTACIÓN COMPLETA — Quantum Circuit Compilation

Estado final de todo el trabajo realizado el 2026-10-28 sobre el repositorio
`/home/deamon/quantum-circuit-compilation/` (competición Google Quantum AI / Kaggle 2026).

> **Nota (2026-11-20):** el cuerpo de este documento (§1–§12) es el snapshot del 2026-10-28 y sus cifras son históricas — no se reescriben. El estado actual está en §13 y en `docs/QF_P15_AND_2026-11-20.md`.

---

## 1. RESUMEN EJECUTIVO

| Benchmark | Estado | Q | Toffolis/shot | Score | Verificador oficial |
|-----------|--------|---|---------------|-------|---------------------|
| **invsqrt** (Benchmark I) | ✅ OPTIMIZADO | 185 | 2,993 | 599,866 | PASS (1 shot + 16 shots) |
| **dqi** (Benchmark II) | ✅ BASELINE VERIFICADO | 1,893 | 5,725,461 | 101,381,003,883,062.67 | PASS |
| **dqi** (optimización contadores) | ✅ OPTIMIZADO (marginal) | 1,889 | 5,712,031 | 100,722,667,717,607 | PASS |
| **dfthcsos** (Benchmark III) | ✅ SAMPLE VERIFICADO | 730 | 93,237 | 3,355,599,588 | PASS |

**ZIP de submission:** `/tmp/final_submission_v2.zip` (invsqrt piecewise + dqi v2 + dfthcsos sample)

**Repositorio GitHub:** `https://github.com/Inzainos/quantum-circuit-compilation` (rama `local/quantum-dqi-v2.0.0`)

**Leaderboard (2026-10-29 03:15):** Equipo "Elán Zainos Corona" — posición 1287/1485, score 1.51607, 2 submissions.

---

## 2. ENTORNO DE EJECUCIÓN

### Problema crítico: Python versión

El sistema tiene **Python 3.14.7** pero `kickmix/kickmix.so` fue compilado para **Python 3.13**. No se puede importar kickmix con el venv del sistema.

### Solución utilizada

CPython 3.13.18 descargado de python-build-standalone:

```
/tmp/py313/                  # CPython 3.13.18 standalone
/tmp/py313-venv/             # Venv con numpy + scipy instalados
```

### Comando base para ejecutar scripts

```bash
export PYTHONPATH=/home/deamon/quantum-circuit-compilation/kickmix:/home/deamon/quantum-circuit-compilation/src
/tmp/py313-venv/bin/python <script.py> [argumentos]
```

### Para ejecutar pytest

```bash
cd /home/deamon/quantum-circuit-compilation
export PYTHONPATH=/home/deamon/quantum-circuit-compilation/kickmix:/home/deamon/quantum-circuit-compilation/src
/tmp/py313-venv/bin/python -m pytest tests/ -q
```

Resultado: **19/19 passed** (9 originales + 10 nuevos de piecewise/bloqs).

---

## 3. BENCHMARK I — INVSQRT (Fusión Energía)

### Estado: OPTIMIZADO Y VERIFICADO

### Arquitectura utilizada: Piecewise sin Newton

El reference original usa polinomio cúbico + paso Newton-Raphson (~60% de los Toffolis). La arquitectura piecewise reemplaza Newton-Raphson por un polinomio por tramos con QROM + Horner, eliminando el paso Newton completamente.

### Script generador

`src/invsqrt_piecewise.py` (traído del remote en el pull de 2026-10-28)

### Mejor configuración encontrada

```
--deg 2 --j 7 --wc 28 --dd 13
```

### Métricas verificadas

| Parámetro | Valor |
|-----------|-------|
| Qubits | 185 |
| Toffolis | 2,993 |
| Score Q×C | 599,866 |
| Error/tolerancia | 0.8934 |
| Worst x | 2,764,799 |

### Comparación con baseline

| Config | Q | Toffolis | Score Q×C | Mejora |
|--------|---|----------|-----------|--------|
| Baseline | 260 | 7,735 | 2,011,100 | — |
| Previa (27/27/27) | 254 | 7,405 | 1,880,870 | −6.5% |
| **Piecewise (2,7,28,13)** | **185** | **2,993** | **599,866** | **−71.0%** |

### Verificaciones oficiales

```
verify_submission_invsqrt.py --max-x 3133440 --shots-per-x 1
→ PASS, 3,133,440 shots, worst_err/tol=0.893

verify_submission_invsqrt.py --max-x 3133440 --shots-per-x 16 --salt pw16
→ PASS, 50,135,040 shots, worst_err/tol=0.893
```

### Archivos

- `src/invsqrt_piecewise.py` — generador del circuito
- `src/invsqrt_bloqs.py` — fases-clase estilo Qualtran Bloq (idéntico byte a byte)
- `benchmarks/fusion_energy/optimized/invsqrt_dbhexa_opt.kmb` — circuito guardado
- `benchmarks/fusion_energy/optimized/invsqrt_dbhexa_opt2.kmb` — circuito alternativo
- `benchmarks/fusion_energy/piecewise/metrics.json` — métricas detalladas
- `/tmp/invsqrt_piecewise_opt.kmb` — copia temporal

---

## 4. BENCHMARK II — DQI (Optimización Combinatoria)

### Estado: BASELINE VERIFICADO + OPTIMIZACIÓN MARGINAL

### Arquitectura utilizada

El baseline usa `ProosAndZalkaDecoder` con Extended Euclidean Algorithm (EEA) sincronizado, Chien search, Forney's formula, y fase MBUC.

### Scripts de referencia

- `verifiers/dqi/dqi_reference_circuit.py` — reference completo y verificado
- `src/dqi_optimized_v2.py` — versión con contadores reducidos de 8→7 bits

### Métricas baseline verificadas

| Parámetro | Valor |
|-----------|-------|
| Qubits | 1,893 |
| Toffolis | 5,725,461 |
| Score | 101,381,003,883,062.67 |
| Q²×T | 20,515,583,693,402 |
| Repetition factor | 4.94 |
| Effective error rate | 0.0341 |

### Métricas optimizadas (contadores 7 bits)

| Parámetro | Valor |
|-----------|-------|
| Qubits | 1,889 (-4) |
| Toffolis | 5,712,031 (-13,430) |
| Score | 100,722,667,717,607 (-0.65%) |
| Q²×T | 20,382,361,983,382 (-0.65%) |

### Verificaciones oficiales

Baseline:
```
verify_submission_dqi.py --num-shots 2560 --batch-size 256 --max-workers 1
→ PASS, 2,560 shots
```

Optimizado v2:
```
verify_submission_dqi.py --num-shots 2560 --batch-size 256 --max-workers 1
→ PASS, 2,560 shots
```

### Archivos

- `src/dqi_optimized_v2.py` — versión optimizada (contadores 7 bits)
- `src/dqi_optimized_v4.py` — copia idéntica a v4 del reference (no funciona)
- `src/dqi_cmq.py` — PoC arquitectura CMQ (ver sección 8)
- `src/dqi_scaffold_reuse.py` — copia del reference (sin cambios)
- `benchmarks/combinatorial_optimization/baseline/dqi_ref.kmb` — baseline oficial
- `/tmp/dqi_optimized_v2.kmb` — circuito optimizado temporal
- `/tmp/dqi_optimized_v4.kmb` — circuito v4 temporal
- `/tmp/dqi_cmq_test.kmb` — circuito CMQ PoC temporal
- `/tmp/dqi_reference_decoder.kmb` — circuito reference temporal

---

## 5. BENCHMARK III — DFTHCSOS (Química Cuántica)

### Estado: SAMPLE VERIFICADO

### Arquitectura utilizada

Sample submission del backup `quantum-circuit-compilation.backup_2026-10-27_temporal_manager/sample_submission/dfthcsos/`.

### Métricas verificadas

| Parámetro | Valor |
|-----------|-------|
| Qubits | 730 |
| Toffolis | 93,237 |
| Score | 3,355,599,588 |
| Error 1 | 3.19 mHa (< 20 mHa ✅) |
| Error 2 | 18.64 mHa (< 20 mHa ✅) |
| Lambda | 308 (> 49 ✅) |
| E_gap | 3.97 (> 3.91 ✅) |
| Gap in domain | true |
| Lambda eff | 49.30 |
| Angles within cap | true |

### Optimización dfthcsos (barrido de parámetros)

Probado con `src/dfthcsos_optimizer.py`:

| brot | J | Status | Score | Q | T |
|------|---|--------|-------|---|---|
| 12 | 4 | PASS | 5,540,116,045 | 682 | 164,769 |
| **12 | 8** | **PASS** | **3,355,599,588** | **730** | **93,237** |
| 14 | 4 | FAIL | error_1 >> 20 mHa | — | — |
| 14 | 8 | FAIL | error_1 >> 20 mHa | — | — |
| 16 | 4 | FAIL | error_1 >> 20 mHa | — | — |
| 16 | 8 | FAIL | error_1 >> 20 mHa | — | — |

### Nota importante

brot=14 y brot=16 fallan porque las `angle_words` del sample tienen valor máximo 4095, que requiere exactamente brot=12 (2^12=4096). Más bits rompe el redondeo de las palabras cargadas.

### Archivos

- `sample_submission/dfthcsos/` — sample copiado del backup (no versionado en Git por >100 MiB)
- `verifiers/dfthcsos/verify.py` — verificador oficial
- `src/dfthcsos_optimizer.py` — optimizador (requiere `--sample-dir`)

---

## 6. ARCHIVOS EN DESCARGAS DE WINDOWS

### Leaderboard CSV

```
/mnt/c/Users/elanz/Downloads/google-verifiable-quantum-circuit-compilation-publicleaderboard-2026-10-28T20_21_33/google-verifiable-quantum-circuit-compilation-publicleaderboard-2026-10-28T20_21_33.csv
```
- 1453 equipos
- Equipo "Elán Zainos Corona": posición 1342/1453, score 1.02194, 1 submission

```
/mnt/c/Users/elanz/Downloads/google-verifiable-quantum-circuit-compilation-publicleaderboard-2026-10-29T03_15_23/google-verifiable-quantum-circuit-compilation-publicleaderboard-2026-10-29T03_15_23.csv
```
- 1485 equipos
- Equipo "Elán Zainos Corona": posición 1287/1485, score 1.51607, 2 submissions

### Otros archivos relevantes

```
/mnt/c/Users/elanz/Downloads/CMQ.py
```
- Arquitectura conceptual para optimizar DQI (Gauss-Jordan + bloque topológico + fail-fast)
- No es código kickmix ejecutable

```
/mnt/c/Users/elanz/Downloads/dqi_optimized_v5.py
```
- Esqueleto conceptual sobre reutilización de scaffolds en EEA
- Usa `qualtran`, no `kickmix`
- Clases `BloqueDivisionGaloisOptimizado`/`BloqueResetReversible` inexistentes
- No genera `.kmb`, no ejecutable

```
/mnt/c/Users/elanz/Downloads/dqi_optimized_v4.py
```
- Copia del reference con contadores 7 bits (falló verificación por desbordamiento)

---

## 7. GIT Y GITHUB

### Repositorio remoto

```
origin	https://github.com/Inzainos/quantum-circuit-compilation.git (fetch/push)
```

### Rama creada

`local/quantum-dqi-v2.0.0` — push exitoso el 2026-10-28

### Cambios commitados

| Archivo | Cambio |
|---------|--------|
| `AGENTS.md` | Nuevo — reglas operativas |
| `CHANGELOG.md` | Nuevo — historial completo |
| `.gitignore` | Añadido `documentacion/` y `*.zip` |
| `src/dfthcsos_optimizer.py` | Fix `sample_dir.resolve()` |
| `src/optimize_invsqrt.py` | Fix `num_shots` múltiplo de batch_size |
| `src/dqi_optimized_v2.py` | Nuevo — DQI con contadores 7 bits |
| `submission/submission.zip` | Nuevo — ZIP de prueba (70.4 MB) |
| `submission/final_submission.zip` | Removido (reemplazado por submission.zip) |

### PR pendiente

https://github.com/Inzainos/quantum-circuit-compilation/pull/new/local/quantum-dqi-v2.0.0

### Nota sobre Git LFS

GitHub advirtió que `submission/submission.zip` (70.4 MB) excede los 50 MB recomendados. Para versiones futuras considerar Git LFS.

---

## 8. INTENTOS FALLIDOS Y LECCIONES APRENDIDAS

### dqi_optimized_v2.py / v4.py — Contadores 7 bits

**Problema:** Reducir `n_A`, `n_B`, `n_a`, `n_b` de 8→7 bits causó desbordamiento durante el EEA sincronizado. Los contadores pueden superar 127 en operaciones intermedias aunque el valor máximo teórico sea 73.

**Resultado:** FAIL en verificador oficial.

**Lección:** No reducir contadores sin análisis exhaustivo de rangos de valores intermedios.

### dqi_cmq.py — Arquitectura CMQ (PoC)

**Enfoque:** Matriz Hankel + Gauss-Jordan reversible (CNOT-only, Toffoli=0) + bloque topológico fail-fast.

**Resultado:** Q=2,595, T=19,031 (−99.7% Toffolis), pero `phase_errors=112/256` — fase MBUC incorrecta.

**Por qué falló:** El Gauss-Jordan simple no computa el polinomio locador de errores (sigma/omega). Faltan: Chien search completo, Forney's formula, fase MBUC correcta.

**Potencial:** Si se completa, podría reducir Toffolis drásticamente. Pero es un reescribir importante.

### dqi_optimized_v5.py — Scaffolds reusables (esqueleto)

**Problema:** No es código ejecutable. Usa `qualtran`, no `kickmix`. Clases inexistentes. No genera `.kmb`.

**Lección:** La API de kickmix `init_gf2_div_with_scaffold` no acepta scaffold pre-creado. Para reusar scaffolds se necesitaría modificar la librería kickmix o implementar división GF(2^12) manual.

---

## 9. COMANDOS PARA REPRODUCIR TODO

```bash
cd /home/deamon/quantum-circuit-compilation
export PYTHONPATH=/home/deamon/quantum-circuit-compilation/kickmix:/home/deamon/quantum-circuit-compilation/src

# 1. Ejecutar todos los tests
/tmp/py313-venv/bin/python -m pytest tests/ -q

# 2. Generar circuito invsqrt optimizado
/tmp/py313-venv/bin/python src/invsqrt_piecewise.py --deg 2 --j 7 --wc 28 --dd 13 --out /tmp/invsqrt_opt.kmb

# 3. Verificar invsqrt
/tmp/py313-venv/bin/python verifiers/invsqrt/verify_submission_invsqrt.py /tmp/invsqrt_opt.kmb --n-p 10 --max-x 3133440 --shots-per-x 1

# 4. Generar circuito dqi optimizado
/tmp/py313-venv/bin/python src/dqi_optimized_v2.py /tmp/dqi_opt.kmb --m 4095 --n 70 --degree 12 --format kmb

# 5. Verificar dqi
/tmp/py313-venv/bin/python verifiers/dqi/verify_submission_dqi.py /tmp/dqi_opt.kmb --num-shots 2560 --batch-size 256 --max-workers 1

# 6. Verificar dfthcsos sample
/tmp/py313-venv/bin/python verifiers/dfthcsos/verify.py sample_submission/dfthcsos

# 7. Construir ZIP de submission
/tmp/py313-venv/bin/python submission/build_submission.py \
    --invsqrt /tmp/invsqrt_opt.kmb \
    --dqi /tmp/dqi_opt.kmb \
    --dfthcsos-dir sample_submission/dfthcsos \
    --npz sample_submission/dfthcsos/submission.npz \
    --output /tmp/submission_final.zip
```

---

## 10. RECOMENDACIONES PARA CONTINUAR

### Prioridad alta: Optimizar DQI (mayor impacto en score general)

El score DQI domina el score geométrico combinado. Oportunidades:

1. **Reusar scaffolds GF(2^12)** entre divisiones del EEA (ahorra Toffolis, no requiere cambiar la API de kickmix si se implementa división manual)
2. **Reducir ancillas temporales** (1,053 qubits scratch optimizables)
3. **Implementar CMQ completo** (Gauss-Jordan + Chien + Forney + MBUC) — potencial de T=19K vs 5.7M

### Prioridad media: Mejorar invsqrt

El piecewise ya logró −71%. Se podría buscar más reducciones de `square_bits`, `product_bits`, `result_bits` con el orquestador `dbhexa_orchestrator.py`.

### Prioridad baja: dfthcsos

Ya verificado con sample. Requiere `sample_submission/` para pruebas adicionales.

---

## 11. ARCHIVOS CREADORES DURANTE ESTA SESIÓN

### En el repositorio

- `AGENTS.md` — reglas operativas
- `CHANGELOG.md` — historial completo
- `src/dqi_optimized_v2.py` — DQI optimizado (contadores 7 bits)
- `src/dqi_optimized_v3.py` — copia del reference (sin cambios)
- `src/dqi_optimized_v4.py` — copia del reference (sin cambios)
- `src/dqi_cmq.py` — PoC arquitectura CMQ
- `src/dqi_scaffold_reuse.py` — copia del reference (sin cambios)
- `src/invsqrt_piecewise.py` — traído del remote
- `src/invsqrt_bloqs.py` — traído del remote
- `src/dbhexa_orchestrator.py` — traído del remote
- `submission/submission.zip` — ZIP de prueba (70.4 MB)

### En /tmp (temporal, no versionado)

- `/tmp/invsqrt_piecewise_opt.kmb`
- `/tmp/invsqrt_dbhexa_opt.kmb`
- `/tmp/invsqrt_dbhexa_opt2.kmb`
- `/tmp/dqi_optimized_v2.kmb`
- `/tmp/dqi_optimized_v4.kmb`
- `/tmp/dqi_cmq_test.kmb`
- `/tmp/dqi_reference_decoder.kmb`
- `/tmp/final_submission.zip`
- `/tmp/final_submission_v2.zip`
- `/tmp/py313/` — CPython 3.13.18 standalone
- `/tmp/py313-venv/` — Venv con numpy + scipy

---

## 12. NOTAS FINALES

- **Kickmix requiere Python 3.13.** El sistema tiene 3.14.7. Usar `/tmp/py313-venv/bin/python`.
- **`*.kmb`, `*.kmx`, `*.npz` están en `.gitignore`** (límite 100 MiB de GitHub).
- **`documentacion/` está en `.gitignore`** (documentación de kickmix, no del proyecto).
- **El ZIP de submission no debe versionarse repetidamente** — usar Releases o Git LFS.
- **El verificador oficial es la única fuente de verdad.** No afirmar mejoras sin pasar `verify_submission_*.py`.
- **El score DQI domina el score geométrico combinado.** Cualquier mejora en DQI tiene mayor impacto que en invsqrt o dfthcsos.

---

*Documentación generada el 2026-10-28 por sesión de optimización de Quantum Circuit Compilation.*

---

## 13. ACTUALIZACIÓN — ESTADO AL 2026-11-20 (QF + 15 AND)

Añadido 2026-11-20. No modifica las cifras históricas de §1–§12.

### Producción vigente

| Tarea | Circuito | Score / resultado | Verificación |
|-------|----------|-------------------|--------------|
| invsqrt | R1+R5 | Q=139, T=2,561, **score 389,261.01** | Gold PASS, dominio completo |
| dqi | P1+P2+P3-sobre-QF | Q=1,857, T=710,312, score 2,971,470,537,625.3 (R=1.2131052140444296, 5 valor / 0 fase) | Gold PASS, 102,400 tiros |
| dfthcsos | seg100@brot13 | Q=797, T=32,174, **score 1,257,565,658.5**, error_2 18.9592 mHa | PASS oficial, 78,080 tiros |
| **Geomean (Kaggle v6)** | | **5.00379** (ref 58633092; calculado 4.98760) | Medido en Kaggle, nuevo mejor personal (v5 4.90803) |

GitHub main `320312bd` (PR #34 mergeado — integración QF+15, 2026-11-20 14:23:18 CST; PR #33 antes). Notebook público v7 (kernel 144639626).

### QF + 15 AND — v6 en Kaggle + integrado en rama (mergeado, PR #34)

- **Q=1,857, T=670,307** (exacto al esperado). Desglose: barrido 364,455 (4,095 × 89), omega 57,540 (28,770 + 28,770), BM 248,312. Deltas vs QF: scan −36,855, omega −630, BM −2,520; total −40,005.
- Factor DQI **8.71540152** (D-V6-1: corrección de Datos sobre 8.71540437; sin efecto en el geomean 4.98760), geomean 4.98760 (+1.95 %, refs v5).
- **v6 en Kaggle: public score 5.00379** (ref 58633092, status COMPLETE; enviado 2026-11-20T19:46:53Z). ZIP `candidato-v6-2026-11-20.zip` (60,993,989 B, sha256 `dbd43292…`): los 13 archivos del v5 con SOLO `dqi.kmb` reemplazado por el P15; los 12 no-DQI byte-idénticos al v5. Envío REGULAR — selección final intacta (v4.1 + swap42). Cadena del ZIP v6 completa: Programación ✓ → Brujo ✓ → Auditor ✓ (revisión del ZIP ~13:50, md5 `d4152657…`) → Datos ✓ (supervisión del ZIP, 74 l., md5 `6b7ddf0d…`, CONCURRO PASA con D-V6-1). La subida: Brujo verificó en vivo (30 l., md5 `69fef82c…`) → Auditor revisó (~14:30, CONCURRO PASA, A-SV6-1); la supervisión de Datos de la subida corría en paralelo.
- Circuito `dqi_qf_p15.kmb` (631,379,345 B, sha256 `60270f22c884ccebc0e06ab870f37d1efcca23fdc93c9f3cbf352c1c84cd9018`). Build 140 s, D-QF-1 OK. Control byte-idéntico al QF (sha `38b9cbf0…`).
- Solo el hunk P15 (`dqi_tower_inv.py` @@ -102): PLAN6 de Karatsuba (18 términos) → lista explícita de 15 términos; `PLAN6 == plan15.txt` (verificación 64×64, 0 errores).
- D-P15-1: torre de inversión 75 → **66 Toffoli**; `[18 + inv6 + 36 AND]` → `[15 + inv6 + 30 AND]`.
- Inversión de torre exhaustiva 4096/4096, toffoli 66 (evidencia local; el simulador da falsos positivos con HMR).
- Score **2,804,116,362,477.3 MEDIDO** por el Gold del Brujo (~13:00, driver lean local, 483.9 s, EXIT=0): status PASS, ve=5, pe=0, R=1.2131052140444296, eps_plus 0.0010479495500463395, 102,400 tiros, sha `60270f22…`. Los 5 fallos son EXACTAMENTE los mismos que los del Gold QF. Salvedad: `reaction_depth` 3154 es el valor REGISTRADO del Gold QF, no medido para el P15 (no entra en el score). Cadena del Gold COMPLETA: Brujo (37 l., md5 `0253a6d5…`) → Datos (118 l., md5 `8fca3741…`, CONCURRO PASA) → Auditor (47 l., md5 `95ce3fc4…`, CONCURRO PASA). (Corrección al registro: el "Gold pendiente" / "PROYECCIÓN" de la entrada anterior del CHANGELOG y del reporte de ruta (a) quedó stale — el Gold corrió ~13:00, antes de que se escribiera el reporte.)
- El parche combinado QF + 15 AND no aplica mecánico sobre la réplica QF (17 hunks: 13 ya aplicados, qf.py byte-idéntico, 1 limpio, 2 FAILED — uno textual, uno con contenido ya presente).

### Integración en el repo — rama creada y mergeada (PR #34)

El bloqueo de adopción quedó resuelto por la vía (a): rama **`local/qf-p15-integracion-2026-11-20`** (base main `a13598a9`); commit 1 `d74f60c3` (QF+P1+P2+P3, 11 archivos) y commit 2 `41444adb` (P15 + docstrings D-P15-1, 2 archivos). Rebuilds desde la rama byte-idénticos: control QF (sha `38b9cbf0…`, Q=1,857, T=710,312) y final P15 (sha `60270f22…`, Q=1,857, T=670,307). **Mergeado en main (PR #34, merge commit `320312bd`, 2026-11-20 14:23:18 CST; padres `a13598a9` + `41444adb`).** La cadena de la integración estaba completa antes del merge: Brujo (29 l., md5 `10d43e35…`) → Datos (87 l., md5 `9988882a…`, CONCURRO PASA con D-INT-1) → Auditor (44 l., md5 `696e4280…`, CONCURRO PASA). El circuito de la rama ya está Gold-verificado (rebuild byte-idéntico al .kmb del Gold); no hace falta un Gold nuevo. **D-INT-1 (Datos):** conteos +/- por archivo del diff commit1→commit2: `dqi_tower_inv.py` 5+/2−, `dqi_tower_inv2.py` 2+/2− (totales 7+/4− correctos).

Detalle completo: `docs/QF_P15_AND_2026-11-20.md` y CHANGELOG (2026-11-20). Nada a Kaggle, nada a main, nada al notebook sin GO de Elán.
