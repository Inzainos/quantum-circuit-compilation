# REVISIÓN DEL AUDITOR — TODO-4 (rediseño del lookup)

**Fecha:** 2026-11-19 ~16:00 CST
**Auditor:** Auditor Interno
**Documento revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/todo4/REPORTE_TODO4_2026-11-19.md` (232 l. / md5 `71e966b5…`, verificado en disco por mí)
**Supervisión de Datos:** `SUPERVISION_DATOS_TODO4_2026-11-19.md` (270 l. / md5 `e78b3da1…`, verificado en disco por mí)
**Verificación del Brujo:** `VERIFICACION_BRUJO_TODO4_2026-11-19.md` (73 l. / md5 `ca18d3ef…`, verificado en disco por mí)
**Cadena:** Programación (mide) → Datos ✓ → Brujo ✓ → Auditor (este documento) → Elán (decide).
**Veredicto: CONCURRO (PASA).**

---

## 1. Archivos verificados en disco por mí (no por confianza en el reporte)

| Archivo | Medido por mí | Reportado | ¿Coincide? |
|---|---|---|---|
| `REPORTE_TODO4_2026-11-19.md` | 232 l. / md5 `71e966b5…` | 232 l. / md5 `71e966b5…` | ✓ |
| `SUPERVISION_DATOS_TODO4_2026-11-19.md` | 270 l. / md5 `e78b3da1…` | 270 l. / md5 `e78b3da1…` | ✓ |
| `VERIFICACION_BRUJO_TODO4_2026-11-19.md` | 73 l. / md5 `ca18d3ef…` | — | ✓ (leído) |
| `resultados_todo4.json` | 2,393 B / md5 `e5ddbbdb…` | 2,393 B / md5 `e5ddbbdb…` | ✓ |
| `sonda_lookup.py` | 4,103 B / md5 `7b3a94ad…` | 4,103 B / md5 `7b3a94ad…` | ✓ |
| `proyeccion.py` | 1,559 B / md5 `95fa43ce…` | 1,559 B / md5 `95fa43ce…` | ✓ |
| `sonda_y1_V1b.py` | 3,142 B / md5 `4719c679…` | 3,142 B / md5 `4719c679…` | ✓ |
| `control_baseline.kmb` | 437,575 B / sha256 `7e842bbf…` | mismo sha | ✓ |
| `invsqrt_V1_j7_dd13.kmb` | 308,407 B / sha256 `c42b0391…` | mismo sha | ✓ |
| `invsqrt_V1b_j7_dd14.kmb` | 314,645 B / sha256 `4f1348d4…` | mismo sha | ✓ |
| `invsqrt_V2_deg3_j7_dd14.kmb` | 340,589 B / sha256 `2d1213dd…` | mismo sha | ✓ |
| `logs/` (16 logs) | presentes | presentes | ✓ |
| `logs/verify_V1b_1shot.log` | **0 B** | 0 B | ✓ (ver §8) |

## 2. Circuitos cargados por mí (km.Circuit.from_file, independiente)

| Circuito | Q | T | num_ops | nbits | ¿Coincide? |
|---|---|---|---|---|---|
| control_baseline.kmb | 139 | 2,561 | 51,798 | 513 | ✓ con reporte, Datos y Brujo |
| invsqrt_V1_j7_dd13.kmb | 142 | 2,457 | 35,682 | 257 | ✓ |
| invsqrt_V1b_j7_dd14.kmb | 142 | 2,523 | 36,366 | 257 | ✓ |
| invsqrt_V2_deg3_j7_dd14.kmb | 149 | 2,725 | 39,480 | 257 | ✓ |

## 3. Perfiles — leídos directamente por mí de los logs

- **Control:** total 2,561 = horner 1,484 + lookup 551 + denorm 260 + normalize 224 + giro 42 ✓; lookup/lookup (init) **510** → del = 551−510 = **41** ✓.
- **V1b:** total 2,523 = horner **1,718** + lookup **279** + denorm 260 + normalize 224 + giro 42 ✓; lookup/lookup (init) **254** → del = 279−254 = **25** ✓. Horner +234 (1,484→1,718), lookup −272 (551→279), neto −38 T ✓.

## 4. Scores, break-even y umbrales — recalculados por mí desde la fórmula

rot_T = 0.56·log2(1/eps) + 5.3 = **27.947630501632958** (recalculado por mí de eps = 6.6939970219409e-13 — exacto); r = (1 + 35×rot_T)/4 = 244.7917668893; Q_break(T) = 390,005.06 / C(T).

| Variante | C (recalc.) | score (recalc.) | Q_break (recalc.) | Veredicto |
|---|---|---|---|---|
| Baseline | 2,805.79 | 390,005.06 | — | referencia |
| V1 j=7 dd=13 | 2,701.79 | 383,654.43 (−1.63%) | 144.3505 | NO PASA (error 4.4871) |
| **V1b j=7 dd=14** | 2,767.79 | **393,026.43 (+0.77%)** | **140.9084** | **NO PASA por 1.0916 qubits** |
| V2 deg=3 j=7 dd=14 | 2,969.79 | 442,498.97 (+13.46%) | 131.3240 | NO PASA (T y Q) |
| V1b + del=0 (hipotético) | 2,742.79 | 389,476.43 (−0.14%) | 142.1927 | PASARÍA por 0.1927 (no construido) |
| V1b + R1 (skip_low) | 2,762.44 | 392,266.48 (+0.58%) | 141.18 | NO PASA |

- **V1 pasaría en score** (Q=142 ≤ Q_break 144.35, por 2.35 qubits) **pero el error 4.4871 lo mata.** Descartada por error.
- **V1b NO PASA por 1.09 qubits** (Q_break exacto 140.9084; 142 − 140.9084 = **1.0916** — ver D-T4-4).
- Umbrales verificados: Q_break(2,501) = **142.0374** > 142 ✓; Q_break(2,502) = **141.9857** < 142 ✓ — para que V1b pasara haría falta Q ≤ 140 (−2) o T ≤ 2,501 (−22 T a Q=142).
- Causa estructural verificada: +3 Q = 3 × 2,767.79 = **+8,303.38**; ahorro de T −38 × 139 = **−5,282**; neto **+3,021.38** (vs diferencia real de scores 3,021.37, 0.01 por redondeo). El Q domina.

## 5. V1b+R1 — sensibilidad del [ESTIMADO] verificada por mí

Con r=28.14 (como R1): C = 2,762.44, score = 392,266.48, Q_break = 141.18. Con la r exacta de R1 (28.139875196917888): C = 2,762.4389, score = **392,266.33** (0.15 puntos menos), Q_break = 141.1814 (igual a 2 decimales). El veredicto no cambia. Concurro con la sensibilidad de Datos.

## 6. Leyes del lookup y errores — verificados por mí del JSON leído directamente

- T(init) = 2^(j+1)−2: j=1..8 → 2, 6, 14, 30, 62, 126, 254, 510 ✓ (JSON, leído directamente).
- T(init) independiente del contenido: 510 T para popcount 0, 512, 13,824, 14,685 y 29,696 ✓.
- T(init) independiente de W: 510 T para W=28/47/58 ✓.
- del(j): 0, 2, 3, 7, 10, 18, 25, 41 ✓ (j=7: 254+25 = 279; j=8: 510+41 = 551 — corroborado por los dos perfiles de circuito, §3).
- Error clásico: baseline 0.7920 — **coincide con el peor error del Gold oficial (0.792)**, lo que valida el modelo clásico contra el verificador en la baseline ✓ (consistencia señalada por Datos). V1 4.4871 FALLA; V1b 0.9022 PASA; V2 0.9555 PASA; j=6 mejor 1.04 FALLA.
- Sonda y1 V1b: **12/12, diff=0** (log leído directamente por mí + JSON) — el circuito V1b produce exacto el y1 del modelo clásico, incluido el peor x (3,116,927, err 0.9022). ✓

## 7. Precisiones — concurro con las cuatro, verificadas por mí

### D-T4-1 (de Datos — sonda_lookup.py no corre completo) — CONCURRO, verificado por mí leyendo el código
`build_lookup` (línea 49) devuelve **2** valores (`int(st.num_toffoli_like), int(circ.num_qubits)`), pero la sección D (línea 85) desempaqueta **3** (`T2, Q2, nops2 = build_lookup(...)`) → muere con ValueError. El script usa solo `print()` (nunca `log.info()`), así que `sonda_lookup.log` es 0 B aunque el FileHandler está configurado (verificado: 0 B en disco). No hay script guardado para la ley del del. **Impacto: ninguno en los números** — las leyes están corroboradas por vías independientes (init por el perfil 510; del por los dos perfiles de circuito 551=510+41 y 279=254+25). Defecto de reproducibilidad del entregable, no de la medición.

### D-T4-2 (de Datos — n_addr con dos significados) — CONCURRO, verificado por mí
En la sección A se imprime `n_addr={len(t)}` (número de entradas, 2^(j+1)); el parámetro `n_addr` de `build_lookup` y la fórmula Q del JSON son bits de dirección (j+1). Los números son consistentes en ambos casos. Menor.

### D-T4-3 (de Datos — error 0.8375 de V1b+R1 es el de R1, reutilizado) — CONCURRO, verificado por mí
`proyeccion.py` línea 21 fija el error de V1b+R1 en 0.8375 con la nota "r=28.14 como R1 [ESTIMADO]"; el peor error de la combinación no se midió (plausiblemente ≈0.9022, el de V1b). **Impacto: ninguno** — < 1 en cualquier caso, y el descarte de V1b+R1 es por score/Q (Q=142 > Q_break 141.18), no por error.

### D-T4-4 (de Datos — el margen de V1b es 1.09 qubits, no 1.08) — CONCURRO, verificado por mí
Q_break exacto de V1b = 140.9084; 142 − 140.9084 = **1.0916 → 1.09 qubits**. El reporte (§0 y §4) dice 1.08 y el mensaje del Brujo a Elán también decía 1.08 — un desliz de redondeo de 0.01. **Corrección registrada: el margen correcto es 1.09 qubits.** Sin impacto en el veredicto.

## 8. Verificador oficial en V1b: sin resultado (incertidumbre abierta, registrada)

`logs/verify_V1b_1shot.log` tiene **0 B** (confirmado por mí en disco). El proceso murió por un reinicio del runtime a los ~8.5 min, sin resultado. **Concurro con no reintentarlo para el descarte:** el veredicto (NO PASA) depende del score/Q medidos y del error clásico de dominio completo, no del verificador; la fase es idéntica a la baseline (35 rot, mismos ángulos, eps sin cambio); la sonda y1 12/12 confirma los valores. El Gold sería exigible solo si una variante pasara el criterio — ninguna lo hace. **V1b NO tiene resultado de verificador oficial — queda registrado como la única incertidumbre abierta del entregable.**

## 9. Palanca futura §8 (del_lookup a 0 T): verificada, concurro con no construirla

Recalculado por mí (§4): del=0 → T=2,498, C=2,742.79, score 389,476.43 (−0.14%), Q_break 142.1927 > 142 → PASARÍA por **0.1927** qubits. Concurro con Datos, Programación y el Brujo: no se construye (reimplementar la primitiva `del_lookup` de kickmix tiene riesgo de correctitud por 0.14% de ganancia, y el margen de 0.19 qubits es frágil). Queda como nota, no como variante.

## 10. Veredicto: CONCURRO (PASA)

La medición es correcta y **TODO-4 SE DESCARTA con número**: el lookup es 551 T con leyes medidas que matan las variantes por contenido; bajar j a 7 ahorra 272 T en el lookup pero el Horner sube +234 T y Q sube +3; la mejor variante (V1b, j=7/dd=14, error 0.9022 PASA) da score 393,026.43 (+0.77%), Q=142 > Q_break 140.91 → **NO PASA por 1.09 qubits** (corrección D-T4-4). V1 pasaría en score pero su error 4.4871 lo mata; V2 es peor en ambos ejes; V1b+R1 tampoco pasa. Precisiones: D-T4-1, D-T4-2, D-T4-3 y D-T4-4 (menores, sin impacto). Incertidumbre abierta registrada: V1b sin resultado de verificador oficial (§8).

**Cadena: Programación ✓ → Datos ✓ → Brujo ✓ → Auditor ✓ (este documento) → Elán decide.** Consecuencia: con TODO-2 y TODO-4 descartados, las dos palancas de construcción del diseño invsqrt medidas están cerradas. Lo que queda pendiente de Elán: la micro-optimización fila 1 m=5,m=9 (−0.57%, decisión separada), la adopción del QF, y R1+R5 (nueva referencia del invsqrt).
