# ESTADO — Adopción fusión + E1d + lbfgs (2026-11-12)

**Fecha:** 2026-11-12
**Orden de Elán (2026-11-12 ~11:59, palabras exactas, relayada por el Coordinador):** "Actualicen github".
**Rama:** `fix/zip-final-2026-11-07` (NO main).

## Puntaje autoritativo medido en Kaggle — nuevo personal best

- **Geomean medido: 3.33544** (antes 3.31949, ref 58113636 "v8", 2026-11-08). Mejora +0.01595 (+0.48%).
- **Envío:** ref 58277509, 2026-11-12T15:34:22.297Z, 66,225,789 B, file_name `submission.zip`, submitted_by `elnzainoscorona`, team_name `Frantal Core`, status **COMPLETE**.
- **Scoring:** ~36 min (subida 15:34:22Z → puntaje 16:10:20Z).
- **Rank:** 2520 de 2917 equipos (user_rank 2520, team_count 2917).
- **Geomean calculado 3.3289x → medido 3.33544** (+0.0065, +0.20% arriba del calculado; la diferencia es por las referencias exactas de Kaggle).
- **La selección final (0 de 2) NO está marcada** (solo Elán puede hacerlo).

## La entrega adoptada

- **ZIP:** `valid_submission_fb4e95b.zip`, sha256 `171d5a81c4ca47b17573d4876acb3b63386b7048a5f7b1f77fae4e4a60a7f87e`, 66,225,789 B (63.2 MB), 13 archivos, íntegro.
- **invsqrt:** logshift2, Q=139, C=2,805.79, score 390,005.06, PASS oficial dominio completo (200,540,928 tiros, peor error 0.7920 tol).
- **DQI:** fusionado+E1d, Q=1,934, T=785,012, geomean 3.3259x. Fusión F1b (inversión directo en alpha + CSWAP, ahorra Pinv 12; Q 1,949→1,937) + E1d (liberar N' antes de los productos, +6 T/inv; Q 1,937→1,934).
- **dfthcsos:** lbfgs (65,60,60), score 3,336,160,975 (−0.58% vs sample), error_1 3.340 mHa, error_2 19.371 mHa, λ_eff 49.0158, PASS oficial 254,464 tiros.
- **Verificación gold-standard DQI:** PASA verificador oficial en la Kali a 102,400 tiros, **2 errores de valor, 0 de fase**, eps_plus 0.000949, R 1.2014, score DQI 3,527,544,869,510.532. Los 2 errores son la tasa intrínseca del decodificador BM (el baseline tuvo 0 fallos a semilla 1 y 2 a semilla 7 en 102,400 tiros); R ya los incluye.

## Notebook público

- **URL:** https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation
- **Kernel ID:** 144639626, ref `elnzainoscorona/verifiable-quantum-circuit-compilation`, versión 2, **PÚBLICO** (`is_private: false`).
- **Ejecución en Kaggle:** sesión COMPLETE, 0 errores, 40 entradas de log, 0 con Traceback/Error; las 5 celdas de código produjeron las salidas documentadas.
- **El notebook en este directorio** (`qcc_submission_logshift2_fused_dqi_lbfgs.ipynb`, sha256 `ad0033be84e0071acc08075ce2605de50b37c51e2c5d4dd44267ba52573b2b97`, 40,894 B, 17 celdas, 0 errores) es el **borrador original**. La copia publicada en Kaggle (sha256 `8d721babe5e21a2b4134a930bc1c6a6ec96390ee1cfcea6cded45e6fce0c3080`) difiere SOLO en `metadata.kernelspec`: `py313` (local) → `python3` (Kaggle). Celdas idénticas, ningún número, atribución ni declaración cambió. La v1 falló por el kernelspec local (`NoSuchKernel: py313`); la v2 corrige solo eso.

## Hallazgo crítico de la adopción (corregido)

El ZIP viejo (`valid_submission_fb4e95b.zip`, sha `f48fcaf5…`) contenía el invsqrt **piecewise** (Q=185, score 599,866), NO logshift2. La adopción también corrigió el invsqrt de la entrega (piecewise → logshift2). Seguir la premisa al pie de la letra habría dado geomean 2.88385x, una regresión. Ver `ADOPCION_REPORTE.md` §2.

## Decisión de Elán revertida explícitamente

La adopción del lbfgs revierte la decisión de Elán "NO insertar" el lbfgs (2026-11-09 ~14:35). Elán la confirmó el 2026-11-12 ~08:35 (vía el widget, palabras exactas): "Sí, adopten todo (fusión + E1d + lbfgs)". El camino de la forma pequeña (8,143,60) se cerró (escalera, refit brot=8, factorización desde cero, mixed brot — todos NO).

## Pendientes (no en este push)

- **Binarios grandes (NO pusheados por el conector — snapshot-only, ≤16 MiB, sin binarios):**
  - ZIP de la entrega, 66,225,789 B (~63 MB): cabe en git (<100 MiB) y el AGENTS.md lo permite como artefacto `submission/final_submission.zip`, pero solo vía un push git completo desde la máquina de Elán.
  - DQI `dqi_fusionado_e1d.kmb`, 624,877,910 B (~596 MB): supera el límite de 100 MiB de GitHub — NO puede ir en git; va por Release (asset) o Git LFS (no configurado en el repo: no hay `.gitattributes`).
  - Ver `GITHUB_REPORTE.md` (en `~/workspace/qcc-data/github/`) para el camino exacto de cada binario.
- **Postura C14/B7 del planner (junta, SIN RESOLVER):** usar el planner full-XOR Apache-2.0 as-is con atribución vs reimplementarlo desde el método. El notebook NO lo incluye como pieza de la entrega y lo dice explícitamente (§6).
- **Selección final en Kaggle (0 de 2):** solo Elán puede marcarla.
- **Actualizar `final_submission.zip` (2c3018f8) e `integracion/submission.zip` (ce1d12a6)** con el DQI E1d (hoy tienen el BM v7 Q=2,016): quedaron intactos a propósito; Elán decide.

## Archivos de este directorio

| Archivo | Contenido |
|---|---|
| `FUSION_MUL_INV_REPORTE.md` | Fusión mul+inv (F1b): Q 1,949→1,937, T idéntico, geomean 3.3237x |
| `REDISENIO_INVERSOR_REPORTE.md` | Rediseño del inversor: E1d gana (Q→1,934, geomean 3.3259x); Itoh-Tsujii, torre cúbica, builtin, lookup NO-GO |
| `VERIFICACION_E1D_REPORTE.md` | Verificación E1d: PASA sim n=6 + oficial Kali 2,560 tiros, 0 errores |
| `VERIFICACION_GOLD_REPORTE.md` | Verificación gold: PASA oficial Kali 102,400 tiros, 2 errores valor, 0 fase, eps_plus 0.000949, R 1.2014 |
| `ADOPCION_REPORTE.md` | Adopción: ZIP reconstruido y verificado, geomean calculado 3.3289x; hallazgo piecewise→logshift2 |
| `SUBIDA_KAGGLE_REPORTE.md` | Subida a Kaggle: ref 58277509, puntaje medido 3.33544, rank 2520/2917 |
| `NOTEBOOK_REPORTE.md` | Borrador del notebook: 17 celdas, 0 errores; corrección C=2,805.79 (redondeo) |
| `PUBLICAR_NOTEBOOK_REPORTE.md` | Publicación del notebook: URL, kernel 144639626, v2, PÚBLICO, run COMPLETE 0 errores; arreglo kernelspec |
| `qcc_submission_logshift2_fused_dqi_lbfgs.ipynb` | El notebook (borrador original, sha `ad0033be…`) |
| `ESTADO_ADOPCION_2026-11-12.md` | Este archivo |
