# REVISIÓN DEL AUDITOR — P3 (PROTOTIPO ESPIRAL, FASE 2, DQI)

**Fecha:** 2026-11-19 ~13:10–13:25 CST
**Orden:** Elán (2026-11-19 ~11:17, vía Coordinador) — prototipo del motor de la espiral; el Brujo coordina.
**Constructor:** Programación (subagente constructor P3).
**Diseño:** `~/workspace/qcc-data/dfthcsos-refit/espiral-rediseno/FASE2_DQI_2026-11-19.md` §1.3 y §P3.
**Reporte revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p3/REPORTE_P3_2026-11-19.md` — **218 l. / md5 `1757c2cab60e5e5ec36ecaade2bc63ed`**.
**Supervisión revisada:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p3/SUPERVISION_DATOS_P3_2026-11-19.md` — **283 l. / md5 `350650e8…`, CONCURRO (PASA)**.
**Verificación revisada:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p3/VERIFICACION_BRUJO_P3_2026-11-19.md` — **153 l. / md5 `26176b943c5214b81c384409e912423b`, CONCURRO (PASA)**.
**Cadena:** Programación (construye) → Brujo (verifica, 12:48) → Datos (supervisa, 12:59) → **Auditor (esta revisión)** → Elán (decide). Nota: en P3 el Brujo verificó antes de que Datos supervisara (ver A-P3-1); ambos concurrieron PASA, así que la cadena está completa en cualquier orden.
**Regla 0:** cada número aquí viene de un log leído o de un cómputo propio en python; lo estimado se marca [ESTIMADO]. Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.

## Veredicto: CONCURRO (PASA)

P3 PASA. Omega emite sus 630 mul/pase como 90 bloques de 7 explícitos (`N_OMEGA_BLOCK = 7`, `_omega_mul_tasks` + `_omega_mul_blocks`, `build_omega_tmp` reescrito para iterar los bloques con las mismas operaciones verbatim), con **26,460 T de mul por pase (52,920 ida+vuelta)**, **Q aislado 1,317 ≤ 1,864**, **`reaction_depth` aislado 391 (fwd 216, rev 181)**, y el circuito resultante es **byte-idéntico a swap42** (sha `746271d9…`, `cmp` confirma). El Gold de swap42 lo cubre por identidad de bytes (PASS, 102,400 tiros, 5 errores de valor / 0 de fase). Impacto en score: 0, como estima el diseño. La ganancia secundaria de localidad no se materializa (medido — el orden está forzado por dependencias).

## 1. Circuito byte-idéntico a swap42 — VERIFICADO (la equivalencia central)

Medidos por mí (sha256):
- `dqi_p3.kmb`: **646,811,990 B**, sha256 `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` ✓.
- `dqi_p3_control.kmb`: **646,811,990 B**, mismo sha `746271d9…` ✓.
- `dqi_swap42.kmb` (referencia): **646,811,990 B**, mismo sha `746271d9…` ✓.
- **`cmp` confirma: P3 byte-idéntico a swap42 y al control** ✓ (corrido por mí). La ruta de build es reproducible en esta caja (control Q=1,864 T=710,312 en 147 s, mismo `live_frontera`).

## 2. Estadísticas — VERIFICADAS (carga directa mía de los 3 .kmb)

Cargados por mí con `km.Circuit.from_file`:

| Variante | Q | num_bits | num_instructions (suma) | CCX | HMR |
|---|---|---|---|---|---|
| swap42 | 1,864 | 198,813 | 74,182,884 | 671,720 | 796,530 |
| P3 | 1,864 | 198,813 | 74,182,884 | 671,720 | 796,530 |
| P3 control | 1,864 | 198,813 | 74,182,884 | 671,720 | 796,530 |

**Idénticos en las tres** ✓. T=710,312 viene de los logs de build y del Gold (la identidad de bytes lo hace redundante). Conteos por puerta del circuito (swap42, verificados por mí en los tres .kmb): NEG 140, BIT_INVERT 21,840, BIT_STORE0 21,839, BIT_STORE1 22,400, X 111,166, Z 27,090, R 661,080, HMR 796,530, CX 64,158,098, CZ 3,684,341, SWAP 3,780, CSWAP 38,592, CCX 671,720, INFO_TAG 14,914, POP_CONDITION 1,974,677, PUSH_CONDITION 1,974,677 — suma 74,182,884 ✓ (ver D-P3-2 y A-P3-2).

## 3. Prueba aislada — RE-CORRIDA POR MÍ (OMEGA_P3_OK)

`test_omega_p3.py`, salida medida por mí en este turno, idéntica a la del reporte (§3, §11), a la del Brujo (§5) y a la de Datos (§1.3):

```
[fwd] tareas=630 (esc=35 acc=595); bloques=90 tamanos=[7]
[fwd] orden == loop original: True
[fwd] aplanar bloques == tareas: True
[rev] tareas=630 (esc=35 acc=595); bloques=90 tamanos=[7]
[rev] orden == loop original: True
[rev] aplanar bloques == tareas: True
[ambos] mismo multiconjunto de tareas por i (ida vs vuelta): True
ESTRUCTURA_OK
[aislado fwd] muls=630; T=29085 (= 630*42 + 35*75); Q=1317
[aislado rev] muls=630; T=29085; Q=1317
[aislado ida+vuelta] muls fwd=630 rev=630; T=58170; Q=1317
init_and mul/pase: 630 x 42 = 26460 T (ida); ida+vuelta 52920 T
MEDICION_OK
OMEGA_P3_OK
```

## 4. Profundidad aislada — RE-CORRIDA POR MÍ (DEPTH_OK)

`stats_omega_depth.py`, salida medida por mí en este turno, idéntica a la del reporte (§8.3), a la del Brujo (§6) y a la de Datos (§1.4):

```
reaction_depth Omega aislado (fwd) = 216
reaction_depth Omega aislado (rev) = 181
reaction_depth Omega aislado (ida+vuelta) = 391
DEPTH_OK
```

**No aditiva: 216+181 = 397 ≠ 391** (el camino más largo del combinado no es la concatenación de los dos más largos) ✓. Frente al total DQI 19,501 (Gold), Omega aporta 391 (~2.0%): **Omega NO es el cuello de profundidad del DQI; BM/scan dominan** ✓. La diferencia fwd/rev (216 vs 181) viene de la posición del escalado (primero por i en ida, al final en vuelta). Nota: el `reaction_depth()` del DQI completo (74M ops) mata el proceso en esta caja (medido en P1); sobre el Omega aislado (~58k T) sí se pudo calcular — por eso esta confirmación es un número medido y no una inferencia.

## 5. Aritmética — VERIFICADA (cómputo propio)

- sum_{i=0}^{34} i = **595**; 35 + 595 = **630** muls/pase ✓
- 630 × 42 = **26,460** T de mul/pase; 35 × 75 = **2,625** (ValueInv/pase); 26,460 + 2,625 = **29,085** T/pase ✓; 2 × 29,085 = **58,170** ida+vuelta ✓
- 2 × 26,460 = **52,920** T de mul ida+vuelta; 2 × 2,625 = **5,250** ✓
- 90 × 7 = **630** ✓; 216 + 181 = 397 ≠ 391 ✓ (no aditivo); 391 / 19,501 = 2.005% ✓
- LO×(LO+1)/2 para LO=35 = 630 ✓
- El T de Omega ida+vuelta (58,170) cuadra con el desglose del diseño (52,920 mul + 5,250 ValueInv) y con el perfil espiral (omega_fwd 29,085 — medido en la vuelta 2 DQI, 2026-11-14) ✓

## 6. Diff — VERIFICADO (solo `dqi_decoder_v1.py` difiere)

`diff -rq --exclude=__pycache__` entre `p3/src/` y el dir swap42: entre los `.py` compartidos **solo `dqi_decoder_v1.py` difiere** (p3 md5 `5bf313db97d53adef8c13e6bdd497bad`, 235 l.; swap42 md5 `0ce12bb4d3c30aa158d3e3a846825227`) ✓. `construir_dqi_p3.py` es nuevo (md5 `584a1d7afb96b9eda35884cb594262f6`, coincide con Datos §1.6); el resto de `.py` son byte-idénticos (los "Only in" restantes son docs/logs/`.kmb`/scripts, no fuentes). El diff muestra exactamente: comentario P3 (líneas 113–120), `N_OMEGA_BLOCK = 7` (línea 121), `_omega_mul_tasks(LO, adjoint)` (124–141: lista ordenada `('esc', i, None)` / `('acc', i, j)`; ida i=LO−1..0 con esc luego acc j=1..i; vuelta i=0..LO−1 con acc j=i..1 luego esc; total `LO*(LO+1)/2` = 630), `_omega_mul_blocks(LO, adjoint)` (143–150: 90 bloques de 7 con aserciones de total y divisibilidad), `build_omega_tmp` reescrito (152–178): itera los bloques y ejecuta por tarea **las mismas operaciones que hoy, copiadas verbatim** (escalado con ValueInv + P + `ixor_kmul` + `del_gf2_mul` + swap + free + undo; acumulado `ixor_kmul`) ✓.

El orden está forzado por dependencias: el escalado de i antes de sus acumulados; i descendente en ida, ascendente en vuelta; solo el orden j dentro de los acumulados de un mismo i es libre (XOR conmuta). Los bloques son trozos consecutivos de la secuencia, no un reordenamiento — verificado por el test re-corrido (§3) ✓.

## 7. Hallazgo de lectura — VERIFICADO (dónde vive Omega en producción)

- `from dqi_omega_stage import build_omega` en `dqi_decoder_v1.py:28` (dir swap42 y copia P3, misma línea); `build_omega` **nunca se llama** en ese archivo (grep por mí: solo la línea 28 y la mención en el docstring de `build_omega_tmp`) ✓.
- `build_decoder` llama `build_omega_tmp` en las líneas **144 (ida) y 146 (vuelta) del original swap42** — en el archivo P3 (40 líneas insertadas por el comentario y las dos funciones nuevas) son **184 y 186** (ver D-P3-4) ✓.
- `dqi_omega_stage.py` existe (`~/workspace/qcc-dqi/src/`, 3,365 B; `def build_omega` en la línea 31) y define `build_omega` con `delta` persistente — pero **es un import muerto para este build** ✓.
- P3 se construyó sobre `build_omega_tmp`, que es lo que emite el candidato swap42. **Concurro con el hallazgo** ✓.

## 8. Gold: PASS por identidad de bytes con swap42 (no se re-corrió)

`verify_swap42_gold.log` (md5 `38d9f639d158b3b8044ac05ad3b5efb8`, sin cambios desde el 14 nov — verificado por mí en P1 y P2): status PASS, score 2,993,914,799,696.024, verified_shots 102,400, value_errors 5, phase_errors 0, repetition_factor 1.2131052140444296, toffoli_count 710,312, reaction_depth 19,501, num_ops 74,182,884, num_qubits 1,864, num_bits 198,813, circuit_sha256 `746271d9…`, exit_gold=0. Score recomputado exacto en P1: R×Q²×T = 1.2131052140444296 × 1,864² × 710,312 = 2,993,914,799,696.024. El `.kmb` P3 tiene el mismo sha256 → mismo circuito → el Gold de swap42 lo cubre. No se re-corrió el Gold del DQI.

## 9. Build logs — LEÍDOS EN DIRECTO

- `build_control.log` (1,071 B): `TOTAL P3 Q=1864 T=710312 en 147s`, `live_frontera` 1794/1794/1794/1794/1724, sha `746271d9…` ✓.
- `build_p3.log` (1,063 B): `TOTAL P3 Q=1864 T=710312 en 143s`, mismo `live_frontera`, sha `746271d9…` ✓.
- Ambos imprimen ratio DQI 8.16189x / geomean 3.52162x / escalado Kaggle 3.53019x — valores del script, ver D-P3-1 ✓.

## 10. Precisiones

**D-P3-1 (del Brujo, CONCURRO — verificada en P1):** el reporte cita la precisión D-P1-1 para los valores 8.16189x / 3.52162x del §6 — es correcto: son los impresos del script de build (ancla desactualizada 7.48129 y 5.32 redondeado); los verdaderos son ratio **8.16289** / geomean **3.52286** (Gold, verificados exactos por mí en P1: ratio DQI 8.162890942147493, geomean 3.522859936910316). El "(idénticos a swap42)" es cierto para los valores impresos (el log de build de swap42 imprime los mismos, verificado por grep en P1).

**D-P3-2 (del Brujo, CONCURRO — verificada por mí):** en esta versión de kickmix, `operation_statistics()` devuelve conteos por tipo de puerta (16 claves: NEG, BIT_INVERT, BIT_STORE0, BIT_STORE1, X, Z, R, HMR, CX, CZ, SWAP, CSWAP, CCX, INFO_TAG, POP_CONDITION, PUSH_CONDITION), no las claves resumen (`num_instructions`, `num_toffoli_like`) que muestra `stats_kmb_p3.log` — esas claves son derivadas (la suma de los conteos por puerta = 74,182,884, verificada por mí en los tres `.kmb`; CCX=671,720, HMR=796,530). Los números coinciden; es solo cómo se presentan. (Ver A-P3-2: los conteos por puerta viven en la interfaz dict del objeto, no como atributos.)

**D-P3-3 (del Brujo, CONCURRO — verificada por mí):** el bug del test era del test, no de P3. La primera versión de `test_omega_p3.py` no reseteaba el contador de muls antes del build ida+vuelta (MEDICION_FAIL con todos los números correctos, conteo acumulado 1,260); el contador se reseteó y el test re-corrido por mí da `OMEGA_P3_OK` limpio (§3).

**D-P3-4 (de Datos, CONCURRO — verificada por mí):** las líneas 144/146 que cita el Brujo (§7) son del archivo ORIGINAL; en el archivo P3 las llamadas a `build_omega_tmp` están en **184/186** (verificado por mí con grep: original 144/146, P3 184/186; la sustancia no cambia — `build_decoder` llama a `build_omega_tmp` ida y vuelta en ambos). Solo la cita de líneas cambia por el desplazamiento de 40 líneas insertadas.

**D-P3-5 (de Datos, CONCURRO — verificada por mí):** el encabezado del reporte dice "construcción ~18:35–18:45 CST". Las mtimes son `dqi_p3_control.kmb` 18:40:17 UTC, `dqi_p3.kmb` 18:44:21 UTC, `build_p3.log` 18:44:23 UTC, reporte 18:45:47 UTC → **ventana real ~12:40–12:45 CST**. Misma trampa de etiqueta que D-P1-4 en P1 y D-P2-2 en P2 (UTC etiquetado como CST, 6 h de diferencia). No cambia ningún número; solo la etiqueta de hora del encabezado.

**Precisión del diseño (§P3, §10 del reporte) — CONCURRO:** "Cada grupo de 7 mul → una matriz 6×7" es ambiguo: **cada mul YA ES una matriz 6×7 (P1)** — 6 ANDs Karatsuba × 7 puntos de evaluación dentro de un producto GF(8). Un bloque de 7 muls son 7 matrices 6×7 (294 ANDs), no una matriz. Lo que P3 expone es la agrupación de la **secuencia de emisión** en 90 bloques de 7. La aritmética y el orden no cambian.

**Ganancia secundaria de localidad (§9 del reporte) — CONCURRO, NO materializada:** con la secuencia de puertas idéntica, el patrón alloc/free es idéntico (el `.kmb` byte-idéntico lo prueba: mismos `live_frontera`, mismo Q aislado 1,317, misma T). Los transitorios `tx,ty,t` viven dentro de cada llamada a `ixor_kmul42` (se allocan y liberan por mul); agrupar los muls no cambia su ciclo de vida porque el orden no cambia. La localidad solo cambiaría si se reordenaran los muls, y el orden está forzado por dependencias (§2 del reporte). P3 es organizacional puro, 0 T, 0 Q.

## 11. Precisiones propias (A-P3-1 a A-P3-3, menores)

- **A-P3-1 (menor — el orden de la cadena en P3):** en P3 el Brujo verificó antes de que Datos supervisara (el informe del Brujo dice "Datos (supervisión)" y la supervisión de Datos dice "Brujo ✓"; fechas 12:48 vs 12:59). El orden usual es Programación → Datos → Brujo → Auditor; aquí fue Programación → Brujo → Datos → Auditor — igual que en P1 (A-P1-2) y P2 (A-P2-1). Ambos concurrieron PASA, así que la cadena está completa en cualquier orden — lo dejo registrado para que el tablero no se confunda.
- **A-P3-2 (menor — dónde viven los conteos por puerta):** mi primera enumeración de `operation_statistics()` vía `dir()` + `getattr` solo mostró los atributos resumen (`num_instructions`, `num_toffoli_like`, `num_t_like`, `num_z_pow`, `z_pow_clifford_hierarchy_counts`) — los 16 conteos por puerta viven en la interfaz dict del objeto (`st.keys()`, `st.items()`, `st['CCX']`), no como atributos. Por eso D-P3-2 importa: `stats_kmb_p3.log` muestra los atributos resumen, mientras CCX=671,720 y HMR=796,530 vienen de la interfaz dict. Verifiqué ambas interfaces yo mismo; los números coinciden en las tres variantes.
- **A-P3-3 (menor — el NEG del Gold no casa con el estático, y no es un problema):** los valores por tiro del Gold (`shot_operation_counts` / 102,400) casan exactos con los conteos estáticos para CCX (671,720) y HMR (796,530), pero el NEG del Gold (7,168,868 / 102,400 = 70.008 por tiro) NO casa con el NEG estático (140) — porque el NEG es dependiente de los datos en el verificador (ramificación por medición). No es una discrepancia de P3: la identidad del circuito descansa en los conteos estáticos y en el sha, ambos verificados.

## 12. Criterio FASE 2 §P3 — CUMPLIDO

- Omega emite sus 630 mul/pase como 90 bloques de 7 explícitos: ✓ (630 tareas, 90×7, orden == loop original en ambas direcciones).
- 26,460 T de mul por pase (52,920 ida+vuelta): ✓ (medido dinámico).
- Q aislado 1,317 ≤ 1,864: ✓ (Omega no marca el pico del DQI).
- `reaction_depth` aislado 391 (fwd 216, rev 181): ✓ (Omega NO es el cuello de profundidad; BM/scan dominan).
- Circuito byte-idéntico a swap42: ✓ (sha256 + `cmp`).
- Gold: ✓ por identidad de bytes (PASS, 102,400 tiros, 5 valor / 0 fase).
- Import muerto `build_omega` confirmado: ✓ (P3 se construyó sobre `build_omega_tmp`, lo que emite swap42).

## 13. Veredicto y cadena

**CONCURRO (PASA)** — P3 pasa: 90 bloques de 7 verificados en módulo y test, 26,460 T de mul por pase, Q aislado 1,317, profundidad aislada 391 (Omega no es el cuello), circuito byte-idéntico a swap42 con Gold PASS por identidad. Precisiones: D-P3-1 (cita a D-P1-1 correcta — concurro), D-P3-2 (conteos por puerta vs claves resumen — concurro, verificada), D-P3-3 (el bug del test era del test — concurro), D-P3-4 (líneas 144/146 son del original, en P3 son 184/186 — concurro), D-P3-5 (ventana UTC etiquetada como CST — concurro) y A-P3-1, A-P3-2, A-P3-3 (mías). Ninguna cambia el veredicto.

**Cadena COMPLETA (P3):** Programación ✓ → Brujo ✓ → Datos ✓ → Auditor ✓ (esta revisión: CONCURRO, PASA) → **Elán** (decide).

**Fase 2 COMPLETA en sus 3 variantes construidas** (P1 matriz 6×7 explícita, P2 bloque 6×1 de escalera, P3 90 bloques de 7 en Omega): las tres PASA, las tres byte-idénticas a swap42, impacto en score 0 en las tres. Queda P5 (interfaz de paridad, anotado en el diseño, fuera del orden de construcción del Brujo) y la combinación P1+P2+P3 sin construir (decisión posterior de Elán). P4 INVALIDADO (A-F2-1).
