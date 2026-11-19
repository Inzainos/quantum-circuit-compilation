# REVISIÓN DEL AUDITOR — R1+R5 (combinación invsqrt)

**Fecha:** 2026-11-19 ~16:03 CST
**Auditor:** Auditor Interno
**Documento revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/r1r5/REPORTE_R1R5_2026-11-19.md` (156 l. / 14,738 B / md5 `995c9626…`, verificado en disco por mí)
**Supervisión de Datos:** `SUPERVISION_DATOS_R1R5_2026-11-19.md` (193 l. / md5 `2d261082…`, verificado en disco por mí)
**Verificación del Brujo:** `VERIFICACION_BRUJO_R1R5_2026-11-19.md` (77 l. / md5 `9ca8e23e…`, verificado en disco por mí)
**Cadena:** Programación (construye) → Datos ✓ → Brujo ✓ → Auditor (este documento) → Elán (decide).
**Veredicto: CONCURRO (PASA).**

---

## 1. Archivos verificados en disco por mí (no por confianza en el reporte)

| Archivo | Medido por mí | Reportado | ¿Coincide? |
|---|---|---|---|
| `REPORTE_R1R5_2026-11-19.md` | 156 l. / 14,738 B / md5 `995c9626…` | 156 l. / md5 `995c9626…` | ✓ |
| `SUPERVISION_DATOS_R1R5_2026-11-19.md` | 193 l. / md5 `2d261082…` | 193 l. / md5 `2d261082…` | ✓ |
| `VERIFICACION_BRUJO_R1R5_2026-11-19.md` | 77 l. / md5 `9ca8e23e…` | — | ✓ (leído) |
| `invsqrt_R1R5.kmb` | 437,536 B / sha256 `a30a1298…` | mismo sha | ✓ |
| `baseline_control.kmb` | 437,575 B / sha256 `7e842bbf…` | mismo sha | ✓ |
| `B_control.kmb` | 437,554 B / sha256 `25024fb4…` | mismo sha | ✓ |
| `R1_control.kmb` | 437,536 B / sha256 `a30a1298…` | mismo sha | ✓ |
| `R5_control.kmb` | 437,575 B / sha256 `7e842bbf…` | mismo sha | ✓ |
| `verify_R1R5_1shot.log` | 495 B / md5 `28a06144…` | 495 B / md5 `28a06144…` | ✓ |
| `verify_R1R5_gold.log` | 497 B / md5 `fc58af7f…` | 497 B / md5 `fc58af7f…` | ✓ |

## 2. Byte-identidad con R1 — verificada por mí con `cmp`

- `cmp invsqrt_R1R5.kmb ../r1/invsqrt_R1.kmb` → **IDÉNTICOS** ✓
- `cmp invsqrt_R1R5.kmb R1_control.kmb` → **IDÉNTICOS** ✓
- `cmp R5_control.kmb baseline_control.kmb` → **IDÉNTICOS** ✓ (R5 = baseline)

El circuito R1+R5 ES R1, byte por byte. Toda medición de R1 aplica exactamente a R1+R5 por construcción.

## 3. Q/T por kickmix — cargados por mí

| Circuito | Q | T | num_ops | nbits | ¿Coincide? |
|---|---|---|---|---|---|
| invsqrt_R1R5.kmb | 139 | 2,561 | 51,795 | 513 | ✓ con reporte, Datos y Brujo |
| R1_control.kmb | 139 | 2,561 | 51,795 | 513 | ✓ (= R1R5) |
| baseline_control.kmb | 139 | 2,561 | 51,798 | 513 | ✓ |
| B_control.kmb | 139 | 2,561 | 51,797 | 513 | ✓ |
| R5_control.kmb | 139 | 2,561 | 51,798 | 513 | ✓ (= baseline) |

R1R5 = R1 en los cuatro números; R5 = baseline en los cuatro; B tiene 51,797 (2 CX más que R1/R1R5, la firma estructural de R1). ✓

## 4. Logs leídos directamente por mí

**Local 1-shot** (`verify_R1R5_1shot.log`): PASS, score 389,261.0125451585, C 2,800.4389391738023, T 2,561, 34 rot, eps 5.276472679105155e-13, Q 139, reaction_depth 1,101, num_ops 51,795, 3,133,440 tiros, peor error 0.8375458188313827 @ x=718,814, sha `a30a1298…` ✓.

**Gold** (`verify_R1R5_gold.log`): PASS, mismos números, 200,540,928 tiros ✓.

**Gold de R1** (`../r1/verify_R1_gold.log`, leído directamente por mí): PASS, score 389,261.0125451585, C 2,800.4389391738023, T 2,561, 34 rot, eps 5.276472679105155e-13, Q 139, reaction_depth 1,101, num_ops 51,795, 200,540,928 tiros, peor error 0.8375458188313827 @ x=718,814, sha `a30a1298…`, exit_gold_R1=0. **El empate es exacto campo por campo contra el Gold de R1 — verificado desde el log de R1, no solo desde el reporte** ✓.

## 5. Score recalculado por mí con la fórmula oficial

rot_T = 0.56·log2(1/eps) + 5.3 con eps = 5.276472679105155e-13 → **28.139875196917888** ✓. C = 2,561 + (1 + 34 × 28.139875196917888)/4 = **2,800.4389391738023** ✓. Score = 139 × C = **389,261.0125451585** ✓ exacto. Ratio = 2,076,774 / 389,261.0125451585 = **5.33517** ✓. Baseline: C = 2,805.7917668892883, score 390,005.05559761106 ✓. Geomean con swap42 + logshift2 = 3.52510; con QF + logshift2 = 3.53396 (coincide con D-QF-2) ✓.

## 6. Diseño (no merge mecánico) — verificado por mí en el código

`diff -rq` del árbol `r1r5/tree/` vs el árbol B/C: **solo los 4 archivos esperados difieren** (`invsqrt_bloqs.py`, `invsqrt_halfsplit.py`, `invsqrt_logshift.py`, `invsqrt_logshift2.py`), más `.pyc` regenerados ✓. **BinarizaS intacta** — 0 ocurrencias de "BinarizaS" en el diff de `invsqrt_logshift.py` (la incidencia de construcción §8.1 quedó corregida antes de construir) ✓. Cambios clave presentes en los diffs: `trunc_low` en `CopiaC0`/`FasePorBits`, `_copia_c0` + `fold_copy` + `trunc_low` en `DesnormLog`, `r5` + `trunc_low` en `PipelineLog2` ✓.

**Estructura verificada por mí importando el módulo** (`PipelineLog2` con `PWSpec(deg=2, j=8, wc=28, dd=13)`, sesgo 1):

| Flags | Fases | `copy_c0` | `fold_copy` |
|---|---|---|---|
| (ninguno) | 6 | sí | False |
| `--r1` | 6 | sí | False |
| `--r5` | **5** | no | **True** |
| `--r1 --r5` | **5** | no | **True** |

Coincide exacto con la tabla del reporte (§3) y de Datos (§7). **R1+R5: 5 fases, sin `copy_c0`, copia plegada truncada, fase con `y1[1:]`** — la estructura de R5 con la truncación de R1 re-ubicada, como exige el diseño.

## 7. Precisiones — concurro con las tres, verificadas por mí

### D-R1R5-1 (md5 del verificador) — CONCURRO, verificado por mí: cierra la observación abierta del Brujo
Medí el md5 en las dos copias locales: `~/workspace/qcc-data/verifiers/invsqrt/verify_submission_invsqrt.py` y `r1r5/tree/verifiers/invsqrt/verify_submission_invsqrt.py` — ambas **`1e06af237023d909c2b3800bef55f2f8`** ✓. El verificador es el documentado.

### D-R1R5-2 (tamaño del árbol) — CONCURRO, verificado por mí
El 1,218,537 B es el tamaño del árbol B/C (medido por mí: 1,218,537 B exacto); el `r1r5/tree/` mide **1,251,844 B** — mayor por los 4 archivos alargados y los `.pyc` regenerados, como es de esperar. No es una discrepancia, solo una lectura.

### D-R1R5-3 (exit_gold no capturado) — CONCURRO, verificado por mí
El log Gold de R1+R5 no trae `exit_gold` (grep: 0 ocurrencias; el Gold de R1 trae `exit_gold_R1=0`): la sesión ssh del lanzador se cerró antes de que el proceso terminara y el `nohup` sobrevivió. El reporte ya lo documenta en §7.2. El `status: PASS` + 200,540,928 tiros + JSON completo establecen que el Gold terminó limpio. Sin impacto.

## 8. Criterio §1.1.3 de la recomendación conjunta — CUMPLIDO

Score = R1 exacto (389,261.0125451585, Gold PASS) con la estructura R5 (5 fases, sin `copy_c0`, copia plegada truncada). La composición está probada por medición: build + Gold, como exigía la recomendación conjunta.

## 9. Veredicto: CONCURRO (PASA)

La combinación es correcta y **R1+R5 PASA**: Gold PASS, score 389,261.0125451585 — empate exacto con R1 en todos los números de score, con la estructura de R5 (5 fases). El `.kmb` es byte-idéntico a R1 (sha `a30a1298…`); la ganancia es estructural y está medida: **una fase menos en el orquestador (6 → 5) con el score de R1**. Criterio §1.1.3 CUMPLIDO. Precisiones: D-R1R5-1 (md5 del verificador verificado por mí), D-R1R5-2 (tamaño del árbol), D-R1R5-3 (exit_gold no capturado, documentado) — menores, sin impacto.

**Cadena: Programación ✓ → Datos ✓ → Brujo ✓ → Auditor ✓ (este documento) → Elán decide.** Recomendación para la cadena: adoptar R1+R5 como la nueva referencia invsqrt (reemplaza a R1). El próximo ZIP que se construya usa R1+R5, no R1. (La decisión es de Elán; nada a producción/ZIP/GitHub/Kaggle sin su GO.)
