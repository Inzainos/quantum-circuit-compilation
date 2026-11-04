# Quantum Circuit Compilation — Google Verifiable Quantum Circuit Competition

> **Shrinking bottleneck quantum subroutines to reduce hardware requirements for near-term quantum advantage.**

## La competición

Esta es una competición de **compilación verificable de circuitos cuánticos** organizada por Google Quantum AI (Kaggle, 2026). El objetivo es encontrar compilaciones más pequeñas y rápidas de subrutinas críticas (kickmix circuits) usando agentes de programación AI, optimización clásica y conocimientos algorítmicos en un bucle de verificación cerrado.

**Pregunta central:** ¿Podemos obtener más de una computadora cuántica simplemente pidiéndole que haga menos?

---

## Los tres benchmarks (tareas)

| Task | Paper | Científico | Cuello de botella a comprimir |
|------|-------|------------|------------------------------|
| **invsqrt** (Fusion Energy) | Benchmark I | Simulación de electrones en grid (Trotter) | Phasing por 1/√x para cada par de electrones (Coulomb, stopping power de partículas alfa) |
| **dqi** (Combinatorial Optimization) | Benchmark II | Decoded Quantum Interferometry (DQI) | Decodador reversible de síndrome de Reed–Solomon |
| **dfthcsos** (Quantum Chemistry & Clean Energy) | Benchmark III | Estimación de fase en Hamiltoniano molecular (FeMoCo) | Factorizaciones tensoriales, árboles de Givens, QROMs |

### Métricas de coste por tarea

Cada tarea tiene su propia función de pérdida (coste):

- **invsqrt**: función de coste basada en qubit count y Toffoli count por shot.
- **dqi**: incluye un upper confidence bound sobre la tasa de fallo del decodador.
- **dfthcsos**: cubre todo el block encoding (no solo los circuitos ANGLE). Cualquier circuito ANGLE con más de 128 qubits es rechazado.

### Evaluación

El *EvaluationSubmission* se evalúa usando la **media geométrica** de la mejora de cada tarea relativa a un baseline:

```
score = geometric_mean(improvement_invsqrt, improvement_dqi, improvement_dfthcsos)
```

donde cada `improvement` mide la reducción de coste respecto al baseline de referencia.

---

## Formato del envío (Submission File)

Debes enviar un archivo **ZIP** conteniendo:

| Archivo | Descripción |
|---------|-------------|
| `invsqrt.kmb` o `invsqrt.kmx` | Circuito de invsqrt (formato kickmix) |
| `dqi.kmb` o `dqi.kmx` | Circuito de dqi (formato kickmix) |
| `dfthcsos/` | Carpeta con circuitos `angle_k_0`, `angle_k_1`, … `angle_k_<n-1>` (numerados desde 0, sin gaps), cada uno como `.kmb` o `.kmx` |
| `dfthcsos/submission.npz` | Factorización `(U, W, H2_I, H1_I, Hsym_lower)` y árbol de Givens `tree_edges` |

**Scoring:** ~45 minutos por envío.

---

## Timeline y premios

### Fechas clave (todos los plazos a las 11:59 PM UTC)

| Fecha | Hito |
|-------|------|
| 22 de octubre de 2026 | Fecha de inicio |
| 20 de noviembre de 2026 | Mid-Competition Milestone Prize (leaderboard público) |
| 4 de enero de 2027 | Longest Leader Prize (notebooks y datasets deben ser públicos) |
| 13 de enero de 2027 | Entry Deadline (aceptar reglas) + Team Merger Deadline |
| 20 de enero de 2027 | Final Submission Deadline |

### Premios

| Premio | Cantidad |
|--------|----------|
| 1º Puesto | $50,000 |
| 2º Puesto | $25,000 |
| 3º Puesto | $10,000 |
| 4º Puesto | $5,000 |
| 5º Puesto | $5,000 |
| 6º Puesto | $5,000 |
| Mid-Competition Milestone | $10,000 |
| Longest Leader | $10,000 |
| Single Task Performance (×3 tareas) | $30,000 ($10,000 cada una) |
| Additional Prizes | $50,000 |

### Requisitos de elegibilidad

- Los notebooks ganadores deben ser públicos y reproducibles.
- Los datasets usados deben mantenerse públicos hasta el Final Submission Deadline.
- Licencias y documentación deben cumplir las Competition Rules.

---

## Estructura del repositorio

```
quantum-circuit-compilation/
├── README.md                          # Esta guía (competición, métricas, premios)
├── pyproject.toml                     # Configuración del proyecto
├── benchmarks/
│   ├── fusion_energy/                 # invsqrt — 1/√x Phasing
│   ├── combinatorial_optimization/    # dqi — Reed–Solomon syndrome decoder
│   └── quantum_chemistry/             # dfthcsos — Hamiltonian Block Encoding (FeMoCo)
├── submission/                        # Plantilla y scripts para construir el ZIP de envío
├── src/                               # Código compartido, wraps kickmix, métricas, agentes AI
├── tests/                             # Pruebas de verificación de circuitos
├── docs/                              # Papers de referencia, glosario, contexto de dominio
└── results/                           # Mejores compilaciones encontradas (metrics.json, QASM)
```

### Publicación en GitHub

`submission/submission.zip` (~74 MB, ~910 MB descomprimido) es el artefacto de envío.
Los circuitos y datasets sueltos (`.kmb`, `.kmx`, `.npz`, `.fcidump`), el entorno
virtual y la copia local del paper no se versionan (`.gitignore`): algunos superan
el límite de 100 MiB por archivo de GitHub. Cada nuevo commit del ZIP infla el
historial; para versiones siguientes usa Releases o Git LFS en lugar de versionar el ZIP.

**Aviso (2026-11-03):** el `submission.zip` commiteado el 2026-10-30 (commits `61a4985`/`67d4234`,
PR #17, ~260 KB) **no pasa los verificadores oficiales** (ver CHANGELOG) y sobrescribió al
zip válido. El último zip válido está en el commit `fb4e95b` (`git show fb4e95b:submission/submission.zip`).
Antes de enviar a Kaggle, corre los tres verificadores sobre los archivos exactos del zip.


## Estado actual (2026-11-03) — solo cifras verificadas con los verificadores oficiales

| Tarea | Circuito | Score / resultado | Verificación |
|-------|----------|-------------------|--------------|
| invsqrt | piecewise mitad-dividida, deg=2, j=8, wc=28, dd=13 (`src/invsqrt_halfsplit.py`) | Q=183, T=2,867, **score 570,323** (−72.5 % vs 2,070,562) | PASS dominio completo, 1 tirada/x (3,133,440 tiradas), error peor 0.893 de la tolerancia. **Falta** la corrida de especificación completa (64 tiradas/x) |
| dqi | `src/dqi_optimized_v10.py` (contadores de 7 bits; Chien+Forney de referencia) | Q=1,888, T=5,708,480, score 100,553,499,141,099 **a 2,560 tiradas** | PASS, 0 errores. Con las 102,400 tiradas por defecto R≈1.19 y el score sería ~2.42×10¹³ |
| dfthcsos | brot=12, J=8, 10 `angle_k` + `submission.npz` (datos de ejemplo) | Q=730, T=93,237, score 3.36×10⁹ | PASS **solo con el sample**; los datos oficiales de FeMoCo no están en el repo |

Notas:
- El score de invsqrt es Q × `toffoli_equivalent` (3,116.52), no Q × Toffolis ni Q². Depende del rango de x probado: el mismo circuito da otro número en un subconjunto pequeño.
- La mejora de DQI viene de los contadores de 7 bits (−1 qubit, −3.5K Toffolis frente a v2). `dqi_optimized_v10.py` importa `galois_iqft` pero **no** lo usa: sigue ejecutando Chien y Forney.
- Cifras que circularon (invsqrt 419,336; DQI Q=138 / "245,000×"; dfthcsos Q=104, T=279) **no tienen circuito verificable** en el repo y los archivos subidos fallaron los verificadores (ver CHANGELOG, 2026-11-03).

### Submission ZIP
Contenido esperado de `submission/submission.zip`: `invsqrt.kmb`, `dqi.kmb`, `dfthcsos/angle_k_*.kmx` y `dfthcsos/submission.npz`
(en la raíz del zip, sin carpeta intermedia). Los circuitos se regeneran con:

```
python3 src/invsqrt_halfsplit.py --deg 2 --j 8 --wc 28 --dd 13 --out invsqrt.kmb
python3 src/dqi_optimized_v10.py dqi.kmb --m 4095 --n 70 --degree 12
```

Para reconstruir el zip completo (invsqrt + dqi regenerados, `dfthcsos/` tomado del zip válido `fb4e95b`):

```
python3 submission/rebuild_valid_zip.py salida/submission.zip
```

`QubitTemporalManager` (`src/qubit_temporal_manager.py`) es solo contabilidad
y no modifica ningún circuito.

### `submission/` — Construcción del ZIP de envío

Contiene scripts y plantillas para generar:
- `invsqrt.kmb` / `invsqrt.kmx`
- `dqi.kmb` / `dqi.kmx`
- Carpeta `dfthcsos/` con `angle_k_0`…`angle_k_<n-1>` + `submission.npz`
- Script `build_submission.py` que empaqueta todo en el ZIP final.

---

## Tecnología clave

- **kickmix library** en Qualtran (Google) — construye y hace fuzz-testing de circuitos con decenas de millones de puertas en entradas clásicas en segundos.
- Circuitos basados en lógica clásica reversible, puertas de fase diagonal y descomputación basada en medición.
- Verificación automática: el simulador kickmix procesa 64–512 test inputs por instrucción de CPU y maneja circuitos con >100 millones de gates en un solo core.
- Fiat–Shamir heuristic: los inputs aleatorios y resultados de medición se seeded con un hash criptográfico salteado de tu submission (no hay test set oculto).

## Optimizaciones implementadas (verificadas)

### invsqrt
- Sin Newton–Raphson: polinomio por tramos (grado 2) con coeficientes cargados por QROM y evaluados con Horner (`src/invsqrt_piecewise.py`).
- Tabla mitad-dividida: M ∈ [2,4) se lleva a M′ = M/2 con el factor 1/√2 integrado a los coeficientes, y la tabla pasa de 3·2^j a 2^(j+1) entradas (`src/invsqrt_halfsplit.py`).
- **Resultado**: Q=183, T=2,867, score 570,323, error 0.893 < 1.0.

### dqi
- Contadores n_A, n_B, n_a, n_b y n_q de 7 bits (`src/dqi_optimized_v10.py`).
- **Resultado**: Q=1,888, T=5,708,480 (2,560 tiradas): −0.82 % frente a la referencia.

### dfthcsos
- Barrido de `brot` y `batch_size` sobre el circuito de ejemplo; mejor resultado con datos de ejemplo: brot=12, J=8 (`results/dfthcsos_opt2/`). Sin los datos oficiales no hay optimización propia medida.


---

## Glosario de términos clave

| Término | Definición |
|---------|------------|
| **Ancilla** (scratch qubit) | Qubit temporal que debe regresar a 0 al final del circuito. |
| **Block encoding** | Circuito que incrusta una copia escalada de una matriz (ej. Hamiltoniano) dentro de una operación cuántica mayor. |
| **Hamiltonian** | Operador que da la energía de un sistema físico. |
| **kickmix circuit** | Circuito hecho solo de puertas clásicas reversibles, puertas de fase y descomputación por medición. Verificable eficientemente en computador clásico. |
| **Logical qubit** | Qubit corregido de errores construido de muchos qubits físicos. |
| **Measurement-based uncomputation** | Limpieza de un qubit scratch midiendo y cancelando el signo resultante con puertas baratas, en lugar de revertir la computación. |
| **QROM** | Tabla de búsqueda cuántica que devuelve la entrada para cada dirección en superposición a la vez. |
| **Syndrome** | Huella compacta de los errores en un codeword, computable sin conocer el mensaje original. |
| **Toffoli gate** | Puerta controlled-controlled-NOT; la operación más costosa en hardware corregido de errores. Métrica clave de coste. |
| **Trotterization** | Simulación de evolución temporal alternando muchos pasos pequeños de evoluciones más simples. |

---

## Contexto de dominio

### ¿Por qué estos circuitos se pueden verificar automáticamente?

Para circuitos cuánticos generales, verificar que un candidato hace lo que debe es intratable clásicamente (más de ~40 qubits está fuera de alcance). Las subrutinas de esta competición son diferentes: están construidas solo con puertas clásicas reversibles, puertas de fase y measurement-based uncomputation (familia **kickmix**). Cada instrucción mapea un bit string definido a otro bit string definido, como máximo cambiando su fase. Por lo tanto, un computador clásico puede ejecutar el circuito input por input, rastreando solo un bit por qubit más una fase.

Como la mecánica cuántica es lineal, un circuito que mapea cada input de bit string al output correcto con la fase correcta, y deja sus qubits scratch limpios, también se comporta correctamente en toda superposición de esos inputs.

El verificador hace **fuzz testing** de tu circuito: simula sobre cada input válido o muchos inputs aleatorios ponderados como el algoritmo real los pondera, verificando que los inputs se restauren, los scratch qubits queden limpios y la fase sea correcta. Los inputs aleatorios y resultados de medición se seeded con un hash criptográfico salteado de tu submission (Fiat–Shamir), así que no hay test set oculto.

### Las tres tareas a un vistazo

| Task | Meta científica | Algoritmo cuántico | Cuello de botella |
|------|----------------|--------------------|-------------------|
| **Fusion Energy** | Predecir deposición de energía en combustible de fusión | Simulación Trotter de electrones en grid | Phasing 1/√x por cada par de electrones |
| **Combinatorial Optimization** | Ventaja cuántica verificable para Optimal Polynomial Intersection | Decoded Quantum Interferometry (DQI) | Decodador reversible Reed–Solomon |
| **Quantum Chemistry** | Entender fijación de nitrógeno (cluster FeMoCo) | Estimación de fase en Hamiltoniano codificado | Tensor factorizations, Givens trees, QROMs |

---

## Referencias

- Khattar et al. (arXiv:2610.23832) — paper acompañante de la competición: kickmix package, garantías de verificación, los tres benchmarks.
- Babbush et al. (arXiv:2603.28846) — introdujo kickmix circuits y este estilo de verificación para estimar coste de romper criptografía de curvas elípticas.
- Rubin et al., PNAS 2024 — stopping power en fusión por confinamiento inercial.
- Jordan et al., Nature 2025 — Decoded Quantum Interferometry y OPI.
- Khattar et al., arXiv:2510.10967 — estimación de coste de DQI y decodificador Reed–Solomon.
- Reiher et al., PNAS 2017 — simulación de FeMoCo / fijación de nitrógeno.
- Low et al., PRX 2025 — algoritmos eficientes de block encoding y QROM.
- **Citación de la competición:** Tanuj Khattar, Nicholas Rubin, Craig Gidney, Michael Broughton, Guang Hao Low, Ryan Babbush, Sohier Dane, Brandon Horton, and María Cruz. Google Quantum AI - Verifiable Quantum Circuit Compilation. https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation, 2026. Kaggle.
