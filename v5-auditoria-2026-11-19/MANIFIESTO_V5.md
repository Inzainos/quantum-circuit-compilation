# Manifiesto v5 — Rama de auditoría para Claude (auditor externo)
Fecha: 2026-11-19. Rama: `local/v5-auditoria-2026-11-19`, base `main` 64d4cec. Orden de Elán (16:55:06, vía Coordinador): poner todo el trabajo de la v5 en una rama para que Claude, el auditor externo, empiece a analizarlo.

## Contenido
- `qf/` — Parche QF (`qf_main64d4cec_0_ehz1.patch`, 18,393 B, md5 d2fdc869…) + cadena completa (Reporte, Supervisión Datos, Verificación Brujo, Revisión Auditor) + build script + Gold logs.
- `r1r5/` — R1+R5, nueva referencia invsqrt: cadena completa + `invsqrt_R1R5.kmb` + controles (B, R1, R5, baseline) + logs Gold/1-shot.
- `p1/`, `p2/`, `p3/` — Las tres P, cadena completa cada una + build script + archivo modificado clave (`dqi_kmul42.py` en P1; `dqi_decoder_v1.py` en P2 y P3) + logs.
- `givens/` — Alcance del árbol de Givens O7 (en construcción por Programación; el trabajo es el MODELO, no un circuito).
- `recomendacion-conjunta/` — Recomendación conjunta de adopción + revisión del Auditor.
- `verificacion-v5/` — Verificación Brujo QF + lbfgs para v5 (este informe).

## Números clave (todos medidos, cadena completa)
- **invsqrt R1+R5 (adoptado):** Q=139, T=2,561, score 389,261.01, Gold PASS (200,540,928 shots). `invsqrt_R1R5.kmb` sha256 `a30a1298…` — byte-idéntico a R1.
- **DQI QF (adoptado, v4.1):** Q=1857 (−7), T=710,312 (ΔT=0), Gold PASS, score 2,971,470,537,625.3, 5 valor / 0 fase, reaction_depth 3,154. Kaggle v4.1 (ref 58579331): **3.54317, personal best**.
- **P1+P2+P3:** las tres PASA, circuitos byte-idénticos a swap42 (sha `746271d9…`, 646,811,990 B). El build combinado P1+P2+P3 sobre código QF tiene GO y está en construcción.
- **dfthcsos lbfgs (adoptado):** Q=730, T=93,237, score 3,336,160,975, error_2 19.371 mHa, error_1 3.340 mHa, PASS oficial (254,464 shots). `.npz` md5 `81ff3249…`; `submission.npz` md5 `521d53c6…` (idéntico en v3 y v4.1).
- **Geomean medido:** QF+R1R5 = 3.53396; Kaggle v4.1 = 3.54317.

## Lo que NO va en la rama (y por qué)
Los .kmb de DQI son binarios grandes (>100 MiB, límite de GitHub para archivos sueltos; repo AGENTS.md: van a Releases o LFS). NO se commitean aquí; se referencian por hash:
- `dqi_qf.kmb` — 628,685,675 B, sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13`
- `dqi_p1.kmb` / `dqi_p2.kmb` / `dqi_p3.kmb` — 646,811,990 B c/u, sha256 `746271d961a74cf2…` (byte-idénticos a swap42)
- Los .kmb de invsqrt SÍ van (437 KB c/u, bajo el límite).

## Cómo verificar
- `sha256sum` / `md5sum` contra los hashes de arriba.
- Los Gold logs están en `qf/` y `r1r5/`; los reportes de cadena (4 firmas: Programación → Datos → Brujo → Auditor) están en cada carpeta.
- Regla del repo: todo cambio de circuito pasa el verificador kickmix (fuzz, Fiat–Shamir); nunca afirmar mejora sin medir contra la baseline.
