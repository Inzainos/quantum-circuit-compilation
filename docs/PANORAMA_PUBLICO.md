# Panorama público de la competencia (leído el 2026-11-04 en repos públicos de otros participantes)

Fuentes (solo lectura, no se usó su código): nasir26/vqcc-kaggle (docs/RULES.md, docs/NOTES.md, docs/*_anatomy.md),
wahyurahmaniar/verifiable-quantum-circuit-compilation, zjukop3/google-quantum-circuit-compilation-2026-support,
somfieao/kickmix-compiler. Las cifras son de terceros; las reglas son un resumen de un participante, no el texto oficial.

## Puntaje
Score = (Π costo_ref/costo)^(1/3). Costos: invsqrt Q·C (C = Toffolis + T/4, rotaciones en T); dqi R(ε+)·Q²·T; dfthcsos λ_eff·T·Q (Q,T de todo el block-encoding).
Referencias: invsqrt 2,076,774 (Q=260, C=7,988); dqi ≈2.44e13 (Q=1893, T=5.73M); dfthcsos 3.3556e9 (Q=730, T=93,237).
Tu score 1.61 = (4.18·1.0·1.0)^(1/3). Frontera pública ≈ 23.7–24; LB top ≈ 26.1 (28.8 visto hoy).
Importante: cualquier fallo en cualquier split invalida TODA la entrega; los tiros fallidos solo se toleran en dqi (cada uno ≈ +0.46 % de costo).

## Qué hacen los demás
| Tarea | Ratio público | Q / T | Idea central |
|---|---|---|---|
| invsqrt | 20.2–20.65 | Q 62–63, T medio ≈1,334 (nuestro: 177 / 2,561) | semilla por tabla (LUT) + Newton, "direct polynomial phasing", dos fusiones 3→2 de ANDs; usa todo el margen de error (0.9993 de la tolerancia); rotaciones no se pueden abaratar |
| dqi | 59–63 | Q 889–897, T 407–440k (nuestro: 1888 / 5.71M) | decodificador tipo Schur (jday96314/QuantumAI → Alex Chilton → SomeJoint), 840 de síndromes + ≈52 de trabajo, palabras de 24 bits, multiplicador GF(2^12) de 42 ANDs (evaluación/interpolación sobre GF(8): 7 puntos × 6 ANDs), GF(2^24) de 99 ANDs, inversos en torre, fase vía producto Clifford, banderas de polo/acarreo con poda de eventos raros |
| dfthcsos | 9.8–10.6 | Q 428–430, T ≈15.7–16.4k (ref 730 / 93,237) | factorización nueva (R,B,C) = (9,143,40) o (8,143,60) de marculera/SomeJoint, palabras de 8 bits, lookups de 5 palabras, cargadores ANGLE por forma normal algebraica con productos emparejados; λ_eff ≥ 46.79 es piso |

## Palancas concretas para nosotros (implementar por nuestra cuenta)
1. DQI, aritmética en torre GF(((2^3)^2)^2)/GF(8)^4: multiplicación 63→54 o 42, inverso 315→≈77, división 378→≈132; cambios de base son redes de CNOT (gratis). Estimado de terceros: −26 % de T (≈1.35×) sobre el EEA actual. Sin medir aquí.
2. DQI, fusionar swap_a_and_b con índices alternantes (−4…7 %) y sacar el control del multiplicador (−6…8 %).
3. DQI, rediseño tipo Schur con estado de O(1) palabras: único camino al orden de magnitud (≈60× en el score de dqi). Requiere estudiar el diseño clásico (jday96314/QuantumAI) y reescribirlo.
4. invsqrt: bajar de Q=177 a ≈62 eliminando los registros de coeficientes (fase directa por tabla) y usar el margen de error completo.
5. dfthcsos: necesita el .npz oficial y una factorización nueva; es una tarea de optimización clásica aparte.

## Calendario
Corte del hito 2026-11-20 (requiere notebook público); entrega final 2027-01-20; 5 envíos/día; hasta 2 finales.
