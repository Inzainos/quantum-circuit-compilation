# AGENTS.md — Quantum Circuit Compilation

Guía operativa para agentes de IA que trabajen en este repositorio (competición Google Quantum AI / Kaggle 2026).

## Qué es este proyecto

Compilación verificable de circuitos cuánticos (familia kickmix) para tres benchmarks: **invsqrt** (energía de fusión), **dqi** (optimización combinatoria) y **dfthcsos** (química cuántica, FeMoCo). Objetivo: reducir qubit count y Toffoli count por shot respecto al baseline, puntuado por media geométrica de mejoras.

## Reglas duras (no romper)

1. **Secretos solo por entorno.** Nunca hardcodear API keys/tokens. Usa `os.environ.get("NOMBRE", "")`.
2. **Cero datos sintéticos.** Los circuitos y datasets no se inventan; se derivan de los benchmarks oficiales.
3. **`data/`, `.venv/`, `results/` y `submission/` no se versionan** salvo el ZIP final de envío (`submission/final_submission.zip`) como artefacto. Los circuitos sueltos (`.kmb`, `.kmx`, `.npz`, `.fcidump`) superan el límite de 100 MiB de GitHub: usa Releases o Git LFS para versiones siguientes.
4. **No tocar los fuentes originales del paper** en `docs/` salvo para lectura.
5. **Los tests deben pasar** antes de commitear (`pytest tests/`).
6. **Git convention:** ramas `local/<feature>-v<version>`; nunca push directo a `main`.
7. **Verificación cerrada:** cada cambio en un circuito debe pasar el verificador kickmix (fuzz testing sobre inputs válidos y aleatorios, Fiat–Shamir seeded). No afirmar mejora sin medirla contra el baseline.

## Estructura del repositorio

```
quantum-circuit-compilation/
├── README.md                          # Competición, métricas, premios, timeline
├── pyproject.toml
├── benchmarks/
│   ├── fusion_energy/                 # invsqrt — 1/√x Phasing
│   ├── combinatorial_optimization/    # dqi — Reed–Solomon syndrome decoder
│   └── quantum_chemistry/             # dfthcsos — Hamiltonian Block Encoding (FeMoCo)
├── submission/                        # Plantilla y scripts para construir el ZIP de envío
├── src/                               # Código compartido, wraps kickmix, métricas, agentes AI
├── tests/                             # Pruebas de verificación de circuitos
├── docs/                              # Papers de referencia, glosario, contexto de dominio
├── results/                           # Mejores compilaciones encontradas (metrics.json, QASM)
├── verifiers/                         # Verificadores kickmix
├── kickmix/                           # Librería kickmix (Qualtran / Google)
├── verifiable_circuit_compilation.pdf
└── submmmission.zip                   # Artefacto de envío (no versionar cambios repetidos)
```

## Benchmarks y métricas

| Task | Benchmark | Cuello de botella | Métrica de coste |
|------|-----------|-------------------|------------------|
| invsqrt | I (Fusion Energy) | Phasing 1/√x por par de electrones | qubit count × Toffoli count por shot |
| dqi | II (Combinatorial Optimization) | Decodador reversible Reed–Solomon | coste + upper confidence bound de fallo |
| dfthcsos | III (Quantum Chemistry) | Tensor factorizations, Givens trees, QROMs | block encoding completo; >128 qubits en ANGLE = rechazo |

**Score:** `geometric_mean(improvement_invsqrt, improvement_dqi, improvement_dfthcsos)`

## Tecnología clave

- **kickmix library** (Qualtran, Google) — construye y hace fuzz-testing de circuitos con decenas de millones de puertas.
- Circuitos solo con puertas clásicas reversibles, puertas de fase y descomputación por medición.
- Verificación automática clásica: rastrea un bit por qubit + fase; válido para superposiciones por linealidad.
- Fiat–Shamir: inputs y mediciones se seeded con hash criptográfico salteado de la submission (no hay test set oculto).

## Estado actual (2026-10-27)

| Tarea | Estado | Evidencia |
|-------|--------|-----------|
| invsqrt | Mejora real ~6.5% (Q×C: 2,070,563 → 1,935,003) | `benchmarks/fusion_energy/optimized/metrics.json` |
| dqi | Sin optimización propia (esqueleto) | `src/dqi_from_zero.py`, `src/dqi_optimizer.py` |
| dfthcsos | Solo barrido de `brot`/`batch_size` | `results/dfthcsos_test/` |

`QubitTemporalManager` (`src/qubit_temporal_manager.py`) es solo contabilidad y no modifica ningún circuito.

## Formato del envío (ZIP)

| Archivo | Descripción |
|---------|-------------|
| `invsqrt.kmb` o `invsqrt.kmx` | Circuito invsqrt (kickmix) |
| `dqi.kmb` o `dqi.kmx` | Circuito dqi (kickmix) |
| `dfthcsos/angle_k_0`…`angle_k_<n-1>` | Circuitos angle numerados desde 0, sin gaps |
| `dfthcsos/submission.npz` | Factorización `(U, W, H2_I, H1_I, Hsym_lower)` + `tree_edges` |

Scoring del envío: ~45 minutos.

## Comandos principales

```bash
cd /home/deamon/quantum-circuit-compilation

# Tests de verificación
.venv/bin/python -m pytest tests/ -q

# Construir ZIP de envío
.venv/bin/python submission/build_submission.py

# Verificar un circuito individual con kickmix (según el verificador en verifiers/)
```

## Referencias

- Khattar et al. (arXiv:2610.23832) — paper acompañante de la competición.
- Babbush et al. (arXiv:2603.28846) — kickmix circuits.
- Citación: Tanuj Khattar, Nicholas Rubin, Craig Gidney, Michael Broughton, Guang Hao Low, Ryan Babbush, Sohier Dane, Brandon Horton, María Cruz. Google Quantum AI - Verifiable Quantum Circuit Compilation. Kaggle, 2026.
