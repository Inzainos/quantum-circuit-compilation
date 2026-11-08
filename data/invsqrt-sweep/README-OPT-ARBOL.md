# Tubería de monomios óptima (invsqrt) — para revisión de Claude

Rama: `local/invsqrt-opt-arbol-2026-11-08` (desde main `3dc0c58c`).
Fecha: 2026-11-08. Autor: Mole (Muse) + Elán Zainos Corona.

## Qué es esto

Nuestra propia tubería de monomios para invsqrt (2/sqrt(x) como fase),
optimizada con todo lo que medimos el 2026-11-08. Es un circuito VÁLIDO
(fase pasa, x restaurada, ancillas limpias, validado multi-semilla),
pero todavía caro: **score ~2.91M** vs logshift2 (390,005, la entrega
actual) y vs V34 público (97,921). NO es reemplazo de la entrega; es
nuestra mejor tubería propia y la base para seguir optimizando.

## Resultados medidos (simulador kickmix, 8 shots + validación multi-semilla)

| Versión | Q | Toffoli-like | Depth | Fase max | Score est. |
|---|---|---|---|---|---|
| segmentos (base) | 273 | 13,159 | 4,409 | 2.370e-09 | ~3.68M |
| árbol (Hamming weight) | 415 | 7,309 | 1,714 | 2.370e-09 | ~3.17M |
| **opt (ramas optimizadas)** | **415** | **6,677** | **1,417** | **2.374e-09** | **~2.91M** |

Validación multi-semilla (5 semillas × 64 shots = 320, incl. x=1,2,3,2^21−1):
0/5 fallan en segmentos, árbol y opt. Fase max 7.45e-09–1.20e-08
(tol 5.96e-08), x restaurada, ancillas 0.

## Archivos

- `lookup_grupos_fase_valor_segmentos.py` — base: monomios en paquetes
  por peso, originales primero, espejos al final, banderas.
- `lookup_grupos_fase_valor_arbol.py` — árbol de peso Hamming (Wallace,
  Boyar–Peralta 2008) en vez de conteo por monomio (iadd/isub).
- `lookup_grupos_fase_valor_opt.py` — **mejor versión**: cada familia es
  una rama con su optimización (B=XOR directo sin árbol, 1 monomio/peso;
  C2*t2=árbol en pesados, XOR en ligeros; S*t=siempre árbol).
- `test_arbol_hamming.py` — prueba aislada del árbol (n=7/13/49, conteo
  exacto, 0 sucios tras deshacer).
- `validar_hmr_multisemilla.py`, `validar_arbol_multisemilla.py`,
  `validar_opt_multisemilla.py` — validación multi-semilla (5 semillas).
- `investigacion-ideas-hmr-monomios.md` — informe de investigación
  (492 líneas, 14 fuentes): por qué el HMR sobre y1 de logshift2 es un
  callejón sin salida (el fixup cuesta la ANF de f(x), densa para y1),
  y por qué el contador era el cuello de la tubería.
- `invsqrt-opt.kmx` — circuito óptimo (Q=415, 6,677 Toffolis).
- `invsqrt-opt-arbol.kmx` — circuito árbol (Q=415, 7,309 Toffolis).

## Cómo reproducir

```bash
export PYTHONPATH=/home/hatch/workspace/qcc-data/kickmix:/home/hatch/workspace/qcc-zip-final/src
python3.13 lookup_grupos_fase_valor_opt.py --tiros 8 --corte -30
python3.13 validar_opt_multisemilla.py
```

## Notas para el revisor (Claude)

1. El HMR vectorial del ACC es VÁLIDO aquí (multi-semilla 0/5 fallan)
   porque el ACC es función lineal de ANDs (ralo). El HMR sobre y1 de
   logshift2 NO lo es (ANF densa, millones de monomios) — eso lo explica
   el informe de investigación (paper kickmix arXiv:2610.23832 §II.1).
2. El verificador oficial NO puede correr estos .kmx directo (13 registros;
   exige un solo registro 'x'). La validación es por simulador multi-semilla.
   Para verificar oficial habría que convertir a un solo registro 'x'.
3. El piso honesto de esta tubería es ~1M (los 748 monomios fijan ~720 ANDs
   + conteo + tablas). No bate logshift2 (390k). El camino a 97,921 sigue
   siendo V34 o mejorar logshift2.
4. Ideas pendientes del informe: compartir ANDs jerárquico (XAG, ~10–20%),
   y el árbol ya está aplicado. El Q subió 273→415 por el árbol (todos los
   bits-monomio vivos a la vez); si se puede bajar Q sin subir C, el score
   mejora directo (score = Q×C).
