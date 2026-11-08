# Validación de las ANF trazadas de V34 contra el circuito simulado (2026-11-08)

Script: `tools/validar_anf_v34.py`. Simula el prefijo de `data/invsqrt-sweep/invsqrt-public-v34.kmx` justo antes de cada uno de los
51 `Z_POW` listados en `rotaciones_anf.json` (el campo `line` es el índice 0-based del `Z_POW`; el qubit objetivo coincide con el campo `qubit`
en las 51) con 256 entradas x (aleatorias + bordes), lee el valor del qubit objetivo y lo compara con la ANF.

Resultado (256 tiros):
- H1 (todas las variables = valor actual del qubit nombrado): acuerdo ≈ 0.5 (mínimo 0.438) en casi todas; solo coinciden al 100 % 1 de 51 (rot. 49, q38, 1 monomio).
- H3 (qN con N<22 = bit de entrada x; N≥22 = valor actual): acuerdo mínimo 0.42 (q28 compuesto a x) y 0.438 (51 ANF). Tampoco coincide.
- La primera rotación (q28, ANF = [q50]) acuerda 0.875, no 1.0: q28 también cambia por CSWAP antes de su CX con q50.

Conclusión: con ninguna de las dos lecturas simples de las variables las ANF reproducen el valor del qubit objetivo. **La semántica de las variables de
`rotaciones_anf.json` (qué significa cada nombre qN en cada monomio) no está documentada y el script que generó el trazado no está en el repo.**
Mientras no se conozca, las ANF no están validadas, y los costos medidos sobre ellas (q28 C=217.6, q50 C=279.3) son costos de implementar esas listas, no de reproducir V34.

Pendiente: el script del trazado (o su definición de variables), o una validación independiente: obtener la forma algebraica en x de cada qubit objetivo
enumerando las 2^22 entradas con el simulador y aplicando la transformada de Möbius.
