# REPORTE — TODO-4: Rediseño del lookup (invsqrt)

**Fecha:** 2026-11-19 ~15:45 CST (21:45 UTC)
**Orden:** Elán (2026-11-19 ~15:25 CST, vía el Brujo). Refuerzo ~15:27: "Mídelo".
**Workspace:** `~/workspace/qcc-data/test-dev/espiral-prototipo/todo4/`
**Árbol usado:** copia fresca del árbol B/C en `todo4/tree/` (el árbol B/C original NO se tocó).
**Base de comparación:** logshift2 (baseline), NO R1+R5 — el diseño TODO-4 se mide contra
la baseline logshift2, como pide la tarea (R1+R5 corre en paralelo y no es la base).

## 0. Veredicto (resumen)

**TODO-4 (rediseño del lookup) SE DESCARTA con número — ninguna variante pasa el break-even.**

El lookup es 551 T = init 510 T (árbol AND de 9 bits de dirección, ley 2^9−2) + del 41 T.
Medí las leyes del lookup con sondas aisladas: **el T es independiente del contenido de la
tabla y del ancho del target** — solo depende del número de bits de dirección. Eso mata de
entrada a diff-QROM, slice y variantes por contenido. La única palanca real es bajar j
(8→7), y la medí construyendo las variantes: **j=7 ahorra 272 T en el lookup pero el Horner
se come casi todo (+234 T por coeficientes más anchos y un paso extra) y Q sube +3** (coef
58→61). La mejor variante construida (V1b, j=7/dd=14, error 0.9022 PASA) da score
393,026.43 (+0.77%), Q=142 > Q_break 140.91 → **NO PASA por 1.08 qubits**. La variante
j=7/dd=13 pasaría en score (−1.63%) pero su error es 4.4871 → FALLA. Grado 3 es peor en
ambos ejes. j=6 falla en error (mejor 1.04). El techo +7.6% [ESTIMADO] de Datos requeriría
borrar el lookup entero; lo medido es que ni borrar la mitad alcanza, porque el Horner
paga el ensanchamiento.

| Variante | T | Q | C | score | Q_break | error/tol | Veredicto |
|---|---|---|---|---|---|---|---|
| Baseline logshift2 | 2,561 | 139 | 2,805.79 | 390,005.06 | — | 0.7920 | referencia |
| **V1** j=7 dd=13 | 2,457 | 142 | 2,701.79 | 383,654.43 (−1.63%) | 144.35 | 4.4871 | **NO PASA (error)** |
| **V1b** j=7 dd=14 | 2,523 | 142 | 2,767.79 | 393,026.43 (+0.77%) | 140.91 | 0.9022 | **NO PASA (score/Q)** |
| V1b sesgo=2 | 2,523 | 142 | 2,767.79 | 393,026.43 (+0.77%) | 140.91 | 0.8715 | NO PASA (mejor margen) |
| **V2** deg=3 j=7 dd=14 | 2,725 | 149 | 2,969.79 | 442,498.97 (+13.46%) | 131.32 | 0.9555 | **NO PASA (T y Q)** |
| V1b + del=0 (hipotético) | 2,498 | 142 | 2,742.79 | 389,476.43 (−0.14%) | 142.19 | 0.9022 | PASARÍA (no construido) |
| V1b + R1 (skip_low) | 2,523 | 142 | 2,762.44 | 392,266.48 (+0.58%) | 141.18 | 0.8375 | NO PASA (r=28.14 [ESTIMADO]) |

## 1. Estructura del lookup medida (el .kmx del baseline)

Perfilador `kmx_profile.py` sobre `control_baseline.kmb` (sha `7e842bbf…`, reproducido
byte-idéntico): lookup total **551 T** = `lookup/lookup` (init, ida) **510 T** +
`lookup/unlookup` (del, vuelta) **41 T** (30 `lookup` + 11 `binary_to_unary`).
El resto del circuito: horner 1,484 · denorm 260 · normalize 224 · giro 42 = 2,561 exacto.

Lectura del .kmx (`control_baseline.kmx`, 51,821 l.; región lookup 305–20672 ida,
51426–51821 vuelta):
- **init_lookup = árbol AND binario sobre los 9 bits de dirección** (8 bits f + sel):
  510 CCX distribuidos 2,4,8,…,256 por nivel (targets q86…q93; q85 es 1 CX).
  Workspace interno: 9 qubits (q85–q93). La carga de la tabla son CXs (0 T):
  15,196 CX totales = 14,685 desde q93 (el AND final = la entrada) + 510 desde nodos
  intermedios (bits compartidos por prefijo, codificación por diferencias en el trie)
  + 1 desde sel. **El popcount de la tabla real es exactamente 14,685** (medido con
  `tabla_mitad`): un CX por cada bit 1 de la tabla.
- **del_lookup = 41 T** con maquinaria HMR (`CZ … if b…` + `HMR` + `Z` en la vuelta;
  109 CSWAP en la región `unary_to_binary`). No es el inverso gratuito del árbol:
  kickmix recomputa parte del árbol y convierte unary→binary con CSWAPs.
- Q del lookup en el circuito: pico 94 (FASE1); composición Q total: x22 + sel1 + sb4 +
  coef58 + lookup-ws9 + Horner-ws45 = 139.

## 2. Leyes del lookup medidas (sonda aislada) — `sonda_lookup.py`, `logs/sonda_lookup.log`

`init_lookup`/`del_lookup` standalone (builder kickmix directo, sin el resto del circuito):

- **A. T(init) = 2^(j+1) − 2 exacto** (j=1..8: 2, 6, 14, 30, 62, 126, 254, 510).
  La ley se cumple en todos los j medidos, con la tabla real de cada j.
- **B. T(init) es INDEPENDIENTE del contenido de la tabla** (j=8, W=58): real
  (popcount 14,685), ceros (0), unos (29,696), aleatoria (13,824), solo-bit0 (512) →
  **510 T en los 5 casos**. La carga es CX (0 T); el contenido solo cambia el número
  de CXs. **Consecuencia: diff-QROM, slice por contenido y array-reuse no pueden
  ahorrar T en kickmix — el T no ve la tabla.**
- **C. T(init) es INDEPENDIENTE del ancho del target W** (j=8): W=28 (solo c0), 47
  (c0+c1), 58 (los 3) → **510 T en los 3**. Q sí cambia (46/65/76). **Consecuencia:
  cargar los coeficientes por separado costaría 3×510 T; el árbol ya se comparte
  entre los 58 bits.**
- **D. init+del = 551 T exacto** (j=8, tabla real) — reproduce el perfil del circuito.
  **del(j) medido:** j=1..8 → 0, 2, 3, 7, 10, 18, 25, 41. j=7: init 254 + del 25 = 279 T.
- **E. Q standalone** = (j+1) + W + (j+1) (dirección + target + workspace): j=8/W=58 →
  76; j=7/W=61 → 77. El workspace del lookup es n_addr = j+1 qubits.

## 3. Error clásico por spec (dominio completo, `modelo()` exacto) — `logs/sonda_error_*.log`

`modelo()` es la aritmética exacta del circuito; el error es el peor error relativo /
2^-24 sobre x ∈ [1, 3,133,452] (3,133,452 valores). Hallazgo estructural: **el error
está dominado por la cuantización de coeficientes (wc), no por la interpolación.**
wc=27 → 1.7436 FALLA (j=8 y j=7); wc=29 → 0.4383/0.4505 PASA. A wc=29, j=7 vs j=8
difieren 0.4505 vs 0.4383: la penalización de interpolación de j=7 es ~0.01.

| spec (deg, j, wc, dd, sesgo) | w | coef | error/tol | |
|---|---|---|---|---|
| (2, 8, 28, 13, 1) baseline | [28,19,11] | 58 | 0.7920 | PASA |
| (2, 7, 28, 13, 1) V1 | [28,20,13] | 61 | 4.4871 | FALLA |
| **(2, 7, 28, 14, 1) V1b** | [28,20,13] | 61 | **0.9022** | PASA |
| (2, 7, 28, 14, 0) | [28,20,13] | 61 | 1.0100 | FALLA (por 0.01) |
| (2, 7, 28, 14, 2) | [28,20,13] | 61 | 0.8715 | PASA (mejor margen) |
| (2, 7, 27, 14, 1) | [27,19,12] | 58 | 1.7436 | FALLA (wc=27) |
| (2, 7, 29, 14, 1) | [29,21,14] | 64 | 0.4505 | PASA (coef +6) |
| (3, 7, 28, 14, 1) V2 | [28,21,13,6] | 68 | 0.9555 | PASA |
| (2, 6, 28, 15, 1/2) | [28,21,15] | 64 | 1.2148 / 1.1255 | FALLA |
| (3, 6, 28, 15, 1) | [28,21,15,9] | 73 | 1.0400 | FALLA |

Por qué V1 falla y V1b pasa: a j=7, dd=13 deja fuera el último bit de mantisa
(m=14; width−1−j = 14). El término caído (u_14·(c>>14)) cuesta ~4.5× tolerancia.
dd=14 usa todos los bits y el error cae a 0.9022. A j=6 ni dd=15 (todos los bits)
salva el error (1.1255): la interpolación ya no alcanza.

## 4. Variantes construidas y medidas (circuitos reales, builder)

Controles: baseline reproducido byte-idéntico (sha `7e842bbf…`, Q=139, T=2,561).
Perfil V1b (`logs/kmx_profile_control.log` + perfil V1b): horner **1,718 T** (vs 1,484
baseline, +234 T) · lookup **279 T** (254+25, vs 551, −272 T) · resto igual (denorm 260,
normalize 224, giro 42). Neto: −38 T. El Horner se come el ahorro del lookup: los
coeficientes se ensanchan (w=[28,20,13] vs [28,19,11]) y cada paso de Horner cuesta más,
más el paso extra m=14 (+66 T: 2,457→2,523 entre V1 y V1b).

- **V1** (`invsqrt_V1_j7_dd13.kmb`, sha `c42b0391…`, 308,407 B): Q=142, T=2,457.
  Score 383,654.43 (−1.63%, Q_break 144.35 > 142) — **pasaría en score, pero el error
  4.4871 lo mata**. Descartada por error.
- **V1b** (`invsqrt_V1b_j7_dd14.kmb`, sha `4f1348d4…`, 314,645 B): Q=142, T=2,523.
  Score 393,026.43 (+0.77%), Q_break 140.91 < 142 → **NO PASA por 1.08 qubits**.
  Q=142 se descompone: coef +3 (58→61), lookup-ws −1 (9→8), Horner-ws +1 (45→46
  derivado: 142 − (22+1+4+61+8) = 46, por los isub más anchos). Error 0.9022 PASA;
  sesgo=2 da 0.8715 con el mismo T/Q (mejor margen, no cambia el veredicto).
- **V2** (`invsqrt_V2_deg3_j7_dd14.kmb`, sha `2d1213dd…`, 340,589 B): Q=149, T=2,725.
  Score 442,498.97 (+13.46%), error 0.9555 PASA. Peor en ambos ejes: la fila extra
  del Horner (+1 fila de 14 pasos) y coef 68 (+10 Q). Descartada.
- **V1b + R1** (skip_low, r=28.14 como R1 [ESTIMADO]): C = 2,523+239.44 = 2,762.44,
  score 392,266.48 (+0.58%), Q_break 141.18 < 142 → NO PASA. El +3 Q domina incluso
  con el ahorro de rotación de R1.

## 5. Variantes descartadas sin construir (con número, sobre primitivas medidas)

- **diff-QROM:** MUERTA por medición B (§2): T(init)=510 T para popcount 0, 512,
  13,824, 14,685 y 29,696. El cargador ya codifica por diferencias en el trie (510 CX
  desde nodos intermedios) y el T no ve el contenido. Ahorro: **0 T**.
- **QROM segmentado (dos lookups de 256 + mux por sel):** 2×254 (init) + 58 CSWAP
  (mux de 58 bits, 1 T c/u) = 566 T init + 2×25 (del) = **616 T vs 551 (+65 T)**,
  más +58 Q (segundo registro coef para el mux). Peor en ambos ejes. La variante
  4+4 con registro intermedio 16×58 bits cuesta **+928 Q**. Muertas.
- **wc variable por coeficiente / wc=27:** los anchos ya son los mínimos
  (max bit_length por fila). wc=27 → error 1.7436 FALLA (§3). wc=29 pasa error
  (0.44) pero coef 58→61 (+3 Q, peor score). Muerta.
- **slice (cargar menos bits):** MUERTA por medición C (§2): T=510 T para W=28/47/58.
- **array-reuse / index compartido:** solo hay UN lookup en el circuito; no hay
  segundo consumidor del árbol de direcciones. Muerta.
- **lookup window / Horner fusionado (cargar c2, usar, descargar, cargar c1…):**
  cada carga es un init_lookup completo (510 T) → 3×510 = 1,530 T. El árbol ya se
  comparte entre los 58 bits en el lookup actual. Muerta.

## 6. Proyección §9.3 y criterio — `proyeccion.py`, `logs/proyeccion.log`

Fórmula oficial: score = Q × C; C = T + (1 + n_rot × rot_T)/4; rot_T = 27.947630501632958;
parte de rotaciones (35 rot) = 244.79. Q_break(T) = 390,005.06 / C(T). PASA si Q ≤ Q_break
Y error/tol < 1. (Ver tabla §0.) Ninguna variante construida pasa. Para que V1b pasara
haría falta Q ≤ 140 (−2) o T ≤ 2,501 (−22 T a Q=142).

## 7. Por qué pierde el lookup (causa estructural, medida)

1. **Bajar j ensancha los coeficientes.** A j=7 los coeficientes crecen (c1 19→20 bits,
   c2 11→13 bits) porque el segmento es 2× más ancho: el coeficiente lineal escala ~h
   y el cuadrático ~h². El registro coef pasa 58→61 (+3 Q) y **cada paso del Horner
   cuesta más** (isub más anchos): el Horner sube 1,484→1,718 T (+234 T), casi todo el
   ahorro del lookup (−272 T). El neto en T es solo −38 T.
2. **El Q es el eje que domina.** +3 Q ≈ +8,400 puntos de score (3 × 2,800), mientras
   el ahorro de T vale −38 × 139 ≈ −5,300. El neto es +3,021 puntos (+0.77%). 1 qubit
   ≈ 20 Toffolis aquí, y el lookup paga 3 qubits por 272 T.
3. **El del_lookup no es gratis (41 T).** La vuelta cuesta 41 T (j=8) / 25 T (j=7)
   por la maquinaria HMR + CSWAPs de `unary_to_binary`. No es el inverso gratuito del
   árbol. Eliminar el del entero (hipotético, §8) apenas voltearía V1b a −0.14%.

## 8. Palanca futura (no construida): el del_lookup a 0 T

Si el `del_lookup` costara 0 T (en vez de 25 T a j=7), V1b sería T=2,498, C=2,742.79,
score 389,476.43 (−0.14%), Q_break 142.19 > 142 → **PASARÍA por 0.19 qubits**. No lo
construí: requeriría reimplementar la primitiva `del_lookup` de kickmix (su
descomputo HMR + `unary_to_binary` con CSWAPs existe por una razón que no verifiqué
a fondo — el descomputo directo con `del_and` inverso puede no aplicar cuando los
nodos del árbol son controles de las cargas), y la ganancia sería 0.14% con riesgo
de correctitud. Queda como nota para el Brujo/Datos, no como variante.

## 9. Verificación

- **Sonda y1 V1b: PASA 12/12** (`sonda_y1_V1b.py`, `logs/sonda_y1_V1b.log`): el circuito
  V1b produce EXACTO el y1 del modelo clásico en los 12 valores, incluido el peor x
  (3,116,927, err 0.9022) y los valores de referencia de R1. Builder y modelo coinciden
  para (j=7, dd=14). El error clásico de dominio completo (§3) es, por tanto, el error
  del circuito en valores.
- **Verificador oficial local (1 tiro/x) en V1b: NO COMPLETÓ.** El proceso murió por un
  reinicio del runtime a los ~8.5 min (log 0 bytes, sin resultado, sin procesos vivos).
  No hay resultado de verificador local para V1b. No se reintentó: el veredicto (NO PASA)
  depende del score/Q medidos y del error clásico de dominio completo, no del
  verificador; y la fase (rotaciones) es idéntica a la baseline (35 rot, mismos ángulos,
  eps sin cambio). Si Datos/Auditor piden el Gold de V1b, se corre en la Kali (avisar
  antes, como pide la tarea).
- **Controles:** baseline byte-idéntico (sha `7e842bbf…`, Q=139, T=2,561).

## 10. Archivos y logs (todo en `todo4/`)

| Archivo | Tamaño | Contenido |
|---|---|---|
| `REPORTE_TODO4_2026-11-19.md` | este reporte | veredicto + números |
| `resultados_todo4.json` | 2,393 B | números medidos (leyes, variantes, errores) |
| `sonda_lookup.py` | 4,103 B | leyes init/del (j, contenido, W, Q) |
| `proyeccion.py` | 1,559 B | proyección break-even exacta |
| `sonda_y1_V1b.py` | 3,142 B | sonda y1 12/12 |
| `control_baseline.kmb` (sha `7e842bbf…`) | 437,575 B | baseline reproducido byte-idéntico |
| `control_baseline.kmx` | 51,821 l. | baseline en texto (análisis del lookup) |
| `invsqrt_V1_j7_dd13.kmb` (sha `c42b0391…`) | 308,407 B | V1: Q=142, T=2,457 (error FALLA) |
| `invsqrt_V1b_j7_dd14.kmb` (sha `4f1348d4…`) | 314,645 B | V1b: Q=142, T=2,523 (score NO PASA) |
| `invsqrt_V2_deg3_j7_dd14.kmb` (sha `2d1213dd…`) | 340,589 B | V2: Q=149, T=2,725 |
| `tree/` | copia del árbol B/C | NO se modificó el árbol original |
| `logs/kmx_profile_control.log` | 3,321 B | lookup 551 = 510+41; resto del circuito |
| `logs/sonda_lookup.log` / `sonda_lookup_resumen.log` | — | leyes A–E |
| `logs/sonda_del.log` | — | del(j) = 0,2,3,7,10,18,25,41 |
| `logs/sonda_error_clasico.log` | — | errores (deg,j) dominio completo |
| `logs/sonda_error_wc_sesgo.log` | — | errores wc/sesgo (dominio de wc) |
| `logs/sonda_error_j6.log` | — | j=6 falla (mejor 1.04) |
| `logs/sonda_peor_x_v1b.log` | — | peor x V1b = 3,116,927 (0.9022) |
| `logs/sonda_y1_V1b.log` | — | y1 12/12 PASA |
| `logs/analisis_kmx_lookup.log` / `analisis_tags_lookup.log` / `analisis_bloques_lookup.log` / `analisis_del_lookup.log` | — | estructura .kmx del lookup |
| `logs/proyeccion.log` | — | proyecciones break-even |
| `logs/verify_V1b_1shot.log` | 0 B | verificador local NO completó (reinicio runtime) |

## 11. Qué NO hice (límites)

- NO corrí Gold en la Kali (ninguna variante es viable; el §9 no lo exige para el
  descarte; si se pidiera el Gold de V1b, avisar al padre antes).
- NO construí la variante del=0 (§8): reimplementar una primitiva kickmix con riesgo
  de correctitud por 0.14% no se justifica en este paso.
- NO toqué: árbol B/C original, árboles R1/R2/R5/P1/P2/P3, workspaces todo2-paso/ y
  r1r5/ (otros subagentes en paralelo), producción, ZIP Adopted v3, candidato swap42,
  entrenamiento SomeJoint en la Kali.
- El desglose Horner-ws 45→46 (§4) es derivado por aritmética (142 − (22+1+4+61+8)),
  no trazado directo; no afecta el veredicto (Q=142 es medido por el builder).
