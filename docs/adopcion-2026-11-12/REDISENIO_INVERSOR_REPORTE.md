# REDISEÑO DEL INVERSOR DQI — REPORTE

**Fecha:** 2026-11-12
**Orden de Elán (2026-11-12 ~01:27, directo):** "Primero revisa el rediseño y sino se ven ganancias pasamos a adoptar las ganancias, y de ahí inicien a armar el notebook".
**Alcance:** SOLO el rediseño (la revisión). El siguiente paso (adoptar las ganancias y armar el notebook) lo lanza el parent, no este trabajo.
**Baseline (medido, reporte de fusión):** DQI fusionado Q=1,937 T=784,172, geomean 3.3237x, Kaggle 3.31949. Pico en ronda 69: 1,930 vivos (Q=1,937 con 7 de sobrecarga del pool). Bloque alpha: 68 vivos (p,t 2 + D 12 + X 12 + alpha 12 + P 12 + andamios 18). Torre ValueInv3: 18 andamios (N 6 + rc 6 + N' 3 + r 3), 75 T por inversión (ida+vuelta).

## VEREDICTO: SÍ HAY GANANCIA (pequeña) — E1d

**E1d (liberar N' antes de los productos) baja Q de 1,937 a 1,934 (−3) con +840 T, geomean 3.3237→3.3259x (+0.0022x).** Medido a nivel circuito completo (build DQI entera, 104 s). Es la única variante con ganancia neta. E1 es un wash (3.3236x) y E2 es peor (3.3218x): las tres pegan en el mismo piso Q=1,934 (el pico del scan), y E1d es la que menos T paga por ese −3. Las demás rutas (otra torre, otro algoritmo, builtin, lookup) son NO-GO.

| Variante (solo bloque alpha, 140 inv) | Q full | T full | Geomean | vs 3.3237x | Veredicto |
|---|---|---|---|---|---|
| Fusionado (baseline) | 1,937 | 784,172 | 3.3237x | — | referencia |
| **E1d (liberar N' antes de productos)** | **1,934** | **785,012 (+840)** | **3.3259x** | **+0.0022x** | **GANANCIA (adoptar)** |
| E1 (recompute N) | 1,934 | 786,692 (+2,520) | 3.3236x | −0.0001x | wash |
| E2 (recompute N,N',r) | 1,934 | 787,952 (+3,780) | 3.3218x | −0.0019x | peor |
| Itoh-Tsujii binario (11 muls) | — | ~1,386/inv | — | — | NO-GO (T y andamios) |
| Itoh-Tsujii cadena óptima (~5 muls) | — | ~315/inv | — | — | NO-GO (315 >> 75 T) |
| Builtin `init_gf2_inverse_with_scaffold` | 84 (standalone) | 315/inv | — | — | NO-GO (48 andamios) |
| Torre cúbica GF(2⁴)³ | ≥20 andamios | ≥884 (solo norma) | — | — | NO-GO |
| Lookup 12 bits | 0 | 4,094/inv | — | — | NO-GO |

**Ganancias chicas juntas con E1d:** fusión + E1d + lbfgs dfthcsos (−0.58%) → **~3.332x** (antes ~3.33x sin E1d). El +0.0022x de E1d se suma.

## 1. Recompute de andamios (E1, E2, E1d) — medido

### 1.1 Las variantes (todas correctas por simulador)
- **E1** (`tower_inv3r.py`, modo `'N'`): libera N (6) tras `inner.forward()` (0 T, MBU) y lo recomputa en el undo (18 T). Andamios tras forward: 18→12. T: 75→93.
- **E2** (`tower_inv3r.py`, modo `'all'`): libera N, N' y r tras `inner.forward()` y los recomputa en el undo (27 T). Andamios tras forward: 18→6. T: 75→102.
- **E1d** (`tower_inv3_e1d.py`): libera N' (3) tras computar r, antes de los productos en rc (0 T, `mulN_del` con N) y lo recomputa en el undo (6 T). Andamios tras forward: 18→15. T: 75→81.
- Las tres son **correctas por simulador**: 4096/4096 valores, basura 0, fase volteada 0 (`medir_torre_r.log`, `medir_torre_e1d.log`).

### 1.2 El Q standalone NO predice el Q del circuito completo (lección medida)
- **Q standalone = 57 en los cuatro casos** (baseline, E1, E2, E1d). Base 36 → pico 21 = 18 andamios + 3 temps. El vivo *tras* el forward sí baja (54→48→42→51), pero el pico standalone ocurre DURANTE el forward/undo (temps + recompute) y no se mueve.
- **Pero el DQI completo SÍ baja Q con E1d/E1/E2 (a 1,934).** El pico real del DQI se fija por el vivo *después* del forward de la torre (donde los andamios ya se liberaron), no por el pico transitorio durante los productos/undo: el pool reutiliza qubits libres para los 3 temps y para el recompute, así que esos picos transitorios no suben el high-water mark del circuito completo. El standalone (pool vacío) sí los cuenta; el circuito completo (pool con libres) no.
- **E1c (liberar N antes de los productos) es INVÁLIDO y se descartó sin correr:** los productos `y ^= r*N0, y ^= r*N1` usan N como entrada. (Archivo borrado.)

### 1.3 Medición a nivel circuito completo (build DQI entera, ~104 s c/u)
| Variante | Q | T | ΔQ | ΔT | Geomean |
|---|---|---|---|---|---|
| Fusionado (baseline) | 1,937 | 784,172 | — | — | 3.3237x |
| E1d solo alpha | **1,934** | 785,012 | −3 | +840 (=140×6) | **3.3259x** |
| E1 solo alpha | 1,934 | 786,692 | −3 | +2,520 (=140×18) | 3.3236x |
| E2 solo alpha | 1,934 | 787,952 | −3 | +3,780 (=140×27) | 3.3218x |
- Las tres dan el mismo Q=1,934: hay un **piso en 1,934 fijado por el pico del scan** (ver §5). E1d gana porque paga el menor T por ese −3. E1 es wash, E2 es peor.
- Fronteras vivas sin cambio en los tres casos (1,864 / 1,864 / 1,864 / 1,864 / 1,724). Solo cambian Q y T.
- Logs: `medir_dqi_e1d.log`, `medir_dqi_e1.log`, `medir_dqi_e2.log`.

## 2. Otro algoritmo: Itoh-Tsujii — medido (NO-GO)

- **Binario (x^4094, 11 muls):** T(ida)=693, ida+vuelta **~1,386 T**; Q=204 (168 andamios sobre la base, guardando los 11 acumuladores intermedios — un Itoh-Tsujii reversible con mul de target fresco no puede sobrescribir el acumulador sin guardar la historia, Bennett). Correcto por simulador 4096/4096, fase 0 (`medir_itoh_builtin4.log`). Frobenius verificado aislado 4096/4096 (`probar_frob.log`).
- **Cadena de adición óptima (~5 muls):** ~315 T, ~24 andamios (no construida; cota inferior). Aun así 315 >> 75 T de la torre.
- **Lecciones de implementación (registradas):** `CX(P→acc2)` + `del_gf2_mul` es INVÁLIDO (el CX entrelaza P con acc2 y el del/HMR mide P entrelazado — corrompe acc2; primer intento dio 1/4096). La forma correcta es **SWAP** con el registro fresco en |0⟩ (mueve el valor, P queda en 0). Además la primera verificación leía `keep` (q24..35) sin escribirlo (1/4096 por bug de lectura, no del circuito).

## 3. Inverso builtin — medido (NO-GO)

- `init_gf2_inverse_with_scaffold`: **48 andamios, 315 T**, Q=84, correcto 4096/4096 (`medir_itoh_builtin.log`). Es el método previo a la torre; la torre lo reemplazó precisamente por esto. NO-GO.

## 4. Otra torre: GF(2⁴)³ (cúbica) — medido simbólicamente (NO-GO)

- **Andamios mínimos 20 > 18 (estructural):** la fórmula cúbica es a⁻¹ = (a¹⁶·a²⁵⁶)·N(a)⁻¹. El numerador P = a¹⁶·a²⁵⁶ es un valor de **12 bits** que debe estar vivo mientras se invierte N (4 bits) por la torre interna (≥4 bits más). 12+4+4 = **20 > 18**.
- **Norma cúbica medida por ANF exacta** (Möbius sobre los 4,096 valores; `medir_norma_cubica.py`): cada bit de N(a) = a·a¹⁶·a²⁵⁶ tiene **~108–115 monomios cúbicos** (grado 3); total **442 monomios cúbicos + 136 cuadráticos** en los 4 bits. A 2 ANDs por monomio cúbico (sin compartir): **≥884 ANDs solo la norma**, más el numerador (~63 T) y la inversión interna. La torre cuadrática total son 75 T. NO-GO por andamios y por T.
- GF(2³)⁴ (cuatro niveles de grado 3) es peor (norma de grado 4, más niveles, más andamios); no se construyó por estar dominada por la cúbica.
- Lookup 12 bits: 4,094 T exactos (`init_lookup` = 2¹²−2, ya medido antes). NO-GO.

## 5. BLOQUEO (determinado desde los logs)

1. **El piso Q=1,934 lo fija el pico del scan.** Pico del scan medido (standalone, base 1,862): **70 sobre la base** (49 regs + 21 torre) → 1,934 en el decoder real (`medir_scan_pico.log`). El scan usa la torre original (18 andamios), así que su pico es 1,934 aunque el bloque alpha baje más. E1d, E1 y E2 liberan 3, 6 y 12 andamios en el alpha, pero las tres pegan en el mismo piso Q=1,934. **Por eso E1d (que menos T paga) es la mejor y E1/E2 no dan más Q.**
2. **Bajar de 1,934 exigiría rediseñar también la torre del scan**, pero el scan tiene 4,095 inversiones: E1d ahí costaría +6×4,095 = **+24,570 T** (geomean ~3.30x, peor). El T del scan mata cualquier ganancia de Q por esa vía.
3. **El recompute no baja el pico standalone (21) porque el recompute en el undo lo recrea** (recomputar N' con N+rc+r vivos + temps = 21), pero eso NO impide la ganancia a nivel circuito completo: el pool absorbe los picos transitorios y el Q real lo fija el vivo tras el forward. La lección es que **el Q standalone no predice el Q del DQI** — hay que medir el circuito completo (como se hizo aquí para E1d/E1/E2).
4. **Las alternativas pagan más T del que ahorran en Q:** Itoh-Tsujii ≥315 T, builtin 315 T, cúbica ≥884 T solo la norma, lookup 4,094 T — todas >> 75 T de la torre, y todas con más andamios.

## 6. Archivos

Scratch: `~/workspace/qcc-data/dqi-perfil/redisenio_inversor/`
- `REDISENIO_INVERSOR_REPORTE.md` (este reporte)
- `tower_inv3r.py` (E1/E2), `tower_inv3_e1d.py` (E1d)
- `medir_torre_r.py` + `medir_torre_r.log` (E1/E2 standalone: Q=57, T 93/102, 4096/4096)
- `medir_torre_e1d.py` + `medir_torre_e1d.log` (E1d standalone: Q=57, T=81, 4096/4096)
- `medir_itoh_builtin.py` + `medir_itoh_builtin4.log` (builtin 48/315; Itoh-Tsujii 168/~1,386, 4096/4096)
- `probar_frob.py` + `probar_frob.log` (Frobenius aislado 4096/4096)
- `medir_norma_cubica.py` + `medir_norma_cubica.log` (ANF norma cúbica: 442 monomios grado 3)
- `medir_scan_pico.py` + `medir_scan_pico.log` (scan: 70 sobre base → pico 1,934)
- `bm_fused_e1d.py`, `medir_dqi_e1d.py` + `medir_dqi_e1d.log` (DQI completo E1d-alpha: Q=1,934 T=785,012, 3.3259x)
- `bm_fused_r.py`, `medir_dqi_r.py` + `medir_dqi_e1.log`, `medir_dqi_e2.log` (DQI completo E1: Q=1,934 T=786,692, 3.3236x; E2: Q=1,934 T=787,952, 3.3218x)

## 7. Siguiente paso y verificación pendiente

- **Adoptar E1d** (junto con la fusión y el lbfgs dfthcsos −0.58% → ~3.332x) **y después armar el notebook** (milestone 2026-11-20). Eso lo lanza el parent, no este trabajo.
- **Verificación pendiente antes de adoptar E1d:** el primitivo E1d está verificado por simulador (4096/4096, fase 0), y es un reemplazo directo de ValueInv3 en el bloque alpha, pero la integración en el BM fusionado **no se verificó con el verificador oficial ni con sim n=6** (solo se midió Q/T en la build completa). Recomendado: correr la verificación n=6 (Tests A–C, como la fusión) o el verificador oficial en la Kali sobre el DQI con E1d antes de moverlo a main. Nada a main ni a Kaggle sin decisión de Elán.
