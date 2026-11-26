# Estado Quantum — 2026-11-26

**Rama:** `local/quantum-estado-2026-11-26` (snapshot de documentación de estado, desde main `457cc742`; no toca main).
**Orden:** Elán 2026-11-26 10:31 — actualizar todo lo de Quantum en GitHub; dejarlo en sus últimas versiones, con changelogs, README y todas las actualizaciones.

## Scores y selección (Kaggle, verificado en vivo)

| Envío | Ref | Score | Estado |
|---|---|---|---|
| v7 (P15+hoisting) | 58647127 | **5.00918** | COMPLETE — mejor personal |
| v6 (P15) | 58633092 | 5.00379 | COMPLETE |
| v5 | 58594222 | 4.90803 | COMPLETE |
| v4.1 | 58579331 | 3.54317 | COMPLETE |

**Selección final: v7 + v6** (Elán marcó el v7; v4.1 fuera — corregido 2026-11-24 11:50, verificado en vivo 11:52).

**Producción vigente:** invsqrt R1+R5 (Q=139, T=2,561, score 389,261.01, factor 5.335×); DQI QF+P15+hoisting (Q=1,857, T=665,819; hoisted.kmb sha `852739c3…`); dfthcsos seg100@brot13 (score 1,257,565,658.5, factor 2.668×, λ_eff 49.04190 finito).

**Fechas oficiales:** entrada/cierre de equipos 13 ene 2027; envío final 20 ene 2027 (11:59 PM UTC).

## GitHub (verificado en vivo 2026-11-24 y 2026-11-26)

- **Main:** `457cc742` (PR #36, B7: `skip_low` en `nr_reference_circuit.py`, 2026-11-21). Sin commits nuevos desde el 21 nov.
- **README en main:** desactualizado — menciona 5.00379/4.90803 (v6/v5), no menciona 5.00918, v7, B7 ni la selección final. Actualizado en esta rama (sección "Estado actual").
- **CHANGELOG en main:** vigente hasta el 20 nov (v6 + PR #34). Actualizado en esta rama (v7, PR #35/#36, H8, Gold segunda corrida, revisión a fondo, Kimi).
- **`submission/final_submission.zip` en main:** SÍ está (67,007,440 B, blob `43a3eb3b…`) = ZIP swap42 (nov 19, 3.53019), no el v7. Actualizarlo a v7 toca main y es decisión de Elán (pendiente).
- **Release adopted-v3:** SÍ existe (publicado, 4 assets) con `dqi_omega_karatsuba.kmb` (629,623,070 B) — era v3 (3.42920), no el DQI vigente. El DQI vigente (QF+P15, sha `852739c3…`) no está en ningún Release (decisión de Elán; subida ~630 MB desde su máquina).
- **Tags:** solo 3 (`v2026-11-13-final`, `swap42-2026-11-19`, `adopted-v3`). **Tag `v5-4.90803` NO existe** — nombre y commit objetivo sin confirmar por Elán (no se creó en esta actualización: main ya está en `457cc742` y el nombre referiría al estado v5).
- **Rama Kimi:** `local/kimi-briefs-v2-2026-11-24`, HEAD `2b80768a` (9 archivos: briefs + verificaciones + parches P15/QF + mapa + regla). Ya estaba actualizada; no se tocó.
- **Rama del motor nuevo:** `local/carry-decoder-2026-11-21` es LOCAL de la Kali, no está en GitHub y no se sube sin GO de Elán.

## Gold (motor nuevo, Fase 2)

- **Segunda corrida: M11 FAIL** (verificador oficial, 102,400 tiros; errores de valor 102,400/102,400; fase 0). Circuito Q=15,432, T=149,796, bits=49,140. Causa raíz: `build_euclid_level` no-op y scan de 1 escalera representativa. M12 no ejecutado. Cadena completa (Datos/Brujo/Auditor CONCURRO PASA — el FAIL documentado con números).
- **Tercera corrida: GO de Elán 2026-11-24 12:18** (rediseño de Q + M6/M9 reales). **BLOQUEADA en la derivación de la opción (b).** Coordinación de diseño enviada a Programación (`COORDINACION_DISENO_GOLD_TERCERA_CORRIDA_2026-11-24.md`); despacho bloqueado hasta la derivación completa.
- **Derivación opción (b) — ABIERTA (incumplió el cierre).** Parte 1 cerrada 2026-11-24 (`DERIVACION_CARRY_PARTE1_CODIGO_2026-11-24.md`, 111 l., md5 `d5ad1cbe…`): el carry es un BIT, la recurrencia es una definición, el marker es el mecanismo in-place, y la corrección se reduce a (A) y (B). **Punto exacto que falta: probar (A) y (B) desde el oráculo** (división de Hermite, `model.py` l.136–146). Compromiso de cierre: 15:00 del 24 nov — **incumplido sin reporte** (reportado a Elán 22:29 del 24 nov; sin actividad en el chat desde las 12:24). Al 2026-11-26 sigue abierta y el Gold sigue bloqueado en ella. No se reporta como cerrada ni como "casi lista": falta la prueba o el contraejemplo exacto.

## H8

- **Conclusión adoptada: el conjunto de fallo del carry NO ES ACOTABLE** ("NO ACOTABLE"). H8 original NO PASA; rehacer NO PASA; corrección mínima (camino (a)) PASA. `H8_REHACER_SUMMARY.md` sigue sin commitear y repite afirmaciones falsas (decisión de Elán: descartar / corregir y commitear / dejar sin commitear).

## Notebook v7

- **Versión 7 pública, contenido v5** (4.90803) — verificado en vivo 2026-11-24 (`VERIFICACION_NOTEBOOK_V7_2026-11-24.md`). Necesita republicación con el contenido correcto + GO de Elán (pendiente).

## Pendientes que de verdad siguen siendo decisión de Elán

1. Tag `v5-4.90803` (nombre + commit objetivo).
2. ¿El DQI vigente (QF+P15) va en un Release?
3. `final_submission.zip` en main: actualizar a v7 o dejar histórico.
4. `H8_REHACER_SUMMARY.md`: descartar / corregir y commitear / dejar sin commitear.
5. Lera: pendiente de su llamada (nov 11).
6. Notebook v7: republicación con el contenido correcto (Kaggle, no GitHub).
7. Tercera corrida Gold: sigue bloqueada en la derivación opción (b) — no es una decisión nueva, es trabajo abierto del Brujo.
