# SUPERVISIÓN DE DATOS — R1+R5 (combinación invsqrt): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~15:57 CST
**Supervisor:** Datos (Analista de datos)
**Cadena:** Programación (construye) → **Datos (este documento)** → Brujo →
Auditor → Elán (decide).
**Veredicto: CONCURRO (PASA).** La combinación es correcta y el criterio
se cumple: **R1+R5 PASA — empata EXACTO con R1 (389,261.0125451585) con
la estructura de R5 (5 fases) y se vuelve la nueva referencia invsqrt.**
Mi supervisión es por cómputo propio sobre los circuitos, los logs y el
código leídos/cargados directamente, no por confianza en el reporte.

## 1. Archivos verificados en disco por mí (medidos, no citados de oídas)

| Archivo | Medido por mí | Reportado | ¿Coincide? |
|---|---|---|---|
| `REPORTE_R1R5_2026-11-19.md` | 156 l. / 14,738 B / md5 `995c9626…` | 156 l. / md5 `995c9626…` | ✓ |
| `invsqrt_R1R5.kmb` | 437,536 B / sha256 `a30a1298…` | mismo sha | ✓ |
| `baseline_control.kmb` | 437,575 B / sha256 `7e842bbf…` | mismo sha | ✓ |
| `B_control.kmb` | 437,554 B / sha256 `25024fb4…` | mismo sha | ✓ |
| `R1_control.kmb` | 437,536 B / sha256 `a30a1298…` | mismo sha | ✓ |
| `R5_control.kmb` | 437,575 B / sha256 `7e842bbf…` | mismo sha | ✓ |
| `verify_R1R5_1shot.log` | 495 B / md5 `28a06144…` | 495 B | ✓ |
| `verify_R1R5_gold.log` | 497 B / md5 `fc58af7f…` | 497 B | ✓ |
| `tree/` (copia del árbol B/C) | presente | presente | ✓ |

## 2. Byte-identidad con R1 — verificada por mí con `cmp`

- `cmp invsqrt_R1R5.kmb ../r1/invsqrt_R1.kmb` → **IDÉNTICOS** ✓
- `cmp invsqrt_R1R5.kmb R1_control.kmb` → **IDÉNTICOS** ✓

El circuito R1+R5 ES R1, byte por byte. Toda medición de R1 aplica
exactamente a R1+R5 por construcción — incluido el peor error clásico y
la sonda y1 de R1 (§7.3 del reporte, concurro).

## 3. Q/T por kickmix — cargados por mí

| Circuito | Q | T | num_ops | nbits |
|---|---|---|---|---|
| R1R5 | **139** | **2,561** | **51,795** | 513 |
| baseline | 139 | 2,561 | 51,798 | 513 |
| B | 139 | 2,561 | 51,797 | 513 |
| R1 | 139 | 2,561 | 51,795 | 513 |
| R5 | 139 | 2,561 | 51,798 | 513 |

R1R5 = R1 en los cuatro números; R5 = baseline en los cuatro; B tiene
51,797 (2 CX más que R1/R1R5, la firma estructural de R1 verificada en
mi supervisión R1). ✓

## 4. Logs leídos directamente por mí

**Local 1-shot** (`verify_R1R5_1shot.log`, 495 B): PASS, score
**389,261.0125451585**, C 2,800.4389391738023, T 2,561, 34 rot, eps
5.276472679105155e-13, Q 139, reaction_depth 1,101, num_ops 51,795,
3,133,440 tiros, peor error 0.8375458188313827 @ x=718,814, sha
`a30a1298…` ✓.

**Gold** (`verify_R1R5_gold.log`, 497 B): PASS, **mismos números**,
200,540,928 tiros ✓.

**Gold de R1** (`../r1/verify_R1_gold.log`, leído directamente por mí):
PASS, score **389,261.0125451585**, C 2,800.4389391738023, T 2,561,
34 rot, eps 5.276472679105155e-13, Q 139, reaction_depth 1,101, num_ops
51,795, 200,540,928 tiros, peor error 0.8375458188313827 @ x=718,814,
sha `a30a1298…`, exit_gold_R1=0. **El empate es exacto campo por campo
contra el Gold de R1 — verificado desde el log de R1, no solo desde el
reporte.** ✓

## 5. Score recalculado por mí con la fórmula oficial

rot_T = 0.56·log2(1/eps) + 5.3 con eps = 5.276472679105155e-13 →
**28.139875196917888** ✓ (la r de R1). C = 2,561 + (1 + 34 ×
28.139875196917888)/4 = **2,800.4389391738023** ✓. Score = 139 × C =
**389,261.0125451585** ✓ exacto. Ratio = 2,076,774 / 389,261.0125451585
= **5.33517** ✓. Baseline: C = 2,805.7917668892883, score
390,005.05559761106 ✓. Geomean con swap42 + logshift2 = 3.52510; con
QF + logshift2 = 3.53396 (coincide con D-QF-2) ✓.

Tabla §6 del reporte verificada: R1+R5 = R1 en Q, T, n_rot, eps, r, C,
score, peor error y num_ops; R5 = baseline en todos; la única diferencia
R1+R5 vs R1 es el número de fases (5 vs 6). ✓

## 6. Criterio de la recomendación conjunta §1.1.3 — CUMPLIDO

Recomendación conjunta (`RECOMENDACION_CONJUNTA_ADOPCION_2026-11-19.md`,
§1.1.3, leída por mí): *"Construir R1+R5, verificar con Gold, y si el
score es = R1 (389,261.01) con la estructura R5, adoptar la combinación
como la nueva referencia invsqrt. Esperado: exactamente el score de R1
(R5 no cambia la secuencia de puertas...). Pero la composición NO está
probada hasta medirla: el build + Gold es obligatorio."* (Matiz de Datos:
no es un merge mecánico — la truncación de R1 vive en `CopiaC0` y R5
elimina esa fase; el constructor debe colocar la truncación correctamente
en la copia plegada. El Gold lo verifica.)

**CUMPLIDO:** score = R1 exacto (389,261.0125451585, Gold PASS) con la
estructura R5 (5 fases, sin `copy_c0`). La composición está probada por
medición: build + Gold, como exigía la recomendación.

## 7. Diseño (no merge mecánico) — verificado en el código y en el módulo

`diff -rq` del árbol `r1r5/tree/` vs el árbol B/C
(`kickmix-motor/fusion-v6/revision-formulas-2026-11-14/construccion-BC/tree`,
1,218,537 B — ver D-R1R5-2): **solo los 4 archivos esperados difieren**
(`invsqrt_bloqs.py`, `invsqrt_halfsplit.py`, `invsqrt_logshift.py`,
`invsqrt_logshift2.py`), más `.pyc` regenerados. Leí los 4 diffs
completos: solo los cambios R1+R5 documentados. **BinarizaS intacta**
(ningún hunk la toca — la incidencia de construcción §8.1 quedó
corregida antes de construir, verificado en el diff final). ✓

Cambios verificados en los diffs:
- `CopiaC0`: nuevo `trunc_low`; con True copia `c0[1:] → y1[1:]` (27
  CX), `y1[0]` en |0⟩ (cambio R1 literal).
- `FasePorBits`: nuevo `trunc_low`; con True recibe `y1[1:]` (cambio R1
  literal; los ángulos quedan idénticos a B/R1).
- `PipelineMitad`: nuevo `trunc_low`; lo pasa a `CopiaC0` y a
  `FasePorBits(skip_low, trunc_low)`.
- `DesnormLog`: nuevo `_copia_c0` (el `fold_copy` de R5) con parámetro
  `trunc_low`; con True copia `c0[1:] → y1[1:]` (27 CX) y `y1[0]` en
  |0⟩; copia antes de rotaciones en ida y después en vuelta.
- `PipelineLog2`: nuevos `trunc_low` y `r5`; con `--r5`, `copy_c0` se
  filtra de `self.fases` y se añade `DesnormLog(..., fold_copy=True,
  trunc_low=trunc_low)`; `swap = "denormalize_log" if self.r5 else
  "copy_c0"`; flags CLI `--r1` y `--r5`.

**Tabla de estructura §3 verificada por mí importando el módulo**
(`PipelineLog2` con `PWSpec(deg=2, j=8, wc=28, dd=13)`, sesgo 1):

| Flags | Fases | `copy_c0` | `fold_copy` | `dn.trunc_low` | `media.trunc_low` |
|---|---|---|---|---|---|
| (ninguno) | 6 | sí | False | False | False |
| `--r1` | 6 | sí | False | False | **True** |
| `--r5` | **5** | no | **True** | False | False |
| `--r1 --r5` | **5** | no | **True** | **True** | **True** |

Las 4 filas coinciden exacto con la tabla del reporte. **R1+R5: 5
fases, sin `copy_c0`, copia plegada truncada, fase con `y1[1:]`** — la
estructura de R5 con la truncación de R1 re-ubicada, como exige el
diseño. El principio de Elán (mínima fricción) se cumple: la copia
plegada emite `y1` ya sin bit 0 y sin etapa intermedia vacía.

## 8. Gold en la Kali — verificado por mí por SSH

- Kali `.kmb` sha256 = `a30a1298…` ✓ (byte-idéntico al local).
- Kali `verify_R1R5_gold.log` md5 = `fc58af7f…` = **el md5 del log local**
  ✓ (log idéntico en ambas cajas; 497 B, mtime 15:11 en la Kali).
- Kali `.kmb` mtime 15:06, log 15:11 — ventana 15:06–15:11 CST ✓.
- SomeJoint seguía vivo durante el Gold (el reporte lo documenta en
  seg43; mi chequeo SSH posterior lo ve en seg51, avanzando por su
  cuenta) — no se tocó. ✓

## 9. Precisiones mías

### D-R1R5-1 (cierra una observación abierta del Brujo — md5 del verificador VERIFICADO por mí)
El Brujo tomó el md5 del verificador (`1e06af237023d909c2b3800bef55f2f8`)
como reportado, sin re-verificarlo porque el script no está en el dir
`construccion-BC-gold` de la Kali. **Lo verifiqué yo en dos copias
locales:** `~/workspace/qcc-data/verifiers/invsqrt/verify_submission_invsqrt.py`
y `r1r5/tree/verifiers/invsqrt/verify_submission_invsqrt.py` — ambas
miden **`1e06af237023d909c2b3800bef55f2f8`** ✓. El verificador es el
documentado.

### D-R1R5-2 (menor, de lectura — el tamaño del árbol)
El reporte dice "Árbol: `r1r5/tree/` = copia del árbol B/C (1,218,537
B...)". Ese 1,218,537 B es el tamaño del **árbol B/C** (medido por mí:
1,218,537 B exacto); el árbol `r1r5/tree/` mide **1,251,844 B** — mayor
por los 4 archivos alargados y los `.pyc` regenerados, como es de
esperar. No es una discrepancia, solo una lectura: el número citado es
el del árbol B/C.

### D-R1R5-3 (menor — el Gold no dejó `exit_gold` capturado)
El log Gold de R1+R5 no trae la línea `exit_gold` (a diferencia del Gold
de R1, que trae `exit_gold_R1=0`): la sesión ssh del lanzador se cerró
antes de que el proceso terminara y el `nohup` sobrevivió. El reporte ya
lo documenta en §7.2 (nota de lanzamiento) y concurro: el `status: PASS`
+ 200,540,928 tiros + JSON completo establecen que el Gold terminó
limpio. Sin impacto.

## 10. Veredicto: CONCURRO (PASA)

La combinación es correcta y **R1+R5 PASA**: Gold PASS, score
389,261.0125451585 — empate exacto con R1 en todos los números de score,
con la estructura de R5 (5 fases, sin `copy_c0`, copia plegada
truncada). El `.kmb` es byte-idéntico a R1 (sha `a30a1298…`); la ganancia
es estructural y está medida: **una fase menos en el orquestador (6 → 5)
con el score de R1**. Criterio §1.1.3 CUMPLIDO. Precisiones mías:
D-R1R5-1 (md5 del verificador verificado), D-R1R5-2 (tamaño del árbol),
D-R1R5-3 (exit_gold no capturado, documentado) — menores, sin impacto.

**Cadena: Programación ✓ → Datos ✓ (este documento) → Brujo → Auditor
→ Elán decide.** Recomendación para la cadena: adoptar R1+R5 como la
nueva referencia invsqrt (reemplaza a R1). El próximo ZIP que se
construya usa R1+R5, no R1. (La decisión es de Elán; nada a
producción/ZIP/GitHub/Kaggle sin su GO.)

## 11. Adenda — revisión del Auditor (2026-11-19 ~16:02 CST)

Revisión del Auditor: `~/workspace/auditoria/REVISION_AUDITOR_R1R5_2026-11-19.md`
(94 l. / md5 `bcba4009…`, verificado en disco por mí) — **CONCURRO
(PASA)**. El Auditor verificó por cómputo propio lo mismo que yo
(byte-identidad por `cmp`; circuitos cargados con kickmix; logs leídos
directamente — 1-shot PASS 3,133,440 tiros, Gold PASS 200,540,928 tiros,
Gold de R1 idéntico campo por campo, exit_gold_R1=0; score recalculado
exacto — rot_T 28.139875196917888, C 2,800.4389391738023, ratio 5.33517,
geomean QF+R1R5 = 3.53396, swap42+R1R5 = 3.52510; diseño — `diff -rq`
solo 4 archivos, BinarizaS intacta, estructura importando el módulo, 5
fases para R1+R5) y **concurrió con D-R1R5-1, D-R1R5-2 y D-R1R5-3**
(cada una verificada por él). **Criterio §1.1.3 CUMPLIDO.**

**Cadena R1+R5 COMPLETA: Programación ✓ → Datos ✓ → Brujo ✓ →
Auditor ✓ → Elán decide.** Recomendación: adoptar R1+R5 como nueva
referencia invsqrt.
