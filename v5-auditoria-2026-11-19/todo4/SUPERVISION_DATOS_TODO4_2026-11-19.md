# SUPERVISIÓN DE DATOS — TODO-4 (rediseño del lookup): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~15:51 CST
**Supervisor:** Datos (Analista de datos)
**Cadena:** Programación (mide) → **Datos (este documento)** → Brujo →
Auditor → Elán (decide).
**Veredicto: CONCURRO (PASA).** La medición es correcta y el veredicto se
sostiene: **TODO-4 (rediseño del lookup) SE DESCARTA con número — ninguna
variante pasa el break-even.**
Mi supervisión es por cómputo propio sobre el JSON, los logs y los
circuitos leídos/cargados directamente, no por confianza en el reporte.

## 1. Archivos verificados en disco por mí (medidos, no citados de oídas)

| Archivo | Medido por mí | Reportado | ¿Coincide? |
|---|---|---|---|
| `REPORTE_TODO4_2026-11-19.md` | 232 l. / 15,498 B / md5 `71e966b5…` | 232 l. / md5 `71e966b5…` | ✓ |
| `resultados_todo4.json` | 2,393 B / md5 `e5ddbbdb…` | 2,393 B | ✓ |
| `sonda_lookup.py` | 4,103 B / md5 `7b3a94ad…` | 4,103 B | ✓ |
| `proyeccion.py` | 1,559 B / md5 `95fa43ce…` | 1,559 B | ✓ |
| `sonda_y1_V1b.py` | 3,142 B / md5 `4719c679…` | 3,142 B | ✓ |
| `control_baseline.kmb` | 437,575 B / sha256 `7e842bbf…` | mismo sha | ✓ |
| `invsqrt_V1_j7_dd13.kmb` | 308,407 B / sha256 `c42b0391…` | mismo sha | ✓ |
| `invsqrt_V1b_j7_dd14.kmb` | 314,645 B / sha256 `4f1348d4…` | mismo sha | ✓ |
| `invsqrt_V2_deg3_j7_dd14.kmb` | 340,589 B / sha256 `2d1213dd…` | mismo sha | ✓ |
| `logs/` (16 logs), `tree/` (copia del árbol B/C) | presentes | presentes | ✓ |
| `logs/verify_V1b_1shot.log` | **0 B** | 0 B | ✓ (ver §10) |

## 2. Baseline y estructura del lookup — verificados por mí

`control_baseline.kmb` es **byte-idéntico al baseline logshift2 de
producción** (sha256 `7e842bbf…`). Cargado por mí con kickmix: **Q = 139,
T = 2,561, num_ops = 51,798, nbits = 513** — Q/T exactos.

Perfilador sobre el control (`logs/kmx_profile_control.log`): lookup
**551 T** = `lookup/lookup` (init) **510 T** + `lookup/unlookup` (del)
**41 T** (30 `lookup` + 11 `binary_to_unary`); resto: horner 1,484 ·
denorm 260 · normalize 224 · giro 42 = **2,561 exacto** ✓.

Estructura del .kmx verificada por mí con grep en la región lookup
(líneas 305–20672): **CCX = 510** (targets q93:256, q92:128, q91:64,
q90:32, q89:16, q88:8, q87:4, q86:2 — suman 510 ✓); **CX = 15,196**
(q93: 14,685 + nodos intermedios 256+128+64+32+16+8+4+2 = 510 + sel
q22: 1 = 15,196 ✓). **El popcount de la tabla real es exactamente
14,685** — un CX por cada bit 1. La vuelta tiene 109 CSWAP en
`unary_to_binary` ✓. Q del lookup en el circuito: pico 94
(22+1+4+58+9); composición Q total 22+1+4+58+9+45 = 139 ✓.

## 3. Leyes del lookup medidas — verificadas (sonda + JSON + perfiles)

- **A. T(init) = 2^(j+1) − 2 exacto** (j=1..8: 2, 6, 14, 30, 62, 126, 254,
  510) ✓ — el árbol AND binario sobre j+1 bits de dirección.
- **B. T(init) INDEPENDIENTE del contenido** (j=8, W=58): real (popcount
  14,685), ceros (0), unos (29,696), aleatoria (13,824), solo-bit0 (512)
  → **510 T en los 5 casos** ✓. La carga es CX (0 T); el contenido solo
  cambia el número de CXs. **Consecuencia: diff-QROM, slice por contenido
  y array-reuse no pueden ahorrar T — el T no ve la tabla.**
- **C. T(init) INDEPENDIENTE del ancho W** (j=8): W=28/47/58 → **510 T
  en los 3** ✓. Q sí cambia (46/65/76). Cargar los coeficientes por
  separado costaría 3×510 T; el árbol ya se comparte entre los 58 bits.
- **D. init+del = 551 T exacto** (j=8, tabla real) — reproduce el perfil
  del circuito. **del(j) medido:** j=1..8 → 0, 2, 3, 7, 10, 18, 25, 41
  ✓ (j=7: init 254 + del 25 = 279 T). El del está corroborado por los dos
  perfiles de circuito (551 = 510+41; 279 = 254+25).
- **E. Q standalone = 2(j+1) + W** (dirección + target + workspace):
  j=1..8 con W=78..58 → 82, 82, 81, 80, 79, 78, 77, 76 ✓; C: W=28/47/58
  → Q 46/65/76 ✓.

## 4. Error clásico por spec (dominio completo, 3,133,452 valores)

`modelo()` es la aritmética exacta del circuito; el error es el peor
error relativo / 2^-24. **El error está dominado por la cuantización de
coeficientes (wc), no por la interpolación** — verificado en las tablas
de los logs (leídas directamente):

| spec (deg, j, wc, dd, sesgo) | coef | error/tol | |
|---|---|---|---|
| (2, 8, 28, 13, 1) baseline | 58 | 0.7920 | PASA |
| (2, 7, 28, 13, 1) V1 | 61 | **4.4871** | FALLA |
| **(2, 7, 28, 14, 1) V1b** | 61 | **0.9022** | PASA |
| (2, 7, 28, 14, 0) | 61 | 1.0100 | FALLA (por 0.01) |
| (2, 7, 28, 14, 2) | 61 | 0.8715 | PASA (mejor margen) |
| (2, 7, 27, 14, 1) | 58 | 1.7436 | FALLA (wc=27) |
| (2, 7, 29, 14, 1) | 64 | 0.4505 | PASA (coef +6) |
| (2, 8, 27, 13, 1) | 55 | 1.7436 | FALLA (wc=27) |
| (2, 8, 29, 13, 1) | 61 | 0.4383 | PASA |
| (3, 7, 28, 14, 1) V2 | 68 | 0.9555 | PASA |
| (2, 6, 28, 15, 1/2) | 64 | 1.2148 / 1.1255 | FALLA |
| (3, 6, 28, 15, 1) | 73 | 1.0400 | FALLA |

Por qué V1 falla y V1b pasa: a j=7, dd=13 deja fuera el último bit de
mantisa (m=14; width−1−j = 22−1−7 = 14). El término caído cuesta ~4.5×
tolerancia. dd=14 usa todos los bits y el error cae a 0.9022. A j=6 ni
dd=15 (todos los bits) salva el error (mejor 1.04): la interpolación ya
no alcanza. Consistencia: el error clásico del baseline (0.7920) es el
peor error del Gold oficial (0.792) — el modelo clásico y el verificador
coinciden en la baseline.

## 5. Variantes construidas — Q/T cargados por mí, scores recalculados

C = T + (1 + 35 × rot_T)/4; rot_T = 27.947630501632958 (recalculado de
eps = 6.6939970219409e-13 ✓); parte de rotaciones = 244.79;
Q_break(T) = 390,005.06 / C(T). PASA si Q ≤ Q_break **Y** error < 1.

| Variante | T | Q | C (recalc.) | score (recalc.) | Q_break (recalc.) | error | Veredicto |
|---|---|---|---|---|---|---|---|
| Baseline | 2,561 | 139 | 2,805.79 | 390,005.06 | — | 0.7920 | referencia |
| **V1** j=7 dd=13 | 2,457 | 142 | 2,701.79 | 383,654.43 (−1.63%) | 144.35 | 4.4871 | **NO PASA (error)** |
| **V1b** j=7 dd=14 | 2,523 | 142 | 2,767.79 | 393,026.43 (+0.77%) | 140.91 | 0.9022 | **NO PASA (score/Q)** |
| V1b sesgo=2 | 2,523 | 142 | 2,767.79 | 393,026.43 (+0.77%) | 140.91 | 0.8715 | NO PASA (mejor margen) |
| **V2** deg=3 j=7 dd=14 | 2,725 | 149 | 2,969.79 | 442,498.97 (+13.46%) | 131.32 | 0.9555 | **NO PASA (T y Q)** |
| V1b + del=0 (hipotético) | 2,498 | 142 | 2,742.79 | 389,476.43 (−0.14%) | 142.19 | 0.9022 | PASARÍA (no construido) |
| V1b + R1 (skip_low) | 2,523 | 142 | 2,762.44 | 392,266.48 (+0.58%) | 141.18 | 0.8375 | NO PASA (r=28.14 [ESTIMADO]) |

Q/T cargados por mí con kickmix: V1 **Q=142, T=2,457**; V1b **Q=142,
T=2,523**; V2 **Q=149, T=2,725** — todos coinciden con el reporte ✓.
Perfil V1b (`tree/logs/kmx_profile.log`): horner **1,718 T** (+234) ·
lookup **279 T** (−272) · resto igual (denorm 260, normalize 224, giro
42) = 2,523 ✓. El paso extra m=14 cuesta +66 T (2,457→2,523 entre V1 y
V1b) ✓; V1 Horner = 1,652 (1,718−66) y su T cuadra: 2,561−1,484−551+
1,652+279 = 2,457 ✓.

- **V1 pasaría en score** (Q=142 ≤ Q_break 144.35, por 2.35 qubits)
  **pero el error 4.4871 lo mata.** Descartada por error.
- **V1b NO PASA por 1.09 qubits** (Q_break exacto 140.9084; 142 −
  140.9084 = 1.0916 — ver D-T4-4).
- **V1b + R1 NO PASA** (Q=142 > Q_break 141.18). Sensibilidad del
  [ESTIMADO]: con la r exacta de R1 (28.139875196917888) en vez de 28.14,
  C = 2,762.4389, score = 392,266.33 (0.15 puntos menos), Q_break 141.18
  igual a 2 decimales — el veredicto no cambia.
- Umbrales verificados: para que V1b pasara haría falta Q ≤ 140 (−2) o
  T ≤ 2,501 (−22 T a Q=142): Q_break(2,501) = 142.04 > 142 ✓;
  Q_break(2,502) = 141.99 < 142 ✓.

## 6. Por qué pierde el lookup (causa estructural, medida)

1. **Bajar j ensancha los coeficientes** (c1 19→20, c2 11→13 bits): el
   registro coef pasa 58→61 (+3 Q) y cada paso del Horner cuesta más:
   el Horner sube 1,484→1,718 T (+234 T), casi todo el ahorro del lookup
   (−272 T). El neto en T es solo −38 T.
2. **El Q es el eje que domina:** +3 Q ≈ +8,303 puntos (3 × 2,767.79),
   mientras el ahorro de T vale −38 × 139 ≈ −5,282. El neto es +3,021
   puntos (+0.77%) — verificado exacto (393,026.43 − 390,005.06 =
   3,021.37). 1 qubit ≈ 20.19 Toffolis aquí, y el lookup paga 3 qubits
   por 272 T. Q=142 se descompone: coef +3 (58→61), lookup-ws −1 (9→8),
   Horner-ws +1 (45→46, derivado: 142 − (22+1+4+61+8) = 46).
3. **El del_lookup no es gratis (41 T / 25 T).** La vuelta cuesta por la
   maquinaria HMR + CSWAPs de `unary_to_binary`. Eliminar el del entero
   (hipotético, §11) apenas voltearía V1b a −0.14%.

## 7. Variantes descartadas sin construir (con número, sobre primitivas medidas)

- **diff-QROM:** MUERTA por medición B (§3): T(init)=510 T para popcount
  0, 512, 13,824, 14,685 y 29,696. Ahorro: **0 T** ✓.
- **QROM segmentado (dos lookups de 256 + mux por sel):** 2×254 + 58
  CSWAP = 566 T init + 2×25 (del) = **616 T vs 551 (+65 T)**, más +58 Q
  ✓. La variante 4+4 con registro intermedio 16×58 bits cuesta **+928 Q**
  (16×58) ✓. Muertas.
- **wc variable / wc=27:** wc=27 → error 1.7436 FALLA (§4); wc=29 pasa
  error (0.44) pero coef 58→61 (+3 Q, peor score). Muerta.
- **slice:** MUERTA por medición C (§3): T=510 T para W=28/47/58 ✓.
- **array-reuse:** solo hay UN lookup en el circuito; no hay segundo
  consumidor del árbol. Muerta.
- **lookup window / Horner fusionado:** cada carga es un init_lookup
  completo (510 T) → 3×510 = 1,530 T. Muerta.

## 8. Sonda y1 V1b: PASA 12/12

`sonda_y1_V1b.py`, `logs/sonda_y1_V1b.log` (leído directamente): el
circuito V1b produce EXACTO el y1 del modelo clásico en los 12 valores
(diff=0 en todos), incluido el peor x (3,116,927, err 0.9022) y el peor x
de R1 (718,814, err 0.3009). Builder y modelo coinciden para (j=7,
dd=14). El error clásico de dominio completo (§4) es, por tanto, el
error del circuito en valores.

## 9. Criterio §6 del reporte — ninguna variante pasa

PASA si Q ≤ Q_break **Y** error/tol < 1. V1 falla error; V1b, V1b
sesgo=2, V2 y V1b+R1 fallan score/Q. El techo +7.6% [ESTIMADO] de Datos
requeriría borrar el lookup entero; lo medido es que ni borrar la mitad
alcanza, porque el Horner paga el ensanchamiento.

## 10. Verificador oficial local en V1b: NO COMPLETÓ (incertidumbre abierta, documentada)

`logs/verify_V1b_1shot.log` tiene **0 bytes** (confirmado por mí) — el
proceso murió por un reinicio del runtime a los ~8.5 min, sin resultado.
No se reintentó. **Concurro con no reintentarlo para el descarte:** el
veredicto (NO PASA) depende del score/Q medidos y del error clásico de
dominio completo, no del verificador; y la fase (rotaciones) es idéntica
a la baseline (35 rot, mismos ángulos, eps sin cambio — el cambio toca
solo lookup/Horner, partes clásico-reversibles, y la sonda y1 12/12
confirma los valores). El Gold sería exigible solo si una variante
pasara el criterio — ninguna lo hace. Si el Auditor pide el Gold de V1b,
se corre en la Kali (avisar antes). **V1b NO tiene resultado de
verificador oficial — queda registrado como la única incertidumbre
abierta del entregable.**

## 11. Palanca futura §8 (no construida): el del_lookup a 0 T

Si el `del_lookup` costara 0 T (en vez de 25 T a j=7), V1b sería T=2,498,
C=2,742.79, score **389,476.43 (−0.14%)**, Q_break **142.19** > 142 →
**PASARÍA por 0.19 qubits** (margen exacto 0.1927). Verificado por mí.
No se construyó: requeriría reimplementar la primitiva `del_lookup` de
kickmix (su descomputo HMR + `unary_to_binary` con CSWAPs existe por una
razón que no se verificó a fondo) y la ganancia sería 0.14% con riesgo de
correctitud. **Concurro con no construirla — y agrego que el margen
(0.19 qubits) es tan delgado que el pase sería frágil.** Queda como nota,
no como variante.

## 12. Precisiones mías

### D-T4-1 (reproducibilidad — el script de la sonda no corre completo como está entregado)
`sonda_lookup.py` (md5 `7b3a94ad…`) **no puede correr hasta el final
como está entregado**, y el reporte no lo dice:
- Primera corrida (21:31, `sonda_lookup_stdout.log`): muere en la
  primera llamada con `AttributeError: 'kickmix.OperationStatistics'
  object has no attribute 'num_operations'` (línea 49; el atributo
  correcto es `num_instructions`).
- El archivo fue editado (mtime 21:32) para quitar ese término, pero la
  sección D sigue desempaquetando 3 valores (`T2, Q2, nops2 =
  build_lookup(...)`) de una función que ahora devuelve 2 → la segunda
  corrida muere en "D del solo" (por eso el resumen no trae esa fila ni
  la línea E).
- `logs/sonda_lookup.log` tiene **0 B** porque el script nunca llama al
  logger (solo `print`): el reporte cita ese log para las leyes, pero la
  evidencia vive en `sonda_lookup_resumen.log`.
- No hay script guardado que genere `sonda_del.log` (la ley del del).
**Impacto: ninguno en los números** — las leyes están corroboradas por
vías independientes (init por el perfil 510; del por los dos perfiles de
circuito 551=510+41 y 279=254+25; Q por las fórmulas verificadas). Es un
defecto de reproducibilidad del entregable, no de la medición.

### D-T4-2 (menor — la etiqueta `n_addr` significa dos cosas)
En `sonda_lookup_resumen.log`, "n_addr=512" es el número de entradas
(2^(j+1)); en la fórmula Q del JSON, `n_addr` son los bits de dirección
(j+1). Los números son consistentes en ambos casos (Q = 2(j+1)+W
verificado en §3); solo la etiqueta cambia de significado.

### D-T4-3 (menor — el error 0.8375 de V1b+R1 es el de R1, reutilizado sin medir la combinación)
`proyeccion.py` fija el error de V1b+R1 en 0.8375 — que es el peor error
de R1 (0.8375458188313827 @ x=718,814), no una medición de la
combinación. El peor error de la combinación no se midió; plausiblemente
es ≈0.9022 (el de V1b en x=3,116,927, donde la truncación aporta poco).
**Impacto: ninguno** — < 1 en cualquier caso, y el descarte de V1b+R1
es por score/Q (Q=142 > Q_break 141.18), no por error.

### D-T4-4 (menor — el margen de V1b es 1.09 qubits, no 1.08)
Q_break exacto de V1b = 140.9084; 142 − 140.9084 = **1.0916 → 1.09
qubits**. El reporte y el mensaje del Brujo dicen 1.08 — un desliz de
redondeo de 0.01. Sin impacto en el veredicto.

## 13. Veredicto: CONCURRO (PASA)

La medición es correcta y **TODO-4 SE DESCARTA con número**: el lookup
es 551 T con leyes medidas que matan las variantes por contenido; bajar
j a 7 ahorra 272 T en el lookup pero el Horner sube +234 T y Q sube +3;
la mejor variante (V1b, j=7/dd=14, error 0.9022 PASA) da score
393,026.43 (+0.77%), Q=142 > Q_break 140.91 → **NO PASA por 1.09
qubits**. V1 pasaría en score pero su error 4.4871 lo mata; V2 es peor
en ambos ejes; V1b+R1 tampoco pasa. Precisiones mías: D-T4-1, D-T4-2,
D-T4-3 y D-T4-4 (menores, sin impacto en el veredicto). Incertidumbre
abierta registrada: V1b sin resultado de verificador oficial (§10).

**Cadena: Programación ✓ → Datos ✓ (este documento) → Brujo → Auditor
→ Elán decide.** Consecuencia: con TODO-2 y TODO-4 descartados, las dos
palancas de construcción del diseño invsqrt medidas están cerradas. Lo
que queda pendiente de Elán: la micro-optimización fila 1 m=5,m=9
(−0.57%, decisión separada), la adopción del QF, y R1+R5 (nueva
referencia del invsqrt según el reporte ~15:50, Gold PASS con empate
exacto con R1).

## 14. Adenda — revisión del Auditor (2026-11-19 ~16:00 CST)

Revisión del Auditor: `~/workspace/auditoria/REVISION_AUDITOR_TODO4_2026-11-19.md`
(102 l. / md5 `0a3351b6…`, verificado en disco por mí) — **CONCURRO
(PASA)**. El Auditor verificó por cómputo propio lo mismo que yo
(circuitos cargados con kickmix, fórmulas recalculadas, JSON y logs
leídos directamente: baseline Q=139/T=2,561/num_ops=51,798; V1
Q=142/T=2,457; V1b Q=142/T=2,523; V2 Q=149/T=2,725; perfiles;
scores/Q_break; umbrales Q_break(2,501)=142.0374 y Q_break(2,502)=
141.9857; causa estructural +8,303.38 −5,282 = +3,021.38; sonda y1 V1b
12/12) y **concurrió con D-T4-1, D-T4-2, D-T4-3 y D-T4-4** (cada una
verificada por él leyendo el código o recalculando). Confirmó además:
V1b sin verificador oficial (log 0 B) — concurre con no reintentarlo
para el descarte; palanca del=0 verificada (389,476.43, margen 0.1927)
— concurre con no construirla.

**Cadena TODO-4 COMPLETA: Programación ✓ → Datos ✓ → Brujo ✓ →
Auditor ✓ → Elán decide.**
