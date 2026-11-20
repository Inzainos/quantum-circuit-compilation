# VERIFICACIÓN DEL BRUJO — P3 (Fase 2, DQI): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~12:48 CST
**Reporte verificado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p3/REPORTE_P3_2026-11-19.md` (218 l. / md5 `1757c2ca…`)
**Constructor:** Programación (subagente constructor P3)
**Diseño:** `FASE2_DQI_2026-11-19.md` §1.3 y §P3
**Cadena:** Programación ✓ → **Brujo ✓ (este informe)** → Datos (supervisión) → Auditor → Elán
**Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.**

## Veredicto: CONCURRO (PASA)

P3 PASA. Omega emite sus 630 mul/pase como 90 bloques de 7 explícitos y el
circuito resultante es **byte-idéntico a swap42** (sha `746271d9…`), así que
el Gold de swap42 lo cubre. Impacto en score: 0, como estima el diseño.
**Fase 2 COMPLETA en sus 3 variantes** (P1, P2, P3 — las tres PASA, las
tres byte-idénticas a swap42).

## Verificado por cómputo propio

### 1. Circuito byte-idéntico a swap42 (la equivalencia central)
- `dqi_p3.kmb` sha256 calculado por mí: `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` (646,811,990 B).
- `dqi_p3_control.kmb` y `dqi_swap42.kmb`: mismo sha `746271d9…`.
- `cmp` confirma: P3 byte-idéntico a swap42 y al control.

### 2. Estadísticas cargadas por mí (los 3 .kmb)
- Q=1,864, num_bits=198,813, suma de operaciones=74,182,884, CCX=671,720,
  HMR=796,530 — **idénticos en los tres** (swap42, P3, P3-control).
- T=710,312: del log de build (`TOTAL P3 Q=1864 T=710312`) y del Gold
  (`toffoli_count: 710312.0`); la identidad de bytes lo hace redundante.
- Build control: Q=1,864, T=710,312 en 147 s, `live_frontera`
  1794/1794/1794/1794/1724 (idénticos a `build_swap42.log`).
  Build P3: Q=1,864, T=710,312 en 143 s, mismo `live_frontera`.

### 3. Gold de swap42 leído en directo — cubre a P3 por identidad de bytes
- `verify_swap42_gold.log`: PASS, score 2,993,914,799,696.024, m=4095,
  n=70, degree=12, r=2016, verified_shots 102,400, **5 value / 0 phase**,
  repetition_factor 1.2131052140444296, toffoli_count 710,312,
  reaction_depth 19,501, num_ops 74,182,884, num_qubits 1,864,
  num_bits 198,813, circuit_sha256 `746271d9…`, `exit_gold=0`.

### 4. Diff leído en full — solo `dqi_decoder_v1.py` difiere
- `diff -rq --exclude=__pycache__` p3/src vs dir swap42: **solo
  `dqi_decoder_v1.py` difiere** (md5 `5bf313db…`, 235 l.); el resto
  byte-idéntico. Script nuevo `construir_dqi_p3.py`.
- Mecanismo confirmado en el código: comentario P3 (113–120),
  `N_OMEGA_BLOCK = 7` (121), `_omega_mul_tasks(LO, adjoint)` (124–141:
  lista ordenada `('esc', i, None)` / `('acc', i, j)`; ida i=LO−1..0 con
  esc luego acc j=1..i; vuelta i=0..LO−1 con acc j=i..1 luego esc;
  total `LO*(LO+1)/2` = 630), `_omega_mul_blocks(LO, adjoint)` (143–150:
  90 bloques de 7 con aserciones de total y divisibilidad),
  `build_omega_tmp` reescrito (152–178): itera los bloques y ejecuta por
  tarea **las mismas operaciones que hoy, copiadas verbatim** (escalado con
  ValueInv + P + `ixor_kmul` + `del_gf2_mul` + swap + free + undo;
  acumulado `ixor_kmul(b, sig[j], S[i-j], S[i])`).
- El orden está forzado por dependencias: el escalado de i antes de sus
  acumulados; i descendente en ida, ascendente en vuelta; solo el orden j
  dentro de los acumulados de un mismo i es libre (XOR conmuta). Los
  bloques son trozos consecutivos de la secuencia, no un reordenamiento —
  verificado por el test re-corrido (§5).

### 5. Test `test_omega_p3.py` re-corrido por mí — OMEGA_P3_OK
- [fwd] y [rev]: tareas=630 (esc=35, acc=595); bloques=90, tamaños=[7];
  **orden == loop original: True** (ambas direcciones);
  **aplanar bloques == tareas: True**; mismo multiconjunto de tareas por
  i (ida vs vuelta): True. ESTRUCTURA_OK.
- Aislado fwd: muls=630, T=29,085 (= 630×42 + 35×75), Q=1,317.
  Aislado rev: igual. Aislado ida+vuelta: muls 630+630, T=58,170, Q=1,317.
  `init_and` mul/pase: 630 × 42 = 26,460 T (ida); ida+vuelta 52,920 T.
  MEDICION_OK. **OMEGA_P3_OK** (reproducido exacto por mí).

### 6. Profundidad aislada re-corrida por mí — DEPTH_OK
- `stats_omega_depth.py` re-corrido: fwd 216, rev 181, **ida+vuelta 391**.
  **No aditiva: 216+181 = 397 ≠ 391** (el camino más largo del combinado
  no es la concatenación de los dos más largos). Frente al total DQI
  19,501 (Gold), Omega aporta 391 (~2.0%): **Omega NO es el cuello de
  profundidad; BM/scan dominan.** La diferencia fwd/rev (216 vs 181)
  viene de la posición del escalado (primero por i en ida, al final en
  vuelta).

### 7. Hallazgo de lectura verificado (dónde vive Omega en producción)
- `from dqi_omega_stage import build_omega` en `dqi_decoder_v1.py:28`
  (dir swap42); `build_omega` **nunca se llama** en ese archivo (grep:
  solo la línea 28 y la mención en el docstring de `build_omega_tmp`).
- `build_decoder` llama `build_omega_tmp` en las líneas 144 (ida) y 146
  (vuelta). `dqi_omega_stage.py` existe (`~/workspace/qcc-dqi/src/`,
  3,365 B; `def build_omega` en la línea 31) y define `build_omega` con
  `delta` persistente — pero **es un import muerto para este build**.
- P3 se construyó sobre `build_omega_tmp`, que es lo que emite el
  candidato swap42. **Concurro con el hallazgo.**

### 8. Aritmética verificada (cómputo propio)
- sum_{i=0}^{34} i = 595; 630 = 35 + 595 ✓
- 630 × 42 = 26,460 T/pase; 35 × 75 = 2,625 (ValueInv/pase);
  26,460 + 2,625 = 29,085 ✓; 2 × 29,085 = 58,170 ✓;
  2 × 26,460 = 52,920 ✓; 2 × 2,625 = 5,250 ✓; 90 × 7 = 630 ✓
- 216 + 181 = 397 ≠ 391 ✓ (no aditivo, §6)

### 9. Precisión del diseño (§P3) — concurro
- "Cada grupo de 7 mul → una matriz 6×7" es ambiguo: **cada mul YA ES una
  matriz 6×7 (P1)** — 6 ANDs Karatsuba × 7 puntos de evaluación dentro de
  un producto GF(8). Un bloque de 7 muls son 7 matrices 6×7 (294 ANDs),
  no una matriz. Lo que P3 expone es la agrupación de la **secuencia de
  emisión** en 90 bloques de 7. La aritmética y el orden no cambian.

### 10. Ganancia secundaria de localidad: NO materializada — concurro
- Con la secuencia de puertas idéntica, el patrón alloc/free es idéntico
  (el `.kmb` byte-idéntico lo prueba: mismos `live_frontera`, mismo Q
  aislado 1,317, misma T). Los transitorios `tx,ty,t` viven dentro de cada
  llamada a `ixor_kmul42` (se allocan y liberan por mul); agrupar los muls
  no cambia su ciclo de vida porque el orden no cambia. La localidad solo
  cambiaría si se reordenaran los muls, y el orden está forzado por
  dependencias (§2). P3 es organizacional puro, 0 T, 0 Q.

## Precisiones propias
- **D-P3-1 (cita del §6 — correcta):** el reporte cita la precisión D-P1-1
  para los valores 8.16189x / 3.52162x del §6 — es correcto: son los
  impresos del script de build (ancla desactualizada 7.48129 y 5.32
  redondeado); los verdaderos son ratio **8.16289** / geomean **3.52286**
  (Gold, verificados por mí en P1). El "(idénticos a swap42)" es cierto
  para los valores impresos (el log de build de swap42 imprime los mismos).
- **D-P3-2 (menor, presentación de stats):** en esta versión de kickmix,
  `operation_statistics()` devuelve conteos por tipo de puerta (CCX, CX,
  HMR…), no las claves resumen (`num_instructions`, `num_toffoli_like`)
  que muestra `stats_kmb_p3.log` — esas claves son derivadas (la suma de
  los conteos por puerta = 74,182,884, verificada por mí en los tres
  `.kmb`). Los números coinciden; es solo cómo se presentan.
- **D-P3-3 (el bug del test era del test, no de P3):** concurro con el §4 —
  la primera versión de `test_omega_p3.py` no reseteaba el contador de
  muls antes del build ida+vuelta (MEDICION_FAIL con todos los números
  correctos); el contador se reseteó y el test re-corrido por mí da
  OMEGA_P3_OK limpio.

## Tabla Fase 2 (verificada)
| Variante | Q | T | sha256 | Score |
|---|---|---|---|---|
| swap42 (referencia) | 1,864 | 710,312 | 746271d9… | 2,993,914,799,696.024 |
| **P1** (matriz 6×7 explícita) | 1,864 | 710,312 | 746271d9… | = swap42 |
| **P2** (bloque 6×1 de escalera) | 1,864 | 710,312 | 746271d9… | = swap42 |
| **P3** (90 bloques de 7 en Omega) | 1,864 | 710,312 | 746271d9… | = swap42 |

**Fase 2 COMPLETA en sus 3 variantes** (las tres PASA, las tres
byte-idénticas a swap42, impacto en score 0 en las tres). Queda P5
(interfaz de paridad, anotado en el diseño, fuera del orden de
construcción) y la combinación P1+P2+P3 sin construir (decisión posterior
de Elán).

## Criterio FASE 2 §P3 — CUMPLIDO
Omega emite sus 630 mul/pase como 90 bloques de 7 explícitos, con 26,460 T
de mul por pase (52,920 ida+vuelta), Q aislado 1,317 ≤ 1,864,
`reaction_depth` aislado 391 (fwd 216, rev 181), y el circuito es
byte-idéntico a swap42.

**P3 PASA. Siguiente: Datos → Auditor → Elán.**
