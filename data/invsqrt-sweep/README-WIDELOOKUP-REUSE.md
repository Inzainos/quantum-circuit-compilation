# WideLookup con reuso — invsqrt (para revisión de Claude)

Fecha: 2026-11-08. Rama: `local/invsqrt-widelookup-reuse-2026-11-08`.
Autor del trabajo: Mole (chat experto invsqrt). Para que Claude lo revise.

## Qué es

El mejor respaldo de invsqrt que tenemos hoy, después de logshift2 (390,005).
Arquitectura: normalización (logshift2) + lookup ancho (B|S|C2, 84 bits)
+ Horner + barrel shift + fase por Z_POW + desnormalización.
Pasa por tres tuberías: WideLookup, ligera/pesada, split con reuso.

## Resultados medidos (simulador kickmix, NO verificador oficial — los .kmx
## tienen varios registros, el verificador exige exactamente un registro 'x')

| Variante | Q | Toffoli-like | Error fase máx | Score est. |
|---|---|---|---|---|
| WideLookup reuso b=6 (ESTE, seguro) | 239 | 1,665 | 4.337e-09 (32 tiros) / 7.451e-09 (bordes) | ~519k |
| WideLookup reuso b=5 (margen delgado) | 239 | 1,619 | 2.221e-08 (32 tiros) / 7.451e-09 (bordes) | ~508k |
| WideLookup reuso b=7 | 239 | 1,839 | 2.693e-09 | ~560k |
| WideLookup reuso b=8 | 239 | 2,289 | 2.591e-09 | ~668k |
| WideLookup simple b=6 (sin reuso) | 267 | 1,521 | 4.337e-09 | ~541k |
| logshift2 (entrega actual) | 139 | ~2,100 | 0.792 (peor) | 390,005 |

Tolerancia de fase: 5.96e-08 vueltas. C = Toffolis + T/4 (T ~2,020 por
síntesis de los 76 Z_POW). Score = Q × C (estimado, no oficial).

## La idea clave (reuso manual)

El builder NO reusa los qubits que libera `del_lookup`. El split divide el
lookup en dos tuberías (C2 primero, luego B|S) y libera C2 tras el MAC 1.
`lookup_grupos_widelookup_reuse.py` reusa a mano los 28 qubits limpios de
regC2 para V (28 reusados + 10 nuevos). Eso baja Q de 267 a 239.
Sin reuso, el split es PEOR (~579k) por el QROM extra.

## Archivos

- `lookup_grupos_widelookup_reuse.py` — el mejor (b por env BSEG, minimax por env MINIMAX=1).
- `lookup_grupos_widelookup_b.py` — WideLookup simple, b por env BSEG.
- `lookup_grupos_widelookup_split.py` — split sin reuso (peor, referencia).
- `minimax_tablas.py` — prueba minimax/Chebyshev de tablas.
- `inventario_ideas.py` — inventario de las 18 ideas del MoE + estimación radix-4.
- `invsqrt-widelookup-reuse-b6.kmx` — circuito b=6 (el seguro).
- `invsqrt-widelookup-reuse-b5.kmx` — circuito b=5 (mejor score, margen delgado).

## Ideas que se murieron hoy (no reintentar sin evidencia nueva)

- **Minimax/Chebyshev de tablas**: en clásico bajaba el error 20x, pero
  FALLA en casos borde (x=1: 9.015e-07, x=3: 1.548e-07 para b=5; b=6
  bordes 1.192e-07; b=4 bordes 6.907e-06). Causa: minimax tiene error
  no-cero en t=0 (borde del segmento) donde Taylor es exacto; los x
  chicos caen justo en t=0.
- **Radix-4 (multiplicación por ventanas)**: estimación clásica MAC b=6:
  shift-and-add 186 ANDs vs radix-4 ~208 ANDs (+22). El mux y precalcular
  3A cuestan más de lo que ahorran a estos tamaños.
- **KAK/Cartan**: no aplica (es para unitarias de 2 cúbits; CX es gratis
  en nuestro score; no baja Toffolis ni T).
- **Polinomios de Fase**: full10 ya falló por acarreo (3.125e-06). Además
  el T-depth no afecta nuestro score (C es total, no profundidad), y en
  kickmix el Toffoli se cuenta como 1 Toffoli, no se tritura en T.
- **CSD**: no aplica (S/C2 son registros cuánticos, no constantes).
- **Monomios del valor / bandera / dos tuberías**: el acarreo es el
  problema duro (ver MEMORY.md). Dos tuberías pasa pero ~1.2-1.4M.

## Qué le pido a Claude que cheque

1. Que el reuso manual de qubits sea correcto (que regC2 esté en |0⟩
   tras del_lookup y que V lo reuse sin corromper nada). x restaurada
   True en todas las pruebas, pero una segunda mirada no sobra.
2. Si ve una forma de bajar Q de 239 hacia 139 (el gap con logshift2)
   sin romper la fase, o de bajar los Toffolis del Horner.
3. Si el minimax restringido (exacto en t=0) valdría la pena, o si hay
   otra forma de hacer b=5 seguro / b=4 viable.
4. Cualquier error en los números de arriba (Q, Toffolis, errores, scores).

## Entorno para reproducir

Intérprete: `/home/hatch/workspace/py313/python/bin/python3.13`
PYTHONPATH: `/home/hatch/workspace/qcc-data/kickmix:/home/hatch/workspace/qcc-zip-final/src:/home/hatch/workspace/qcc-zip-final/verifiers/invsqrt`
Ejemplo: `BSEG=6 /home/hatch/workspace/py313/python/bin/python3.13 lookup_grupos_widelookup_reuse.py --tiros 32`
