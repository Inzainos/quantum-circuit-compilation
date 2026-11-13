# ADOPCIÓN — FUSIÓN + E1d + lbfgs — REPORTE

**Fecha:** 2026-11-12 (08:35–14:45 CST, America/Mexico_City)
**Decisión de Elán (2026-11-12 ~08:35, vía el widget, palabras exactas, relayada por el Coordinador):** "Sí, adopten todo (fusión + E1d + lbfgs)". Esta decisión revierte explícitamente la decisión de Elán "NO insertar" el lbfgs (2026-11-09 ~14:35).
**Alcance:** SOLO la adopción. El notebook público lo lanza el agente padre después de este veredicto.
**Regla 0:** cada número viene de un log citado; lo no medido se dice, no se asume.

## VEREDICTO: LA ADOPCIÓN QUEDÓ — ZIP RECONSTRUIDO Y VERIFICADO, GEOMEAN ~3.329x

**Nuevo ZIP de la entrega:** `~/workspace/qcc-data/valid_submission_fb4e95b.zip`
- sha256 `171d5a81c4ca47b17573d4876acb3b63386b7048a5f7b1f77fae4e4a60a7f87e`
- 66,225,789 B (63.2 MB), 13 archivos, `testzip` = None (íntegro).
- **Geomean calculado: 3.3289x** (referencias documentadas; ver §4). La estimación de la tarea era ~3.332x; la diferencia (0.003) es redondeo en los ratios de referencia (6.77x y 1.00583x, 3 cifras).

| Pieza | Archivo en el ZIP | sha256 | Medido (verificado) |
|---|---|---|---|
| invsqrt | invsqrt.kmb (437,575 B) | `7e842bbf…faf79` | logshift2, Q=139, C=2,805.79, score 390,005.06, PASS oficial dominio completo |
| dqi | dqi.kmb (624,877,910 B) | `16e06d61…3664` | fusionado+E1d, Q=1,934, T=785,012, geomean 3.3259x, PASS sim n=6 + PASS verificador oficial Kali (2,560 tiros, 0 err) |
| dfthcsos | angle_k_0..9.kmx + submission.npz (4,537,436 B) | npz `d89772be…7fa4d` | lbfgs (65,60,60), score 3,336,160,975, error_2 19.371 mHa, error_1 3.340 mHa, PASS oficial (254,464 tiros) |

**Backup del ZIP viejo:** `~/workspace/qcc-data/adopcion/backup/valid_submission_fb4e95b.zip.OLD` (sha `f48fcaf5…91f42`, 73,923,748 B — coincide con el ZIP viejo antes de reemplazarlo).

---

## 1. Cómo se construye el ZIP (medido)

Script: `~/workspace/qcc-dqi/submission/build_submission.py` (clon, rama fix/zip-final-2026-11-07, HEAD a40a82f). Empaqueta: `invsqrt.kmb`, `dqi.kmb`, `dfthcsos/angle_k_0…angle_k_<n-1>` (numerados desde 0 sin gaps, .kmb o .kmx) y `dfthcsos/submission.npz` (claves requeridas: U, W, H2_I, H1_I, Hsym_lower, tree_edges). El script valida las entradas y lo escribió en `adopcion/nuevo_zip/submission_adopcion_2026-11-12.zip` (log `construir_zip.log`).

Script canónico alternativo (NO usado para este build, solo leído): `~/workspace/qcc-dqi/submission/rebuild_valid_zip.py` — regenera invsqrt (logshift2, `src/invsqrt_logshift2.py --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1`) y DQI (`src/dqi_decoder_v1.py`) desde el repo y toma dfthcsos del zip fb4e95b. No lo usé porque regenerar el DQI desde el repo da el BM v7 (Q=2,016, ver §2), no el fusionado+E1d (Q=1,934) que es la pieza a adoptar.

---

## 2. HALLAZGO CRÍTICO — LA PREMISA DE LA TAREA ERA INCORRECTA (verificado por sha256)

La tarea decía que la entrega actual era "logshift2 invsqrt + DQI Q=1,949 + dfthcsos sample" y que el invsqrt "NO cambia". **Eso no coincide con ningún ZIP existente.** Lo medido (sha256 de cada miembro, streaming, sin extraer):

| ZIP / directorio | invsqrt | dqi | dfthcsos | geomean |
|---|---|---|---|---|
| `valid_submission_fb4e95b.zip` (sha `f48fcaf5…`, el ZIP nombrado por la tarea) | **piecewise** (Q=185, score 599,866, sha `c6e080b0…`), de `entrega-2026-11-04` | baseline (Q=1,949, sha `ef1fc095…`, 885 MB) | **sample** (npz `14d5cc25…`, score 3,355,599,588) | ~2.87x (calculado) |
| `zip-final-2026-11-07/final_submission.zip` (sha `2c3018f8…`, 57.8 MB) | **logshift2** (sha `7e842bbf…`) | BM v7 (**Q=2,016**, T=784,172, sha `2b9eb49f…`, 631 MB) | **lbfgs** (npz `d89772be…`) | ~3.24x (documentado) |
| `integracion/submission.zip` (sha `ce1d12a6…`) | **logshift2** (sha `7e842bbf…`) | BM v7 (sha `b555bbed…`, 631 MB, build 2026-11-06) | **lbfgs** (npz `d89772be…`) | ~3.24x |
| `submission_valid/` (directorio) | **halfsplit** (Q=183, sha `47c56f52…`, `gen_invsqrt.log` 2026-11-06) | baseline (sha `ef1fc095…`) | sample (.kmb + npz `14d5cc25…`) | — |

Fuentes (logs, no memoria):
- El invsqrt del ZIP viejo es piecewise: su sha `c6e080b0…` aparece en `entrega-2026-11-04/qcc-local/benchmarks/fusion_energy/piecewise/metrics.json` (Q=185, T=2,993, toffoli_equivalent=3,242.52, score Q×C=599,866.49, PASS 1 y 16 tiros/x) y en `~/workspace/qcc-dqi/benchmarks/fusion_energy/piecewise/metrics.json`. Medido por mí: el invsqrt.kmb extraído del ZIP tiene `num_qubits=185` (kickmix, `py313`); logshift2 tiene 139.
- El DQI de `final_submission.zip` es Q=2,016: `logs/qcc.jsonl` (run `17a51760f72b`, `dqi_decoder_v1`, 2026-11-07T12:49:03Z): `{"toffoli": 784172, "qubits": 2016}`, sha `2b9eb49f…`, 631,663,465 B. Y `correccion-sec7-ESTADO_FINAL-2026-11-07.md` (Mole, 2026-11-07 ~07:40): "dqi: BM v7 (`2b9eb49f…`, Q=2,016, T=784,172), 0 fallos en 102,400 tiros" y "Geomean: ~3.24×", verificado "contra el ZIP nuevo de 57.8 MB (sha `2c3018f8…`)".
- El dfthcsos del ZIP viejo es el sample: su npz sha `14d5cc25…` = el de `submission_valid/dfthcsos/submission.npz`; su verificación oficial (`verify_sample_official.log`): PASS, score 3,355,599,588.32, lambda_eff 49.30137, T=93,237, Q=730, 254,464 tiros.
- El dfthcsos de `final_submission.zip` es el lbfgs: sus 10 angle_k_*.kmx tienen los mismos sha que el candidato (`adf19022…`, `6104ef8f…`, etc.) y su npz es `d89772be…`.

**Consecuencia para la adopción:** si hubiera seguido la tarea al pie de la letra (mantener el invsqrt del ZIP viejo = piecewise), el ZIP nuevo habría dado geomean **2.88385x** (calculado en `verificar_zip.log`), una REGRESIÓN frente al 3.31949 de Kaggle, no ~3.332x. El ~3.332x REQUIERE logshift2. Como la tarea misma presupone que el invsqrt ES logshift2 ("El invsqrt (logshift2) NO cambia") y la decisión de Elán es adoptar para llegar a ~3.332x, **el nuevo ZIP usa logshift2** (sha `7e842bbf…`, el mismo de `final_submission.zip` y del mushroom kingdom, byte-idéntico). Es decir: la adopción también CORRIGE el invsqrt de la entrega (piecewise → logshift2). El DQI y el dfthcsos son los adoptados según lo ordenado (fusión+E1d y lbfgs).

**Lo que NO toqué:** `final_submission.zip`, `integracion/submission.zip`, `submission_valid/`, `submission_fb4e95b/` (fuente desempaquetada del ZIP viejo). Quedan intactos para que Elán decida si se actualizan o si el nuevo `valid_submission_fb4e95b.zip` es ahora la entrega.

---

## 3. Piezas adoptadas (verificación por sha256, no por confianza)

**DQI fusionado+E1d** (`dqi_fusionado_e1d.kmb`, 624,877,910 B, sha `16e06d61…3664`):
- Fuente: `~/workspace/qcc-data/dqi-perfil/verificacion_e1d/dqi_fusionado_e1d.kmb`. Verificado por mí: sha coincide con el reporte de verificación.
- Medido (reporte `VERIFICACION_E1D_REPORTE.md`, verificado por Mole contra sus logs): Q=1,934, T=785,012, geomean 3.3259x; PASA sim n=6 (Tests A–C) y PASA verificador oficial en Kali (2,560 tiros, 0 errores de valor, 0 de fase). Build re-medida en la verificación: `TOTAL E1d-alpha Q=1934 T=785012`, ΔQ=−3, ΔT=+840 (=140 inv alpha × 6 T).
- El DQI fusionado (sin E1d, Q=1,937, sha `7a5815f4…`) también PASA el verificador oficial en Kali (2,560 tiros, 0 err) — su verificación pendiente queda cerrada — pero el adoptado es el E1d (mejor).

**dfthcsos lbfgs (65,60,60)** (`candidates/lbfgs_ep100_rho1e-4/`):
- `submission.npz` sha `d89772be…7fa4d` (verificado por mí; distinto del sample `14d5cc25…`).
- `summary.json`: brot 12, batch_size 8, num_vectors 3976, num_angles 75, 10 circuitos angle_k_0..9.kmx (119 qubits c/u, max_magic 3,974), T=93,237, Q=730, score 3,336,160,974.98, error_1 0.00334038813 Ha (3.340 mHa), error_2 0.01937060272 Ha (19.371 mHa), lambda_eff 49.01577193.
- `verify_official.log`: status PASS, score 3,336,160,974.9820175, verified_shots 254,464, submission_sha256 `aa57a7d8…`.
- `check_factorization.log`: error_2 continuo 16.9850 mHa, error_1 continuo ~0; `encode.log` (brot 12): error_1 3.340e-03 Ha, error_2 19.3706 mHa, lambda_eff 49.01577.
- Los 10 angle_k_*.kmx del candidato tienen los mismos sha que los de `final_submission.zip` (ver §2) — doble confirmación de identidad.

**invsqrt logshift2** (`mushroom_kingdom/invsqrt_mushroom_kingdom.kmb`, 437,575 B, sha `7e842bbf…faf79`):
- Medido por mí: `num_qubits=139` (kickmix). Byte-idéntico a logshift2 (reporte consolidado: el ensamblaje Mushroom Kingdom es byte-idéntico a logshift2) y al invsqrt de `final_submission.zip` (mismo sha).
- Score 390,005.06, PASS oficial dominio completo, worst error 0.7920 tol (reporte consolidado).

---

## 4. Verificación del ZIP nuevo (log `verificar_zip.log`)

- Integridad: `testzip` = None (íntegro). 13 archivos, estructura correcta (invsqrt.kmb, dqi.kmb, dfthcsos/angle_k_0..9.kmx, dfthcsos/submission.npz).
- **Los 13 miembros coinciden por sha256 con las piezas verificadas** (invsqrt logshift2, DQI E1d, 10 ángulos lbfgs, npz lbfgs). `TODOS LOS MIEMBROS COINCIDEN: True`.
- ZIP sha256 `171d5a81c4ca47b17573d4876acb3b63386b7048a5f7b1f77fae4e4a60a7f87e`.
- Verificado de nuevo en su ubicación final tras el reemplazo (log `verificar_final.log`): mismo sha, testzip None, 13 archivos.
- **Geomean calculado** (referencias documentadas: invsqrt ref 2,070,563; DQI ratio 6.77x para Q=1,949; dfthcsos sample ratio 1.00583x):
  - invsqrt ratio = 2,070,563 / 390,005.06 = **5.30907**
  - DQI ratio = 6.77 × (1949/1934)² × (784172/785012) = **6.86807**
  - dfthcsos ratio = 1.00583 × (3,355,599,588 / 3,336,160,975) = **1.01169**
  - producto = 36.88930 → **geomean = 3.32890x**
  - Anterior (logshift2 + DQI 1,949 + sample) = 3.30657x → mejora +0.0223x.
  - Con el invsqrt piecewise del ZIP viejo (599,866) + E1d + lbfgs = 2.88385x (lo que habría dado seguir la premisa incorrecta).

**Caveats (leer antes de citar el geomean):**
1. El 3.3289x es CALCULADO desde las referencias documentadas, no medido en Kaggle. El geomean autoritativo lo da el scoring de Kaggle (~45 min) tras subir el ZIP — eso es decisión de Elán, no de este trabajo. Nada se subió a Kaggle.
2. La estimación de la tarea (~3.332x) difiere de mi cálculo (3.3289x) en 0.003 (0.09%) — redondeo en los ratios de referencia (6.77x y 1.00583x, 3 cifras). Mismo valor dentro del redondeo.
3. El ZIP en sí NO pasó por el verificador oficial completo de la entrega (~45 min en Kaggle). Cada pieza SÍ pasó su verificador oficial por separado (invsqrt logshift2 PASS dominio completo; DQI E1d PASS sim n=6 + PASS oficial Kali 2,560 tiros; dfthcsos lbfgs PASS oficial 254,464 tiros). La verificación del ZIP completo aquí es: integridad + identidad por sha256 de cada miembro contra las piezas verificadas.
4. El Kaggle 3.31949 (2026-11-07) vino del "zip a741cc7 (DQI Q=1,949)", que NO es ninguno de los tres ZIPs que encontré (no lo localicé como archivo). No afirmo que el nuevo ZIP supere ese 3.31949 en Kaggle hasta que se mida allí.

---

## 5. Qué cambió vs el ZIP viejo (para el reporte al Coordinador)

| | ZIP viejo (`f48fcaf5…`) | ZIP nuevo (`171d5a81…`) |
|---|---|---|
| invsqrt | piecewise, Q=185, score 599,866 | **logshift2, Q=139, score 390,005.06** |
| dqi | baseline, Q=1,949, T=784,172 | **fusionado+E1d, Q=1,934, T=785,012** |
| dfthcsos | sample, score 3,355,599,588 | **lbfgs, score 3,336,160,975** |
| geomean (calculado) | ~2.87x | **~3.329x** |

---

## 6. Archivos

Scratch: `~/workspace/qcc-data/adopcion/`
- `ADOPCION_REPORTE.md` — este reporte.
- `nueva_entrega/` — fuente desempaquetada del ZIP nuevo (invsqrt.kmb logshift2, dqi.kmb E1d, dfthcsos/ lbfgs + summary.json).
- `nuevo_zip/submission_adopcion_2026-11-12.zip` — el ZIP construido (sha `171d5a81…`, idéntico al de la entrega).
- `backup/valid_submission_fb4e95b.zip.OLD` — backup del ZIP viejo (sha `f48fcaf5…`).
- `zip_actual/invsqrt.kmb` — el invsqrt piecewise extraído del ZIP viejo (evidencia).
- `construir_zip.log`, `verificar_zip.log`, `verificar_final.log` — logs de construcción y verificación.

Entrega: `~/workspace/qcc-data/valid_submission_fb4e95b.zip` (sha `171d5a81…`, 66,225,789 B).

## 7. Pendientes (no son de esta adopción)

- **Notebook público** (milestone 2026-11-20): lo lanza el agente padre después de este veredicto.
- **Subir a Kaggle / marcar la selección final (0 de 2):** decisión de Elán, solo él puede hacerlo. Nada se subió.
- **Decidir si `final_submission.zip` (2c3018f8) e `integracion/submission.zip` (ce1d12a6) se actualizan** con el DQI E1d (hoy tienen el BM v7 Q=2,016): quedaron intactos a propósito; Elán / el Coordinador deciden.
- Opcional: verificación completa del DQI E1d a 102,400 tiros en la Kali (~65 min, gold-standard) — no corrida; la evidencia actual (sim n=6 exacto + 2,560 tiros 0 errores) es sólida para adoptar.
