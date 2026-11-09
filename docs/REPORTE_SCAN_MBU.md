# Scan MBU del DQI: el −23 Toffoli/posición ya está realizado — 2026-11-08

## Veredicto

**El ahorro teórico de −23 Toffoli/posición del scan MBU NO es un ahorro
adicional: ya está realizado en el código actual.** El scan cuesta 98.0
Toffoli/posición, y una baseline correcta con descomputo Bennett cuesta
121.0 Toffoli/posición. La diferencia (23) es exactamente el MBU que el
código ya aplica (`del_and` + `TI.undo()`). No hay más MBU que aplicar en
el scan: todos los descomputos ya son por medición y todos los costos
restantes son cómputos hacia adelante, donde el MBU no aplica.

**Números reales (sin cambio):** Q=1,949, T=784,172, ratio DQI 6.77x,
geomean 3.31x. La proyección con scan MBU (T=689,987, 7.69x, 3.45x) queda
**invalidada**. Las proyecciones combinadas con BM in-place que incluían
el scan MBU (22.10x/4.91x y 36.73x/5.82x) también quedan invalidadas en
su parte de scan; el BM in-place solo sigue en 19.45x/4.70x (Q≈1,150) y
32.32x/5.57x (Q≈892).

## 1. Descomposición del 98 Toffoli/posición (medido)

Código: `src/dqi_decoder_v1.py::build_scan_inv` (con `TowerInv3`).
Medido con `scan_mbu_medicion.py` (1, 4 y 8 posiciones, exacto en los tres):

| Componente | Toffoli/posición | Naturaleza |
|---|---|---|
| TowerInv3 forward (w = dd⁻¹) | 75 | cómputo hacia adelante |
| Escalera f = [s==0] (11 init_and) | 11 | cómputo hacia adelante |
| Fase g_a = f AND u_a (12 init_and) | 12 | cómputo hacia adelante |
| Escalera f: 11 del_and | 0 | MBU (ya presente) |
| Fase g: 12 del_and | 0 | MBU (ya presente) |
| TowerInv3 undo | 0 | MBU (HMR + fixup, ya presente) |
| Lineales (CX, X, push/pop_condition) | 0 | Clifford |
| **Total** | **98** | |

Mediciones de soporte (todas en `scan_mbu_medicion.py`):
- `init_and + del_and` = 1 Toffoli-like → **del_and = 0**.
- `init_and + init_and` = 2 → el segundo init_and cuesta 1 (no es gratis).
- TowerInv3 forward solo = 75; forward+undo = 75 → **undo = 0**.

## 2. El MBU ya está presente: baseline Bennett = 121/posición

Se construyó una variante Bennett correcta del scan (descomputo con
Toffoli propio, ver §3 por qué NO con re-init_and) y se midió:

| Variante | T/posición | T total (4,095 pos) |
|---|---|---|
| Real (MBU, `del_and` + `TI.undo()`) | 98.0 | 401,310 |
| Bennett (Toffoli propio para f y g) | 121.0 | 495,495 |
| **Ahorro MBU ya realizado** | **23.0** | **94,185** |

El ahorro de 23 es exactamente el que el doc
`docs/OPTIMIZACION_DQI_SCAN.md` ("Próximas optimizaciones" 1 y 2) propone
como futuro. Pero el propio doc `docs/PLAN_SCAN_OPT_MBU.md` §1 ya lo dice:
**"Descomputación por medición ya presente: `del_and` en kickmix es HMR +
CZ condicionado → 0 Toffoli. Por tanto los 11 del_and de la escalera y los
12 del_and de fase ya son 0 Toffoli."** El −23 del perfil es un
doble conteo: el 121 → 98 ya ocurrió cuando se adoptó `del_and`.

## 3. Hallazgo: `init_and` NO es autoinverso en kickmix

Medido (simulador kickmix, un AND a=1, b=1, t=0):

| Secuencia | t final | fase | T |
|---|---|---|---|
| init_and | 1 | 0 | 1 |
| init_and + init_and | **1** | 0 | 2 |
| init_and + Toffoli (`multi_controlled_x`) | 0 | 0 | 2 |
| Toffoli + Toffoli | 0 | 0 | 2 |
| init_and + del_and | 0 | 0 | 1 |

`init_and` es un AND de fase relativa (tipo Margolus): calcula bien el AND
pero **re-aplicarlo NO lo deshace** (deja el bit en 1). El descomputo
correcto es `del_and` (MBU, 0 T) o un Toffoli propio (1 T). Por eso la
primera variante Bennett que escribí (re-init_and) salió rota: dejaba 11
temporales sucios en la escalera y daba fase incorrecta. La variante
Bennett válida usa `multi_controlled_x` y es correcta (ver §5).

Consecuencia: en kickmix **no existe** un descomputo Bennett barato para
ANDs; `del_and` (MBU) es la única vía gratuita y ya se usa en todo el scan.
El "121 con uncomputo completo" del doc nunca fue una baseline real en
kickmix con `init_and` (con re-init_and el circuito queda roto, no solo
más caro).

## 4. Costo del fixup por temporal (por su ANF)

La lección del invsqrt (HMR kick) dice que el costo del fixup = el costo
de la ANF de la función guardada en el qubit medido. En el scan, todos los
fixups son CZ (gratis, 0 Toffoli):

| Temporal | Función guardada | ANF | Fixup | Costo |
|---|---|---|---|---|
| lad[i] (escalera f) | AND de 2 bits (lad[i-2] & s[i]) | grado 2, 1 monomio | 1 CZ | 0 T |
| f | AND de 2 bits (lad[9] & s[11]) | grado 2, 1 monomio | 1 CZ | 0 T |
| g_a | AND de 2 bits (f & u_a) | grado 2, 1 monomio | 1 CZ | 0 T |
| w (12 bits, torre) | dd⁻¹ (función compleja) | — | HMR(w) + `_phase_terms`: CZs condicionadas a los bits medidos | 0 T |

Cada `del_and` es un AND de grado 2, así que su fixup es un solo CZ. El
undo de la torre mide w (12 bits) y corrige la fase con CZs condicionadas
(`_phase_terms` en `dqi_tower_inv3.py`), todas Clifford. **Costo total de
fixups del scan: 0 Toffoli.** El MBU no tiene costo oculto aquí.

## 5. Verificación en el simulador a escala chica

Script `scan_mbu_simulador.py`: scan de 4 posiciones (LS=6, LO=5), sigma
construido con raíz en la posición 1 (f=1 ahí, f=0 en las demás), omega y
máscaras E aleatorias. Fase clásica esperada (Forney por posición,
`tools/dqi_phase_model.py`): 1.

| Variante | Q | T (4 pos) | sig/om intactos | temporales sucios | fase sim | fase esp | OK |
|---|---|---|---|---|---|---|---|
| MBU (actual) | 202 | 392 | sí | 0 | 1 | 1 | **sí** |
| Bennett (Toffoli propio) | 202 | 484 | sí | 0 | 1 | 1 | **sí** |

Ambas variantes son correctas y limpias (todos los ancillas en |0⟩, leídos
todos los qubits, no solo el resultado). La única diferencia es el costo:
98 vs 121 Toffoli/posición. El MBU no es un falso positivo del simulador.

## 6. La otra vía del scan (inversión condicional) está bloqueada

El doc propone además la inversión condicional (ítem 3): f=1 solo en
~1/4095 posiciones, así que condicionar el TowerInv (75 T) a f bajaría el
costo medio a ~0.018/posición. Pero en kickmix **no se puede condicionar
a un bit cuántico**:

```
push_condition(qubit) -> TypeError: Expected a km.b but got condition=km.q(0)
```

`push_condition` exige un bit clásico (`km.b`); f es un qubit. Medir f
en base Z para volverlo clásico rompería la superposición (el scan es una
fase coherente; el verificador exige corrección por linealidad). Controlar
cada puerta del TowerInv con el qubit f (control cuántico) subiría el
costo estático (cada Toffoli pasaría a ser una puerta de 3 controles),
no lo bajaría. La inversión condicional no es una vía MBU y queda fuera
del alcance de esta medición (sería un diseño aparte, con costo estático
mayor).

## 7. Impacto en las proyecciones

| Escenario | Q | T | ratio DQI | geomean | Estado |
|---|---|---|---|---|---|
| Actual | 1,949 | 784,172 | 6.77x | 3.31x | vigente |
| Scan MBU −23/pos (teórico) | 1,949 | 689,987 | 7.69x | 3.45x | **INVALIDADO** |
| BM in-place Q≈1,150 | 1,150 | 784,172 | 19.45x | 4.70x | vigente (sin scan MBU) |
| BM in-place Q≈892 | 892 | 784,172 | 32.32x | 5.57x | vigente (sin scan MBU) |
| BM in-place + scan MBU | 1,150 | 689,987 | 22.10x | 4.91x | **INVALIDADO** (parte scan) |
| In-place Q≈892 + scan MBU | 892 | 689,987 | 36.73x | 5.82x | **INVALIDADO** (parte scan) |

El margen del DQI queda solo en el BM in-place (proyecto mayor: derivar
la recurrencia de Schur) y, en T, en la inversión condicional (bloqueada
por ahora). El scan, con 98/posición, ya está en su piso MBU.

## 8. Archivos

- `REPORTE_SCAN_MBU.md` — este reporte.
- `scan_mbu_medicion.py` — descomposición por componente + variante Bennett.
- `scan_mbu_simulador.py` — verificación en simulador (MBU y Bennett).
- `scan_mbu_ablacion.py` — ablación MBU vs Bennett por separado (f y g).
- `scan_mbu_ladder_min.py` — escalera f mínima (aisló el hallazgo de §3).
- Main y ZIP intactos; todo es scratch en `~/workspace/qcc-data/dqi-perfil/`.

## Caveats

- El verificador DQI completo no corre en esta caja (8 GB,
  `reaction_depth` → bad_alloc); las cifras R≈1.20 y baseline ≈2.42e13 son
  de la recalibración 2026-11-07. La correctitud del scan a escala chica
  se verificó con el simulador kickmix; el circuito completo vigente ya
  pasó el verificador oficial (sha 6108f5c3…).
- Los conteos de Toffoli son `num_toffoli_like` del profiler/verifier
  (del_and y HMR cuentan 0; init_and y Toffoli propio cuentan 1).
