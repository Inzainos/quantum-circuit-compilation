# VERIFICACIÓN DEL BRUJO — Parche QF −7 qubits (Claude), build + Gold en la Kali

**Fecha:** 2026-11-19 ~14:47 CST
**Verificador:** El Brujo
**Cadena:** Programación (construye + Gold) → Brujo (verifica, este documento) → Datos → Auditor → Elán (decide).
**Veredicto: CONCURRO (PASA).**

---

## 1. Entregables verificados en disco (esta caja)

| Archivo | Medido por mí | Reportado por Programación |
|---|---|---|
| `REPORTE_QF_2026-11-19.md` | 257 l. / md5 `83d8791c…` | 257 l. |
| `dqi_qf.kmb` | 628,685,675 B / sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` | mismo sha, mismo tamaño |
| `build_qf.log` | 858 B | 858 B |
| `verify_qf_gold.log` | 1,415 B, PASS, exit_gold=0 | 1,415 B |
| `verify_qf_gold_control.log` | 1,412 B, PASS, exit_gold=0 | 1,412 B |
| `construir_dqi_qf.py` | 2,746 B | 2,746 B |
| `run_verify_qf_gold.sh` | 1,220 B | 1,220 B |
| `run_verify_qf_gold_control.sh` | 934 B | 934 B |

**El `.kmb` local es BYTE-IDÉNTICO a mi control independiente** (`~/workspace/qcc-data/claude-parche/dqi_qf.kmb`, mismo sha `38b9cbf0…`, mismo tamaño 628,685,675 B). El bug de mezcla D-QF-1 **NO** afectó el build de la Kali (verificado por identidad de hash, no por confianza en el script).

## 2. Gold control — swap42 con --seed explícito: REPRODUCE EXACTO

Leído por mí directamente de `verify_qf_gold_control.log` (13:49:44–14:02:13, exit_gold=0):

| Campo | Gold control (mismo seed) | Gold publicado swap42 |
|---|---|---|
| status | PASS | PASS |
| score | 2,993,914,799,696.024 | 2,993,914,799,696.024 |
| repetition_factor R | 1.2131052140444296 | 1.2131052140444296 |
| value_errors | 5 | 5 |
| phase_errors | 0 | 0 |
| mean_error_weight | 31.046737331746634 | 31.046737331746634 |
| reaction_depth | 19,501 | 19,501 |
| num_ops | 74,182,884 | 74,182,884 |
| num_qubits / T | 1,864 / 710,312 | 1,864 / 710,312 |
| circuit_sha256 | `746271d9…` | `746271d9…` |

**El seed queda validado empíricamente.** La comparación con seed fijo es manzana con manzana.

## 3. Gold QF — PASS con el mismo seed

Leído por mí directamente de `verify_qf_gold.log` (14:06:51–14:19:01, exit_gold=0):

| Campo | swap42 (control) | QF | Delta |
|---|---|---|---|
| status | PASS | PASS | — |
| score | 2,993,914,799,696.024 | **2,971,470,537,625.3** | −0.7497% |
| repetition_factor R | 1.2131052140444296 | **1.2131052140444296** | 0 (idéntico) |
| value_errors | 5 | 5 | 0 |
| phase_errors | 0 | 0 | 0 |
| mean_error_weight | 31.046737331746634 | 31.046737331746634 | 0 |
| toffoli_count | 710,312 | 710,312 | 0 |
| num_qubits | 1,864 | **1,857** | −7 |
| num_bits | 198,813 | 198,813 | 0 |
| num_ops | 74,182,884 | **72,168,849** | −2,014,035 |
| reaction_depth | 19,501 | **3,154** | −16,347 (÷6.18) |

## 4. Aritmética verificada por cómputo propio (no estimada)

- Factor (1857/1864)² = **0.9925033731510986** (recalculado por mí, coincide).
- Score esperado = 2,993,914,799,696.024 × 0.9925033731510986 = **2,971,470,537,625.2993**; medido = 2,971,470,537,625.3; diff **0.0005** = redondeo float — **exacto**.
- Mejora real del score: **−0.7497%** (solo el factor Q²; R, errores y T idénticos).
- DQI ratio QF = 2.4439e13 / 2,971,470,537,625.3 = **8.22455** (recalculado, coincide).
- DQI ratio swap42 = **8.16289** (recalculado, coincide).

## 5. Precisión D-QF-2 (mía, IMPORTANTE — el geomean depende del invsqrt)

Programación reporta geomean medido QF **3.53171** y Kaggle-escala **3.53906**. Esos números son correctos **con logshift2 como invsqrt** (el invsqrt de Adopted v3, ratio 5.32499):

- (5.32499 × 8.22455 × 1.005827)^(1/3) = 3.53171 ✓
- 3.53171 × (3.53019/3.52286) = 3.53906 ✓

Pero la recomendación conjunta Datos + Auditor adopta **R1** como referencia de invsqrt (ratio 5.33517, score 389,261.01). Con R1, el geomean QF es:

- Geomean medido QF + R1 = (5.33517 × 8.22455 × 1.005827)^(1/3) = **3.53396**
- Geomean Kaggle-escala QF + R1 = 3.53396 × (3.53019/3.52286) = **3.54131**

La diferencia (0.064%) es exactamente la mejora R1 vs logshift2. **Los números DQI (score, ratio, R, errores) no cambian.** Al citar el geomean, decir con qué invsqrt va: 3.53171 (logshift2) o 3.53396 (R1).

## 6. HALLAZGO — reaction_depth 19,501 → 3,154 (÷6.18): VERIFICADO

Recalculado por mí de los dos JSON Gold leídos directamente (mismo seed, mismas 102,400 muestras):

- reaction_depth: 19,501 → 3,154; ratio **6.183×**, diff **16,347**. ✓
- R por tiro: 67,694,592,000 → 10,311,168,000; ratio **6.565×**. ✓
- HMR por tiro: 81,564,672,000 → 24,181,248,000; ratio **3.373×**. ✓
- CX: 6,569,789,235,200 → 6,535,702,323,200; diff **−34,086,912,000**. ✓
- CZ: 188,636,410,370 → 159,946,096,370; diff **−28,690,314,000**. ✓
- CCX: 68,784,128,000 → 68,784,128,000; **igual** (mismo T). ✓
- X, SWAP, CSWAP, INFO_TAG, POP/PUSH: iguales. ✓

El hallazgo es real y medido. No estaba en el reporte de Claude ni en mi revisión estática (no teníamos el Gold). El score no cambia por esto (score = R × Q² × T), pero la profundidad de reacción es tiempo real de ejecución en hardware: el circuito QF es 6.18× menos profundo. La interpretación de Programación (las formas en el sitio + Toffoli con fan-out eliminan las cadenas secuenciales de ancillas HMR/R que dominaban la profundidad) es consistente con los números medidos (R y HMR son los que colapsan; CCX no se mueve).

## 7. El parche y el build — verificado

- Parche original `qf_main64d4cec_0_ehz1.patch` (18,393 B, md5 `d2fdc869…`, 451 l., 8 archivos, 16 hunks); la reconstrucción del PDF NO se usó (correcto).
- Worktree `/home/deamon/quantum-circuit-compilation-qf`, rama `local/claude-qf-minus7-2026-11-19`, HEAD 64d4cec; 7 modificados + `src/qf.py` nuevo (57 l.); diff 76 inserciones / 117 eliminaciones; py_compile OK; qf importa con las 5 helpers.
- `build_qf.log`: los 4 módulos desde `/home/deamon/quantum-circuit-compilation-qf/src/`; live_frontera 1794/1794/1794/1794/1724 (idénticos a swap42); TOTAL QF Q=1857 T=710312 en 136 s.
- El árbol sucio principal (local/final-submission-2026-11-13 @ d78e970) NO se tocó (verificado intacto por Programación tras los reboots).
- **NO push a GitHub** (la rama queda local en la Kali). Correcto.

## 8. Precisión D-QF-3 (mía, menor — conteo de reinicios)

El reporte dice que el reinicio de las ~13:19 fue el 3º del día y el de las ~14:36 el 5º. Yo tenía registrados 3 antes de las 13:19 (~04:59, 08:29:31, ~13:19), así que hay un 4º reinicio entre las 13:41 y las 14:36 que yo no registré (probablemente el que mató el seg40 de SomeJoint — ver §9). La sustancia no cambia: los Golds completaron, el .kmb está intacto, el entrenamiento necesita relanzarse.

## 9. SomeJoint — PARADO por el reinicio (aviso de Programación, confirmado por mí)

El driver SomeJoint murió por el reinicio (el de las ~13:19 mató el PID 183966; yo lo relancé a las 13:23:18, PID 2200, y completó seg37 13:28:27, seg38, seg39 13:41:42; un reinicio posterior — el 4º o el de las ~14:36:05 — lo mató de nuevo en seg40). **Último checkpoint bueno: `somejoint_long_seg39.npz` (13:41:42).** El seg40 empezó (existe `somejoint_long_seg40.log` con seed=seg39) pero no hay `seg40.npz`. **El Brujo relanzó el entrenamiento** (mismo script, `bash` explícito, auto-resume desde seg39) — ver el reporte al Coordinador. No es una decisión nueva: es continuar el trabajo autorizado (GO Punto 2 §b Fase 3).

## 10. Veredicto: CONCURRO (PASA)

QF cumple el criterio de la recomendación conjunta: Q=1,857 (−7), T=710,312 (0), Gold PASS con seed fijo, R idéntico a swap42 (1.2131052140444296), 5 errores de valor / 0 de fase (igual que swap42), score exactamente el esperado (2,971,470,537,625.3 = swap42 × (1857/1864)²). Mejora real del score: 0.7497% (ratio 8.22455). Hallazgo adicional verificado: reaction_depth 19,501 → 3,154 (÷6.18).

**Pasa al Auditor (y a Datos) para su revisión. La adopción la decide Elán.**
