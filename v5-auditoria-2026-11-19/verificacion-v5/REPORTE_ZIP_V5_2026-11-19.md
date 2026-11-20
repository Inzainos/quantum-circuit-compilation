# REPORTE ZIP v5 — seg100@brot13 + R1+R5 + P1+P2+P3 sobre QF

**Fecha:** 2026-11-19 (empaquetado ~20:54 CST, verificación ~20:55–21:00 CST)
**Orden:** Elán (2026-11-19 ~20:51 CST, vía Coordinador): armar el ZIP v5 con el seg100@brot13.
**Nada a Kaggle sin GO nuevo de Elán** — la subida es decisión aparte.
**Constructor:** Subagente (Mole).
**Cadena:** Programación → Datos → Brujo → Auditor → Elán.

---

## 1. Qué es v5

El ZIP v5 reúne los tres mejores CONFIRMADOS de cada tarea, todos con cadena completa:

- **invsqrt:** R1+R5 (adoptado por Elán; byte-idéntico a R1, estructura de R5 con 5 fases).
- **DQI:** P1+P2+P3 sobre QF (byte-idéntico al QF .kmb, "es el DQI del v5").
- **dfthcsos:** seg100@brot13 (mejor confirmado, reemplaza a g2; el árbol de Givens sobre el
  seg100 se cerró con número el 2026-11-19 ~20:53: ningún candidato supera al seg100@brot13,
  brot=13 es el óptimo — el v5 usa el seg100@brot13 tal cual).

## 2. Insumos (solo lectura, verificados por hash COMPLETO antes de empaquetar)

| Componente | Fuente | Hash verificado |
|---|---|---|
| invsqrt R1+R5 | `~/workspace/qcc-data/test-dev/espiral-prototipo/r1r5/invsqrt_R1R5.kmb` (437,536 B) | sha256 `a30a12983f003d7eed60a3122aa870ad1299eabb7f7ad95b510271600a3584b1` |
| DQI P1+P2+P3-QF | `~/workspace/qcc-data/test-dev/espiral-prototipo/p1p2p3-qf/dqi_p1p2p3_qf.kmb` (628,685,675 B) | sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` |
| dfthcsos seg100@brot13 | `~/workspace/qcc-data/dfthcsos-refit/somejoint-final/verificacion_seg100_brot13/` (10 angle_k .kmx + submission.npz) | submission.npz md5 `60e77048be5707f0a0223703bfce118f`; angle_k sha256 (ver §4) |

Los tres hashes coinciden con los confirmados (R1R5, P1P2P3-QF, brot13). Ningún hash
falló; no hubo que detenerse.

## 3. El ZIP

**ZIP:** `/home/hatch/workspace/qcc-data/candidato-v5-2026-11-19/candidato-v5-2026-11-19.zip`
**Tamaño:** 60,104,444 B
**sha256:** `d1392960b0e64bf4a40ec1f2019cfd10bdc71118b801655cfb633f261ab6407a`
**Compresión:** ZIP_DEFLATED (método 8), igual que el v4.1.
**Estructura:** 13 archivos, mismos nombres y orden que el v4.1
(`candidato-qf-2026-11-19.zip`, 62,985,968 B, sha256
`1fa819e8562d600c57673d69db85b853c24b0f2161026728ce18475ab3d1d829`).
El v5 es más chico que el v4.1 porque los angle_k a brot=13 son más chicos
(543–858 KB vs 2.2–2.6 MB) y el submission.npz también (1,370,892 vs 4,537,436 B).

### Lista de archivos (13)

| Archivo | Tamaño (B) |
|---|---:|
| invsqrt.kmb | 437,536 |
| dqi.kmb | 628,685,675 |
| dfthcsos/angle_k_0.kmx | 543,773 |
| dfthcsos/angle_k_1.kmx | 632,456 |
| dfthcsos/angle_k_2.kmx | 691,502 |
| dfthcsos/angle_k_3.kmx | 696,929 |
| dfthcsos/angle_k_4.kmx | 845,995 |
| dfthcsos/angle_k_5.kmx | 848,111 |
| dfthcsos/angle_k_6.kmx | 852,303 |
| dfthcsos/angle_k_7.kmx | 858,870 |
| dfthcsos/angle_k_8.kmx | 854,930 |
| dfthcsos/angle_k_9.kmx | 841,195 |
| dfthcsos/submission.npz | 1,370,892 |
| **Total sin comprimir** | **638,160,167** |

## 4. Verificación del contenido del ZIP (hash por hash, desde dentro del ZIP)

Los 13 archivos se hashearon desde dentro del ZIP (`unzip -p | sha256sum/md5sum`)
y coinciden EXACTO con los insumos verificados en §2:

| Archivo en el ZIP | sha256 / md5 | Coincide |
|---|---|---|
| invsqrt.kmb | sha256 `a30a12983f003d7eed60a3122aa870ad1299eabb7f7ad95b510271600a3584b1` | SÍ |
| dqi.kmb | sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` | SÍ |
| dfthcsos/angle_k_0.kmx | sha256 `4eba84f5582807828dfc8bbd992258250b62b8600a4a07a319e00837ed506d93` | SÍ |
| dfthcsos/angle_k_1.kmx | sha256 `7521ae7111fc9943297d48ff151bf0a7efacef26d67c776f12c0b8b64b8b16ae` | SÍ |
| dfthcsos/angle_k_2.kmx | sha256 `6a425f22ec29cfedc41ce8d3318b0b8a4d3aa3da16488fc723598466266068a2` | SÍ |
| dfthcsos/angle_k_3.kmx | sha256 `5184dc4848da6c08a593db22e86ede1945896b5c44086fc93f833784b63a1ccd` | SÍ |
| dfthcsos/angle_k_4.kmx | sha256 `ff14f8c4bb1daa4552db85b8307e9c0da1e8e7617c6afd6efbbf14b9897456e3` | SÍ |
| dfthcsos/angle_k_5.kmx | sha256 `a0d84be00935a9c7fdaad3c514078de709432440e17308dc6d480c5814c79b28` | SÍ |
| dfthcsos/angle_k_6.kmx | sha256 `615e3885469081223911bc80bf065be157660b26f11eaa9a831e9c886c35f3cf` | SÍ |
| dfthcsos/angle_k_7.kmx | sha256 `53f83d51ec86ffc61d544cee9754a91e7d00fe80b1bf31a77dd0fffd54276f2e` | SÍ |
| dfthcsos/angle_k_8.kmx | sha256 `63f4b22c41f9fb12d4fdb5136fad459183af43ed3c3ba28aa27ed7a468bd404e` | SÍ |
| dfthcsos/angle_k_9.kmx | sha256 `3b12e3dfffa7f3d6c027e08e5ec758b2bc1d3debdbcb304f767597c2d5a44844` | SÍ |
| dfthcsos/submission.npz | md5 `60e77048be5707f0a0223703bfce118f` | SÍ |

## 5. Re-verificación oficial del ZIP completo (desde el ZIP extraído)

El ZIP se extrajo a `extraido/` (en este mismo directorio, NO en /tmp: tmpfs de
512 MB, el .kmb pesa 628 MB) y cada componente se verificó con su verificador
oficial sobre los archivos extraídos.

### 5.1 dfthcsos — ✅ PASA (verificador oficial Task 3, re-corrido sobre el ZIP)

- **Comando (exacto del brot13):** `cd starter-kit/starter_kit &&
  PYTHONPATH=~/workspace/qcc-data/kickmix:~/workspace/qcc-dqi/src python3.13
  verifier/verify.py FeMoCo76o113e <extraido>/dfthcsos/submission.npz <extraido>/dfthcsos`
- **Log:** `logs/verify_v5_dfthcsos.log` (exit 0, 29.6 s).
- **Resultado:** `{"status": "PASS", "score": 1257565658.5356445, ...}` — **idéntico al
  confirmado** (diff 0.0): error_2 0.018959195983612506 Ha (18.9592 mHa),
  error_1 0.0016462185558529722 Ha, Lambda 306.6282728147105, E_gap 3.947269608579518,
  λ_eff 49.041900324749406, T=32,174, Q=797, brot 13, 10 circuitos,
  reaction_depth 100, num_ops 637,391, verified_shots 78,080,
  submission_sha256 `f084ae5502529a2c34f55926d84ce899dd6d7ebe8433629b30f907ea889fb5fb`.
- **Incidencia (documentada):** el primer intento usó `verifiers/dfthcsos/verify.py`
  y falló con `{"status": "FAIL", "error": "tree_edges is required unless circuits
  is a directory with submission.npz"}` — es otra versión del verificador (md5
  `49e2743e…` vs `dd3bcb5d…` del starter-kit). Se usó el verificador del starter-kit,
  el mismo de la confirmación brot13, con el mismo comando. El log fallido quedó
  sobrescrito por el PASS (mismo archivo de log).

### 5.2 invsqrt — ✅ PASA (verificador oficial, 1 tiro/x, dominio completo, sobre el ZIP)

- **Comando (exacto del R1R5 §7.1):**
  `PYTHONPATH=~/workspace/qcc-data/kickmix:~/workspace/qcc-data python3.13 -m
  verifiers.invsqrt.verify_submission_invsqrt <extraido>/invsqrt.kmb
  --shots-per-x 1 --max-x 3133440 --batch-size 256`
- **Log:** `logs/verify_v5_invsqrt_1shot.log` (exit 0, 19.7 s).
- **Resultado:** `{"status": "PASS", "score": 389261.0125451585, ...}` — **idéntico al
  confirmado y al Gold** (diff 0.0): toffoli_equivalent 2800.4389391738023,
  toffoli_count 2,561, rotation_count 34, rotation_eps 5.276472679105155e-13,
  num_qubits 139, reaction_depth 1,101, num_ops 51,795, verified_shots 3,133,440,
  worst_error_over_tolerance 0.8375458188313827 @ x=718,814,
  circuit_sha256 `a30a12983f003d7eed60a3122aa870ad1299eabb7f7ad95b510271600a3584b1`.
- El local 1-shot predice el Gold exactamente (documentado en el reporte R1R5 §7.2:
  Gold 64 tiros/x, mismo score 389261.0125451585).

### 5.3 DQI — ✅ CONFIRMADO POR BYTE-IDENTIDAD + GOLD EN REGISTRO (re-corrida local NO viable)

**El score Gold del DQI del ZIP es 2,971,470,537,625.3 (PASS), confirmado por
byte-identidad con el archivo Gold-verificado. La re-corrida del Gold en esta
caja NO es posible (limitación del entorno, no del circuito) — detalle abajo.**

**Byte-identidad (tres vías independientes, todas `38b9cbf0…`):**

1. Desde dentro del ZIP: `unzip -p candidato-v5-2026-11-19.zip dqi.kmb | sha256sum`
   → `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13`.
2. Sobre el archivo extraído: `sha256sum extraido/dqi.kmb` → mismo hash.
3. Round-trip con kickmix: `Circuit.from_file(extraido/dqi.kmb)` → `to_file(path)`
   → sha256 del archivo re-escrito → mismo hash, mismo tamaño (628,685,675 B).
   Además `num_qubits` leído del circuito: 1,857.

**Gold en registro para esos bytes exactos** (`p1p2p3-qf/verify_p1p2p3_qf_gold.log`,
md5 `7f7e31e6…`; JSON idéntico en todos los campos al Gold QF):

```json
{"status": "PASS", "score": 2971470537625.3, "m": 4095, "n": 70, "degree": 12,
 "r": 2016, "verified_shots": 102400, "value_errors": 5, "phase_errors": 0,
 "empirical_error_rate": 4.8828125e-05, "effective_error_rate": 0.0010479495500463395,
 "log2_delta": -128.0, "repetition_factor": 1.2131052140444296,
 "mean_error_weight": 31.046737331746634, "toffoli_count": 710312.0,
 "reaction_depth": 3154, "num_ops": 72168849, "num_qubits": 1857, "num_bits": 198813,
 "circuit_sha256": "38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13"}
```

exit_gold=0. Seed fijo = seed del Gold de swap42
(`52642227205936912575373656611044064096114070193057152544535209180255000077827`).

**Por qué byte-identidad + Gold en registro ES la confirmación:** el Gold es
determinista dados los mismos bytes y el mismo seed fijo (mismo seed = mismas
muestras = mismos resultados; documentado en el reporte P1P2P3-QF §3 y en
`run_verify_p1p2p3_qf_gold.sh`). El `dqi.kmb` del ZIP es byte-idéntico al archivo
sobre el que corrió ese Gold, así que una re-corrida reproduciría el mismo JSON.
No se re-corrió el Gold en la Kali: reproduciría el JSON idéntico y la Kali está
con el beam GPU del Sabueso (CASMI). Mismo precedente que el v4.1: el ZIP se
verificó hash por hash y el Gold QF quedó en registro sin re-correrse para el ZIP.

**Intentos locales documentados (ambos fallan por el entorno, no por el circuito):**

1. Verificador oficial directo (`verifiers/dqi/verify_submission_dqi.py`,
   `--num-shots 2048 --batch-size 256 --max-workers 1 --seed <fijo>`):
   `{"status": "FAIL", "error": "Failed to write to file."}` en 1.7 s.
   Causa: `_circuit_sha256` llama `circuit.to_file(BytesIO)` y el kickmix.so de
   esta caja rechaza el BytesIO. Log: `logs/verify_v5_dqi_probe2048.log`.
2. Workaround (wrapper `run_verify_dqi_local.py`, en este directorio): reemplaza
   solo el sumidero de la serialización (BytesIO → archivo temporal en el
   workspace, nunca /tmp) sin tocar el verificador; el round-trip da el sha256
   correcto (`38b9cbf0…`). Con el wrapper, la corrida de 2048 tiros fue
   **matada por OOM (exit 137) a los 33.5 s**: la caja (6 GB compartidos, 1.5 CPU)
   no puede simular el circuito DQI completo (el proceso Gold en la Kali usó
   ~2.6 GiB RSS). La simulación DQI completa solo corre en la Kali.
   (`to_file` a `/tmp` también falla: tmpfs de 512 MB, el .kmb pesa 628 MB.)

## 6. Geomean esperado

| Componente | Score confirmado |
|---|---:|
| invsqrt R1+R5 | 389,261.0125451585 |
| DQI P1+P2+P3-QF (Gold) | 2,971,470,537,625.3 |
| dfthcsos seg100@brot13 | 1,257,565,658.5356445 |

- **Geomean medido por Datos / verificado por el Auditor: 4.88904**
  (+38.43% vs adoptado, +37.65% vs g2; factor dfthcsos 2.66833×).
- Referencia: v4.1 en Kaggle 3.54317 (medido 3.53171, escala Kaggle 3.53906).
  El v5 mejora sobre el v4.1 por el dfthcsos (lbfgs → seg100@brot13, −62.31%) y
  marginalmente por el invsqrt (logshift2 390,005.06 → R1+R5 389,261.01, −0.19%).
- El score real en Kaggle solo se conoce al subir (decisión aparte, con GO nuevo).

## 7. Restricciones cumplidas

- Insumos solo leídos, NO modificados: v4.1, adoptado, g2, seg100 original,
  `verificacion_seg100/`, `verificacion_seg100_brot13/`, R1R5, P1P2P3-QF.
- Nada a Kaggle, main, GitHub. No se marcó final selection (solo Elán).
- Solo CPU; GPU no tocada (es del Sabueso). No se usó /tmp para archivos grandes
  (todo en `~/workspace/`).
- `staging/` (copias de trabajo con nombres del ZIP) y `extraido/` (ZIP extraído
  para la re-verificación) quedan en este directorio como evidencia de auditoría;
  no forman parte del envío.

## 8. Entregables (todo en `~/workspace/qcc-data/candidato-v5-2026-11-19/`)

| Archivo | Contenido |
|---|---|
| `candidato-v5-2026-11-19.zip` | ZIP v5, 60,104,444 B, sha256 `d1392960b0e64bf4a40ec1f2019cfd10bdc71118b801655cfb633f261ab6407a` |
| `REPORTE_ZIP_V5_2026-11-19.md` | Este reporte |
| `logs/verify_v5_dfthcsos.log` | PASS dfthcsos desde el ZIP, score 1,257,565,658.5356445 |
| `logs/verify_v5_invsqrt_1shot.log` | PASS invsqrt desde el ZIP, score 389,261.0125451585 |
| `logs/verify_v5_dqi_probe2048.log` | Intento DQI directo (FAIL "Failed to write to file", entorno) |
| `run_verify_dqi_local.py` | Wrapper del verificador DQI (solo cambia el sumidero de `to_file`) |
| `staging/` | Copias de trabajo de los 13 archivos con nombres del ZIP |
| `extraido/` | ZIP extraído (re-verificación) |

## 9. Siguiente paso

Cadena: Datos supervisa → Brujo verifica → Auditor revisa → **Elán decide si se
sube a Kaggle** (GO nuevo, decisión aparte). Si Elán da el GO: subir con el script
`~/workspace/qcc-data/kaggle-subida/submit_competition.py` (mismo flujo que el v4.1),
descripción sugerida: "v5: P1P2P3-QF DQI (Q=1857, T=710312) + R1R5 invsqrt (Q=139)
+ seg100@brot13 dfthcsos; expected geomean 4.88904". NO marcar como final selection
(solo Elán lo marca).
