# SUPERVISIÓN DE DATOS — P3 (Fase 2, DQI): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~12:59 CST
**Reporte supervisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p3/REPORTE_P3_2026-11-19.md` — **218 l. / md5 `1757c2cab60e5e5ec36ecaade2bc63ed`** (medido por mí).
**Verificación del Brujo supervisada:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p3/VERIFICACION_BRUJO_P3_2026-11-19.md` — **153 l. / md5 `26176b943c5214b81c384409e912423b`** (medido por mí).
**Constructor:** Programación (subagente constructor P3).
**Diseño:** `FASE2_DQI_2026-11-19.md` §1.3 y §P3.
**Cadena:** Programación ✓ → Brujo ✓ → **Datos ✓ (este informe)** → Auditor → Elán.
**Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.**

## Veredicto: CONCURRO (PASA)

P3 cumple el criterio de FASE 2 §P3: Omega emite sus 630 mul/pase como
90 bloques de 7 explícitos (`N_OMEGA_BLOCK = 7`, `_omega_mul_tasks` +
`_omega_mul_blocks`, `build_omega_tmp` reescrito para iterar los bloques
con las mismas operaciones verbatim), con **26,460 T de mul por pase
(52,920 ida+vuelta)**, **Q aislado 1,317 ≤ 1,864**,
**`reaction_depth` aislado 391 (fwd 216, rev 181)**, y el circuito
resultante es **byte-idéntico a swap42** (equivalencia probada por hash
y por `cmp`; el Gold de swap42 lo cubre). Impacto en score: 0, como
estima el diseño. La ganancia secundaria de localidad no se materializa
(medido — el orden está forzado por dependencias).

## 1. Verificado por cómputo propio

### 1.1 Circuito byte-idéntico a swap42 (la equivalencia central)

Medido por mí en este turno (`sha256sum` + `cmp`):

| Archivo | Tamaño (B) | sha256 |
|---|---|---|
| `dqi_p3.kmb` | 646,811,990 | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |
| `dqi_p3_control.kmb` | 646,811,990 | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |
| `dqi_swap42.kmb` | 646,811,990 | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |

- `cmp dqi_p3.kmb dqi_swap42.kmb` → **idéntico** (sin diferencias).
- `cmp dqi_p3.kmb dqi_p3_control.kmb` → **idéntico** (sin diferencias).
- La ruta de build es reproducible en esta caja: el control (copia sin
  modificar) reproduce el candidato exacto.

### 1.2 Estadísticas leídas por mí de los tres .kmb (carga directa con `km.Circuit.from_file`)

Script `/tmp/stats_p3_datos.py` (corrido por mí en este turno):

| Variante | Q | num_bits | num_instructions (suma) | CCX | HMR |
|---|---|---|---|---|---|
| swap42 (referencia) | 1,864 | 198,813 | 74,182,884 | 671,720 | 796,530 |
| **P3** | **1,864** | **198,813** | **74,182,884** | **671,720** | **796,530** |
| P3 control | 1,864 | 198,813 | 74,182,884 | 671,720 | 796,530 |

Idénticos en los tres. T=710,312 viene de los logs de build y del Gold
(ver §1.7 y §3); la identidad de bytes lo hace redundante. Coinciden con
el reporte §7 y con el `stats_kmb_p3.log` del reporte. (Ver D-P3-2
sobre la presentación de las estadísticas.)

### 1.3 Prueba aislada re-corrida por mí (`test_omega_p3.py`)

Salida medida por mí en este turno, idéntica a la del reporte (§3, §11)
y a la del Brujo (§5):

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

### 1.4 Profundidad aislada re-corrida por mí (`stats_omega_depth.py`)

Salida medida por mí en este turno, idéntica a la del reporte (§8.3)
y a la del Brujo (§6):

```
reaction_depth Omega aislado (fwd) = 216
reaction_depth Omega aislado (rev) = 181
reaction_depth Omega aislado (ida+vuelta) = 391
DEPTH_OK
```

**No aditiva: 216+181 = 397 ≠ 391** (el camino más largo del combinado
no es la concatenación de los dos más largos). Frente al total DQI
19,501 (Gold), Omega aporta 391 (~2.0%): **Omega NO es el cuello de
profundidad del DQI; BM/scan dominan.** La diferencia fwd/rev (216 vs
181) viene de la posición del escalado (primero por i en ida, al final
en vuelta). Nota: el `reaction_depth()` del DQI completo (74M ops)
mata el proceso en esta caja (medido en P1); sobre el Omega aislado
(~58k T) sí se pudo calcular — por eso esta confirmación es un número
medido y no una inferencia.

### 1.5 Aritmética verificada por mí (python)

- sum_{i=0}^{34} i = **595**; 35 + 595 = **630** muls/pase ✓
- 630 × 42 = **26,460** T de mul/pase; 35 × 75 = **2,625** (ValueInv/pase);
  26,460 + 2,625 = **29,085** T/pase ✓; 2 × 29,085 = **58,170** ida+vuelta ✓
- 2 × 26,460 = **52,920** T de mul ida+vuelta; 2 × 2,625 = **5,250** ✓
- 90 × 7 = **630** ✓; 216 + 181 = 397 ≠ 391 ✓ (no aditivo)
- El T de Omega ida+vuelta (58,170) cuadra con el desglose del diseño
  (52,920 mul + 5,250 ValueInv) y con el perfil espiral (omega_fwd
  29,085 — medido en la vuelta 2 DQI, 2026-11-14).

### 1.6 Diff leído por mí en full (solo `dqi_decoder_v1.py` difiere)

- `diff -rq --exclude=__pycache__` p3/src vs dir swap42: entre los
  `.py` compartidos **solo `dqi_decoder_v1.py` difiere** (las demás
  entradas "Only in" son docs/logs/`.kmb`/scripts, no fuentes).
- `src/dqi_decoder_v1.py` md5 **`5bf313db97d53adef8c13e6bdd497bad`**
  (235 l.) — coincide con el reporte (§4, §11) y con el Brujo (§4).
- `src/construir_dqi_p3.py` md5 **`584a1d7afb96b9eda35884cb594262f6`**
  — script nuevo, sin contraparte en swap42.
- Mecanismo confirmado en el código (diff leído en full por mí):
  comentario P3 (líneas 113–120), `N_OMEGA_BLOCK = 7` (línea 121),
  `_omega_mul_tasks(LO, adjoint)` (124–141: lista ordenada
  `('esc', i, None)` / `('acc', i, j)`; ida i=LO−1..0 con esc luego acc
  j=1..i; vuelta i=0..LO−1 con acc j=i..1 luego esc; total
  `LO*(LO+1)/2` = 630), `_omega_mul_blocks(LO, adjoint)` (143–150: 90
  bloques de 7 con aserciones de total y divisibilidad),
  `build_omega_tmp` reescrito (152–178): itera los bloques y ejecuta
  por tarea **las mismas operaciones que hoy, copiadas verbatim**
  (escalado con ValueInv + P + `ixor_kmul` + `del_gf2_mul` + swap +
  free + undo; acumulado `ixor_kmul`).
- El orden está forzado por dependencias: el escalado de i antes de sus
  acumulados; i descendente en ida, ascendente en vuelta; solo el orden
  j dentro de los acumulados de un mismo i es libre (XOR conmuta). Los
  bloques son trozos consecutivos de la secuencia, no un reordenamiento
  — verificado por el test re-corrido (§1.3).

### 1.7 Hallazgo de lectura verificado (dónde vive Omega en producción)

- `from dqi_omega_stage import build_omega` en
  `dqi_decoder_v1.py:28` (dir swap42 y copia P3, misma línea);
  `build_omega` **nunca se llama** en ese archivo (grep por mí: solo
  la línea 28 y la mención en el docstring de `build_omega_tmp`).
- `build_decoder` llama `build_omega_tmp` en las líneas **144 (ida) y
  146 (vuelta) del original swap42** — las líneas que cita el Brujo
  (§7) son las del original; en el archivo P3 (40 líneas insertadas
  por el comentario y las dos funciones nuevas) son **184 y 186**.
  La afirmación es la misma; solo cambia el desplazamiento por la
  inserción (ver D-P3-4).
- `dqi_omega_stage.py` existe (`~/workspace/qcc-dqi/src/`, 3,365 B;
  `def build_omega` en la línea 31) y define `build_omega` con `delta`
  persistente — pero **es un import muerto para este build**.
- P3 se construyó sobre `build_omega_tmp`, que es lo que emite el
  candidato swap42. **Concurro con el hallazgo.**

### 1.8 Build logs leídos en directo

- `build_control.log` (1,071 B): `TOTAL P3 Q=1864 T=710312 en 147s`,
  `live_frontera` 1794/1794/1794/1794/1724, sha `746271d9…`.
- `build_p3.log` (1,063 B): `TOTAL P3 Q=1864 T=710312 en 143s`,
  mismo `live_frontera`, sha `746271d9…`.
- Ambos imprimen ratio DQI 8.16189x / geomean 3.52162x / escalado
  Kaggle 3.53019x — valores del script, ver D-P3-1.

## 2. Precisiones

### D-P3-1 (del Brujo, cita del §6) — CONCURRO

El reporte cita la precisión D-P1-1 para los valores 8.16189x /
3.52162x del §6 — es correcto: son los impresos del script de build
(ancla desactualizada 7.48129 y 5.32 redondeado); los verdaderos son
ratio **8.16289** / geomean **3.52286** (Gold, verificados exactos por
mí en P1: ratio DQI 8.162890942147493, geomean 3.522859936910316). El
"(idénticos a swap42)" es cierto para los valores impresos (el log de
build de swap42 imprime los mismos, verificado por grep en P1).

### D-P3-2 (del Brujo, menor, presentación de stats) — CONCURRO

Verificado por mi propia carga (§1.2): en esta versión de kickmix,
`operation_statistics()` devuelve conteos por tipo de puerta (16
claves: BIT_INVERT, BIT_STORE0, BIT_STORE1, CCX, CSWAP, CX, CZ, HMR,
INFO_TAG, NEG, POP_CONDITION, PUSH_CONDITION, R, SWAP, X, Z), no las
claves resumen (`num_instructions`, `num_toffoli_like`) que muestra
`stats_kmb_p3.log` — esas claves son derivadas (la suma de los
conteos por puerta = 74,182,884, verificada por mí en los tres
`.kmb`; CCX=671,720, HMR=796,530). Los números coinciden; es solo
cómo se presentan.

### D-P3-3 (del Brujo — el bug del test era del test, no de P3) — CONCURRO

La primera versión de `test_omega_p3.py` no reseteaba el contador de
muls antes del build ida+vuelta (MEDICION_FAIL con todos los números
correctos, conteo acumulado 1,260); el contador se reseteó y el test
re-corrido por mí da `OMEGA_P3_OK` limpio (§1.3).

### D-P3-4 (mía, menor, desplazamiento de líneas) — las 144/146 del Brujo son del original

El Brujo (§7) cita `build_decoder` llamando `build_omega_tmp` en las
líneas 144/146. Verificado por mí: esas son las líneas del **original
swap42** (`dqi_decoder_v1.py:144` ida, `:146` vuelta); en el archivo
P3 las llamadas están en **184/186** (el comentario P3 + las dos
funciones nuevas insertan 40 líneas antes). La afirmación es cierta en
ambos archivos; solo hay que decir de cuál archivo son las líneas.

### D-P3-5 (mía, menor, etiqueta de hora) — la ventana de construcción del reporte es UTC, no CST

El encabezado del reporte dice "construcción ~18:35–18:45 CST". Las
mtimes de los archivos (UTC) son: `dqi_p3_control.kmb` 18:40:17,
`dqi_p3.kmb` 18:44:21, `build_p3.log` 18:44:23, reporte 18:45:47 UTC
→ **ventana real ~12:40–12:45 CST**. Es la misma trampa de etiqueta
que D-P1-4 en P1 y D-P2-2 en P2 (UTC etiquetado como CST, 6 h de
diferencia). No cambia ningún número; solo la etiqueta de hora del
encabezado.

### Precisión del diseño (§P3, §10 del reporte) — CONCURRO

"Cada grupo de 7 mul → una matriz 6×7" es ambiguo: **cada mul YA ES
una matriz 6×7 (P1)** — 6 ANDs Karatsuba × 7 puntos de evaluación
dentro de un producto GF(8). Un bloque de 7 muls son 7 matrices 6×7
(294 ANDs), no una matriz. Lo que P3 expone es la agrupación de la
**secuencia de emisión** en 90 bloques de 7. La aritmética y el orden
no cambian.

### Ganancia secundaria de localidad (§9 del reporte) — CONCURRO, NO materializada

Con la secuencia de puertas idéntica, el patrón alloc/free es idéntico
(el `.kmb` byte-idéntico lo prueba: mismos `live_frontera`, mismo Q
aislado 1,317, misma T). Los transitorios `tx,ty,t` viven dentro de
cada llamada a `ixor_kmul42` (se allocan y liberan por mul); agrupar
los muls no cambia su ciclo de vida porque el orden no cambia. La
localidad solo cambiaría si se reordenaran los muls, y el orden está
forzado por dependencias (§2 del reporte). P3 es organizacional puro,
0 T, 0 Q.

## 3. Gold: PASS por identidad de bytes con swap42 (no se re-corrió)

`~/workspace/qcc-data/dqi-perfil/swap42/verify_swap42_gold.log`,
leído en directo por mí en P1 (md5 `38d9f639d158b3b8044ac05ad3b5efb8`,
sin cambios desde el 14 nov) y citado por el Brujo en su §3:

```
status: PASS, score: 2993914799696.024, verified_shots: 102400
value_errors: 5, phase_errors: 0, repetition_factor: 1.2131052140444296
toffoli_count: 710312, reaction_depth: 19501, num_ops: 74182884
num_qubits: 1864, num_bits: 198813
circuit_sha256: 746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603
exit_gold=0
```

El `.kmb` P3 tiene **el mismo sha256** (ver §1.1) → mismo circuito →
el Gold de swap42 lo cubre. Score recomputado exacto en P1:
R×Q²×T = 1.2131052140444296 × 1,864² × 710,312 =
2,993,914,799,696.024. No se re-corrió el Gold del DQI.

## 4. Criterio FASE 2 §P3 — cumplido

- Omega emite sus 630 mul/pase como 90 bloques de 7 explícitos: ✓
  (630 tareas, 90×7, orden == loop original en ambas direcciones).
- 26,460 T de mul por pase (52,920 ida+vuelta): ✓ (medido dinámico).
- Q aislado 1,317 ≤ 1,864: ✓ (Omega no marca el pico del DQI).
- `reaction_depth` aislado 391 (fwd 216, rev 181): ✓ (Omega NO es el
  cuello de profundidad; BM/scan dominan).
- Circuito byte-idéntico a swap42: ✓ (sha256 + `cmp`).
- Gold: ✓ por identidad de bytes (PASS, 102,400 tiros, 5 valor /
  0 fase).
- Import muerto `build_omega` confirmado: ✓ (P3 se construyó sobre
  `build_omega_tmp`, lo que emite swap42).

## 5. Lo que NO se tocó (verificado)

- Fuente swap42 local: el `.kmb` sigue en sha `746271d9…`; el diff
  muestra solo el cambio P3 en la copia test-dev.
- Candidato swap42 (ZIP), ZIP Adopted v3, docs de diseño, árboles
  R1/R2/R5, árboles P1/P2: sin cambios en esta tarea.
- Entrenamiento SomeJoint en la Kali: ni mirado.

**P3 PASA. Siguiente: Auditor → Elán.**

**Fase 2 COMPLETA en sus 3 variantes construidas** (P1 matriz 6×7
explícita, P2 bloque 6×1 de escalera, P3 90 bloques de 7 en Omega):
las tres PASA, las tres byte-idénticas a swap42, impacto en score 0
en las tres. Queda P5 (interfaz de paridad, anotado en el diseño, fuera
del orden de construcción) y la combinación P1+P2+P3 sin construir
(decisión posterior de Elán). P4 INVALIDADO (A-F2-1).
