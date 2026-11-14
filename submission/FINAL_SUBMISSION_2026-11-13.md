# Final Submission — Google Quantum AI Verifiable Quantum Circuit Compilation

**Fecha:** 2026-11-13  
**Rama:** `local/final-submission-2026-11-13`  
**Commit:** ver tag `v2026-11-13-final`  
**Autor:** Elán Zainos Corona (Fractal Core Research)

---

## Resumen Ejecutivo

Entrega final para la competición **Google Quantum AI - Verifiable Quantum Circuit Compilation** (Kaggle 2026). Tres benchmarks verificados con el **verificador oficial kickmix** (gold standard):

| Benchmark | Circuito | Métricas | Verificación Oficial |
|-----------|----------|----------|---------------------|
| **invsqrt** (Fusión) | `logshift2` (deg=2, j=8, wc=28, dd=13) | Q=139, T=2,561, Score=390,005.06 | ✅ **PASS** (200,540,928 shots) |
| **DQI** (Optimización) | `omega/Karatsuba` (sin t, fusión + E1d) | Q=1,864, T=774,932, Score=3.235×10¹² | ✅ **PASS** (102,400 tiros, gold) |
| **dfthcsos** (Química) | `lbfgs` (65,60,60, brot=12, J=8) | Q=730, T=93,237, Score=3.336×10⁹ | ✅ **PASS** (254,464 tiros) |

**Geomean calculado:** ~3.43×  
**Kaggle medido (ref 58289295):** **3.42920** (nuevo personal best, +0.37% vs anterior 3.41660)

---

## Archivo de Entrega

**ZIP:** `submission/final_submission.zip`  
**SHA256:** `83b0c75615274769a36d3822da2f8f5c63470dc59f6820bee516a0952c7b1c4d`  
**Tamaño:** 66,674,933 bytes (63.6 MB comprimido; 659,187,615 bytes / 629 MB sin comprimir)  
**Estructura:** 13 archivos

```
final_submission.zip
├── invsqrt.kmb                    (437 KB)   — logshift2
├── dqi.kmb                        (629 MB)   — omega/Karatsuba
└── dfthcsos/
    ├── angle_k_0.kmx .. angle_k_9.kmx  (10 circuitos)
    └── submission.npz            (4.5 MB)  — factorización lbfgs
```

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
- **Circuito:** `omega/Karatsuba` (sin t, fusión mul+inv, E1d)
- **SHA256:** `209d53e2da4e815797a8f420fd91372f84c256ad9a2374f67dbbbcb0a1a5c884`
- **Verificador:** `verifiers.dqi.verify_submission_dqi`
- **Shots:** 102,400 (gold standard, m=4095, n=70, degree=12, r=2016)
- **Resultado:** **PASS**
  - Score: 3,234,735,110,839
  - Q=1,864, T=774,932, Toffoli-equiv=774,932
  - Value errors: 2, Phase errors: 0
  - eps_plus: 0.0009488 (< 1/16), R: 1.2014
  - Circuit SHA256 match: ✅ byte-idéntico

### dfthcsos — Quantum Chemistry (FeMoCo)
- **Circuito:** `lbfgs` (65,60,60, brot=12, J=8, batch=8)
- **Factorización:** `submission.npz` (U, W, H2_I, H1_I, Hsym_lower + tree_edges)
- **SHA256 submission:** `d89772be6b4b8484cc090ea065baf61c0f8cedc2ad0e6689106c44ef87b7fa4d`
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
| **T** | 2,561 | 774,932 | 93,237 | — |
| **Score** | 390,005 | 3.235×10¹² | 3.336×10⁹ | — |
| **Ratio vs baseline** | 5.31× | 7.49× | 1.01× | **~3.43×** |
| **Kaggle score** | — | — | — | **3.42920** |

**Rank Kaggle (ref 58289295):** 2,545 / 2,940 equipos

---

## Historial de Cambios (Esta Rama)

### Circuitos Adoptados
- **invsqrt:** `logshift2` — mejora sobre `piecewise` (Q=185→139, score 599,866→390,005)
- **DQI:** `omega/Karatsuba` — fusión mul+inv (F1b) + E1d + sin t → Q=1,864, T=774,932 (vs baseline Q=1,949, T=784,172)
- **dfthcsos:** `lbfgs` — optimización de factorización tensorial (brot=12, J=8)

### Verificaciones Completadas
1. **invsqrt:** Verificación exhaustiva dominio completo (3.13M x) + oficial 200M shots
2. **DQI:** Gold standard 102,400 tiros (Kali) + oficial 102,400 shots
3. **dfthcsos:** Verificación completa 254,464 tiros

### Instrumentos Desarrollados
- `verificar_multiregistro.py` — Verificador kickmix adaptado a multi-registro (invsqrt)
- `medir_fase3_rank.py` — Búsqueda exacta mínimo AND para GF(2^m) (DQI)
- `medir_fase3_lookup.py` — Coste real init_lookup/del_lookup (DQI)
- `verificar_multiregistro.py` adaptado para dfthcsos

---

## Archivos en el Commit

| Archivo | Descripción |
|---------|-------------|
| `submission/final_submission.zip` | **Entrega final (66,674,933 B)** — 13 archivos, SHA `83b0c756...` |
| `submission/FINAL_SUBMISSION_2026-11-13.md` | Este documento |
| `verifiers/invsqrt/verify_submission_invsqrt.py` | Verificador oficial invsqrt (sin cambios) |
| `verifiers/dqi/verify_submission_dqi.py` | Verificador oficial DQI (sin cambios) |
| `verifiers/dfthcsos/verify.py` | Verificador oficial dfthcsos (sin cambios) |

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

- **Último envío:** ref 58289295 (2026-11-13T00:17:18Z)
- **Score público:** 3.42920
- **Rank:** 2,545 / 2,940
- **Selección final:** 0 de 2 (pendiente marcar manualmente)

---

## Próximos Pasos

1. [ ] Marcar selección final en Kaggle (ref 58289295)
2. [x] Push a GitHub (`git push origin local/final-submission-2026-11-13`)
3. [ ] PR a `main` (merge limpio probado)

---

**Firmado:** Elán Zainos Corona — Fractal Core Research  
**Fecha:** 2026-11-13

*Nota de corrección (Mole, 2026-11-13 ~22:05): la primera versión de este doc citaba el SHA
y el tamaño del ZIP v4 (ref 58329687, 3.42257) con el score del Adopted v3; corregido a los
datos del Adopted v3 verificado (SHA 83b0c756..., 66,674,933 B, angle_k .kmx, score 3.42920,
ref 58289295). El asset del Release v2026-11-13-final también se reemplazó por el ZIP Adopted v3.*
