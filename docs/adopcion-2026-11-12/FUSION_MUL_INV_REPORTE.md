# Fusión mul+inv del bloque alpha — DQI Q 1,949→1,937 (no 1,934)

**Fecha:** 2026-11-11/12 (sesión subagente). **Orden:** Elán (2026-11-11 ~22:42, vía Coordinador): "Fusión primero". **Estado:** trabajo en scratch en `~/workspace/qcc-data/dqi-perfil/fusion_mul_inv/`. Main y ZIP intactos. Nada a Kaggle. Nada descargado. Clon `~/workspace/qcc-dqi/` limpio (HEAD a40a82f, solo lectura).

## 0. Veredicto (corto)

| Pregunta | Respuesta |
|---|---|
| ¿La fusión baja Q a ~1,934? | **NO.** Baja Q a **1,937** (−12), no a 1,934 (−15). Faltan 3 qubits. |
| ¿El geomean llega a ~3.33x? | **NO.** Llega a **~3.324x** (3.31 → 3.3237x), no a ~3.33x. |
| ¿La fusión funciona (baja Q sin subir T)? | **SÍ, y está verificada.** Q 1,949→1,937 (−12), **T idéntico 784,172** (ΔT=0), correctitud verificada por simulador a n=6 (forward idéntico, ida+vuelta restaura, baseline==fusionada). Es una ganancia real, medida, pero **no alcanza el objetivo 1,934**. |
| ¿Cuál es el bloqueo de los 3 restantes? | **Los 18 andamios de la torre son estructurales** (N 6 + N' 3 + r 3 + rc 6, todos vivos a la vez, todos genuinamente necesarios); **el mul tiene 0 andamios que compartir**; los demás registros del pico (D, X, alpha, P, p, t) son todos genuinamente necesarios; y la sobrecarga del pool (7) es propiedad del alocador. Reducir los 3 restantes exige **rediseñar el primitivo de inversión** (otra torre / otro algoritmo), no la fusión. |

**Consecuencia (orden de Elán ~22:51, vía Coordinador):** "Y sino funciona fusión inicien con factorización desde 0". Como la fusión **no baja Q a ~1,934**, la contingencia se activa: **iniciar la factorización nueva desde cero con brot=8 en el loop**. (El circuito fusionado Q=1,937 queda construido y verificado en scratch; no se mueve a main ni a Kaggle sin decisión de Elán.)

**Estado vigente (referencia):** DQI Q=1,949, T=784,172, ratio 6.77x, geomean 3.31x, Kaggle 3.31949. El DQI tiene CERO rotaciones. Orden de Elán: Q primero (al cuadrado), luego T, luego R.

---

## 1. El bloque alpha (composición medida)

Del `REPORTE_PALANCAS_Q_DQI.md` §2 (re-verificado aquí, §2): en la ronda 69 de `bm_forward`, base 1,862 (S 840 + sigma 432 + tau 432 + d 8 + H 12 + flags p/t 138) + 80 transitorios = **1,942 vivos**, Q_circuito=1,949 (7 de sobrecarga del pool), T=185,034.

| Componente del pico | Qubits | ¿Por qué están vivos a la vez? |
|---|---|---|
| p, t | 2 | Banderas de la ronda (se guardan). Necesarias. |
| D | 12 | Discrepancia; P = X·D la necesita. Necesario. |
| X | 12 | sigma_0 anterior; P = X·D la necesita. Necesario. |
| alpha | 12 | Coeficiente de actualización; salida del mux. Necesario. |
| P | 12 | Producto X·D; Pinv = inv(P) y alpha = mux(P, Pinv). Necesario. |
| Pinv | 12 | Inverso de P; alpha = mux(P, Pinv). Necesario. |
| Andamios (mul + inv) | 18 | Ancillas internas de `init_gf2_mul` y `ValueInv3`. |
| **Total** | **80** | |

El bloque alpha en sí son **42 qubits** (P 12 + Pinv 12 + andamios 18). El código (`dqi_bm_stage_v1.py`, `forward_round`): `P = init_gf2_mul(X, D)`; `Pinv = alloc(12)`; `scaf = _inv_init(P, Pinv)` (ValueInv3, torre); `_alpha_sel(P, Pinv, p, alpha)` (alpha = p ? Pinv : P; 12 CCX + 36 CX); [swap, update, _dupd]; `_alpha_sel` (alpha → 0); `_inv_del` (undo inv); `free(Pinv)`; `del_gf2_mul` (P → 0); `free(P)`.

## 2. Andamios: el mul tiene 0, la torre tiene los 18 (medido)

Script `medir_andamios.py` → `medir_andamios.log`:

| Primitivo | Vivos antes | Vivos después | Andamios | T (ida+vuelta) |
|---|---|---|---|---|
| `init_gf2_mul` solo | 24 (X+D) | 36 (X+D+P) | **0** | 63 (ida; vuelta 0 por MBU) |
| `ValueInv3` sola | 24 (A+W) | 42 | **18** | 75 |
| Bloque alpha tal cual | 37 (X+D+alpha+p) | 79 | **18** (P 12 + Pinv 12 + 18) | 162 (= 63 mul + 75 inv + 12 mux + 12 unmux) |

**Conclusión:** los 18 andamios son TODOS de la torre de inversión (N 6 + N' 3 + r 3 + rc 6, ver §6). El mul builtin no tiene andamios persistentes (usa ANDs con `del_and`/MBU, 0 T en la vuelta). **No hay nada que compartir entre mul e inv en andamios** — la vía "reutilizar los andamios" está cerrada por medición, no por razonamiento.

## 3. El primitivo fusionado (F1b): inversión directo en alpha + selección por CSWAP

**Diseño.** La inversión no es in-place (ValueInv3 necesita un registro destino en |0⟩), así que la fusión es: **calcular inv(P) directo en alpha** (el registro destino ya existe y está en |0⟩) y **seleccionar por CSWAP** entre P y alpha. No se materializa Pinv.

- Forward: `P = init_gf2_mul(X, D)`; `scaf = _inv_init(P, alpha)` (alpha = inv(P)); `x(p); cswap(p, P, alpha); x(p)` → alpha = p ? inv(P) : P; P = p ? P : inv(P).
- Undo: `x(p); cswap(p, P, alpha); x(p)` (restaura P y alpha=inv(P), el CSWAP es autoinverso); `_inv_del(scaf, P, alpha)` (hmr en alpha → 0); `del_gf2_mul(X, D, target=P)` (P → 0); `free(P)`.
- El `x(p)` antes/después del CSWAP invierte el control (se quiere intercambiar si p==0); p se restaura (X = 0 Toffoli). El CSWAP es su propio inverso, así que la misma llamada selecciona y deselecciona.
- Costo de selección: **12 CSWAP = 12 Toffoli + 24 CX** (vs 12 CCX + 36 CX del mux original `_alpha_sel`). **Mismo Toffoli (12), menos CX (24 vs 36).**
- **Ahorro: el registro Pinv (12 qubits).** El bloque fusionado añade 30 vivos (P 12 + andamios 18) en vez de 42.

**Enfoques examinados (método de Elán, todos con medición):**
- **F1a (asignación condicional con 1 ancilla):** alpha ^= (¬p)·(P XOR alpha) bit a bit con un bit ancilla. NO se usó: el ancilla vive durante la selección (+1 vivo en el pico) y el CSWAP (F1b) es más limpio (0 ancillas, menos CX). No se midió en circuito (F1b domina).
- **F1b (inv en alpha + CSWAP):** ELEGIDO y medido (§4–§5).
- **F2 (compartir andamios mul/inv):** NO-GO — el mul tiene 0 andamios (§2). Medido, no asumido.
- **F3 (P en sitio sobre X o D):** NO-GO — X y D se necesitan después (X en `_xmux`, D en `_dclear`); P debe existir como registro propio para `del_gf2_mul`. Razonado desde el código (no se construyó).
- **F4 (fusionar el multiplicador en la primera capa de la torre):** NO intentado — el producto P es entrada de la torre; expresar las operaciones internas de la torre directo en X,D duplicaría los ANDs del producto (cada bit de P se usa varias veces en la torre) y subiría T. Es rediseño del primitivo, no fusión. Queda como investigación (sin evidencia).
- **Reducción de los 18 andamios de la torre:** NO es la fusión (es rediseñar el inversor); ver §6 (bloqueo).

## 4. Medición: Q y T (medido, no estimado)

### 4.1 Bloque alpha solo (medir_fusion.py)

| | Original | Fusionado (F1b) | Δ |
|---|---|---|---|
| Vivos que añade el bloque | +42 | **+30** | **−12** |
| T (ida+vuelta) | 162 | **162** | **0** |
| Q (circuito solo) | 82 | **70** | **−12** |

### 4.2 BM forward a n=70 (medir_fusion.py)

| | Baseline | Fusionada | Δ |
|---|---|---|---|
| Pico ronda 69 (vivos) | 1,942 | **1,930** | **−12** |
| Q_circuito | 1,949 | **1,937** | **−12** |
| T (bm_forward) | 185,034 | **185,034** | **0** |
| Live final | 1,864 | 1,864 | 0 |

Composición del pico fusionado: base 1,862 + 68 (p,t 2 + D 12 + X 12 + alpha 12 + P 12 + andamios 18) = 1,930.

### 4.3 DQI completo (medir_dqi_fusionado.py → medir_dqi_fusionado.log)

Construye `build_decoder()` con `BMStageFused` en vez de `BMStageV1` (omega y scan sin tocar). 116 s.

| | Baseline | Fusionado | Δ |
|---|---|---|---|
| **TOTAL Q** | **1,949** | **1,937** | **−12** |
| **TOTAL T** | **784,172** | **784,172** | **0** |
| Live frontera bm_forward / omega_fwd / scan / omega_rev / bm_reverse | — | 1,864 / 1,864 / 1,864 / 1,864 / 1,724 | — |
| **Geomean** | **3.31x** | **3.3237x** | **+0.0041x** |

Geomean: 3.31 × (1949/1937)^(2/3) × (784172/784172)^(1/3) = 3.31 × 1.004127 = **3.3237x**. El objetivo 1,934 daría 3.31 × (1949/1934)^(2/3) = 3.327x ≈ 3.33x. **La fusión llega a 3.3237x, no a ~3.33x.**

Circuito guardado: `dqi_fusionado.kmb` (624,726,290 B, sha256 `7a5815f4b36eb67bdb93b89bcb66c0acd6b7497e865bbde58b3ac8d87dc463cd`). No se mueve a main ni a Kaggle sin decisión de Elán.

## 5. Verificación por simulador a n=6 (verificar_fusion.py → verificar_fusion2.log)

n=6, LS=6, 64 tiros, S aleatorio (semilla 7), misma semilla para baseline y fusionada. Layout: S@0, sigma@72, tau@144, d@216, H@224.

| Test | Resultado |
|---|---|
| **A: forward baseline vs fusionada** (S/sigma/tau/d/H) | **PASA** — idénticos en los 64 tiros (sigma, tau, d, H iguales; fase volteada 0 en ambos) |
| **B: fusionada ida+vuelta restaura el estado inicial** | **PASA** (True) — S + sigma_0=1 + tau_1=1 + d=1, resto 0 |
| **C: baseline ida+vuelta == fusionada ida+vuelta** (regs persistentes) | **PASA** (True) |
| Q/T a n=6 | Forward: Q 333→**321** (−12), T 4,302 idéntico. Ida+vuelta: Q 333→**321**, T 7,680 idéntico. |

**Corrección (regla 0):** la primera corrida marcó "Test A FALLA" por un check mío erróneo ("transitorios en 0"): los qubits del pool incluyen las flags p/t (2 por ronda), que legítimamente valen 0/1 — no son transitorios en 0. El check se quitó; los checks reales (S/sigma/tau/d/H idénticos) pasaban en ambas corridas. El Test C chocó en la primera corrida por la diferencia de forma (333 vs 321 qubits — justo los 12 de Pinv); se corrigió comparando solo los registros persistentes (0..235).

**Caveat:** el DQI completo a n=70 NO se simuló (demasiado grande) y el verificador DQI oficial NO corre en esta caja. La verificación es: la etapa BM fusionada por simulador a n=6 (Tests A–C) + el DQI completo construido y medido en Q/T (omega y scan sin tocar). Si el circuito lo justifica, correr el verificador oficial en la Kali (pendiente de decisión; el circuito es una mejora real pero no llega al objetivo).

## 6. El bloqueo de los 3 restantes (desde los logs)

**Medición fina dentro de la torre** (`medir_pico_fino_torre.py` → `medir_pico_fino_torre.log`): reproduje el forward de la torre paso a paso en la ronda 69 a n=70, con logging de vivo tras cada alloc:

| Paso | Vivo |
|---|---|
| base ronda 69 | 1,862 |
| alloc p,t,D,X,alpha | 1,900 (+38) |
| tras _disc / _flags / cx sigma0→X | 1,900 |
| tras init_gf2_mul (P) | 1,912 (+50) |
| tras alloc N(6) torre | 1,918 (+56) |
| tras alloc rc(6) | 1,924 (+62) |
| tras alloc N'(3) inner | 1,927 (+65) |
| tras alloc r(3) inner | **1,930 (+68)** |
| tras inv8_init / mulN / C2P / _mulN_to / V2C inverso / CSWAP | **1,930 (+68)** |

**PICO MÁXIMO en la ronda 69 = 1,930** (incluidos los transitorios). Los transitorios tx/ty/t de `_mulN_to` y `mulN_init` **no suben el vivo por encima de 1,930** (el pool los reutiliza; se liberan dentro de la llamada). El vivo real es 1,930, pero **Q=1,937** — la sobrecarga del pool es **7** (1,937−1,930), igual que en el baseline (1,949−1,942=7).

**Por qué no se llega a 1,934 (los 3 que faltan):**
1. **Los 18 andamios de la torre son estructurales.** N (6) = norma de a en GF(64); rc (6) = N⁻¹; N' (3) = norma de N en GF(8); r (3) = N'⁻¹ en GF(8). Los 4 están vivos a la vez (del forward al undo) y todos son genuinamente necesarios para la inversión por torre (la fórmula del inverso en la extensión cuadrática necesita la norma Y su inverso). Reducirlos exige **rediseñar el primitivo de inversión** (otra torre, p. ej. GF(2⁴)³ o GF(2³)⁴, u otro algoritmo) — sin evidencia de que use menos de 18, y fuera del alcance de la fusión.
2. **El mul tiene 0 andamios** (§2) — no hay nada que compartir.
3. **Los demás registros del pico son irreducibles:** D (12), X (12), alpha (12), P (12) son elementos de campo de 12 bits, todos necesarios a la vez; p, t son 1 bit cada uno. La base 1,862 (S 840 + sigma 432 + tau 432 + d 8 + H 12 + flags 138) ya es mínima (d y H no se recortan; LS=36 no se baja sin romper L alto).
4. **La sobrecarga del pool (7) es propiedad del alocador** (Q − vivo máximo), no controlable desde el diseño del circuito (salvo cambiar el patrón de alocación, que es frágil y no es un lever de principio).

**Conclusión del bloqueo:** la fusión (F1b) agota lo que la fusión puede dar: Pinv (12). Los 3 restantes viven en el primitivo de inversión (18 andamios estructurales) y en el alocador (7 de sobrecarga). **No hay una segunda fusión dentro del bloque alpha que los saque.**

## 7. Qué queda (no hecho)

1. **Contingencia de Elán (~22:51): factorización nueva desde cero con brot=8 en el loop** — trabajo grande, sin evidencia de que funcione. Se activa porque la fusión no baja Q a ~1,934.
2. **Rediseño del primitivo de inversión** (otra torre / otro algoritmo con <18 andamios vivos) — investigación abierta, no es la fusión; si bajara los andamios de 18 a ≤15, el pico llegaría a 1,927 (Q≈1,934).
3. **Verificación con el verificador oficial en la Kali** (muestreo/sim; el verificador DQI completo no corre en esta caja) — pendiente de decisión; el circuito fusionado es una mejora real (Q=1,937, T idéntico) pero no llega al objetivo.
4. Medir el COSTO con la tabla 8-bit (paso 3, hueco: el planner NO fue descargado — orden de Elán).

## 8. Archivos

En `~/workspace/qcc-data/dqi-perfil/fusion_mul_inv/`:
- `FUSION_MUL_INV_REPORTE.md` — este reporte.
- `bm_fused.py` — `BMStageFused` (subclase de `BMStageV1`; `_alpha_sel_fused` + `forward_round`/`reverse_round` fusionados).
- `medir_andamios.py`, `medir_andamios.log` — andamios mul 0 / inv 18 (§2).
- `medir_fusion.py`, `medir_fusion.log` — bloque alpha solo + pico fino n=70 (§4.1–4.2).
- `verificar_fusion.py`, `verificar_fusion.log`, `verificar_fusion2.log` — simulador n=6, Tests A–C (§5).
- `medir_dqi_fusionado.py`, `medir_dqi_fusionado.log` — DQI completo (§4.3).
- `medir_pico_fino_torre.py`, `medir_pico_fino_torre.log` — vivo fino dentro de la torre (§6).
- `dqi_fusionado.kmb` (624,726,290 B, sha256 `7a5815f4…463cd`) — DQI completo fusionado (Q=1,937, T=784,172).

## 9. Caveats (regla 0)

- Todo número de este reporte viene de un log de correr un script (ver archivos). Lo estimado se marca ESTIMADO (geomean 3.3237x, calculado desde Q/T medidos con la fórmula del ratio DQI).
- El DQI completo a n=70 NO se simuló; la verificación es la etapa BM a n=6 por simulador (Tests A–C) + Q/T medidos del DQI completo. El verificador DQI oficial no corre en esta caja.
- La sobrecarga del pool (7) es una propiedad medida del alocador (Q − vivo máximo), igual en baseline y fusionada.
- El primer intento de un trabajo relacionado se cortó por límite de tokens de salida; este trabajo se completó con respuesta final corta (el detalle va en este archivo).
