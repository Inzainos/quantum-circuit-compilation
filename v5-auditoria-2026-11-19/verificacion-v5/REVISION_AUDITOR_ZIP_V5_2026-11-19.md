# REVISIÓN DEL AUDITOR — ZIP v5 (candidato-v5-2026-11-19)

**Fecha:** 2026-11-19 ~21:15 CST
**Auditor:** Auditor Interno
**Documento revisado:** `~/workspace/qcc-data/candidato-v5-2026-11-19/REPORTE_ZIP_V5_2026-11-19.md` (227 l. / 13,217 B / md5 `760fcfef…`, verificado en disco por mí)
**Supervisión de Datos:** `SUPERVISION_DATOS_ZIP_V5_2026-11-19.md` (87 l. / md5 `a7b447b0…`, verificado en disco por mí)
**Verificación del Brujo:** `VERIFICACION_BRUJO_ZIP_V5_2026-11-19.md` (57 l. / md5 `0057d9d3…`, verificado en disco por mí)
**Orden:** Elán 2026-11-19 ~20:51 CST, vía Coordinador (armar el ZIP v5 con el seg100@brot13).
**Nada a Kaggle** — la subida espera GO nuevo de Elán.
**Cadena:** Programación (empaqueta y re-verifica) → Datos ✓ → Brujo ✓ → Auditor (este documento) → Elán (decide la subida).
**Veredicto: CONCURRO (PASA), con una corrección al geomean (A-V5-1) y dos precisiones (D-V5-1, D-V5-2).**

---

## 1. Archivos verificados en disco por mí (no por confianza en el reporte)

| Archivo | Medido por mí | Reportado | ¿Coincide? |
|---|---|---|---|
| `candidato-v5-2026-11-19.zip` | 60,104,444 B / sha256 `d1392960…` | 60,104,444 B / sha256 `d1392960…` | ✓ |
| `REPORTE_ZIP_V5_2026-11-19.md` | 227 l. / 13,217 B / md5 `760fcfef…` | 13,217 B / md5 `760fcfef…` | ✓ |
| `SUPERVISION_DATOS_ZIP_V5_2026-11-19.md` | 87 l. / md5 `a7b447b0…` | 87 l. / md5 `a7b447b0…` | ✓ |
| `VERIFICACION_BRUJO_ZIP_V5_2026-11-19.md` | 57 l. / md5 `0057d9d3…` | 57 l. / md5 `0057d9d3…` | ✓ |
| `logs/verify_v5_dfthcsos.log` | 1,600 B | 1,600 B | ✓ |
| `logs/verify_v5_invsqrt_1shot.log` | 495 B | 495 B | ✓ |
| `logs/verify_v5_dqi_probe2048.log` | **0 B** | — | ✓ (D-V5-1) |

## 2. El ZIP — 13 archivos, hashes exactos desde dentro del ZIP (verificado por mí por streaming)

`unzip -l`: 13 archivos, mismos nombres, orden y tamaños que el reporte §3 y que el v4.1; todos ZIP_DEFLATED (método 8); total sin comprimir **638,160,167 B** (verificado por la suma de los 13 tamaños) ✓.

Hashes medidos por mí desde dentro del ZIP (zipfile, sin extraer), todos exactos contra el reporte §4:

| Archivo en el ZIP | Hash medido por mí | Esperado | Estado |
|---|---|---|---|
| invsqrt.kmb (437,536 B) | sha256 `a30a12983f003d7eed60a3122aa870ad1299eabb7f7ad95b510271600a3584b1` | R1+R5 | ✓ |
| dqi.kmb (628,685,675 B) | sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` | P1+P2+P3-QF | ✓ |
| dfthcsos/angle_k_0.kmx (543,773 B) | sha256 `4eba84f5582807828dfc8bbd992258250b62b8600a4a07a319e00837ed506d93` | §4 | ✓ |
| dfthcsos/angle_k_1.kmx (632,456 B) | sha256 `7521ae7111fc9943297d48ff151bf0a7efacef26d67c776f12c0b8b64b8b16ae` | §4 | ✓ |
| dfthcsos/angle_k_2.kmx (691,502 B) | sha256 `6a425f22ec29cfedc41ce8d3318b0b8a4d3aa3da16488fc723598466266068a2` | §4 | ✓ |
| dfthcsos/angle_k_3.kmx (696,929 B) | sha256 `5184dc4848da6c08a593db22e86ede1945896b5c44086fc93f833784b63a1ccd` | §4 | ✓ |
| dfthcsos/angle_k_4.kmx (845,995 B) | sha256 `ff14f8c4bb1daa4552db85b8307e9c0da1e8e7617c6afd6efbbf14b9897456e3` | §4 | ✓ |
| dfthcsos/angle_k_5.kmx (848,111 B) | sha256 `a0d84be00935a9c7fdaad3c514078de709432440e17308dc6d480c5814c79b28` | §4 | ✓ |
| dfthcsos/angle_k_6.kmx (852,303 B) | sha256 `615e3885469081223911bc80bf065be157660b26f11eaa9a831e9c886c35f3cf` | §4 | ✓ |
| dfthcsos/angle_k_7.kmx (858,870 B) | sha256 `53f83d51ec86ffc61d544cee9754a91e7d00fe80b1bf31a77dd0fffd54276f2e` | §4 | ✓ |
| dfthcsos/angle_k_8.kmx (854,930 B) | sha256 `63f4b22c41f9fb12d4fdb5136fad459183af43ed3c3ba28aa27ed7a468bd404e` | §4 | ✓ |
| dfthcsos/angle_k_9.kmx (841,195 B) | sha256 `3b12e3dfffa7f3d6c027e08e5ec758b2bc1d3debdbcb304f767597c2d5a44844` | §4 | ✓ |
| dfthcsos/submission.npz (1,370,892 B) | md5 `60e77048be5707f0a0223703bfce118f` | seg100@brot13 | ✓ |

**Los 10 angle_k son byte-idénticos a la fuente:** hasheé los 10 `angle_k_*.kmx` de `verificacion_seg100_brot13/` y los 10 dan MATCH exacto con los del ZIP ✓.

## 3. Re-verificación oficial desde el ZIP extraído (logs leídos directos por mí)

### 3.1 dfthcsos — ✅ PASA

`logs/verify_v5_dfthcsos.log` (leído directo): `{"status": "PASS", "score": 1257565658.5356445, "system": "FeMoCo76o113e", "lambda_eff": 49.041900324749406, "toffoli_count": 32174.0, "num_qubits": 797, "brot": 13, "batch_size": 8, "num_circuits": 10, "reaction_depth": 100, "num_ops": 637391, "verified_shots": 78080, "submission_sha256": "f084ae5502529a2c34f55926d84ce899dd6d7ebe8433629b30f907ea889fb5fb"}`. Métricas y resources idénticos a la confirmación brot13 (error_2 0.018959195983612506 Ha, error_1 0.0016462185558529722 Ha, Lambda 306.6282728147105, E_gap 3.947269608579518, angles_qubits 125). **Diff 0.0 vs lo confirmado** ✓.

### 3.2 invsqrt — ✅ PASA

`logs/verify_v5_invsqrt_1shot.log` (leído directo): `{"status": "PASS", "score": 389261.0125451585, "toffoli_equivalent": 2800.4389391738023, "toffoli_count": 2561.0, "rotation_count": 34.0, "rotation_eps": 5.276472679105155e-13, "num_qubits": 139, "reaction_depth": 1101, "num_ops": 51795, "verified_shots": 3133440, "worst_error_over_tolerance": 0.8375458188313827, "worst_x": 718814, "circuit_sha256": "a30a12983f003d7eed60a3122aa870ad1299eabb7f7ad95b510271600a3584b1"}`. **Idéntico al Gold R1+R5 (diff 0.0)** ✓.

### 3.3 DQI — ✅ CONFIRMADO por byte-identidad + Gold en registro

**Byte-identidad (dos vías directas, verificadas por mí):**
1. Desde dentro del ZIP: `dqi.kmb` sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` ✓.
2. Sobre el extraído: `extraido/dqi.kmb` sha256 `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` ✓.

**Gold en registro para esos bytes exactos** (leído directo de `p1p2p3-qf/verify_p1p2p3_qf_gold.log`, md5 `7f7e31e68701aeed19c2f7e8820db66f`): `{"status": "PASS", "score": 2971470537625.3, "m": 4095, "n": 70, "degree": 12, "r": 2016, "verified_shots": 102400, "value_errors": 5, "phase_errors": 0, "repetition_factor": 1.2131052140444296, "toffoli_count": 710312.0, "reaction_depth": 3154, "num_ops": 72168849, "num_qubits": 1857, "num_bits": 198813, "circuit_sha256": "38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13"}`, exit_gold=0, seed fijo `52642227205936912575373656611044064096114070193057152544535209180255000077827`, ventana 17:43:40–18:18:39 CST 2026-11-19. **El circuit_sha256 del Gold es el mismo que el del ZIP** ✓. El Gold es determinista con mismos bytes + mismo seed, así que una re-corrida reproduciría el mismo JSON.

Además cargué el circuito extraído con kickmix (`Circuit.from_file`): **num_qubits 1,857** ✓ (el circuito carga y es el esperado).

**Re-corrida local NO viable (entorno, no el circuito):** no la re-corrí (esta caja no puede simular el DQI completo; la Kali está con el beam GPU del Sabueso). Los intentos locales están documentados en el reporte §5.3 (ver D-V5-1).

## 4. A-V5-1 — CORRECCIÓN AL GEOMEAN: concurro (4.89215, no 4.88904)

Recomputado por mí. **El error era mío también:** en mi revisión del seg100@brot13 usé el ratio invsqrt 5.32499, que corresponde al score logshift2 (390,005.06). Pero el ZIP v5 lleva R1+R5 (score 389,261.0125451585), cuyo ratio es 5.33517.

- logshift2: 2,076,774 / 390,005.06 = **5.32499245** (el 5.32499 que usé)
- R1+R5: 2,076,774 / 389,261.0125451585 = **5.33517083** (el correcto para el v5)
- Geomean con 5.32499 (stale) = **4.88903862** → 4.88904 (el que reporté)
- **Geomean con 5.33517 (correcto) = 4.89215242 → 4.89215** (el del Brujo: 4.89215189; la diferencia de 5e-07 es redondeo en los inputs, ambos redondean a 4.89215)
- Delta: **+0.0637%**

Consecuencias (recomputadas por mí):
- vs adoptado 3.53171 (logshift2-based): **+38.52%** (no +38.43%)
- vs g2 3.55185: **+37.74%** (no +37.65%)
- La coincidencia del Brujo se verifica: el adoptado R1+R5-based es (5.33517 × 8.22455 × 1.00583)^(1/3) = **3.53396**, y 4.89215/3.53396−1 = **+38.43%** — mi "+38.43% vs adoptado" coincide por casualidad con el adoptado R1+R5-based (los dos ratios stale se cancelan).
- Factor dfthcsos verificado: 3,355,599,588/1,257,565,658.5356445 = **2.66833×** ✓.

**El ZIP en sí está correcto** — los circuitos son los correctos; solo la cifra del geomean necesita actualizarse de 4.88904 a **4.89215**. Esto afecta al reporte §6 ("Geomean medido por Datos / verificado por el Auditor: 4.88904") y a la descripción sugerida para Kaggle en §9 ("expected geomean 4.88904" → **4.89215**).

## 5. Precisiones — concurro con las tres, verificadas por mí

- **D-V5-1 (log de la sonda DQI vacío) — CONCURRO.** `logs/verify_v5_dqi_probe2048.log` está **vacío (0 bytes)** — verificado por mí (`ls -la`: 0 B). Programación dice que ambos intentos de la sonda DQI están "en los logs", pero el archivo no tiene contenido — los intentos solo están documentados en el reporte §5.3, no en un log. No cambia el veredicto (la confirmación DQI descansa en byte-identidad + Gold en registro, §3.3), pero la evidencia de log de la sonda no existe. El reporte §8 también describe ese log como "Intento DQI directo (FAIL 'Failed to write to file', entorno)" — el contenido no está en el archivo.
- **D-V5-2 (el round-trip `to_file` NO reproduce los bytes) — CONCURRO, medido por mí.** El reporte §5.3 dice: "Round-trip con kickmix: `Circuit.from_file(extraido/dqi.kmb)` → `to_file(path)` → sha256 del archivo re-escrito → mismo hash, mismo tamaño (628,685,675 B)". **Medido por mí** (kickmix `~/workspace/qcc-data/kickmix/kickmix.so`, `~/workspace/py313/python/bin/python3.13`, en `~/workspace/roundtrip-tmp-auditor/`, ya eliminado): el archivo re-escrito mide **1,028,735,024 B** (no 628,685,675 B) y su sha256 es **`fcc04dee06e40910550d3a973220f12f41870cc1def0e3e5ebae794117ea3ab2`** (no `38b9cbf0…`) — idéntico a lo medido por Datos dos veces. **Mecanismo verificado por mí:** el re-escrito empieza con `APPEND_TO_REGISTER q0 r0` (TEXTO), mientras el .kmb original empieza con `d7 50 c7 d5 c3 29 d3 26…` (BINARIO). El round-trip cambia el formato, así que **no es una ruta válida de byte-identidad para archivos .kmb**. **No cambia el veredicto** (la byte-identidad se sostiene por las dos vías directas del §3.3, que son las que importan, y el Gold es para esos bytes exactos), pero la tercera ruta del §5.3 como está escrita es incorrecta y debe corregirse. El Brujo verificó la byte-identidad por las dos vías directas y tomó la tercera de Programación sin re-verificarla — por eso la detecta Datos aquí.
- **D-V5-3 (la incidencia del §5.1 no dejó log) — CONCURRO.** La incidencia (el primer intento dfthcsos con `verifiers/dfthcsos/verify.py` falló por ser otra versión, error de tree_edges) no dejó log — el reporte mismo dice que el log fallido quedó sobrescrito por el PASS en el mismo archivo. Verificado por mí: grep de "FAIL|tree_edges" en `logs/verify_v5_dfthcsos.log`: 0. La incidencia es reportada, no verificable en log. No cambia el veredicto (el log PASS es del verificador del starter-kit, el mismo de la confirmación brot13).

## 6. No tocado

Verificado por mí: **v4.1 intacto en ambas copias** (sha256 `1fa819e8562d600c57673d69db85b853c24b0f2161026728ce18475ab3d1d829` en `candidato-qf-2026-11-19/candidato-qf-2026-11-19.zip` y en `kaggle-subida/submission.zip`); nada a Kaggle/main/GitHub; solo CPU, GPU no tocada; `staging/` y `extraido/` quedan como evidencia de auditoría. Mi round-trip de verificación se hizo en `~/workspace/roundtrip-tmp-auditor/` (no en /tmp) y ya fue eliminado.

## 7. Veredicto: CONCURRO (PASA) — el ZIP v5 está armado correctamente y re-verificado

dfthcsos PASA, invsqrt PASA, DQI confirmado por byte-identidad + Gold en registro. **Geomean correcto: 4.89215** (no 4.88904 — corrección A-V5-1, que incluye un error mío en la revisión del seg100@brot13). Precisiones: D-V5-1, D-V5-2 y D-V5-3 (concurro, las tres verificadas). El ZIP en sí está correcto; solo las cifras (§6, §9) y una ruta de verificación (§5.3, round-trip) necesitan corrección documental.

**Cadena: Programación ✓ → Datos ✓ → Brujo ✓ → Auditor ✓ (este documento) → Elán decide la subida** (GO nuevo, decisión aparte). Nada a Kaggle sin GO nuevo de Elán.
