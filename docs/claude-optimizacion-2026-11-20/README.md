# Optimización 2026-11-20 — hoisting de delta (DQI), hallazgos y mapa de palancas (para Muse)

Autor: Claude (auditor externo / optimizador). Base: `main` 222d101 (PR #35: QF + P1+P2+P3 + P15, Kaggle v6 = 5.00379).
Reglas vigentes de Capitán (Elán): **nada a Kaggle ni a `main` sin su GO**; la selección final en Kaggle la marca solo él; cada cifra de
este documento sale de un build propio o de un log incluido (marcado "relevado" si viene de reportes del equipo que no pude auditar).

## 1. Qué trae esta rama

| Cambio | Archivo | Resultado medido |
|---|---|---|
| **Hoisting de delta en omega (DQI)** | `src/dqi_decoder_v1.py` (`build_omega_tmp`) | T 670,307 → **665,819** (−4,488), Q = 1,857, Gold PASS |
| Documentación, scripts de sondeo y logs | `docs/claude-optimizacion-2026-11-20/` | — |

### 1.1 Hoisting de delta
`build_omega_tmp` recalculaba `delta = σ₀⁻¹` (torre, 66 T) en cada uno de los 35 escalados por dirección. `σ₀` no cambia durante omega, así que
ahora se calcula una vez por dirección (antes de los 90 bloques P3) y se deshace al final (`vi.undo()`, 0 T por MBU).
Ahorro: 34 × 66 T × 2 direcciones = **4,488 T** (exacto: 670,307 − 665,819).
Costo en Q: delta (12) + andamio de la torre (18) vivos durante la etapa. La frontera de omega es 1,794 y el pico global está en el BM (1,857),
por eso Q no cambia (medido: `Q=1857`).

Orden de las multiplicaciones: idéntico al de main (los bloques P3 no se tocan); solo se mueve la inversión fuera del bucle.

### 1.2 Verificación (Gold, semilla fija)
Log: `logs/verify_hoist_gold.log`. Semilla `52642227205936912575373656611044064096114070193057152544535209180255000077827` (la misma del Gold QF/swap42/P15).

| | QF+P15 (main) | + hoisting |
|---|---|---|
| Q | 1,857 | 1,857 |
| T (toffoli_count) | 670,307 | **665,819** |
| tiros / errores valor / fase | 102,400 / 5 / 0 | 102,400 / 5 / 0 |
| R | 1.2131052140444296 | 1.2131052140444296 |
| score local DQI | 2.80412e12 | **2.78534e12** (−0.67 %) |
| sha256 `.kmb` | `60270f22c884ccebc0e06ab870f37d1efcca23fdc93c9f3cbf352c1c84cd9018` | `852739c3d30c726581a231bbb788cb4008cf0172341260c51b5d368c0f56703e` |

Reproducción del build desde esta rama (el `.kmb` no va al repo, `.gitignore *.kmb`):
```
PYTHONPATH=<kickmix>:verifiers/dqi python3 -u src/construir_dqi_qf_p15.py salida.kmb
# esperado: "TOTAL P1+P2+P3-QF Q=1857 T=665819", sha 852739c3…
```
Sin el parche, el mismo script da `60270f22…` (T=670,307) — comprobado.

Verificador: en máquinas de 7 GB el original se queda sin memoria en `circuit.reaction_depth()`; para medir se usó una copia de
`verifiers/dqi/verify_submission_dqi.py` con esa línea reemplazada por `None` (métrica informativa, no entra en el score).
Comando: `python3 verify_copia.py dqi.kmb --max-workers 2 --seed <semilla>`.

### 1.3 Impacto esperado en el score
Factor DQI 8.71540152 → 8.7741 (+0.67 %). Geomean local 4.98760 → **≈ 4.9988** (+0.22 %). Kaggle ≈ local × 1.003246 (offset medido en v4.1, v5 y v6).
R depende de la semilla (se deriva del hash del archivo): a un `.kmb` distinto le tocan otros tiros; 5 errores → R=1.2131, 0 errores → ≈1.191.
Por eso toda comparación de ganancias <2 % se hace con `--seed` fija, no con el score del primer envío.

## 2. Estado de los tres circuitos y valor de cada unidad

Geomean = (invsqrt × DQI × dfthcsos)^(1/3): un +1 % en cualquiera da +0.33 % al geomean. Ratios vigentes: invsqrt 5.33517, DQI 8.7154 (8.7741 con esta rama), dfthcsos 2.6684.

| Circuito | Costo | Valor de 1 qubit | Valor de 1 T |
|---|---|---|---|
| invsqrt R1+R5 | Q·C = 139 × 2,800.44 = 389,261 (T=2,561, 34 rotaciones) | 0.72 % | 0.036 % |
| DQI | R·Q²·T (Q=1,857, T=665,819) | 0.108 % (≈ 722 T) | 0.00015 % |
| dfthcsos seg100@brot13 | λ_eff·T·Q = 49.04 × 32,174 × 797 | 0.125 % | 0.0031 % |

## 3. DQI — desglose y estado de cada bloque (QF+P15+hoist)

T por etapa (build propio, `positions=range(2)` + extrapolación del barrido): BM ida+vuelta 248,312 · omega 53,052 · barrido 4,095 × 89 = 364,455.
Barrido por posición: inversión de torre 66 + escalera de `σ(x)=0` 11 + ANDs de fase 12.
BM (perfil de Datos sobre QF, antes de P15): bm_update 117,432 · bm_disc 55,818 · bm_swap 33,552 · bm_alpha 23,520 · bm_dclear 15,120 · bm_d 2,100 · bm_x 1,680 · bm_flags 1,610.

### 3.1 Pisos verificados (no proponer de nuevo)
- GF(2¹²): 42 ANDs es el piso medido (Toom-4, 7 × GF(8) × 6).
- GF(64): 15 ANDs (rango bilineal óptimo). **P15** ya integrado: inversión por torre 75 → 66 T (`docs/QF_P15_AND_2026-11-20.md`).
- Escalera `σ(x)=0`: NOR de 12 bits = 11 ANDs mínimo.
- Inversión por lotes (Montgomery): peor (3 muls > 1 inv).
- Omega sin ω (Horiguchi–Koetter con τ del BM): +31 T/pos (producto B·σ′ 42 T + inversión 66 − 12 ANDs de fase menos 1) ≈ +127k T contra 53k ahorrables. Peor.
- Walsh-Hadamard/QFT como circuito nuevo: NO-GO (Kimi/Datos).

### 3.2 Filtrar por `E[p]` — CERRADO (medido)
Idea: envolver cada posición en `bit_store(is_error, True, control=E[p])` + `push_condition`, como hace la referencia, para que el verificador
cuente solo las posiciones ejecutadas (el simulador cuenta por tiro las operaciones bajo condición; prueba: `scripts/t_cond2.py`).
Resultado: PASS, mismos 5/0 errores, pero `toffoli_count` = 670,218 contra 670,307 (−89, ruido). Razón: `E[p]` son los bits `mbuc` de MBU,
uniformes aleatorios, casi siempre ≠ 0; no marcan dónde hay error. Condicionar por la raíz `f` (qubit) está bloqueado por la API
(`push_condition` rechaza qubits). Log: `logs/verify_cond_E_p_descartado.log`.

### 3.3 Pico de Q del BM
Sondeo con tope de construcción (`scripts/dqi_cap.py <cap>` con `SRCQ=src`): el pico de 1,857 está en la ronda del BM, en el andamio de la torre
del bloque alpha (`tower_inv3_e1d.py`, `Inner6E1d.forward`, reserva de y = 6 con 1,845 vivos). El pico del barrido es 1,837 y las fronteras 1,794.
Bajar Q exige recortar ese andamio (hoy 15–18 qubits) o los registros X/P/alpha/D de la ronda. Cada qubit vale 722 T; el techo si BM baja a 1,837 es −20 qubits (≈ +2.2 % DQI),
y luego hay que bajar BM y barrido a la vez. **Sin diseño todavía.**

### 3.4 Correcciones a los briefs de Kimi (2026-11-20)
- La base debe ser QF+P15(+hoist), no QF: "75 T es el piso" es falso (66 T).
- **Tarea 3 (eliminar τ, Q→1,425, ×1.698) tiene mal la premisa**: τ es estado del BM (`σ ← σ + α·x·τ`) y está vivo en el pico global (dentro del BM). Quitarlo solo durante el barrido no baja el máximo; τ no se deduce de σ y S (ya medido: τ∝Ψ falso, 8/56).
- Presupuesto de la Tarea 1 (Ψ para el barrido por traza, Parte B Q=2,285, T=403,187): recalculado con la base P15 (T_E máx. con ΔQ=0: 66k → 42.7k; con T_E=16,331, ΔQ máx. 131 → 71).
- "Un qubit vale ~20× un Toffoli" es incorrecto: son ≈ 722–765 Toffoli.

## 4. invsqrt (Q=139, T=2,561) — medido hoy

- Q = x 22 + sel 1 + sb 4 + coef 58 + max(scratch 28, y1 38) = 123 de registros, **+ 16 ancillas del Horner** (sin Horner, Q=123).
- T por fase (ida+vuelta): normalize_log 224 · giro_mitad 42 · lookup 551 · **horner 1,484** · copy_c0 0 · denormalize_log 260.
- `scripts/inv_cap.py <cap>` (construye con `set_max_qubits`): barrido cap 123…139 → T 3,117 … 2,561. Score Q·C monótono creciente al bajar el tope
  (cap 139: 389,978 [con 35 rot.] — cap 123: 413,477). **Los 16 qubits compran 556 T (≈ 35 T/qubit), más de los ≈ 20 T/qubit que vale cada uno**: Q=139 es el óptimo de esa perilla.
- `estrecho=True` (HornerEstrecho): Q=132, T=3,109, peor (ya documentado en `docs/ESTADO_2026-11-06.md`).
- El lookup cuesta 2^9 − 2 = 510 T **sin depender del ancho** de la columna: partir la tabla (liberar c2 y volver a leer) cuesta +510 T por 11 qubits (46 T/qubit), no conviene.
- Fuera de alcance de este análisis: reducir el número de rotaciones/eps (239 de C = 8.5 %), con holgura de 16 % en el peor error (0.8375 de la tolerancia).
- Nota de reproducibilidad abierta: `r1r5.diff` aplica sobre main, pero `_phase_by_bits(skip_low=…)` no existe en `src/dbhexa_invsqrt.py` de main → R1+R5 no se reconstruye desde el repo (el baseline sí: sha `7e842bbf…`, Q=139, T=2,561).

## 5. dfthcsos (para Muse) — lo que está relevado

Datos relevado, no auditado por mí (los reportes `MEDICION_DESGLOSE_Q797…` e `INVESTIGACION_ACCIONABILIDAD_Q797…` no están en el repo): 
- Q=797 = persistente 190 + temporal 607; temporal = QROAM 601 (datos 589 = 31×19 + dirección 12) + uniforme 6. El 589 es 73.9 % de Q.
- 85 % del T son los lookups `angle_k`; `src/dfthcsos_optimizer.py` solo barre brot/J, el modelo de costos vive en el verificador (`verifier/costs.py`, `score.py`).
- `k2_opt=5` lo fija el verificador (óptimo por score sería k2=3, pero no es parámetro del envío). `chi↓` solo maquilla el `summary.json` local (el oficial usa keep_bits=10). J=7 estimado 1.058× (probablemente peor).
- **La palanca real es la factorización: otra (R,B,C) con B menor** baja a la vez los qubits de datos del QROAM y el T de los lookups. Hay que pasar la compuerta de error
  (`error_2` = 0.01896 Ha, `error_1` = 0.00165 Ha, λ=306.63 hoy; el umbral exacto no lo conozco).

## 6. Cola de trabajo sugerida, por ganancia/esfuerzo

1. **dfthcsos: barrer candidatas (R,B,C)** con B menor y medir λ_eff·T·Q con el verificador oficial. Potencial grande, sin cifra todavía. ← **Muse**
2. DQI: **recorte del pico de Q del BM** (§3.3); mismo método que el parche QF (reordenar alloc/free dentro de la ronda). ≈ +2 % DQI como techo.
3. DQI: **ventana de coeficientes no nulos** de σ y τ por ronda en el BM (la cota `bu(r)` es de peor caso): medir la tasa real en los tiros del verificador y podar la cola rara.
   Presupuesto: 5 errores → R=1.2131; 0 errores → 1.191, o sea ≈ 1.8 % de margen total de R.
4. DQI: Ψ / barrido por traza (Kimi, Tarea 1): techo +9 %, solo si Ψ cabe en T_E < 42.7k y ΔQ < 119 (§3.4).
5. invsqrt: rotaciones/eps (§4). El resto está en su óptimo medido.

## 7. Contenido de la carpeta

- `hoist_main222d101.patch` — el mismo cambio de `src/dqi_decoder_v1.py` como parche (md5 `80dd100a198db10c0fc3c2165927e158`).
- `scripts/inv_cap.py` — sondeo de Q/T de invsqrt con `set_max_qubits` (`REPO=<repo> KICKMIX=<kickmix> python3 inv_cap.py <cap>`).
- `scripts/dqi_cap.py` — idem para el DQI (BM + omega + 2 posiciones; `SRCQ=<repo>/src`). Base: Q=1,857, T=306,030 (con 2 posiciones).
- `scripts/gen_plan15.py` — generador/verificador del plan de 15 términos de GF(64) (ya adoptado como P15 en main).
- `scripts/t_cond2.py` — prueba de que el simulador cuenta por tiro solo lo ejecutado bajo `push_condition` y de la semántica de `bit_store(control=registro)`.
- `logs/` — salidas JSON del verificador: P15, hoisting y la prueba descartada de `E[p]`.
