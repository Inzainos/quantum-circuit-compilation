# VERIFICACIÓN DEL BRUJO — TODO-4 (rediseño del lookup): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~15:57 CST
**Verificador:** Brujo (El brujo)
**Cadena:** Programación (mide) → Datos (supervisa, CONCURRO) → **Brujo (este documento)** → Auditor → Elán (decide).
**Veredicto: CONCURRO (PASA).** La medición es correcta y el veredicto se sostiene: **TODO-4 (rediseño del lookup) SE DESCARTA con número — ninguna variante pasa el break-even.**

Verifiqué por cómputo propio (cargando los circuitos y recalculando las fórmulas), no por confianza en el reporte ni en la supervisión de Datos.

## 1. Documentos verificados en disco por mí

| Archivo | Medido por mí | ¿Coincide? |
|---|---|---|
| `REPORTE_TODO4_2026-11-19.md` | 232 l. / md5 `71e966b5…` | ✓ con el reporte |
| `SUPERVISION_DATOS_TODO4_2026-11-19.md` | 270 l. / md5 `e78b3da1…` | ✓ con lo que Datos reportó |
| `resultados_todo4.json` | 2,393 B / md5 `e5ddbbdb…` | ✓ |
| `sonda_lookup.py` | 4,103 B / md5 `7b3a94ad…` | ✓ |
| `proyeccion.py` | 1,559 B / md5 `95fa43ce…` | ✓ |
| `sonda_y1_V1b.py` | 3,142 B / md5 `4719c679…` | ✓ |
| `control_baseline.kmb` | sha256 `7e842bbf…` | ✓ byte-idéntico al baseline |
| `invsqrt_V1_j7_dd13.kmb` | sha256 `c42b0391…` | ✓ |
| `invsqrt_V1b_j7_dd14.kmb` | sha256 `4f1348d4…` | ✓ |
| `invsqrt_V2_deg3_j7_dd14.kmb` | sha256 `2d1213dd…` | ✓ |
| `logs/verify_V1b_1shot.log` | 0 B (confirmado por Datos) | ✓ |

## 2. Circuitos cargados por mí (km.Circuit.from_file, independiente)

| Circuito | Q | T | num_ops | nbits | ¿Coincide? |
|---|---|---|---|---|---|
| control_baseline.kmb | 139 | 2,561 | 51,798 | 513 | ✓ con reporte y Datos |
| invsqrt_V1_j7_dd13.kmb | 142 | 2,457 | 35,682 | 257 | ✓ |
| invsqrt_V1b_j7_dd14.kmb | 142 | 2,523 | 36,366 | 257 | ✓ |
| invsqrt_V2_deg3_j7_dd14.kmb | 149 | 2,725 | 39,480 | 257 | ✓ |

Q/T de las tres variantes coinciden con el reporte y con la supervisión de Datos. (Nota: el num_ops de la baseline es 51,798; el de R1/R1+R5 es 51,795 — los 2 CX menos de la truncación, consistente.)

## 3. Scores, break-even y umbrales recalculados por mí

Fórmula: C = T + (1 + 35 × 27.947630501632958)/4; Q_break(T) = 390,005.06 / C(T). Recalculado de cero con Python:

| Variante | C (recalc.) | score (recalc.) | Q_break (recalc.) | Veredicto |
|---|---|---|---|---|
| Baseline | 2,805.79 | 390,005.06 | — | referencia |
| V1 j=7 dd=13 | 2,701.79 | 383,654.43 (−1.63%) | 144.3505 | NO PASA (error 4.4871) |
| **V1b j=7 dd=14** | 2,767.79 | **393,026.43 (+0.77%)** | **140.9084** | **NO PASA por 1.0916 qubits** |
| V2 deg=3 j=7 dd=14 | 2,969.79 | 442,498.97 (+13.46%) | 131.324 | NO PASA (T y Q) |
| V1b + del=0 (hipotético) | 2,742.79 | 389,476.43 (−0.14%) | 142.1927 | PASARÍA por 0.1927 (no construido) |
| V1b + R1 (skip_low) | 2,762.44 | 392,266.48 (+0.58%) | 141.18 | NO PASA |

Umbrales verificados: Q_break(2,501) = 142.0374 > 142 ✓; Q_break(2,502) = 141.9857 < 142 ✓ — para que V1b pasara haría falta Q ≤ 140 o T ≤ 2,501.

Causa estructural verificada: +3 Q ≈ +8,303.38 (3 × 2,767.79); ahorro de T −38 × 139 = −5,282; neto +3,021.38 (393,026.43 − 390,005.06 = 3,021.37, diferencia de redondeo 0.01). El Q domina.

## 4. Precisiones de Datos — verificadas por mí

- **D-T4-1 (reproducibilidad — sonda_lookup.py no corre completo): CONFIRMADO** leyendo el código. `build_lookup` devuelve 2 valores (`int(st.num_toffoli_like), int(circ.num_qubits)`) aunque su docstring dice "(T, Q, num_ops)"; la sección D desempaqueta 3 (`T2, Q2, nops2 = build_lookup(...)`) → muere con ValueError. El script usa solo `print()` (nunca `log.info()`), así que `sonda_lookup.log` es 0 B aunque el FileHandler está configurado. No hay script guardado para la ley del del. **Impacto: ninguno en los números** — las leyes están corroboradas por vías independientes (init por el perfil 510; del por los dos perfiles de circuito 551=510+41 y 279=254+25). Defecto de reproducibilidad del entregable, no de la medición.
- **D-T4-2 (n_addr con dos significados): CONFIRMADO.** En la sección A se imprime `n_addr={len(t)}` (número de entradas, 2^(j+1)); el parámetro `n_addr` de `build_lookup` y la fórmula Q del JSON son bits de dirección (j+1). Los números son consistentes en ambos casos. Menor.
- **D-T4-3 (error 0.8375 de V1b+R1 es el de R1, reutilizado): CONFIRMADO** leyendo `proyeccion.py`. El caso V1b+R1 tiene el error hardcodeado en 0.8375 con la nota "r=28.14 como R1 [ESTIMADO]"; el peor error de la combinación no se midió. Plausiblemente ≈0.9022 (el de V1b). **Impacto: ninguno** — < 1 en cualquier caso, y el descarte de V1b+R1 es por score/Q (Q=142 > Q_break 141.18), no por error. Concurro con la sensibilidad de Datos (r exacta 28.139875196917888 → score 392,266.33, 0.15 pts menos; Q_break 141.18 igual).
- **D-T4-4 (el margen de V1b es 1.09 qubits, no 1.08): CONFIRMADO.** Q_break exacto de V1b = 140.9084 (recalculado por mí, §3); 142 − 140.9084 = **1.0916 → 1.09 qubits**. El reporte dice 1.08 y mi mensaje a Elán también decía 1.08 — un desliz de redondeo de 0.01. **Corrección registrada aquí: el margen correcto es 1.09 qubits.** Sin impacto en el veredicto.

## 5. Verificador oficial en V1b: sin resultado (incertidumbre abierta, registrada)

`logs/verify_V1b_1shot.log` tiene 0 B (confirmado por Datos). El proceso murió por un reinicio del runtime a los ~8.5 min, sin resultado. **Concurro con no reintentarlo para el descarte:** el veredicto (NO PASA) depende del score/Q medidos y del error clásico de dominio completo, no del verificador; la fase es idéntica a la baseline (35 rot, mismos ángulos, eps sin cambio); la sonda y1 12/12 confirma los valores. El Gold sería exigible solo si una variante pasara el criterio — ninguna lo hace. Si el Auditor pide el Gold de V1b, se corre en la Kali (avisar antes). **V1b NO tiene resultado de verificador oficial — queda registrado como la única incertidumbre abierta del entregable.**

## 6. Palanca futura §8 (del_lookup a 0 T): verificada, concurro con no construirla

Recalculado por mí (§3): del=0 → T=2,498, C=2,742.79, score 389,476.43 (−0.14%), Q_break 142.1927 > 142 → PASARÍA por 0.1927 qubits. Concurro con Datos y Programación: no se construye (reimplementar la primitiva `del_lookup` de kickmix tiene riesgo de correctitud por 0.14% de ganancia, y el margen de 0.19 qubits es frágil). Queda como nota, no como variante.

## 7. Veredicto: CONCURRO (PASA)

La medición es correcta y **TODO-4 SE DESCARTA con número**: el lookup es 551 T con leyes medidas que matan las variantes por contenido; bajar j a 7 ahorra 272 T en el lookup pero el Horner sube +234 T y Q sube +3; la mejor variante (V1b, j=7/dd=14, error 0.9022 PASA) da score 393,026.43 (+0.77%), Q=142 > Q_break 140.91 → **NO PASA por 1.09 qubits** (corrección D-T4-4). V1 pasaría en score pero su error 4.4871 lo mata; V2 es peor en ambos ejes; V1b+R1 tampoco pasa. Precisiones: D-T4-1, D-T4-2, D-T4-3 y D-T4-4 (menores, sin impacto). Incertidumbre abierta registrada: V1b sin resultado de verificador oficial (§5).

**Cadena: Programación ✓ → Datos ✓ → Brujo ✓ (este documento) → Auditor → Elán decide.** Consecuencia: con TODO-2 y TODO-4 descartados, las dos palancas de construcción del diseño invsqrt medidas están cerradas.
