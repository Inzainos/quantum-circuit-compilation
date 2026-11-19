# VERIFICACIÓN DEL BRUJO — R1+R5 (combinación invsqrt): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~16:01 CST
**Verificador:** Brujo (El brujo)
**Cadena:** Programación (construye) → Datos (supervisa, CONCURRO) → **Brujo (este documento)** → Auditor → Elán (decide).
**Veredicto: CONCURRO (PASA).** La combinación es correcta y el criterio se cumple: **R1+R5 PASA — Gold PASS, score 389,261.0125451585, empate exacto con R1 en todos los números de score, con la estructura de R5 (5 fases), y se vuelve la nueva referencia invsqrt.**

Verifiqué por cómputo propio (byte-identidad, carga de circuitos, lectura directa de logs y recálculo de fórmulas), no por confianza en el reporte ni en la supervisión de Datos.

## 1. Documentos verificados en disco por mí

| Archivo | Medido por mí | ¿Coincide? |
|---|---|---|
| `REPORTE_R1R5_2026-11-19.md` | 156 l. / 14,738 B / md5 `995c9626…` | ✓ |
| `SUPERVISION_DATOS_R1R5_2026-11-19.md` | 193 l. / md5 `2d261082…` | ✓ con lo que Datos reportó |
| `invsqrt_R1R5.kmb` | 437,536 B / sha256 `a30a1298…` | ✓ |
| `baseline_control.kmb` | 437,575 B / sha256 `7e842bbf…` | ✓ |
| `B_control.kmb` | 437,554 B / sha256 `25024fb4…` | ✓ |
| `R1_control.kmb` | 437,536 B / sha256 `a30a1298…` | ✓ |
| `R5_control.kmb` | 437,575 B / sha256 `7e842bbf…` | ✓ |
| `verify_R1R5_1shot.log` | 495 B / md5 `28a06144…` | ✓ |
| `verify_R1R5_gold.log` | 497 B / md5 `fc58af7f…` | ✓ |

## 2. Byte-identidad con R1 — verificada por mí con `cmp`

- `cmp invsqrt_R1R5.kmb ../r1/invsqrt_R1.kmb` → **IDÉNTICOS** ✓
- `cmp invsqrt_R1R5.kmb R1_control.kmb` → **IDÉNTICOS** ✓

El circuito R1+R5 ES R1, byte por byte. Toda medición de R1 aplica exactamente a R1+R5 por construcción.

## 3. Q/T por kickmix — cargados por mí

| Circuito | Q | T | num_ops | ¿Coincide? |
|---|---|---|---|---|
| invsqrt_R1R5.kmb | 139 | 2,561 | 51,795 | ✓ con reporte y Datos |
| R1_control.kmb | 139 | 2,561 | 51,795 | ✓ (= R1R5) |
| baseline_control.kmb | 139 | 2,561 | 51,798 | ✓ |
| B_control.kmb | 139 | 2,561 | 51,797 | ✓ |
| R5_control.kmb | 139 | 2,561 | 51,798 | ✓ (= baseline) |

## 4. Logs leídos directamente por mí

**Local 1-shot** (`verify_R1R5_1shot.log`): PASS, score 389,261.0125451585, C 2,800.4389391738023, T 2,561, 34 rot, eps 5.276472679105155e-13, Q 139, reaction_depth 1,101, num_ops 51,795, 3,133,440 tiros, peor error 0.8375458188313827 @ x=718,814, sha `a30a1298…` ✓.

**Gold** (`verify_R1R5_gold.log`): PASS, mismos números, 200,540,928 tiros ✓.

**Gold de R1** (`../r1/verify_R1_gold.log`, leído directamente por mí): PASS, score 389,261.0125451585, C 2,800.4389391738023, T 2,561, 34 rot, eps 5.276472679105155e-13, Q 139, reaction_depth 1,101, num_ops 51,795, 200,540,928 tiros, peor error 0.8375458188313827 @ x=718,814, sha `a30a1298…`, exit_gold_R1=0. **El empate es exacto campo por campo contra el Gold de R1 — verificado desde el log de R1, no solo desde el reporte** ✓.

## 5. Score recalculado por mí con la fórmula oficial

rot_T = 0.56·log2(1/eps) + 5.3 con eps = 5.276472679105155e-13 → **28.139875196917888** ✓. C = 2,561 + (1 + 34 × 28.139875196917888)/4 = **2,800.4389391738023** ✓. Score = 139 × C = **389,261.0125451585** ✓ exacto. Ratio = 2,076,774 / 389,261.0125451585 = **5.33517** ✓. Baseline: C = 2,805.7917668892883, score 390,005.05559761106 ✓.

## 6. Gold en la Kali — verificado por mí por SSH

- Kali `.kmb` sha256 = `a30a1298…` ✓ (byte-idéntico al local).
- Kali `verify_R1R5_gold.log`: contenido idéntico al local (leído por SSH); Datos añade el md5 `fc58af7f…` = el md5 del log local (verificado por mí, §1) ✓.
- SomeJoint vivo durante el Gold (seg43 según el reporte; Datos lo vio después en seg51, avanzando por su cuenta) — no se tocó ✓.

## 7. Diseño (no merge mecánico) — verificado en el código

`diff -rq` del árbol `r1r5/tree/` vs el árbol B/C (`construccion-BC/tree`, 1,218,537 B): **solo los 4 archivos esperados difieren** (`invsqrt_bloqs.py`, `invsqrt_halfsplit.py`, `invsqrt_logshift.py`, `invsqrt_logshift2.py`), más `.pyc` regenerados. Leí los 4 diffs completos: solo los cambios R1+R5 documentados (CopiaC0/FasePorBits/PipelineMitad `trunc_low`; DesnormLog `_copia_c0` con `trunc_low` 27 CX; PipelineLog2 `r5` + flags CLI). **BinarizaS intacta** — la incidencia de construcción §8.1 quedó corregida antes de construir, verificado en el diff final ✓.

## 8. Precisiones de Datos — verificadas por mí

- **D-R1R5-1 (md5 del verificador): VERIFICADO POR MÍ — cierra mi observación abierta.** Medí el md5 en las dos copias locales: `~/workspace/qcc-data/verifiers/invsqrt/verify_submission_invsqrt.py` y `r1r5/tree/verifiers/invsqrt/verify_submission_invsqrt.py` — ambas **`1e06af237023d909c2b3800bef55f2f8`** ✓. El verificador es el documentado.
- **D-R1R5-2 (tamaño del árbol): CONCURRO.** El 1,218,537 B es el tamaño del árbol B/C (medido por mí: 1,218,537 B exacto); el `r1r5/tree/` mide 1,251,844 B — mayor por los 4 archivos alargados y los `.pyc`, como es de esperar. No es una discrepancia.
- **D-R1R5-3 (exit_gold no capturado): CONCURRO.** El log Gold de R1+R5 no trae `exit_gold` (a diferencia del Gold de R1, que trae `exit_gold_R1=0`); la sesión ssh del lanzador se cerró antes de que el proceso terminara y el `nohup` sobrevivió. El reporte ya lo documenta en §7.2. El `status: PASS` + 200,540,928 tiros + JSON completo establecen que el Gold terminó limpio. Sin impacto.

## 9. Criterio §1.1.3 — CUMPLIDO

Score = R1 exacto (389,261.0125451585, Gold PASS) con la estructura R5 (5 fases, sin `copy_c0`, copia plegada truncada). La composición está probada por medición: build + Gold, como exigía la recomendación conjunta.

## 10. Veredicto: CONCURRO (PASA)

La combinación es correcta y **R1+R5 PASA**: Gold PASS, score 389,261.0125451585 — empate exacto con R1 en todos los números de score, con la estructura de R5 (5 fases). El `.kmb` es byte-idéntico a R1 (sha `a30a1298…`); la ganancia es estructural y está medida: **una fase menos en el orquestador (6 → 5) con el score de R1**. Criterio §1.1.3 CUMPLIDO. Precisiones: D-R1R5-1 (md5 del verificador verificado por mí), D-R1R5-2 (tamaño del árbol), D-R1R5-3 (exit_gold no capturado, documentado) — menores, sin impacto.

**Cadena: Programación ✓ → Datos ✓ → Brujo ✓ (este documento) → Auditor → Elán decide.** Recomendación para la cadena: adoptar R1+R5 como la nueva referencia invsqrt (reemplaza a R1). El próximo ZIP que se construya usa R1+R5, no R1. (La decisión es de Elán; nada a producción/ZIP/GitHub/Kaggle sin su GO.)
