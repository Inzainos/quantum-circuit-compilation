# Palancas baratas de Q del DQI — flags y pico del BM (medido)

**Fecha:** 2026-11-09 ~09:30. **Estado:** las flags de −29 qubits NO son
identificables en el código; no se tocó ninguna flag. El pico del BM está
medido con composición fina. **No se tocó main ni el ZIP.** Todo el trabajo
es scratch en `~/workspace/qcc-data/dqi-perfil/`. El verificador DQI
completo no corre en esta caja; validación por construcción y conteo de
qubits con kickmix.

## 0. Resumen ejecutivo

| Pregunta | Respuesta (medida) |
|---|---|
| ¿Cuáles son las flags de −29 qubits? | **No existen.** No hay ningún conjunto de 29 qubits-flag en el camino activo del DQI. Las únicas flags son las p/t (140), probadas necesarias por dependencia circular. **No se tocó ninguna flag.** |
| Pico del BM (Q) | **1,949** (Q del circuito), **1,942** vivos simultáneos máx. en la ronda 69 de bm_forward. Base 1,862 + 80 transitorios. |
| Efecto medido en Q, T, geomean | **0.** No se aplicó ningún cambio (no hay lever barato identificable). Q=1,949, T=784,172, geomean 3.31×, sin cambio. |
| Palanca real del pico | El bloque alpha (P + Pinv + andamios = **42 qubits** en el pico). Reducirlo exige fusionar mul+inv (cambio algorítmico, no barato). No se intentó. |

## 1. Las flags de −29 qubits: no identificables

### 1.1 Búsqueda en el código (camino activo: `dqi_bm_stage_v1.py` + `dqi_decoder_v1.py`)

Se buscaron todas las menciones de "flag" y todas las alocaciones de 1 qubit
en el camino activo del DQI (el que construye el ZIP vigente, commit a741cc7).

**Únicas flags en el camino activo:**
- **p/t (140 qubits):** 2 por ronda × 70 rondas, guardadas en `self.flags`
  (`dqi_bm_stage_v1.py:38,159,185,189`). Son las banderas del BM
  (p = [D≠0 ∧ d≥0] replace, t = [D≠0 ∧ d<0] retain). **Probadas necesarias**
  por dependencia circular (reporte `REPORTE_BANDERAS_RECOMPUTO.md`):
  recomputarlas en la vuelta exige D_old y d_old, pero D_old solo se
  reconstruye vía `_dclear`, que usa p y t como controles. **No son los −29.**
  No se tocan.

**Otras alocaciones de 1 qubit (todas transitorias, liberadas en su ámbito,
no contribuyen al pico):**
- `_flags`: `z` (1), `nz` (1) — se liberan dentro de `_flags`.
- `build_scan_inv`: `tmp` (1), `f` (1), `g` (1) — transitorios del scan.
- `dqi_bm_stage.py` (v0, no activo), `dqi_bma_v11.py`, `dqi_cmq.py`,
  `dqi_optimized.py`: no forman parte del build vigente.

**Registros vivos (no son flags):** S 840, sigma 432, tau 432, d 8, H 12.
Ninguna combinación de estos suma 29 (d+H = 20; H = 12; d = 8).

**Conclusión:** no hay ningún conjunto de 29 qubits que sean "flags" en el
código. La propuesta de Claude ("flags −29 qubits") no está sustentada por
el código que construye el ZIP. **No se tocó ninguna flag.** Si Claude tiene
una identificación concreta (archivo, línea, registro), que la especifique;
sin ella, la palanca no existe.

### 1.2 Nota sobre el "+1% al geomean"

La aritmética de Claude es consistente con −29 qubits (Q 1,949→1,920,
Q² ×1.0305, DQI 6.77×→~6.98×, geomean 3.31×→~3.34×, ≈+1%). Pero como los
−29 qubits no son identificables, el efecto medido es **0**. El +1% era
una proyección sobre una palanca no localizada, no una medición.

## 2. Pico del BM (medido, composición fina)

Script: `pico_bm_fino.py` (replica `forward_round` paso a paso con logging
de `b.num_allocated_qubits`). Medido a escala chica (n=6) y completa (n=70).

### 2.1 Escala completa (n=70, commit a741cc7)

| Punto en la ronda 69 | Vivos | Δ vs base |
|---|---|---|
| Base (antes de la ronda 69) | 1,862 | — |
| alloc p,t,D,X,alpha | 1,900 | +38 |
| tras _disc, _flags, cx | 1,900 | +38 |
| **tras bloque alpha (P, Pinv, andamios)** | **1,942** | **+80** |
| tras swap, update, _dupd | 1,942 | +80 |
| tras alpha undo (P, Pinv liberados) | 1,900 | +38 |
| tras _xmux, _dclear | 1,900 | +38 |
| tras free alpha, X, D (fin de ronda) | 1,864 | +2 |

- **Pico vivos simultáneos: 1,942** (base 1,862 + 80 transitorios).
- **Q del circuito: 1,949** (7 más que el pico de vivos; sobrecarga del
  pool del alocador: qubits liberados que el pool no reutiliza al instante).
- **T de bm_forward: 185,034** (verificado, coincide con el perfil).
- Base 1,862 = S 840 + sigma 432 + tau 432 + d 8 + H 12 + flags p/t 138
  (rondas 0–68). Tras la ronda 69: 1,864 (140 flags).

### 2.2 Composición de los 80 transitorios del pico

| Componente | Qubits | ¿Por qué están vivos a la vez? |
|---|---|---|
| p, t | 2 | Banderas de la ronda (se guardan). Necesarias. |
| D | 12 | Discrepancia; P = X·D la necesita. Necesario. |
| X | 12 | sigma_0 anterior; P = X·D la necesita. Necesario. |
| alpha | 12 | Coeficiente de actualización; salida del mux. Necesario. |
| P | 12 | Producto X·D; Pinv = inv(P) y alpha = mux(P, Pinv). Necesario. |
| Pinv | 12 | Inverso de P; alpha = mux(P, Pinv). Necesario. |
| Andamios (mul + inv) | 18 | Ancillas internas de `init_gf2_mul` y `ValueInv`. |
| **Total** | **80** | |

Los 80 son genuinamente necesarios a la vez en el paso 5 (bloque alpha).
No hay "desperdicio" que recortar sin cambiar el algoritmo. Los
temporales de `_flags` (lad 10 + z 1 + nz 1 = 12) y de `_dclear` (u 12)
**no** contribuyen al pico: se liberan dentro de su función antes de que
se aloque el bloque alpha.

### 2.3 La palanca real del pico (no barata)

El bloque alpha es **42 qubits** en el pico (P 12 + Pinv 12 + andamios 18).
Reducirlo exige **fusionar la multiplicación y la inversión**: calcular
alpha = p ? inv(X·D) : (X·D) sin materializar P y Pinv por separado.
Eso es un cambio algorítmico (diseño de un nuevo primitivo), no una
eliminación de flags. No se intentó: requiere diseño, prototipo y
verificación con el simulador, y no es lo que se pidió (palancas baratas).
Queda como trabajo futuro, con el mismo criterio de parada: medir Q y T
antes de afirmar nada.

Otras reducciones posibles (todas menores o no baratas):
- Andamios (18): cambiar el multiplicador/inversor subyacente; afecta T
  y es un componente compartido. No es un lever específico del DQI.
- Sobrecarga del pool (7): depende del alocador de kickmix, no del circuito.
- d (8) y H (12): ya mínimos (d es un contador de 8 bits; H es una sola
  entrada de historial de 12 qubits). No hay recorte ahí.
- LS=36 (sigma/tau 432 c/u): reducirlo rompería los casos de L alto.

## 3. Verificación de integridad

- Clon `~/workspace/qcc-dqi/`: `git status` limpio, HEAD a40a82f. No se
  modificó ningún archivo del repo. Todo el trabajo es scratch en
  `~/workspace/qcc-data/dqi-perfil/` (`pico_bm_fino.py` y este reporte).
- `dqi-1949.kmb` (reproducido antes): sha256 `6108f5c344b995221f3cf57cd357a174…`,
  Q=1,949, T=784,172. Coincide con el ZIP vigente. Main y ZIP intactos.
- Nada a Kaggle, nada a main.

## 4. Archivos

- `~/workspace/qcc-data/dqi-perfil/pico_bm_fino.py` — medición fina del pico.
- `~/workspace/qcc-data/dqi-perfil/REPORTE_PALANCAS_Q_DQI.md` — este reporte.

## 5. Mensaje de relevo para Claude

Ver §6 (mensaje aparte en el chat). Resumen: que audite con el verificador
oficial cuando vuelva; las flags de −29 no son identificables (que
especifique archivo/línea/registro si las tiene); el pico del BM está
medido (Q=1,949, 1,942 vivos, 80 transitorios, bloque alpha 42); no se
tocó nada.
