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

## Forma exacta en x del qubit objetivo (enumeración de 2^22 entradas + Möbius), 2026-11-08
Script: `tools/anf_en_x_v34.py` (≈3–12 s por rotación; el simulador procesa 65,536 entradas en ≈0.13 s sobre un prefijo de 15,000 líneas).
Resultado para las primeras 9 rotaciones de q28 (las siguientes se interrumpieron para no agotar memoria):

| Rotación | Ángulo | Monomios exactos en x | Grado máx. | ANF trazada (monomios) |
|---|---|---|---|---|
| 0 | 7.6e-06 | 170 | 9 | 1 |
| 1 | 1.5e-05 | 1,792 | 14 | 2 |
| 2 | 3.1e-05 | 3,642 | 14 | 3 |
| 3 | 6.1e-05 | 11,414 | 15 | 4 |
| 4 | 1.2e-04 | 104,450 | 20 | 5 |
| 5 | 2.4e-04 | 344,788 | 20 | 7 |
| 6 | 4.9e-04 | 811,782 | 21 | 9 |
| 7 | 9.8e-04 | 1,820,406 | 22 | 11 |
| 8 | 2.0e-03 | 2,198,494 | 21 | 11 |

Lectura:
- La función que ve cada `Z_POW` es una función **densa** de x (hasta millones de monomios, grado hasta 22), no un polinomio de pocos términos. Es el valor de qubits producidos por aritmética (acarreos), no por ANDs de bits de x.
- Por tanto las listas "compuestas a x" (`rotaciones_q28_en_x.json`: 336–406 monomios; `intermedios_q28_to_x.json`: q50 = 7 monomios) **no son la función real en x**: p. ej. q50 al comienzo ya tiene 170 monomios exactos en x. Las ANF trazadas (1–105 monomios) son expresiones sobre qubits intermedios, no sobre x.
- Consecuencia: implementar las rotaciones como polinomio directo en x no es viable (cientos de miles a millones de monomios por rotación). El costo de V34 está en calcular esos valores intermedios con aritmética reversible (≈830 de sus ≈1,050 Toffoli en el tramo central), y esa parte no se reduce a ANDs compartidos sobre x.
