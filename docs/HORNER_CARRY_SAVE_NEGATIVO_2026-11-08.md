# Horner carry-save (windowed): resultado negativo — 2026-11-08

Prototipo de la vuelta del Horner con acumulación carry-save (descomputación
por medición, estilo Gidney "Windowed quantum arithmetic" 2019). La raíz
diseña y prueba; Claude verifica. Rama `docs/horner-trunc-negativo-2026-11-08`.

## Contexto

- Base: logshift2, Q=139, 2,561 Toffoli, Q·C = 390,005 (verificador oficial PASS).
- Horner: 1,484 Toffoli (57.9%) = isub 531 + iadd 531 + 422 ANDs (init_and).
- En `_add_row_estrecha` el `del_and` YA es gratis (HMR + fixup CZ interno),
  así que la vuelta solo cuesta el `isub` (531). La única forma de bajarla
  es evitar el isub: acumular sin acarreo (carry-save) y convertir una sola
  vez al final.

## Medidas (A = Bennett, B = carry-save)

### A. Una fila, ida + vuelta

| Versión | Q | Toffoli | depth |
|---|---|---|---|
| A Bennett 1 fila ida+vuelta | 47 | 46 | 32 |
| B carry-save 1 fila (sin conversión) | 49 | 12 | 1 |

La fila carry-save evita el iadd/isub por fila (solo paga init_and + XOR
gratis). Script: `tools/horner_carry_save/proto_horner_windowed.py`.

### B. Un paso completo (t1 = c1 + u·c2, 13 filas)

| Versión | Q | Toffoli | depth |
|---|---|---|---|
| A Bennett 1 paso ida+vuelta | 90 | 278 | 125 |
| B carry-save 1 paso (ida, sin vuelta) | 108 | 149 | 35 |

B ahorra ~110 Toffoli por paso (la vuelta solo pagaría la conversión final,
~19), pero sube Q +18 por paso (el acumulador s+c es 2× el ancho del
target). Script: `tools/horner_carry_save/proto_horner_paso.py`.

## Estimación con Wallace (NO medida)

Con reducción Wallace, la ida carry-save sumaría 149 + ~92 + ~19 ≈ 260
Toffoli por paso, contra 278 de Bennett: ~18 Toffoli menos por paso, y a
~20 Toffoli por qubit eso se come con +18 Q. Rango estimado de score
360k–432k, que cruza la base (390,005): no es una mejora demostrada.

## Dos puntos sin medir (no son resultado medido)

1. El 260 es una suma (149 + 92 + 19), no una medición.
2. Falta cómo se desomputa el acumulador carry-save sin vuelta.

Ninguno cambia la conclusión, pero se dejan escritos para que no parezcan
resultado medido.

## Conclusión

El mecanismo funciona (la vuelta baja de 742 Toffoli), pero el score Q·C no
baja de 390,005 con claridad: el ahorro de Toffoli se lo come el aumento
de Q y el costo de la conversión. **Se detiene aquí** (criterio de parada
fijado con Claude). El ZIP vigente (390,005) queda intacto.

## Precisión de redacción (Claude)

"La raíz está exprimida" es demasiado fuerte. Lo comprobado es que el
recorte, el carry-save sobre el Horner y la traducción literal no bajan el
score. Quedan sin probar la normalización/desnormalización (484 Toffoli,
19%) y la reconstrucción completa estilo V34.
