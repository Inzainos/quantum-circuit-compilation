# NOTEBOOK PÚBLICO (BORRADOR) — REPORTE

**Fecha:** 2026-11-12 (08:47–15:00 CST, America/Mexico_City)
**Tarea:** armar el BORRADOR del notebook público para la competición Google Quantum AI Verifiable Quantum Circuit Compilation (Kaggle), milestone 2026-11-20 ($10k prize requiere un notebook PÚBLICO; hoy no existe ninguno). Es el siguiente paso de la secuencia de Elán (2026-11-12 ~01:27): el rediseño dio ganancia (E1d), la adopción quedó (ZIP reconstruido y verificado, geomean ~3.329x calculado), y ahora toca el notebook.
**Alcance:** SOLO el borrador. NO publicado en Kaggle, NO subido nada, NO marcada la selección final (0 de 2, solo Elán puede hacerlo).
**Regla 0:** cada número del notebook viene de un log citado; lo no medido se dice, no se asume.

## VEREDICTO: EL BORRADOR ESTÁ LISTO PARA QUE ELÁN LO REVISE

**Notebook:** `qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` (17 celdas: 12 markdown, 5 código; 40,894 B, ejecutado).
**Ejecución: 0 errores.** Las 5 celdas de código corren y sus salidas coinciden con los números documentados (ver §2).
**Estado: BORRADOR, no publicado.** Nada a Kaggle.

## 1. Qué contiene el notebook

Título: "Verifiable Quantum Circuit Compilation — logshift2 + fused DQI (Q=1,934) + lbfgs chemistry". Autor: Elán Zainos Corona (Fractal Core).

| § | Contenido |
|---|---|
| Portada | Tabla de la entrega adoptada + **honesty box** (qué es calculado vs medido en Kaggle; el ZIP completo NO pasó por el verificador oficial completo; selección final 0 de 2; estado BORRADOR) |
| §0 | La competición y el score (geomean de ratios; costo por tarea: invsqrt Q×C, DQI R·Q²·T, dfthcsos λ_eff·T·Q) + hechos del verificador (TOL 2⁻²⁴ relativa por x; ancillas \|0⟩ + x restaurado; exactamente un registro 'x' de 22 qubits; la profundidad NO entra al score) + reglas C14/B7/C6a/C5d/C6b/B6 |
| §0 (código) | Geomean recomputado desde las referencias documentadas |
| §1 | invsqrt logshift2: método (PipelineLog2 deg=2, j=8, wc=28, dd=13, sesgo=1), perfil (Horner 1,484; lookup 551; desnorm 260; norm 224; medio giro 42), linaje (NR 2,070,562 → dbhexa 1,935,003 → halfsplit 570,323 → logshift v1 526,689 → logshift2 497,462 → PR #19 390,005), verificación PASS oficial dominio completo (200,540,928 tiros, peor error 0.7920 tol en x=2,764,799) |
| §1 (código) | Score Q×C y ratio invsqrt |
| §1.3 | V34: referencia (97,870; dominio completo 97,921.58; Q=62, C=1,579.38, 41 rotaciones, peor error 0.9993 tol), procedencia y licencia (SomeJoint/Agniv Banerjee, yoyobar, Ehan Mallick, Alex Chilton, Apache 2.0), **declaración de derivación** (reconstruir estilo V34 con nuestro constructor; nunca el V34 literal en el ZIP, C14), lo que V34 enseñó (medido), estado honesto de invsqrt (u24+M2a podado 107,683, 10% arriba de V34; escala bloqueada; Prototipo A ANGLE_OFF causa raíz ABIERTA) |
| §2 | DQI fusionado+E1d: método (F1b: inv directo en alpha + CSWAP, ahorra Pinv 12; E1d: libera N′ antes de los productos, +6 T/inv), tabla de variantes (baseline 1,949 → fusionada 1,937 → fusionada+E1d 1,934; E1 wash 3.3236x, E2 peor 3.3218x), piso Q=1,934 fijado por el pico del scan, lección medida (el Q standalone NO predice el Q del circuito completo) |
| §2 (código) | Ratios DQI y cadena de geomean |
| §2.2–2.3 | Verificación DQI (sim n=6 Tests A–C PASS; oficial Kali 2,560 tiros, 0 errores, PASS; caveats: R=4.94 es artefacto del muestreo; gold-standard 102,400 tiros NO corrido) + alternativas medidas y cerradas (Itoh-Tsujii, torre cúbica, builtin, lookup, BM in-place/q-d, rombo bloque) |
| §3 | dfthcsos lbfgs (65,60,60): método (LBFGS rho=1e-4, eps=0.017, 100 épocas, 2,562.1 s; brot=12, batch 8, 3,976 vectores, 75 ángulos, 10 circuitos angle 119 qubits), números (score 3,336,160,975; λ_eff 49.0158; error₁ 3.340 mHa, error₂ 19.371 mHa; T=93,237, Q=730; PASS oficial 254,464 tiros), por qué este factor (la forma pequeña (8,143,60) NO pasó: escalera, refit brot=8, factorización desde cero, mixed brot; criterio de rango medido: productos ≤~225 Y high_cache ≤~69 por lote) |
| §3 (código) | Ratio dfthcsos |
| §4 | El ZIP: estructura, script `build_submission.py`, tabla de miembros con sha256, verificación (testzip None, 13 archivos, los 13 miembros coinciden por sha256) |
| §4 (código) | Chequeo de integridad del ZIP si está adjunto como dataset (defensivo: prueba `/kaggle/input/...` y la ruta local; si no está, imprime los sha esperados) |
| §5 | Estado de verificación y caveats (tabla por pieza; el ZIP completo NO pasó por el verificador oficial; geomean calculado 3.3289x vs estimado ~3.332x por redondeo; Kaggle best 3.31949 es de la entrega anterior; selección final 0 de 2) |
| §6 | Atribuciones, licencia y lo que la entrega NO es (V34/Apache 2.0; C14/B7/C6; principio "el trabajo debe ser nuestro"; **la postura del planner es ABIERTA y NO es parte de la entrega**) |
| §7 | Reproducibilidad: comandos exactos del generador (invsqrt, DQI, dfthcsos, ZIP), estado del repo (rama fix/zip-final-2026-11-07, HEAD a40a82f; worktree quantum-sandbox @ 4ac3d45), entornos (caja py313; Kali 16 CPUs/7 GB; verificador DQI 6.6 GB RSS a 1 worker) |
| §8 | Abiertos y trabajo futuro (gold-standard DQI; frontera química (8,143,60)+full-XOR; escala u24; ANGLE_OFF; selección final Kaggle) |

## 2. Ejecución — celdas que corrieron y pasaron

Entorno de ejecución local: `/home/hatch/workspace/py313/python/bin/python3.13` con nbformat 5.11.1, nbconvert 7.17.2, ipykernel 7.4.0 (instalados en ese venv con TMPDIR=$HOME/.pip-tmp; kernelspec `py313` registrado en `~/.local/share/jupyter/kernels/py313`). Comando: `jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=py313 --ExecutePreprocessor.timeout=300`. **TOTAL ERRORS: 0.**

Salidas medidas (todas coinciden con los números documentados):

| Celda | Salida |
|---|---|
| §0 geomean | invsqrt ratio = 5.30907; DQI ratio = 6.86807; dfthcsos ratio = 1.01169; producto = 36.88930; **geomean = 3.32890x (CALCULATED)**; composición anterior 3.30657x; mejora +0.0223x |
| §1 invsqrt | score Q×C = 139 × 2805.7918 = **390,005.06**; ratio = 5.30907; PASS oficial dominio completo (200,540,928 tiros), peor error 0.7920 tol |
| §2 DQI | baseline Q=1949 T=784172 ratio 6.77000; fused Q=1937 ratio 6.85414; **fused+E1d Q=1934 T=785012 ratio 6.86807**; cadena 3.31x → 3.3237x → 3.3259x |
| §3 dfthcsos | lbfgs score = 3,336,160,975 (sample 3,355,599,588, −0.58%); ratio = 1.01169; error₁ 3.340 mHa, error₂ 19.371 mHa, λ_eff 49.0158; PASS oficial 254,464 tiros |
| §4 ZIP | ZIP local encontrado; **sha256 match: True** (`171d5a81c4ca47b1…`); **testzip: None**; 13 miembros; invsqrt.kmb, dqi.kmb y dfthcsos/submission.npz sha match: True |

## 3. Qué quedó como referencia a logs (no ejecutable en el notebook)

Estas verificaciones requieren el verificador oficial o la Kali y NO se pueden ejecutar dentro de un notebook de Kaggle; en el notebook se citan con sus logs, no se inventan:

- **invsqrt PASS oficial dominio completo** (200,540,928 tiros, peor error 0.7919559187816102 en x=2,764,799) — fuente: `REPORTE_CONSOLIDADO_RAIZ_2026-11-10.md` §1.2.
- **DQI fused+E1d PASS sim n=6 (Tests A–C) + PASS oficial Kali (2,560 tiros, 0 errores)** — fuentes: `dqi-perfil/verificacion_e1d/VERIFICACION_E1D_REPORTE.md`, `verify_kali.log`, `verificar_e1d.log`. Gold-standard 102,400 tiros NO corrido (~65 min/circuito).
- **dfthcsos lbfgs PASS oficial (254,464 tiros)** — fuente: `dfthcsos-refit/candidates/lbfgs_ep100_rho1e-4/verify_official.log` (score 3,336,160,974.98, λ_eff 49.01577).
- **ZIP: integridad + identidad por sha256 de los 13 miembros** — fuente: `adopcion/verificar_zip.log` (`TODOS LOS MIEMBROS COINCIDEN: True`), `adopcion/verificar_final.log`. El ZIP completo NO pasó por el verificador oficial completo de la entrega (~45 min en Kaggle).
- **V34 (97,870; dominio completo 97,921.58)** — fuente: `REPORTE_CONSOLIDADO_RAIZ_2026-11-10.md` §2.1–2.3.

## 4. Corrección encontrada y arreglada durante la ejecución (regla 0)

**El C de logshift2 es un redondeo, no un valor exacto.** La primera versión de la celda §1 calculaba `139 × 2,805.79 = 390,004.81`, que contradice el score documentado **390,005.06** por 0.25. Causa: C = 2,805.79 es el redondeo a 2 decimales del C exacto (390,005.06 / 139 = 2,805.7918…). La celda se corrigió para tomar el score documentado (390,005.06) como autoritativo y derivar C de él, con la nota de redondeo explícita en el código y en el markdown §1.2. El ratio no cambió (5.30907 en ambos casos a 5 decimales) y el geomean no cambió (usa 390,005.06). La referencia invsqrt 2,070,563 se confirmó como el redondeo de 2,070,562.5658 (`benchmarks/fusion_energy/baseline/metrics.json`: `score_q_times_c: 2070562.565826548`, Q=260).

## 5. Decisiones abiertas que Elán debe confirmar antes de publicar

1. **Postura C14/B7 del planner (junta, SIN RESOLVER):** usar el planner full-XOR Apache-2.0 as-is con atribución (como una librería) vs reimplementarlo desde el método. El notebook NO lo incluye como pieza de la entrega y lo dice explícitamente (§6). Si la junta decide incluirlo, el notebook debe actualizarse (y la entrega también).
2. **Publicación en Kaggle + subida del ZIP + selección final (0 de 2):** solo Elán puede hacerlo. Este trabajo no subió nada.
3. **Atribuciones:** las del notebook son las verificadas (SomeJoint/Agniv Banerjee, yoyobar, Ehan Mallick, Alex Chilton, Apache 2.0; Khattar et al. arXiv:2610.23832; Babbush et al. arXiv:2603.28846). Si Elán quiere añadir o quitar alguna, debe decirlo antes de publicar.
4. **El ZIP viejo tenía el invsqrt piecewise (Q=185, score 599,866), NO logshift2** — la adopción lo corrigió (piecewise → logshift2); ver `adopcion/ADOPCION_REPORTE.md` §2. Esa historia interna NO está en el notebook público (solo se presenta el ZIP adoptado y su verificación); si Elán quiere que se mencione, debe decirlo.
5. **El geomean 3.3289x es CALCULADO, no medido en Kaggle** — el notebook lo dice en la portada, en §0, en §5 y en la salida de la celda. No se afirma que supere el 3.31949 de Kaggle hasta medirlo allí.

## 6. Archivos

Scratch: `~/workspace/qcc-data/notebook/`
- `qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` — el borrador del notebook (17 celdas, ejecutado, 0 errores).
- `build_notebook.py` — script que genera el .ipynb (nbformat; re-ejecutable).
- `NOTEBOOK_REPORTE.md` — este reporte.

Entrega y repo intactos. Nada a Kaggle. Nada descargado. (Solo se instalaron nbformat/nbconvert/jupyter_client/ipykernel en el venv local py313, y se registró el kernelspec `py313` en `~/.local/share/jupyter/kernels/py313`.)
