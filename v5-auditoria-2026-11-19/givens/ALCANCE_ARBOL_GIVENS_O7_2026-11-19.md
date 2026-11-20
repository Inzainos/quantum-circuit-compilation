# ALCANCE — Árbol de Givens (O7): búsqueda conjunta + topología del árbol

**Fecha:** 2026-11-19 ~16:05 CST
**Diseño:** Brujo (El brujo)
**Decisión de Elán:** GO 2026-11-19 ~16:04 (vía Coordinador): *"Y sí, de hecho sean los este Árbol de Givens."*
**Origen:** Punto 4 §b Fase 3 (2026-11-19 ~09:50) — FAVORABLE, alcance como trabajo nuevo cuando Elán lo pidiera. Lo pide ahora.
**Cadena:** Brujo (este alcance) → Programación (construye la búsqueda) → Datos (supervisa) → Brujo (verifica) → Auditor (revisa) → Elán (decide).

## 1. Qué es (definición del plan, §3.7 — leída, no asumida)

El playbook de la frontera (field-guide §7.3): buscar **rank (R,B,C), umbrales de poda, topología del árbol de Givens y precisión de ángulos JUNTOS**, re-evaluando 20 mHa, Λ y E_gap después de CADA refit clásico; forzar el ancho ANGLE ≤128 en generación, no en empaquetado.

Nosotros optimizamos el factor (LBFGS) y el compilador (barrido brot/J) por separado; el barrido brot/J está agotado. **No tocamos la topología del árbol de Givens.** Es trabajo sin medir ni estimar — este documento lo acota.

## 2. Objeto: el MODELO, no el circuito

- Las rotaciones de Givens son **3,450 T (3.7% de 93,237 T)**, 75 rotaciones por vector, topología **log_depth** (plan §1, FASE 3 §46).
- La parte analítica (inner + Givens + outer) es **13,757 T (14.8%)** y es **modelo** (`SpinFreeData_V1` / `heuristic_costs`), no circuito.
- **El objeto de trabajo es el modelo.** La búsqueda no construye un .kmx; construye y mide candidatos del modelo (rank, poda, topología, precisión) con su T analítico, su error_2, su Λ y su E_gap. Solo un candidato que pase el criterio (§5) se convierte después en circuito y se verifica con el verificador oficial.

## 3. Espacio de búsqueda (conjunto, no por separado)

| Dimensión | Valores a explorar | Nota |
|---|---|---|
| Rank (R,B,C) | alrededor y lejos de (65,60,60) adoptado | el rank manda el T y el error |
| Umbrales de poda | qué ángulos/términos se podan | la poda mueve T y error_2 juntos |
| Topología del árbol de Givens | log_depth (actual, 75 rot/vector) vs path (y otras) | **la dimensión que nunca tocamos** |
| Precisión de ángulos | redondeo de ángulos (brot/precisión) | afecta error_2 y el ancho ANGLE |
| Restricción | **ANGLE ≤128 en generación** | no en empaquetado (playbook §7.3) |

La búsqueda es CONJUNTA: las cuatro dimensiones se mueven a la vez y cada candidato se re-evalúa completo (20 mHa, Λ, E_gap) después de su refit clásico. No se optimiza una dimensión con las demás fijas (eso ya lo hicimos: LBFGS por un lado, brot/J por otro).

## 4. Techos (calculados por mí, no citados)

- **Solo Givens (3,450 T → 0):** score química 3,336,160,975 → 3,212,714,753; ratio 1.00583 → 1.04447; geomean ×1.01265 → **+1.26% geomean**. Ese es el techo de la dimensión Givens sola.
- **Parte analítica entera (13,757 T → 0):** score → 2,843,914,694; ratio → 1.17992; geomean ×1.05465 → **+5.47% geomean**. Coincide exacto con el O4 del plan — verificado por mí.
- **Consecuencia:** la ganancia realista es pequeña (el techo de Givens sola es +1.26%); la búsqueda conjunta puede encontrar algo en el resto de la parte analítica, pero el techo absoluto del trabajo es +5.47%. El test se mide para saber si hay algo, no porque se espere mucho.

## 5. Criterio de aceptación (el mismo que el entrenamiento)

Un candidato entra a la entrega solo si cumple AMBAS:
- **(a) PASS oficial** — error_2 ≤ 20 mHa (verificador oficial, no solo el modelo clásico); y
- **(b) score < 3,336,160,975** — mejor que el lbfgs adoptado.

Nada a la entrega, al ZIP, a GitHub ni a Kaggle sin que el candidato pase (a) y (b) y sin GO de Elán.

## 6. Restricciones (no interferencia)

- **SomeJoint sigue corriendo en la GPU de la Kali** (driver PID 3918, seg51+). NO se toca, NO se usa la GPU para esto.
- **CASMI sigue corriendo en la GPU** (PID 5599). NO se toca.
- La búsqueda es **clásica (modelo, CPU)**. Corre en esta caja o en la CPU de la Kali, nunca en la GPU.
- NO se toca el lbfgs adoptado, el ZIP v4.1, el entrenamiento SomeJoint ni la referencia R1+R5 recién adoptada.
- El trabajo es de medición: si la búsqueda no encuentra nada que pase el criterio, se descarta con número (como TODO-2 y TODO-4).

## 7. Entregables (Programación)

1. Script de búsqueda (reutilizable): genera candidatos (rank, poda, topología, precisión), refit clásico por candidato, evalúa error_2, Λ, E_gap y T analítico.
2. Tabla de resultados: por candidato, rank, poda, topología, precisión, T, error_2, Λ, E_gap, y si pasa el criterio.
3. Reporte con el veredicto: mejor candidato vs lbfgs adoptado (3,336,160,975), y si alguno pasa (a) y (b).

## 8. Siguiente paso

Programación construye la búsqueda (§7) con este alcance. Datos supervisa, Brujo verifica, Auditor revisa, Elán decide. Pregunta abierta para la construcción: dónde corre la búsqueda (esta caja vs CPU de la Kali) y cuántos candidatos por tanda — lo define Programación en su reporte, no aquí.
