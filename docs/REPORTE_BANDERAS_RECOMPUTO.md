# Costo de recomputar las banderas p/t en vez de guardarlas — 2026-11-08

## 0. Resumen ejecutivo — NO FACTIBLE

Recomputar las banderas p/t en la vuelta **no es posible** en la formulación
BM v1, y no es solo una cuestión de costo: es una **dependencia circular en
el flujo de datos**. La D que se necesitaría para recomputar p/t solo se
puede reconstruir en la vuelta usando p/t. La única ruta sin p/t para
obtener D (`_disc` sobre el sigma post-update) es **incorrecta** — medida
empíricamente: difiere de la D verdadera en 4/4 rondas con D != 0.

- **Q que se ahorraría si fuera posible:** 140 qubits (Q 1,949 → 1,809).
- **Costo del recómputo (hipotético, si `_disc` fuera correcto):**
  +65,676 Toffoli (+840 `_flags` en la vuelta, +71,766 `_disc` en la vuelta,
  −6,930 `_dclear` en la vuelta que ya no haría falta).
- **Score hipotético (si `_disc` fuera correcto):** 3.31x → **3.39x**
  (ratio DQI 6.77x → 7.25x), NO 3.48x como proyectaba el perfil con T sin
  cambio. La proyección de 3.48x asumía T constante, lo cual es incorrecto:
  el recómputo necesariamente suma Toffolis.
- **Score real:** el recómputo es **inviable**; la proyección de 3.48x del
  perfil queda **invalidada**. Las 140 banderas son necesarias en esta
  formulación. El margen real sigue estando en el BM in-place (Q≈1,150),
  no en las banderas.

## 1. Dónde están las banderas

`src/dqi_bm_stage_v1.py`, clase `BMStageV1` (decodificador BM v1, commit
`a741cc7`, rama `fix/zip-final-2026-11-07`).

**Forward (`forward_round`, r = 0..69):**
- `p, t = b.alloc_qubits(1)` — 2 qubits por ronda, **persistentes**.
- `D = _disc(r)` — discrepancia D = Σ sigma_i · S_{r-i} (bilineal).
- `_flags(D, p, t, inverse=False)` — calcula:
  - `nz = [D != 0]` (árbol AND de 12 bits, 11 Toffoli),
  - `p = nz AND (d >= 0)` (1 Toffoli, "replace"),
  - `t = nz XOR p` (gratis, "retain").
- p y t se usan como controles en toda la ronda: `_alpha_sel` (ccx),
  `bm_swap` (cswap), `_dupd` (cx/iadd), `_xmux` (ccx), `_dclear`
  (ccx con p, cswap con t).
- Al final: `self.flags.append((p, t))` — **se guardan** (140 qubits).
  D, X, alpha se liberan.

**Reverse (`reverse_round`, r = 69..0):**
- `p, t = self.flags.pop()` — se consumen las guardadas.
- `_dclear(D, p, t)` — **reconstruye D** usando p y t:
  `ccx(p, inv(sigma_0), D)` (caso replace: D = inv(sigma_0)) y
  `cswap(t, D, H)` (caso retain: D = H, la única entrada de historial).
- p, t se usan como controles en `_xmux`, `_alpha_sel`, `_dupd`,
  `bm_update`, `bm_swap`.
- `_flags(D, p, t, inverse=True)` — descomputa p, t (11 Toffoli: el árbol
  AND se reconstruye para obtener nz; `del_and` de p es gratis).
- `_disc_clear(r, D)` — limpia D por MBU (0 Toffoli).
- `b.free(p); b.free(t)` — se liberan.

## 2. La dependencia circular (por qué no se puede recomputar)

Para recomputar p/t en la vuelta harían falta D_old y d_old (la d
pre-update), porque `p = [D_old != 0 AND d_old >= 0]`,
`t = [D_old != 0 AND d_old < 0]`. Pero:

1. **D_old no se puede obtener sin p/t.** La única reconstrucción de D en
   la vuelta es `_dclear`, que usa p (ccx) y t (cswap) como controles.
   Sin p/t no hay D_old.
2. **D_old tampoco se puede obtener vía `_disc`.** `_disc` calcula
   Σ sigma_i · S_{r-i} sobre el sigma **post-update** (el estado al inicio
   de `reverse_round`). Por la propiedad definitoria de BM, el sigma
   post-update tiene discrepancia **cero** en la posición r (la
   actualización se diseñó para anularla). Así que `_disc` en la vuelta
   da 0 (o un valor incorrecto), no D_old. Verificado empíricamente
   (§3) y con el modelo clásico (§4).
3. **La información del caso se pierde en la actualización.** p/t
   codifican el caso (replace / retain / cero). El estado post-update no
   lo determina: cuando p=0 y H != 0, no se puede distinguir "retain
   (D_old = H)" de "cero (D_old = 0, H es resto de un retain anterior)".
   Por eso el algoritmo guarda las banderas: la actualización forward
   no es invertible desde el post-estado sin el caso.
4. **d_old tampoco se recupera sin p.** `d_new = d_old + 1` si p=0,
   `d_new = -d_old + 1` si p=1; el signo de d_old es ambiguo desde d_new
   cuando d_new <= 0. (En el caso de prueba de §5 el signo no se llegó
   a manifestar porque d nunca se hizo negativo; es un segundo modo de
   fallo independiente, no el principal.)

Conclusión: en esta formulación, **los 2 bits por ronda son información
que debe guardarse**. No hay atajo: ni `_disc`, ni el invariante
(inv(sigma_0)/H), ni re-correr el forward (185,034 Toffoli, absurdo),
ni guardar D_old (12 qubits/ronda = 840, peor que 140), ni bits
clásicos (no hay medición en base Z para leer un qubit a un bit
clásico usable en `push_condition`).

## 3. Prueba empírica 1 — `_disc` en la vuelta NO devuelve D_old

`test_disc_recompute2.py`: BM v1 a escala chica (n=6 rondas, LS=6,
sindrome válido de k=2 errores). Forward completo, reverse normal hasta
la ronda r, y en el punto de `reverse_round(r)` se compara D1 (vía
`_dclear`, la reconstrucción correcta con p/t guardadas) contra D2
(vía `_disc` sobre el sigma post-update). D1 ^ D2 == 0 significaría
que `_disc` devuelve D_old.

| Ronda | D_old (clásico) | D1 ^ D2 | Veredicto |
|---|---|---|---|
| 5 | 0 | 0 | trivial (D=0) |
| 3 | 2712 | **3884** | `_disc` INCORRECTO |
| 2 | 89 | **3080** | `_disc` INCORRECTO |
| 1 | 2975 | **2538** | `_disc` INCORRECTO |
| 0 | 1818 | **1819** | `_disc` INCORRECTO |

`_disc` en la vuelta difiere de la D verdadera en **4/4 rondas con
D != 0**. El recómputo de D vía `_disc` está muerto.

## 4. Prueba empírica 2 — el invariante clásico

`check_disc_postupdate.py`: con el modelo clásico de `dqi_bm_model.py`,
tras la actualización BM la discrepancia del sigma nuevo en la posición
r es 0 en todas las rondas con actualización (salvo el artefacto de la
ronda 0, donde la suma solo incluye i=0). Esto es la razón teórica de
que `_disc` en la vuelta dé 0 y no D_old.

## 5. Prueba empírica 3 — `_flags` con D correcta y d_new

`test_flags_recompute.py`: con D_old correcta (vía `_dclear`) y la d
actual (d_new), `_flags` recomputa p/t correctas en las 5 rondas
probadas (p2^p=0, t2^t=0). **Pero** en este caso de prueba d nunca se
hizo negativa (d_new = 3, 1, 0, 1, 0), así que no hubo rondas retain
(t=1) y el problema del signo de d no se manifestó. Es un segundo modo
de fallo independiente; el fallo principal es el de D (§3), que por sí
solo ya invalida el recómputo.

## 6. Control — el baseline es correcto

`test_bm_baseline_control.py`: BM v1 forward+reverse (banderas
guardadas) a escala chica, simulado con `km.Simulator`: S restaurado,
sigma=[1,0,0,0,0,0], tau=[0,1,0,0,0,0], d=1, H=0, fase volteada 0.
El baseline es correcto, así que `_dclear` reconstruye la D verdadera
y la comparación D1 vs D2 (§3) es válida.

Nota: la D del circuito v1 **difiere** de la D del modelo clásico
estándar en rondas 1 y 3 (`test_dclear_sanity.py`: D1=3884/2538 vs
2712/2975 clásico; solo coincide en ronda 0). Es esperable: la v1 es
una formulación reversible con invariantes propios
("sigma_0·delta=1"), no el BM estándar. Por eso la referencia correcta
es D1 (vía `_dclear`), no el modelo clásico.

## 7. Costos medidos (del perfil por etapa, `REPORTE_PERFIL_DQI.md`)

| Componente | Toffoli | Notas |
|---|---|---|
| `bm_flags` total | 1,610 | forward 840 (12/ronda) + reverse 770 (11/ronda) |
| `bm_disc` total | 71,766 | todo en forward (~1,025/ronda) |
| `bm_dclear` total | 13,860 | forward 6,930 + reverse 6,930 (99/ronda) |
| **Total DQI** | **784,172** | Q=1,949 |

Desglose de `_flags` por ronda: árbol AND 11 Toffoli (se construye
tanto en forward como en reverse para obtener nz) + 1 Toffoli por el
`init_and` de p en forward (en reverse es `del_and`, gratis).
Total 23 Toffoli/ronda (12 fwd + 11 rev).

## 8. Escenarios y números (R≈1.20, baseline≈2.42e13, invsqrt 5.32x, dfthcsos 1.00583x)

| Escenario | Q | T | costo R·Q²·T | ratio DQI | geomean |
|---|---|---|---|---|---|
| Actual (baseline) | 1,949 | 784,172 | 3.5745e12 | 6.77x | 3.31x |
| Perfil: banderas fuera, T sin cambio (SUPUESTO INCORRECTO) | 1,809 | 784,172 | 3.0794e12 | 7.86x | 3.48x |
| Hipotético: recomputo si `_disc` fuera correcto (+840 flags, +71,766 disc, −6,930 dclear_rev) | 1,809 | 849,848 (+65,676) | 3.3373e12 | 7.25x | 3.39x |
| **Real: recomputo INVIABLE** | — | — | — | — | **3.31x (sin cambio)** |

La proyección de 3.48x del perfil queda **invalidada**: asumía T
constante, pero el recómputo suma Toffolis necesariamente (mínimo
+840 de `_flags`, y realísticamente +71,766 de `_disc`). Incluso en el
hipotético falso (si `_disc` fuera correcto) el neto sería 3.39x,
no 3.48x. Y en la realidad `_disc` es incorrecto, así que no hay
ganancia alguna por esta vía.

## 9. Conclusión y qué sigue

- **Las banderas p/t (140 qubits) son necesarias en la formulación BM
  v1. No se pueden recomputar en la vuelta.** La dependencia es
  circular y está medida, no es una conjetura.
- **La palanca de 3.48x del perfil no existe.** El margen real sigue
  estando en el BM in-place (Q≈1,150 → geomean 4.70x) y en el scan
  MBU (teórico, −23/posición), no en las banderas.
- **Próximo paso sugerido:** el BM in-place (eliminar sigma/tau como
  registros separados). Es el único camino al orden de magnitud, pero
  exige rediseñar la etapa BM evitando la historia (BM con historia ya
  descartado: Q→2,700, efecto neto ≈1.0x).

## 10. Archivos

- `REPORTE_BANDERAS_RECOMPUTO.md` — este archivo
- `test_disc_recompute.py` / `test_disc_recompute2.py` — prueba
  empírica 1 (`_disc` vs `_dclear`, varias rondas)
- `check_disc_postupdate.py` — prueba empírica 2 (invariante clásico)
- `test_flags_recompute.py` — prueba empírica 3 (`_flags` con D
  correcta y d_new)
- `test_bm_baseline_control.py` — control (baseline forward+reverse
  correcto en simulador)
- `test_dclear_sanity.py` — D1 vs D_old clásico (la v1 difiere del BM
  estándar; la referencia correcta es D1)

Caveats: el verificador DQI completo no corre en esta caja (8 GB,
`reaction_depth` → bad_alloc); R≈1.20 y baseline≈2.42e13 son de la
recalibración 2026-11-07. Las pruebas son a escala chica (n=6, LS=6,
k=2) con el simulador kickmix; el argumento de la dependencia circular
es estructural (no depende de la escala). Main y el ZIP vigente no se
tocaron; todo el trabajo es scratch en `~/workspace/qcc-data/dqi-perfil/`.
