# Formato de archivo de envío — Referencia técnica

Este documento detalla el formato exacto requerido para el ZIP de envío de la competición.

## Estructura del ZIP

```
submission.zip
├── invsqrt.kmb                    # O invsqrt.kmx
├── dqi.kmb                        # O dqi.kmx
└── dfthcsos/
    ├── angle_k_0.kmb              # O .kmx (circuito ANGLE k=0)
    ├── angle_k_1.kmb              # O .kmx (circuito ANGLE k=1)
    ├── ...                         # sin gaps, numerados desde 0
    ├── angle_k_<n-1>.kmb          # Último circuito ANGLE
    └── submission.npz             # Factorización + árbol de Givens
```

## Formatos de archivo

### .kmb / .kmx (kickmix)

Formatos de circuito de la librería kickmix (Qualtran, Google). Contienen:
- Secuencia de puertas (reversibles clásicas, fase diagonal, medición)
- Número de qubits
- Metadatos del circuito

### .npz (NumPy)

Archivo comprimido de NumPy que contiene:

| Clave | Descripción |
|-------|-------------|
| `U` | Matriz de factorización (parte de la factorización tensorial) |
| `W` | Matriz de factorización |
| `H2_I` | Componente del Hamiltoniano |
| `H1_I` | Componente del Hamiltoniano |
| `Hsym_lower` | Parte triangular inferior del Hamiltoniano simétrico |
| `tree_edges` | Árbol de rotaciones de Givens (bordes del árbol) |

## Reglas de validación

1. **Numeración angle_k_***: debe comenzar en 0 y no tener gaps.
   - Válido: `angle_k_0, angle_k_1, angle_k_2`
   - Inválido: `angle_k_1, angle_k_2` (falta el 0)
   - Inválido: `angle_k_0, angle_k_2` (gap en el 1)

2. **Límite de qubits**: cualquier circuito ANGLE con > 128 qubits es rechazado automáticamente.

3. **submission.npz**: debe contener todas las claves: `U, W, H2_I, H1_I, Hsym_lower, tree_edges`.

## Ejemplo de uso del script de construcción

```bash
cd quantum-circuit-compilation

python submission/build_submission.py \
    --invsqrt benchmarks/fusion_energy/optimized/invsqrt.kmb \
    --dqi benchmarks/combinatorial_optimization/optimized/dqi.kmb \
    --dfthcsos-dir benchmarks/quantum_chemistry/optimized/dfthcsos \
    --npz benchmarks/quantum_chemistry/optimized/submission.npz \
    --output submission/final_submission.zip
```

## Scoring

- Tiempo aproximado: 45 minutos por envío.
- Métrica: media geométrica de la mejora de cada tarea relativa al baseline.
- No hay test set oculto: los inputs aleatorios se seeded con un hash criptográfico salteado de tu submission (Fiat–Shamir).
