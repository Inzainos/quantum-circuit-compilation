# PROMPT — GOLD TERCERA CORRIDA: REDISEÑO DE Q + M6/M9 REALES
# BORRADOR — NO DESPACHAR ANTES DE LAS 15:00 (falta la derivación completa del Brujo: prueba de (A)/(B) o contraejemplo exacto)

**GO de Elán (2026-11-24 12:18):** "el Gold sí se va con M6/M9 reales." Tercera corrida: rediseño de Q + M6/M9 reales.
**Base:** segunda corrida, HEAD `c483d35` (rama `local/carry-decoder-2026-11-21`), reporte 192 l. / md5 `c295511a…`, Q=15,432, T=149,796, M11 FAIL (102,400/102,400 errores de valor), M12 no ejecutado. El T ya está bajo presupuesto (149,796 < 367,398); falta Q y los bloques reales.
**Diseño:** el del Brujo (derivación opción (b) — Parte 1 verificada: `DERIVACION_CARRY_PARTE1_CODIGO_2026-11-24.md`, 111 l. / md5 `d5ad1cbe…`; la Parte 2 — prueba de (A)/(B) desde el oráculo, o el contraejemplo exacto — llega 15:00 y se ANEXA a este prompt antes de despachar).
**Regla vigente:** `REGLA_EVIDENCIA.md` (`/home/deamon/carry-decoder/`). HECHO exige artefacto + comando en log + número medido. PREPARADO nunca es HECHO. No re-marques nada como completo sin ejecutarlo.

## 1. Semántica del carry (del Brujo, Parte 1 — NO usar la fórmula del reporte H8)

- **El carry es un BIT, no un elemento de campo.** P(g) = `zero_flag(D)` (1 si D==0 en el nodo). `carry_next`: `flag(g−1) = [marker(g−1)==0] ∧ flag(g)` con sándwich X(pole)…X(pole); F_16 = pole_16 verdadero. La recurrencia es una DEFINICIÓN, no un teorema. **M7 se construye sobre esta semántica de bit** (zero_flag + cswap + normalización), NUNCA sobre la fórmula del reporte H8 (P_principal = coeficiente de r_g): esa fórmula es FALSA bajo sus propias definiciones — contraejemplo verificado: (r_{g−1}, r_g, r_{g+1}) = (0, 3, 6) con q_g=2 cumple 2·3 ⊕ 6 = 0 pero la fórmula exige 3 = 0.
- **El marker ES el mecanismo de reutilización in-place.** marker = `combine(words[grupos[g−1]['word']: +2])` — el registro N del grupo g−1 leído durante el RETORNO del grupo g, en sus valores FORWARD (el retorno va 16→5 y el grupo g−1 aún no se descomputa). Equivalencia derivada del código: [marker(g−1)==0] ⟺ pole_{g−1} ∨ [N_final(g−1)==0]. **El rediseño de Q debe conservar la disciplina de orden del retorno (16→5) y la colocación del marker** — ahí viven los 840 qubits de S reutilizados in-place. No se toca el orden del retorno sin re-derivar la equivalencia.
- **La corrección del carry se reduce a (A) y (B) (punto exacto pendiente — llega 15:00).** Carry correcto ⟺ (A) pole_g=0 ⟹ pole_{g−1}=0 (los polos forman un sufijo en g) Y (B) pole_g=1 ∧ [N_final(g−1)==0] ⟹ pole_{g−1}=1. Son propiedades de los polos VERDADEROS de la ejecución real (función del síndrome), no identidades algebraicas. **Si (A) o (B) falla, el hallazgo viene con el contraejemplo exacto y el diseño debe manejarlo — no se construye encima de una (A)/(B) sin probar.** [ANEXAR AQUÍ LA PARTE 2 DEL BRUJO ANTES DE DESPACHAR.]

## 2. Qué construir (en orden)

1. **Rediseño de Q (restricciones e invariantes del diseño — la asignación concreta es construcción bajo estas restricciones, verificada por medición).** La segunda corrida midió Q=15,432 (Gate 2d FAIL, objetivo 901) — pool de 600 temporales + índices monotónicos de kickmix. El diseño fija: (a) los 840 qubits de S son el conjunto de trabajo y NUNCA se duplican — extracción/síntesis/conversión trabajan in-place sobre S; (b) un solo pool acotado de temporales con free explícito en el punto en que el valor muere (la segunda corrida ya bajó de 17,149 a 15,432 con un pool de 52 temporales y frees en el rework — ese es el piso de partida, no el techo); (c) disciplina de orden del retorno 16→5 y colocación del marker intactas (el marker es el patrón in-place: leer N del grupo g−1 durante el retorno del grupo g, antes de descomputarlo); (d) ningún `alloc_qubits` dentro de un bucle sin su `free` en la misma iteración. La asignación concreta (qué temporal va dónde) la calculas tú bajo estas restricciones y se verifica por medición (Q ≤ 901 + disciplina del pool). **Si no puedes cerrar Q con el pool acotado, repórtalo con el pico medido y dónde vive, no lo escondas con índices monotónicos.**
2. **M6 real (requisitos — el detalle interno es construcción bajo estos requisitos, desde el diseño de Fase 2 corregido (H1) + H3-1, que van como contexto).** `build_euclid_level` era un no-op (retorna los coeficientes sin cambios). Implementar el descenso de Euclides extendido real con cswaps para predicados de hueco y dot cache (costo exacto por dirección 54,426/54,947 T, H3-1). Si el descenso no cierra contra ese residual, reporta la brecha con el número, no pongas un no-op.
3. **M9 real (requisitos — el detalle interno es construcción bajo estos requisitos).** El scan "simulaba" el bucle de 4,025 puntos con UNA escalera zero_hold (12 T medidos vs 44,275 T esperados). Implementar el bucle Chien/Forney real de 4,025 puntos desrollado (evaluación A(β)/B(β), residuo ω(β)/σ'(β), CCZ con máscaras) — 44,275 T esperados. La escalera de 1 representante queda PROHIBIDA.
4. **M7 real** sobre la semántica de bit (§1) — solo después de la Parte 2 (15:00). La prueba de (A)/(B) decide si el carry necesita una rama para violaciones — no se puede diseñar el M7 definitivo antes de saberlo. [ANEXAR AQUÍ LA PARTE 2 DEL BRUJO ANTES DE DESPACHAR.]
5. **Circuito reversible completo** con uncomputation por etapa, tokens HMR y asserts de fase vacía. Q ≤ 901 assert en todo momento.
6. **M11 verificador oficial** sobre el circuito completo (102,400 tiros). El simulador NO basta con HMR. Si FALLA, diagnostica (valor vs fase, en qué x) y corrígelo — no lo escondas, no fuerces un PASS.
7. **M12 Gold:** 102,400 tiros, dos semillas — M0 `52642227205936912575373656611044064096114070193057152544535209180255000077827` verbatim + por defecto. Criterio: 0 errores (R≈1.19126, geomean ~10.11) o ≤5 errores (R≈1.2131, geomean ~10.05). **Si da >5 errores, repórtalo tal cual.**
8. **Reporte actualizado** (`REPORTE_GOLD_DECODIFICADOR_COMPLETO_2026-11-23.md`) con las mediciones REALES (Q/T por bloque medidos, no proyectados), el resultado del verificador oficial y el del Gold. Corrige la tabla de milestones a su estado real. **Commit** en la rama `local/carry-decoder-2026-11-21` y actualiza `GOLD_PLAN.md` con el estado real y la ETA.

## 3. Criterios de aceptación medibles

- M11 PASS con el verificador oficial (102,400 tiros, 0 errores de valor y 0 de fase, o dentro del presupuesto R).
- Q objetivo 901; T ≤ 367,398 (total de diseño).
- Los 10 circuitos con SHA256 distintos (dos iguales = stub).
- Ningún bloque placeholder sin declarar; forward medido, no proyectado.

## 4. Reglas (vigentes)

- Nada a main / GitHub / Kaggle. Solo rama local `local/carry-decoder-2026-11-21`.
- No se editan en su lugar los documentos verificados por la cadena (paquete, diseño, reportes H8, H1, H3, H3-1). Las correcciones van en documentos nuevos. (El reporte Gold y GOLD_PLAN.md son TUS documentos de trabajo — esos SÍ se actualizan.)
- C14/B7 — reconstruir, no meter literal. Veracidad técnica absoluta, cero datos sintéticos. Métrica de fase SIEMPRE % 2.0 con min(d, 2.0−d).
- NO tocar: `H8_REHACER_SUMMARY.md` (sin commitear, decisión de Elán); `REPORTE_PROTOTIPO_KERNEL24.md`, `verify_design_ring.py` (pre-existentes).
- Reporta en cada milestone en el log. Si un milestone se retrasa o un proceso muere, déjalo registrado en el log y en disco — no sigas en silencio.

## 5. Arranque

Trabaja en `/home/deamon/quantum-circuit-compilation-fase2/` (rama `local/carry-decoder-2026-11-21`, HEAD `c483d35`). Intérprete: `/home/deamon/quantum-circuit-compilation/.venv/bin/python`. **Log de ESTA corrida: `/home/deamon/carry-decoder/gold-opencode-4.log`** (los logs 1–3 quedan intactos como registro). Contexto en `/home/deamon/carry-decoder/gold/` (paquete, diseño, lecturas, REGLA_EVIDENCIA). Lee primero el reporte Gold, el log anterior (`gold-opencode-3.log`) y la derivación del Brujo (Parte 1 + Parte 2) antes de construir.
