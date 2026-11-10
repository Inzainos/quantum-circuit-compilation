# Plan de entrenamiento dfthcsos — forma pequeña (8,143,60)

**Fecha:** 2026-11-09. **Decisión de Elán (WhatsApp ~14:35): ENTRENAR.**
No se inserta el candidato lbfgs_ep100_rho1e-4 (−0.58%). **No arrancar el
entrenamiento sin confirmar el plan y los recursos con Elán.** Primero
optimizar las entregas, después el notebook público (milestone 20 nov).
Nada a Kaggle sin decisión de Elán.

## 0. Resumen

| | |
|---|---|
| Forma objetivo | **(8, 143, 60)** — rank 8, bases 143, copies 60 (la de clduab11) |
| Forma actual | (65, 60, 60) — agotada, tope ~−0.6% |
| Objetivo | T=16,366, Q=430, ~9.78× (frontera); hoy T=93,237, Q=730, 1.00583× |
| Estimación | ~46 h (50,000 épocas a 3.3 s/época en CPU); **a medir en piloto** |
| Solver | **LBFGS** (Adam destruyó la semilla en el piloto) |
| Estado | Plan listo; **sin arrancar**; falta decisión de dónde corre |

## 1. La forma (8,143,60): qué es

- La factorización DF-THC tiene forma (rank, bases, copies) = (R, B, C).
  - Actual (65,60,60): rank 65, bases 60, copies 60. Score 3,355,599,588.
  - Objetivo (8,143,60): rank 8, bases 143, copies 60. La de clduab11.
- Por qué es mejor: el costo en Toffolis escala con el rank (número de
  vectores a codificar en ángulos). Rank 8 → muchos menos ángulos que
  rank 65, de ahí T=16,366 vs 93,237. Las bases suben a 143 para mantener
  la precisión (error_2 ≤ 20 mHa, E_gap sobre el piso).
- **Semilla:** se parte de `FeMoco76_65_60_60.npz` (la semilla (65,60,60),
  2.1 MB, ya en el starter kit). `load_seed_params` adapta la forma:
  crea un `Params` nuevo (8,143,60) y copia la región que se solapa
  (rank 0..7, bases 0..59, copies 0..59); las bases nuevas (60..142) se
  inicializan frescas (aleatorio, seed 0). Es el procedimiento estándar
  del starter kit, no un invento.

## 2. Datos y scripts (todo existe, nada que crear)

| Qué | Dónde | Estado |
|---|---|---|
| Integrales FeMoCo | `starter-kit/.../data/integrals/FeMoCo76o113e.fcidump` (128 MB) | Presente |
| Semilla (65,60,60) | `starter-kit/.../task1_factorization/FeMoco76_65_60_60.npz` (2.1 MB) | Presente |
| Entrenador | `dfthcsos-refit/refit.py` (--rank 8 --bases 143 --copies 60) | Probado |
| Constructor + verificador | `dfthcsos-refit/build_candidate.sh` | Probado |
| Verificación continua | `check_factorization.py` | Probado |
| Entorno | `~/workspace/py313-venv` (JAX 0.12 CPU + optax + h5py) | Probado |

- El pipeline completo ya está probado: con él se hizo el candidato
  lbfgs_ep100_rho1e-4 (score 3,336,160,975, PASS oficial, 254,464 shots).
- **No hace falta ningún dato nuevo.** No hay que descargar nada de Kaggle
  para entrenar (las integrales y la semilla ya están locales).

## 3. Dónde corre (la decisión que falta)

| Opción | Hardware | Ritmo | Problema |
|---|---|---|---|
| **Esta caja** | CPU, 4 cores, 7 GB RAM, JAX CPU | ~3.3 s/época → 50,000 ép = **46 h** | VM reemplazable (se pierde el progreso); sin GPU; no fiable para 46 h seguidas. **No recomendada para el run largo.** |
| **Katana** (máquina de Elán) | Por confirmar (GPU?) | Por medir | Ataría su máquina ~46 h (o lo que mida el piloto). Hay que saber qué GPU tiene y si puede dedicarla. |
| **Kaggle** | T4 x2 (2×16 GB), ~30 h GPU/semana, sesión máx 12 h, 20 GB en /kaggle/working | GPU (más rápido que CPU; factor exacto por medir en piloto) | **46 h > 30 h/semana**: no cabe en una semana; hay que partirlo en 2 semanas y en sesiones de ≤12 h. Exige checkpointing. |

- **JAX en esta caja es solo CPU** (verificado: `[CpuDevice(id=0)]`). No hay
  GPU aquí.
- **El factor GPU es desconocido** hasta medirlo: el piloto debe correr en
  el hardware elegido y medir s/época real para la forma (8,143,60).

## 4. Checkpointing (imprescindible, hoy no existe)

- `refit.py` **solo guarda al final** (`save_solution` tras entrenar).
  Si se interrumpe (límite 12 h de Kaggle, reemplazo de VM), se pierde todo.
- Para un run de ~46 h hay que partirlo en tramos:
  - **Opción A (sin tocar código):** correr `refit.py` por tramos
    (p. ej. 500 épocas), guardar el `.npz`, y relanzar con
    `--seed-file <el .npz guardado>` para el siguiente tramo. Funciona
    porque `load_seed_params` acepta cualquier `.npz` de la misma forma.
    Pega: al reanudar se resetea el estado interno de LBFGS
    (aproximación del Hessiano inverso); es una aproximación aceptable,
    no un continuo exacto.
  - **Opción B (tocar código):** añadir guardado intermedio a `refit.py`
    (cada N épocas). Más limpio, pero hay que modificar el script y
    probarlo antes del run largo.
- **Recomendación:** Opción A para empezar (no toca código), y si el run
  se alarga, valorar la B. En cualquier caso, **el piloto debe probar el
  mecanismo de reanudación** (un tramo corto + reanudar) antes del run largo.

## 5. Fases

### Fase 0 — Piloto (corto, antes de comprometer recursos)
- **Qué:** entrenar (8,143,60) con LBFGS, pocas épocas (20–50), en el
  hardware elegido. Medir: s/época real, que el pipeline acepte la forma,
  score/error_2/λ_eff iniciales, y que el mecanismo de reanudación
  funcione (parar y reanudar desde el .npz).
- **Dónde:** en el hardware elegido (Katana o Kaggle). Si es Kaggle, un
  notebook corto de prueba (CPU o GPU, pocas épocas, <1 h de cuota).
- **Salida:** tiempo real por época → proyección del run completo
  (¿sigue siendo ~46 h, o menos con GPU?). Decisión informada de seguir.

### Fase 1 — Entrenamiento completo
- **Qué:** correr hasta convergencia (o hasta el presupuesto de épocas
  que fije el piloto). Por tramos con reanudación (ver §4).
- **Dónde:** donde decida Elán (Katana o Kaggle).
- **Monitoreo:** guardar el `.npz` de cada tramo + log (eps, Lambda,
  λ_eff, E_gap). Si error_2 se dispara o E_gap cae bajo el piso, parar
  y revisar (como pasó con Adam).

### Fase 2 — Construcción y verificación
- **Qué:** `build_candidate.sh <npz> <nombre> 12 8` → check continuo,
  encode brot=12, circuitos ángulo, **verificador oficial**.
- **Criterio:** solo entra en la entrega si PASS oficial Y score <
  3,355,599,588 (mejor que el sample). Si no pasa o no mejora, no se toca
  la entrega.
- **Dónde:** en esta caja (el verificador oficial ya corre aquí para
  dfthcsos; lo hizo con el candidato lbfgs).

## 6. Qué se necesita de Elán antes de arrancar

1. **Dónde corre:** ¿Katana o Kaggle?
   - Si Katana: ¿qué GPU tiene? ¿puede dedicarla las horas que mida el
     piloto? ¿corre él el script o me da acceso?
   - Si Kaggle: ¿apruebas usar la cuota GPU (~30 h/semana) para esto?
     El run completo (~46 h en CPU; menos con GPU, por medir) no cabe en
     una semana: ¿lo partimos en 2 semanas?
2. **Presupuesto de tiempo:** ¿te parece bien un run de ~46 h (o lo que
   mida el piloto), o prefieres un tope de épocas/horas menor y ver qué
   sale?
3. **Checkpointing:** ¿Opción A (tramos con reanudación, sin tocar código)
   o B (añadir guardado intermedio a refit.py)?
4. **Nada más:** no hace falta ningún dato, cuenta ni descarga nueva.
   Todo el material ya está local y probado.

## 7. Riesgos

- **No converge / no mejora:** la forma (8,143,60) es la de la frontera,
  pero nuestro entrenamiento parte de una semilla adaptada; puede no
  llegar a T=16,366. El piloto dirá si la trayectoria es buena.
- **E_gap bajo el piso:** el encode puede subir el gap (pasó con el
  candidato lbfgs: el shift de encode lo levantó +8 mHa). Hay que vigilar
  E_gap en cada tramo.
- **Cuota Kaggle:** si se elige Kaggle, el run compite con el resto del
  trabajo de Kaggle por las ~30 h/semana.
- **Tiempo:** 46 h es la estimación en CPU; con GPU puede ser menos, pero
  no está medido. El piloto es obligatorio antes de prometer fecha.

## 8. Archivos de referencia

- Este plan: `~/workspace/qcc-data/dfthcsos-refit/PLAN_ENTRENAMIENTO_8_143_60.md`
- Entrenador: `~/workspace/qcc-data/dfthcsos-refit/refit.py`
- Constructor: `~/workspace/qcc-data/dfthcsos-refit/build_candidate.sh`
- Estado previo: `~/workspace/qcc-data/dfthcsos-refit/REFIT.md`
- Candidato anterior: `~/workspace/qcc-data/dfthcsos-refit/candidates/lbfgs_ep100_rho1e-4/`
