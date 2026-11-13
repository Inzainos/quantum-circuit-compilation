# ESTADO — Promoción DQI sin t a producción (2026-11-12)

**Fecha:** 2026-11-12
**Decisión de Elán (2026-11-12 ~16:47, palabras exactas):** "Promovemos de inmediato dqi_sin_t.kmb (Q = 1,864, T = 786,272) a producción."
**Rama:** `fix/zip-final-2026-11-07` (NO main).

## Puntaje autoritativo medido en Kaggle — nuevo personal best

- **Geomean medido: 3.41660** (antes 3.33544, ref 58277509, 2026-11-12). Mejora +0.08116 (+2.43%). Exacto a la proyección (3.41660x escalando el medido 3.33544x; calculado 3.40990x).
- **Envío:** ref 58286822, 2026-11-12T22:52:49.910Z, 66,288,156 B, file_name `submission.zip`, submitted_by `elnzainoscorona`, team_name `Frantal Core`, status **COMPLETE**.
- **Scoring:** ~40 min (subida 22:52:49Z → puntaje 23:33:16Z, poll 9). **Rank:** 2538 de 2936 equipos.
- **Geomean calculado 3.40990x → medido 3.41660** (+0.0067, +0.20% arriba del calculado; la diferencia es por las referencias exactas de Kaggle).
- **La selección final (0 de 2) NO está marcada** (solo Elán puede hacerlo; marcar el ref 58286822).

## La entrega adoptada (v2)

- **ZIP:** `valid_submission_fb4e95b.zip`, sha256 `ba222d1c130acec71406b1b5473e78140ce87f4af8041db5907dc4ff8b9e0703`, 66,288,156 B (63.2 MB), 13 archivos, íntegro. Backup del ZIP anterior (fused+E1d, Q=1,934): sha `171d5a81…`, en `adopcion-sin-t/backup/`.
- **invsqrt:** logshift2, Q=139, C=2,805.79, score 390,005.06, PASS oficial dominio completo (200,540,928 tiros, peor error 0.7920 tol). Sin cambio.
- **DQI:** fusionado+E1d, **t eliminada**, Q=1,864, T=786,272, geomean calculado 3.4099x. Fusión F1b (Q 1,949→1,937) + E1d (Q 1,937→1,934) + t eliminada (Q 1,934→1,864, T +1,260). La t se reconstruye desde d: t = (¬p) ∧ (d_post ≤ 0), 9 T × 140 llamadas (Opción B simétrica — la prescripción literal de 0 T en la ida no era implementable: del_and limpia el target, no un control).
- **dfthcsos:** lbfgs (65,60,60), score 3,336,160,975 (−0.58% vs sample), error_1 3.340 mHa, error_2 19.371 mHa, λ_eff 49.0158, PASS oficial 254,464 tiros. Sin cambio.
- **Verificación gold-standard DQI sin t:** PASA verificador oficial en la Kali a 102,400 tiros, **2 errores de valor, 0 de fase**, eps_plus 0.000949, R 1.2014 — idénticos dígito a dígito a los del Gold del DQI E1d. Score DQI 3,527,544,869,511 → 3,282,070,743,071 (−6.96%); ratio DQI 6.86807 → 7.38175. La reserva teórica (D=0, d<0) no generó ni un error adicional.

## Código generador (reproducibilidad)

- `src/dqi_bm_stage_v1.py`, `src/bm_fused.py`, `src/bm_fused_e1d.py` — versiones sin-t en el repo, commit `c0fb9a57e6d99977fb102676343dc7c05139c851` (verificado 3/3 por blob SHA; pytest 34 passed con los módulos sin-t).
- Build: `dqi-perfil/rama_t_eliminada/construir_dqi_sin_t.py` → `dqi_sin_t.kmb` (TOTAL SIN-T Q=1864 T=786272, sha `8dd3e6a3…6bf`).
- Reporte de la rama: `dqi-perfil/rama_t_eliminada/RAMA_T_ELIMINADA_REPORTE.md`. Reporte de esta promoción: `adopcion-sin-t/PROMOCION_SIN_T_REPORTE.md`.

## Notebook público

- **URL:** https://www.kaggle.com/code/elnzainoscorona/verifiable-quantum-circuit-compilation
- **Kernel ID:** 144639626, ref `elnzainoscorona/verifiable-quantum-circuit-compilation`, **versión 3**, **PÚBLICO** (`is_private: false`).
- Ejecución en Kaggle: sesión COMPLETE, 42 entradas de log, 0 con Traceback; las salidas coinciden con los números documentados (geomean 3.40990x, DQI ratio 7.38175, ZIP sha `ba222d1c…`).
- Generador: `notebook/build_notebook_v3.py` (34 sustituciones exactas verificadas). Ejecución local: 0 errores.

## Pendientes (no en este push)

- **Binarios grandes (NO pusheados por el conector — snapshot-only, ≤16 MiB, sin binarios):**
  - ZIP de la entrega, 66,288,156 B (~63 MB): cabe en git (<100 MiB) y el AGENTS.md lo permite como artefacto `submission/final_submission.zip`, pero solo vía un push git completo desde la máquina de Elán.
  - DQI `dqi_sin_t.kmb`, 624,960,230 B (~596 MB): supera el límite de 100 MiB de GitHub — NO puede ir en git; va por Release (asset) o Git LFS (no configurado en el repo: no hay `.gitattributes`).
- **Postura C14/B7 del planner (junta, SIN RESOLVER):** usar el planner full-XOR Apache-2.0 as-is con atribución vs reimplementarlo desde el método. El notebook NO lo incluye como pieza de la entrega y lo dice explícitamente (§6).
- **Selección final en Kaggle (0 de 2):** solo Elán puede marcarla (ref 58286822).
- **Actualizar `final_submission.zip` (2c3018f8) e `integracion/submission.zip` (ce1d12a6)** con el DQI sin-t (hoy tienen el BM v7 Q=2,016): quedaron intactos a propósito; Elán decide.
- **Siguiente palanca medida (no verificada como cambio):** `build_omega_tmp` usa el constructor de 63 T en 630 gf_mul por dirección; Karatsuba (54 T) ahorraría 11,340 T (~1.44% de T) sin subir Q. Necesita su propia rama, build y verificación oficial — otro agente, después de asegurar esta entrega en Kaggle.
