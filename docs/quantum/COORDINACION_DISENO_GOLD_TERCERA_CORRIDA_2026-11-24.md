# Coordinación de diseño — Tercera corrida Gold (rediseño de Q + M6/M9 reales)

**GO de Elán:** 2026-11-24 12:18 CST — "Yo te había confirmado lo de Quantum, lo de Gold sí se va con M6/M9 reales."
**Coordinación:** Brujo → Programación, 2026-11-24 12:24–12:32 CST (mensajes 15074441 y 9988e5e1).
**Base:** segunda corrida Gold, HEAD Kali `c483d35`, reporte `c295511a…` (192 l.), Q=15,432, T=149,796, M11 FAIL (102,400/102,400 errores de valor), M12 no ejecutado. T bajo presupuesto (149,796 < 367,398); falta Q y los bloques reales.
**Estado al 2026-11-26:** el despacho al agente está BLOQUEADO hasta la derivación completa de la opción (b) (compromiso 15:00 del 24 nov, incumplido sin reporte; sigue abierta — ver `ESTADO_QUANTUM_2026-11-26.md`). Borrador del prompt: `PROMPT_GOLD_TERCERA_CORRIDA_BORRADOR.md` (en este mismo directorio).

## 1. El carry es un BIT, no un elemento de campo

En el código real, P(g) = `zero_flag(D)` (1 si D==0 en el nodo). `carry_next` pone `flag(g−1) = [marker(g−1)==0] ∧ flag(g)` con sándwich X(pole)…X(pole); F_16 = pole_16 verdadero. La recurrencia es una DEFINICIÓN, no un teorema. **El M7 se construye sobre esta semántica de bit** (zero_flag + cswap + normalización), NUNCA sobre la fórmula del reporte H8 (P_principal = coeficiente de r_g): esa fórmula es FALSA bajo sus propias definiciones — contraejemplo verificado: (r_{g−1}, r_g, r_{g+1}) = (0, 3, 6) con q_g=2 cumple 2·3 ⊕ 6 = 0 pero la fórmula exige 3 = 0. Detalle en `DERIVACION_CARRY_PARTE1_CODIGO_2026-11-24.md`.

## 2. El marker ES el mecanismo de reutilización in-place

El marker = `combine(words[grupos[g−1]['word']: +2])` — el registro N del grupo g−1 leído durante el RETORNO del grupo g, en sus valores FORWARD (el retorno va 16→5 y el grupo g−1 aún no se descomputa). Equivalencia derivada del código: [marker(g−1)==0] ⟺ pole_{g−1} ∨ [N_final(g−1)==0]. **El rediseño de Q debe conservar la disciplina de orden del retorno (16→5) y la colocación del marker** — ahí es donde viven los 840 qubits de S reutilizados in-place. No se toca el orden del retorno sin re-derivar la equivalencia.

## 3. La corrección del carry se reduce a (A) y (B) — punto exacto pendiente

Carry correcto ⟺ (A) pole_g=0 ⟹ pole_{g−1}=0 (los polos forman un sufijo en g) Y (B) pole_g=1 ∧ [N_final(g−1)==0] ⟹ pole_{g−1}=1. Son propiedades de los polos VERDADEROS de la ejecución real (función del síndrome), no identidades algebraicas. La enumeración H8 (0 fallos/100,000 en el modelo) y el notebook (0 errores/102,400 tiros) son consistentes con que (A) y (B) valen para síndromes válidos; el conjunto de fallo es exactamente donde (A) o (B) se viola. **La prueba de (A)/(B) desde el oráculo (`model.py` l.136–146, división de Hermite) es lo que falta.** Si (A) o (B) falla, el hallazgo viene con el contraejemplo exacto y el diseño debe manejarlo — no se construye encima de una (A)/(B) sin probar.

## 4. Rediseño de Q — restricciones e invariantes (no un mapa qubit por qubit)

El diseño fija restricciones, no una asignación concreta (eso sería inventarla sin construirla):

- (a) Los 840 qubits de S son el conjunto de trabajo y NUNCA se duplican — extracción/síntesis/conversión trabajan in-place sobre S.
- (b) Un solo pool acotado de temporales con free explícito en el punto en que el valor muere (la segunda corrida ya bajó de 17,149 a 15,432 con un pool de 52 temporales y frees — piso de partida, no techo).
- (c) Disciplina de orden del retorno 16→5 y colocación del marker intactas.
- (d) Ningún `alloc_qubits` dentro de un bucle sin su `free` en la misma iteración.

La asignación concreta (qué temporal va dónde) la calcula el agente bajo estas restricciones y se verifica por medición (Q ≤ 901 + disciplina del pool). Si el agente no puede cerrar Q con el pool acotado, lo reporta con el pico medido y dónde vive, no lo esconde con índices monotónicos.

## 5. M6 y M9 reales, sin atajos

Segunda corrida: `build_euclid_level` era un no-op (el descenso Euclides NO implementado) y el scan era UNA escalera representativa (12 T medidos vs 44,275 T esperados para 4,025 puntos). Tercera corrida: M6 = descenso Euclides extendido real con cswaps para predicados de hueco y dot cache (costo exacto H3-1: 54,426 T ida / 54,947 T vuelta; si no cierra contra ese residual, se reporta la brecha con el número, no un no-op). M9 = barrido Chien/Forney real de 4,025 puntos desrollado (evaluación A(β)/B(β), residuo ω(β)/σ'(β), CCZ con máscaras; 44,275 T esperados; la escalera de 1 representante queda PROHIBIDA). Los niveles exactos y la estructura del bucle los decide el agente desde el diseño de Fase 2 corregido (H1) + H3-1, que van como contexto en el despacho.

## 6. Criterios de aceptación medibles (REGLA_EVIDENCIA)

- M11 PASS con el verificador oficial (102,400 tiros, 0 errores de valor y 0 de fase, o dentro del presupuesto R).
- Q objetivo 901; T ≤ 367,398 (total de diseño).
- Los 10 circuitos con SHA256 distintos (dos iguales = stub).
- Ningún bloque placeholder sin declarar; forward medido, no proyectado.
- Cadena: Programación construye → Datos supervisa → Brujo verifica → Auditor revisa → Elán decide. Nada a main/GitHub/Kaggle sin GO de Elán.
