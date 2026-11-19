# REPORTE QF — Parche −7 qubits de Claude aplicado en la Kali, DQI construido + Gold con seed fijo

**Fecha:** 2026-11-19 (construcción ~12:52–12:55 CST; Gold control 13:49:44–14:02:13; Gold QF 14:06:51–14:19:01)
**Orden:** Elán (2026-11-19 ~12:49, vía el Brujo) — "dile a la gente local que aplique el parche".
**Constructor:** Programación (subagente constructor QF).
**Cadena:** Programación (construye + Gold) → Brujo (verifica) → Datos (supervisa) → Auditor (revisa) → Elán (decide).
**Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán. NO push a GitHub.**

---

## 1. Qué es QF

El parche de Claude quita las 3 ancillas de los multiplicadores y de la torre
de inversión (formas lineales en el sitio + Toffoli con fan-out, mismo T),
mueve el update de `d` a un punto de menos carga, reordena el andamio de la
torre, forma `s` y `dd` en el sitio en el barrido. Esperado: **Q 1,864 → 1,857,
T sin cambio (710,312)**. Revisión estática + Q/T del Brujo: CONCURRO
(`REVISION_BRUJO_PARCHE_CLAUDE_2026-11-19.md`, 168 l. / md5 `b379dee5…`).

## 2. El parche (ORIGINAL, no la reconstrucción del PDF)

- Archivo: `~/workspace/user/files/qf_main64d4cec_0_ehz1.patch`
  (18,393 B, md5 `d2fdc8694fe5d21af8af08d14b4e9beb`, 451 l., 8 archivos, 16 hunks).
- md5 verificado ANTES de copiarlo y DESPUÉS en la Kali (mismo md5).
- Copia en la Kali: `/home/deamon/qf_main64d4cec_0_ehz1.patch` (md5 verificado).
- La reconstrucción desde el PDF
  (`~/workspace/qcc-data/claude-parche/qf_main64d4cec.patch`) NO se usó —
  no es fiable, queda superada.

## 3. Aplicación en la Kali (worktree aparte, árbol sucio intacto)

Repo: `/home/deamon/quantum-circuit-compilation`.
Estado ANTES (verificado, no tocado): rama `local/final-submission-2026-11-13`
@ `d78e970`, árbol SUCIO (`M submission/final_submission.zip` + 4 archivos sin
seguimiento: `TODO_CLON_QUANTUM.md`, `input.html - brief-contexto-modelos.pdf`,
`prueba.md`, `wt_deamonx/`). Estado DESPUÉS: idéntico (verificado tras los
reboots — ver §9).

- `git fetch origin` → `origin/main` = `64d4cec3edcae9a4d68ed1d721d7686e473220db`
  (verificado por `ls-remote`).
- Worktree: `/home/deamon/quantum-circuit-compilation-qf`, rama nueva
  `local/claude-qf-minus7-2026-11-19`, HEAD `64d4cec` (Merge PR #32).
- `git apply --check -p1 --directory=src` → **OK**; aplicado → **OK**.
- `git status`: 7 modificados + `src/qf.py` nuevo (57 l., 1,830 B).
- `git diff --stat`: 7 archivos, 76 inserciones, 117 eliminaciones.
  `bm_fused.py` 20 · `dqi_decoder_v1.py` 42 · `dqi_kmul42.py` 21 ·
  `dqi_tower_inv.py` 25 · `dqi_tower_inv2.py` 29 · `dqi_tower_inv3.py` 24 ·
  `tower_inv3_e1d.py` 32.
- `py_compile` OK en los 8; `qf` importa con las 5 helpers (`form_ip`,
  `unform_ip`, `fan_ccx`, `mul_terms_init`, `mul_terms_phase`); todos los
  módulos DQI importan (`dqi_bm_stage_v1`, `dqi_decoder_v1`, `dqi_kmul42`,
  `dqi_tower_inv`, `dqi_tower_inv2`, `dqi_tower_inv3`, `tower_inv3_e1d`,
  `bm_fused`, `bm_fused_e1d`).

## 4. El bug de mezcla D-QF-1 — verificado que NO me afectó

El Brujo advirtió (~13:04): su primer build de scratch salió MEZCLADO
(Q=1,861, T=736,772) porque `dqi_decoder_v1` se cargó desde `qcc-dqi/src`
(sin parche): `dqi_tower_inv3.py` y `dqi_scan_stage.py` hacen
`sys.path.insert(0, str(ROOT / "src"))` con ROOT de su propio `__file__` y
rompen el shadowing. Su fix: importar el decoder primero + aserción de
módulos desde scratch. Leí su revisión completa antes de construir.

**Mi build NO se mezcló (medido, no asumido):**
- El worktree tiene el `src/` COMPLETO de main 64d4cec + parche (no un
  scratch parcial): todos los módulos se cargan desde el worktree, y los
  `sys.path.insert` de `tower_inv3`/`scan_stage` apuntan de vuelta al
  worktree (su `__file__` es del worktree).
- `build_qf.log` prueba la procedencia: los 4 módulos del build vienen de
  `/home/deamon/quantum-circuit-compilation-qf/src/` (ver §5).
- **El `.kmb` resultante es BYTE-IDÉNTICO al control independiente del
  Brujo** (`~/workspace/qcc-data/claude-parche/dqi_qf.kmb`, 628,685,675 B):
  mismo sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13`,
  mismo tamaño, mismo Q/T (ver §5). Si hubiera mezcla, el sha diferiría.

## 5. El build (Kali, ruta swap42, CPU con nice)

Script: `/home/deamon/workspace/qcc-data/claude-qf/construir_dqi_qf.py`
(adaptado de `construir_dqi_omega.py`; `sys.path` = worktree `src/`; OUT =
`/home/deamon/workspace/qcc-data/claude-qf/dqi_qf.kmb`).
Copia local del script: `construir_dqi_qf.py` (2,746 B).

`build_qf.log` (858 B):
- Módulos: `dqi_bm_stage_v1`, `bm_fused`, `bm_fused_e1d`, `dqi_decoder_v1` —
  TODOS desde `/home/deamon/quantum-circuit-compilation-qf/src/`.
- `live_frontera` 1794/1794/1794/1794/1724 (idénticos a swap42).
- **TOTAL QF Q=1857 T=710312 en 136 s.**
- Delta Q=−7, Delta T=0 (esperado Delta Q=−7, Delta T=0). ✓
- **Circuito: `dqi_qf.kmb` (628,685,675 B, sha256
  `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13`) —
  BYTE-IDÉNTICO al control del Brujo** (verificado por sha256sum en la Kali
  y en esta caja tras la copia).
- Los prints de ratio/geomean del script (8.16189x / 3.52162x) usan el ancla
  desactualizada 7.48129 y NO corrigen por el cambio de Q (D-P1-1): los
  verdaderos están en §8.
- Estadísticas cargadas del `.kmb` (verificadas por mí y por el Brujo):
  Q=1,857, T=710,312, num_bits=198,813 (igual que swap42),
  num_instructions=72,168,849 (swap42: 74,182,884 — 2,014,035 menos).

## 6. El seed — derivación y validación (el punto crítico)

El Gold de swap42 (`run_verify_swap42_gold.sh`) NO pasó `--seed`. El
verificador (`verify_submission_dqi.py`, leído en la Kali) deriva el seed
del sha256 del circuito salvo `--seed`:

```python
def _initial_seed(circuit_hash: str, salt: str) -> int:
    if not salt:
        return int(circuit_hash, 16)
    return int(hashlib.sha256(f'{circuit_hash}{salt}'.encode('utf-8')).hexdigest(), 16)
```

Por tanto el seed del Gold de swap42 es:

**seed = int("746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603", 16)
= 52642227205936912575373656611044064096114070193057152544535209180255000077827**
(77 dígitos; roundtrip verificado: `format(seed, '064x') == hash`).

El mismo seed alimenta las muestras y los resultados HMR/R del simulador,
así que con `--seed` fijo la comparación QF vs swap42 es manzana con
manzana. El seed se validó empíricamente con el control (§7): si la
derivación fuera incorrecta, el control NO reproduciría el Gold publicado.

## 7. Gold control — swap42 con --seed explícito: REPRODUCE EXACTO

Script: `run_verify_qf_gold_control.sh` (misma ruta que
`run_verify_swap42_gold.sh` + `--seed <seed swap42>`).
Log: `verify_qf_gold_control.log` (1,412 B), 13:49:44–14:02:13 (12.5 min).

Resultado: **PASS, exit_gold=0 — TODOS los números idénticos al Gold
publicado de swap42** (ver `verify_swap42_gold.log`):
score 2,993,914,799,696.024 · R=1.2131052140444296 · 5 errores de valor /
0 de fase · 102,400 tiros · T=710,312 · Q=1,864 · reaction_depth 19,501 ·
num_ops 74,182,884 · num_bits 198,813 · `circuit_sha256` 746271d9…

**El seed queda validado.** (El primer intento del control, PID 340623,
lanzado 12:57:04, murió a los ~22 min por el reinicio de la Kali a las
13:19:03 sin resultado — ver §9. El segundo intento, PID 1261, es el que
completó.)

## 8. Gold QF — PASS con seed fijo (mismo seed que swap42)

Script: `run_verify_qf_gold.sh` (misma ruta + `--seed <seed swap42>`).
Log: `verify_qf_gold.log` (1,415 B), 14:06:51–14:19:01 (12 min 10 s).
Circuito verificado: sha256 `38b9cbf0…` (el `.kmb` QF).

Resultado: **PASS, exit_gold=0.**

| Campo | swap42 (control, mismo seed) | QF (mismo seed) | Delta |
|---|---|---|---|
| status | PASS | PASS | — |
| score | 2,993,914,799,696.024 | **2,971,470,537,625.3** | −22,444,262,070.724 (−0.7497%) |
| repetition_factor R | 1.2131052140444296 | **1.2131052140444296** | 0 (idéntico) |
| value_errors | 5 | 5 | 0 |
| phase_errors | 0 | 0 | 0 |
| verified_shots | 102,400 | 102,400 | 0 |
| empirical_error_rate | 4.8828125e-05 | 4.8828125e-05 | 0 |
| effective_error_rate | 0.0010479495500463395 | 0.0010479495500463395 | 0 |
| mean_error_weight | 31.046737331746634 | 31.046737331746634 | 0 |
| log2_delta | −128.0 | −128.0 | 0 |
| toffoli_count | 710,312 | 710,312 | 0 |
| num_qubits | 1,864 | **1,857** | −7 |
| num_bits | 198,813 | 198,813 | 0 |
| num_ops | 74,182,884 | **72,168,849** | −2,014,035 |
| reaction_depth | 19,501 | **3,154** | −16,347 (÷6.18) |

**Aritmética verificada por cómputo propio (no estimada):**
- Factor (1857/1864)² = 0.9925033731510986 → mejora real 0.7497%.
- Score esperado = 2,993,914,799,696.024 × 0.9925033731510986
  = 2,971,470,537,625.2993; medido = 2,971,470,537,625.3
  (diff 0.0005 = redondeo float — **exacto**).
- DQI ratio QF = 8.16289 / 0.9925033731510986 = **8.22455**
  (esperado del Brujo: 8.22455 ✓).
- Geomean medido QF = 3.52286 / 0.9925033731510986^(1/3) = **3.53171**
  (esperado del Brujo: 3.53171 ✓).
- Geomean escala Kaggle QF = 3.53019 / 0.9925033731510986^(1/3) = **3.53906**
  (esperado del Brujo: 3.53906 ✓).

**La mejora del score es EXACTAMENTE el factor Q²** — R es idéntico, los
errores son idénticos, T es idéntico. El ruido de seed queda eliminado por
el seed fijo: la comparación es limpia.

## 9. HALLAZGO — reaction_depth colapsa 19,501 → 3,154 (÷6.18)

No estaba en el reporte de Claude ni en la revisión del Brujo (no tenían el
Gold). Medido de los dos JSON Gold (mismo seed, mismas 102,400 muestras):

- **reaction_depth: 19,501 → 3,154 (−16,347, factor 6.18×).**
- Operaciones por tiro (shot_operation_counts, 102,400 tiros):
  - R: 67,694,592,000 → 10,311,168,000 (÷6.57).
  - HMR: 81,564,672,000 → 24,181,248,000 (÷3.37).
  - CX: 6,569,789,235,200 → 6,535,702,323,200 (−34,086,912,000).
  - CZ: 188,636,410,370 → 159,946,096,370 (−28,690,314,000).
  - CCX: 68,784,128,000 → 68,784,128,000 (igual — mismo T).
  - X, SWAP, CSWAP, INFO_TAG, POP/PUSH: iguales.
- Interpretación (medida, no teorizada): las formas en el sitio + el
  Toffoli con fan-out eliminan las cadenas secuenciales de ancillas (HMR/R)
  que dominaban la profundidad. El score no cambia por esto (score =
  R × Q² × T), pero la profundidad de reacción es tiempo real de ejecución
  en hardware: el circuito QF es 6.18× menos profundo.

## 10. Incidencias — la Kali reinició 2 veces durante el trabajo

- **Reinicio ~13:19:03 (3er reinicio del día):** mató el primer intento del
  Gold control (PID 340623, ~22 min, sin resultado) y al driver SomeJoint
  (PID 183966, seg37). Verificado tras el reinicio: `.kmb` QF intacto
  (sha `38b9cbf0…`), worktree intacto (64d4cec, 7 modificados + qf.py),
  repo principal intacto (d78e970, sucio, sin tocar), parche intacto
  (md5 `d2fdc869…`). El control se re-lanzó (PID 1261) y completó.
- **Reinicio ~14:36:05 (5º reinicio del día):** rompió el primer `scp` del
  `.kmb` a esta caja (71%, 444,426,240 B, "Broken pipe"). La copia se
  completó con `rsync --partial` (reanudó desde 444 MB): sha256 local
  `38b9cbf0…` — **idéntico al de la Kali y al control del Brujo**.
  (El exit 23 de rsync fueron solo errores `chown` EPERM en el receptor —
  cosmético; el contenido está completo y verificado por hash.)
- La carga de la Kali durante los Gold: 10–18 (los Gold tardaron 12–12.5 min
  en vez de ~6.5 min). Los Gold se corrieron con `nice -n 10` (CPU, sin GPU).

## 11. Veredicto: PASA

QF cumple el criterio: Q=1,857 (−7), T=710,312 (0), Gold PASS con seed fijo,
R idéntico a swap42 (1.2131052140444296), 5 errores de valor / 0 de fase
(igual que swap42), score exactamente el esperado
(2,971,470,537,625.3 = swap42 × (1857/1864)²). Mejora real del score:
0.7497% (ratio 8.22455, geomean medido 3.53171, Kaggle-escala 3.53906).
Hallazgo adicional: reaction_depth 19,501 → 3,154 (÷6.18).

**No tocado:** fuente DQI en la Kali fuera del worktree, candidato swap42
(ni su `.kmb` ni su ZIP), ZIP Adopted v3, entrenamiento SomeJoint en la Kali
(driver PID 183966 — ni mirado; murió por el reinicio, no por mí), docs de
diseño, árboles R1/R2/R5/P1/P2/P3, árbol de trabajo actual de la Kali
(local/final-submission-2026-11-13, sucio). **NO push a GitHub** — la rama
`local/claude-qf-minus7-2026-11-19` queda local en la Kali.

## 12. Evidencia (archivos citados)

En `~/workspace/qcc-data/test-dev/espiral-prototipo/claude-qf/` (esta caja):
- `dqi_qf.kmb` — 628,685,675 B, sha256
  `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13`
  (idéntico al de la Kali y al control del Brujo).
- `REPORTE_QF_2026-11-19.md` — este reporte.
- `build_qf.log` (858 B) — TOTAL QF Q=1857 T=710312 en 136 s.
- `verify_qf_gold.log` (1,415 B) — Gold QF PASS, exit_gold=0.
- `verify_qf_gold_control.log` (1,412 B) — Gold control PASS (reproduce el
  publicado exacto), exit_gold=0.
- `construir_dqi_qf.py` (2,746 B) — script de build (Kali).
- `run_verify_qf_gold.sh` (1,220 B) + `run_verify_qf_gold_control.sh` (934 B).

En la Kali: worktree `/home/deamon/quantum-circuit-compilation-qf` (rama
`local/claude-qf-minus7-2026-11-19`, HEAD 64d4cec, parche aplicado sin
commitear); `/home/deamon/workspace/qcc-data/claude-qf/` (`.kmb`, logs,
scripts); parche `/home/deamon/qf_main64d4cec_0_ehz1.patch` (md5 `d2fdc869…`).
Referencia swap42: `~/workspace/qcc-data/dqi-perfil/swap42/`
(`dqi_swap42.kmb` sha `746271d9…`, `verify_swap42_gold.log` PASS).
Control del Brujo: `~/workspace/qcc-data/claude-parche/dqi_qf.kmb`
(sha `38b9cbf0…`); revisión
`~/workspace/qcc-data/claude-parche/REVISION_BRUJO_PARCHE_CLAUDE_2026-11-19.md`.
