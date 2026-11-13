# Estado de la entrega adoptada v3 — DQI omega/Karatsuba (2026-11-12)

**Fecha:** 2026-11-12/13 (promoción 2026-11-12 ~18:11–00:50 CST, America/Mexico_City)
**Decisión de Elán (2026-11-12 ~18:11, palabras exactas):** "promovemos de inmediato dqi_omega_karatsuba.kmb (Q = 1,864, T = 774,932) a producción y subimos a Kaggle."

## Descripción canónica (Elán, 2026-11-12 ~18:47, vía Coordinador) — VERBATIM

"Adopted v3: logshift2 invsqrt (Q=139) + DQI omega/Karatsuba without t (Q=1864, T=774932) + lbfgs dfthcsos; calc geomean 3.42645x; DQI gold-verified 102400 shots PASS (2 value errors, 0 phase)"

## Los tres circuitos definitivos

| Task | Circuito | Métricas | Ratio / Score |
|---|---|---|---|
| invsqrt | logshift2 (deg=2, j=8, wc=28, dd=13) | Q = 139, T = 2,561 | 5.30907× (Score = 390,005.06) |
| DQI | omega/Karatsuba + sin t + fusionado + E1d | Q = 1,864, T = 774,932 | 7.48977× (Score = 3.2347e12) |
| dfthcsos (FeMoCo) | lbfgs (65,60,60, brot=12, J=8) | Q = 730, T = 93,237 | 1.00583× (Score = 3.3362e9) |

## Medición en Kaggle (oficial)

- **Submission ref: 58289295** — 2026-11-13T00:17:18Z, 66,674,933 B, file_name `submission.zip`, status **COMPLETE**.
- **Geomean medido: 3.42920** — nuevo personal best (antes 3.41660, ref 58286822, +0.01260, +0.37%).
- Geomean calculado: 3.42645×. El medido quedó +0.00275 sobre el calculado (+0.08%); el escalado previo (~3.43319×) era una estimación, no una medición.
- **Rank: 2,545 de 2,940 equipos** (antes 2,538/2,936 — entraron más equipos).
- Descripción del envío en Kaggle: idéntica, carácter por carácter, a la descripción canónica de arriba (verificado por lectura independiente con `get_competition_submission`).

## Piezas de la entrega

- **ZIP en producción:** `valid_submission_fb4e95b.zip`, sha256 `83b0c75615274769a36d3822da2f8f5c63470dc59f6820bee516a0952c7b1c4d`, 66,674,933 B, 13 archivos, `testzip` None. Solo cambia `dqi.kmb` respecto al ZIP anterior (omega, sha `209d53e2…a1a5c884`). Backup del ZIP anterior (sin-t) como `.OLD` (sha `ba222d1c…`).
- **DQI omega/Karatsuba:** Q = 1,864 intacto, T = 774,932 (−11,340 exacto). Gold oficial en Kali, 102,400 tiros: **PASS**, 2 value errors, 0 phase, eps_plus 0.0009488155716079551, R 1.2013880602795501 (idénticos al sin-t).
- **Notebook público:** versión 4, kernel 144639626, misma URL (https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation), sesión **COMPLETE**, 42 entradas, 0 Traceback. Incluye la descripción canónica verbatim.
- **GitHub (rama `fix/zip-final-2026-11-07`):** `src/dqi_decoder_v1.py` (omega, commit `4d1ba483…`, verificado por blob SHA) + docs de esta promoción. pytest 34 passed.

## Pendientes (solo Elán)

- **Marcar la selección final en Kaggle (0 de 2)** — a mano en su cuenta; el envío a marcar es el ref **58289295 (3.42920)**.
- **Actualizar main en GitHub** — el repo NO tiene rama `main`; la rama por defecto es `main/quantum-circuit-compilation-v0.1.0` (HEAD `3dc0c58c…`). El merge de `fix/zip-final-2026-11-07` en ella se probó en local y es LIMPIO (40 archivos, +4,693/−18, sin conflictos). Pasos exactos en `PROMOCION_OMEGA_REPORTE.md` §6.
- `final_submission.zip` e `integracion/submission.zip` siguen intactos (BM v7 Q=2,016) — Elán decide si se actualizan.
- El experimento del motor clásico en FeMoCo (ALS/Gauss-Newton) sigue en paralelo en scratch; no afecta a esta entrega.
