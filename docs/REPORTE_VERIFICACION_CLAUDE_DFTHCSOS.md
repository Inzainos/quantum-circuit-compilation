# Verificación de las correcciones de Claude + pool 7 qubits + perfil dfthcsos

**Fecha:** 2026-11-09 ~12:00. **Por orden de Elán (WhatsApp).** Relevo de
Claude leído de la rama (915e57f). **No se tocó main ni el ZIP.** Todo el
trabajo es scratch en `~/workspace/qcc-data/dqi-perfil/` (salvo el respaldo
a Drive, que ya está hecho). El verificador DQI completo no corre en esta
caja; validación por construcción y conteo con kickmix.

## 0. Resumen ejecutivo

| Punto de Claude | ¿Cuadra? | Medición |
|---|---|---|
| Pico 1,942 vivos, Q=1,949, T bm_forward 185,034 | **Sí** | Confirmado por mis mediciones (pico_bm_fino.py). |
| Desglose 80 transitorios, bloque alpha 42 qubits | **Sí** | Coherente; medido. |
| "−29" era empaquetado base-3 (no flags identificables) | **Sí, la aritmética cuadra** | log₂3 = 1.585 bits/ronda × 70 = 111 qubits; ahorro 140−111 = 29. p/t mutuamente excluyentes (3 estados/ronda). No es palanca barata (conversión en cada ronda, ida y vuelta). Descartada, igual que yo. |
| Suelo del barrido 1,934 | **Sí, medido** | Pico del scan Q=1,934 (ver §2). Fusión mul+inv solo bajaría Q de 1,949 a 1,934 (−15, ~1.5% DQI, ~0.5% geomean). |
| Pool 7 qubits (1,949 vs 1,942 vivos) | **Sí existe, pero NO recuperable por reordenar** | Probé el reordenamiento más directo (un solo registro en `_flags`): delta_Q=0, delta_T=0. Correcto (n=6 OK), pero no recupera nada. El hueco es del alocador interno (andamios mul/inv), no de mis alloc/free. |
| dfthcsos: razón actual y perfil | Ver §3 | Entrega (sample): ratio **1.00583×**. Candidato verificado −0.58% NO en entrega: ratio **1.01169×**. Frontera 9.78×. |

## 1. Empaquetado base-3 (la corrección del "−29")

Claude aclara: en su doc `DQI_Q_ANALISIS_2026-11-07.md` el "−29" era una
idea de EMPAQUETADO, no 29 qubits-flag. Verificación:

- p y t son mutuamente excluyentes: por ronda hay 3 estados —
  (p=1,t=0) replace, (p=0,t=1) retain, (p=0,t=0) cero. Nunca p=t=1.
  (Código: `_flags` hace `t = nz xor p`, y `nz = [D!=0]`; si D=0,
  p=t=0; si D≠0, exactamente uno de p,t es 1.)
- 3 estados = log₂3 = **1.58496 bits por ronda**.
- 70 rondas × 1.58496 = **110.95 ≈ 111 qubits** (vs 140 con 2 bits/ronda).
- Ahorro = 140 − 111 = **29.05 ≈ 29 qubits**. La aritmética cuadra.

**Conclusión: correcta la aritmética, y correcta la decisión de descartarla.**
Empaquetar 70 tríadas en base 3 exige aritmética de conversión
(codificar/decodificar el dígito base-3) en CADA ronda, y las banderas se
leen y escriben en la ida y en la vuelta (forward guarda, reverse consume).
El costo en Toffolis de la conversión comería el ahorro en Q, y no es una
palanca barata. Claude la descarta igual que yo. No hay nada que hacer ahí.

## 2. Suelo del barrido: 1,934 (medido, confirma a Claude)

Medición: construí los registros vivos tras bm_forward (S 840 + sigma 432
+ tau 432 + d 8 + H 12 + flags 140 = 1,864) SIN correr BM (para que el pico
del BM no enmascarara el del scan), luego omega_fwd y el scan completo
(4,095 posiciones). Resultado:

| Etapa | Q (pico) | Vivos al final |
|---|---|---|
| Base (registros vivos) | — | 1,864 |
| omega_fwd | 1,906 | 1,864 |
| **scan** | **1,934** | 1,864 |

- **Pico del scan = 1,934. Confirmado.** (El andamio de TowerInv3 es 18
  qubits, medido en aislamiento; registros del scan 49; 1,864+49+18=1,931
  por componentes, 1,934 medido — 3 qubits de transitorios adicionales.)
- **Consecuencia (confirma a Claude):** aunque se fusione mul+inv y el BM
  baje 42 qubits, Q solo bajaría de 1,949 a 1,934 (−15 qubits), porque el
  scan pone el suelo en 1,934.
  - Q 1,949→1,934: (1,949/1,934)² = 1.0156 → DQI ~+1.5% (6.77×→~6.88×),
    geomean ~+0.5% (3.31×→~3.33×). Techo de la fusión mul+inv: ~0.5% en
    el geomean. No vale el rediseño por tan poco, salvo que se quiera.

## 3. Los 7 qubits del pool: probado, NO recuperable por reordenar

**Hipótesis de Claude:** los 7 qubits de sobrecarga del pool (Q=1,949 vs
1,942 vivos) se recuperarían reordenando alloc/free. **Probado: no.**

### 3.1 Experimento

Cambio (scratch, `pool-test/dqi_bm_stage_v1_pool.py`, NO en el repo): en
`_flags`, alocar lad+z+nz como UN solo registro de 12 qubits (en vez de
10+1+1), para que al liberarse sea un chunk contiguo de 12 que P (12)
pueda reutilizar exactamente. El cambio no altera la lógica (mismos
qubits, mismo orden de operaciones).

### 3.2 Resultado medido

- **Correctitud (n=6, simulador): OK.** S restaurado, sigma/tau/d/H
  restaurados. Q=333, T=7,680 (igual que el baseline).
- **Escala completa (n=70, bm_forward): Q=1,949, T=185,034, live=1,864.
  delta_Q=0, delta_T=0.** El cambio NO recupera ningún qubit.

### 3.3 Por qué no se recupera (medido)

El hueco de 7 qubits ya está presente tras la ronda 0 (Q=323 con live=238;
el pico de vivos en la ronda 0 es 316; 323−316=7) y es CONSTANTE (7 tanto
a n=6 como a n=70). No es acumulación por ronda. El hueco viene del
alocador interno de kickmix con los andamios de `init_gf2_mul` y
`ValueInv` (18 qubits de andamio en el bloque alpha), no de los
alloc/free que yo controlo en `_flags`/`_dclear`. Reordenar mis
allocaciones no lo mueve. Para recuperarlo habría que tocar el alocador
de kickmix o los multiplicadores/inversores subyacentes, que es otro
nivel de intervención y no es "casi gratis".

**Conclusión: la palanca de los 7 qubits del pool NO existe en la práctica
para el DQI.** Q se queda en 1,949. El efecto medido es 0.

## 4. dfthcsos: razón actual contra la referencia y perfil

### 4.1 Números verificados (oficial)

| | Entrega actual (sample) | Candidato verificado (NO en entrega) | Frontera pública |
|---|---|---|---|
| Score | **3,355,599,588** | **3,336,160,975** | (8,143,60) T=16,366, Q=430 |
| Q | 730 | 730 | 430 |
| T (Toffoli) | 93,237 | 93,237 | 16,366 |
| λ_eff | 49.301 | 49.016 | — |
| error_2 | 18.640 mHa | 19.371 mHa | — |
| error_1 | 0.003185 | 0.003340 | — |
| Veredicto | PASS (sample) | **PASS** (oficial, 254,464 shots) | ~9.78× |
| Ratio vs referencia | **1.00583×** | **1.01169×** | ~9.78× |

- **Referencia (derivada del ratio 1.00583×):** 3,355,599,588 × 1.00583
  = **3,375,162,734**. Es la referencia contra la que se calcula el ratio;
  el ratio 1.00583× viene del trabajo verificado previo (no la re-derivé
  de Kaggle en este turno).
- **Candidato:** mejora −0.58% vs el sample (19,438,613 menos). Su ratio
  sería 3,375,162,734 / 3,336,160,975 = **1.01169×**. Geomean con el
  candidato: ~3.313× vs ~3.307× con el sample (cálculo con invsqrt 5.309×
  y DQI 6.77×; el Kaggle real es 3.31949 — la diferencia es redondeo de
  los ratios). **El candidato NO está en la entrega** (pendiente decisión
  de Elán desde 2026-11-08).
- **Frontera (clduab11, forma (8,143,60) + compilador full-XOR, J=5):**
  T=16,366, Q=430, ~9.78×. La brecha es casi toda T (93,237→16,366, 5.7×)
  y Q (730→430, 1.7×). Esa forma hay que ENTRENARLA (~46 h), no truncar
  la actual: el refit (65,60,60) está agotado (tope ~−0.6%).

### 4.2 Perfil de costo del dfthcsos actual (T=93,237)

Del `summary.json` verificado del candidato (mismos T/Q que el sample):

| Componente | Toffoli | % de T |
|---|---|---|
| Ángulos (QROM + rotaciones, 2 pasadas × 39,740) | 79,480 | 85.2% |
| Heurística (state prep + Givens) | 13,757 | 14.8% |
| · inner_state_prep | 9,461 | 10.1% |
| · givens_rotations | 3,450 | 3.7% |
| · outer_state_prep | 846 | 0.9% |
| **Total** | **93,237** | 100% |

- Qubits: 730 (persistentes 186 + temporales 544).
- El cuello es el bloque de ángulos (85% de T). Para acercarse a la
  frontera (T=16,366) hay que cambiar la FORMA (entrenar (8,143,60)),
  no afinar la actual.

### 4.3 Estado y siguiente paso (para Claude)

- El DQI está cerrado en lo barato: q-d muerto (ε≈21%), flags no
  identificables, base-3 descartado, pool 7 no recuperable, fusión
  mul+inv con techo ~0.5% geomean. ZIP vigente (Q=1,949, T=784,172)
  se queda.
- El dfthcsos es donde está el margen grande (1.00583× vs 9.78× de la
  frontera), pero exige entrenar la forma pequeña (~46 h), no un ajuste.
- Decisión pendiente de Elán: meter el candidato −0.58% en la entrega,
  o ir directo a entrenar la forma (8,143,60).

## 5. Archivos

- `~/workspace/qcc-data/dqi-perfil/pico_scan.py` — medición del pico del
  scan (falló el monkey-patch; la medición buena es el script inline de
  §2, reproducido en el reporte).
- `~/workspace/qcc-data/dqi-perfil/pool-test/dqi_bm_stage_v1_pool.py` —
  BM con `_flags` de un solo registro (scratch).
- `~/workspace/qcc-data/dqi-perfil/pool-test/pool_test.py`,
  `pool_correctitud.py` — medición y correctitud del pool.
- `~/workspace/qcc-data/dqi-perfil/REPORTE_VERIFICACION_CLAUDE_DFTHCSOS.md`
  — este reporte.
- Respaldo Drive: `Respaldos Fractal Core / quantum-circuit-compilation/`
  (4 archivos, verificado: dqi-1949.kmb 624,814,210 B, dqi.kmb
  631,663,465 B, bm_forward.kmb 29,952,664 B, zip 103,403 B).
