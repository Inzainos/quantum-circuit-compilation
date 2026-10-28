# submission — Construcción del ZIP de envío

Este directorio contiene scripts y plantillas para generar el archivo ZIP que se envía a la competición.

## Estructura requerida del ZIP

```
submission.zip/
├── invsqrt.kmb          (o invsqrt.kmx)
├── dqi.kmb              (o dqi.kmx)
└── dfthcsos/
    ├── angle_k_0.kmb    (o .kmx)
    ├── angle_k_1.kmb    (o .kmx)
    ├── ...
    ├── angle_k_<n-1>.kmb (o .kmx)
    └── submission.npz   # factorización + árbol de Givens
```

### Reglas críticas

1. Los archivos `angle_k_*` deben estar numerados desde **0** con **no gaps** (0, 1, 2, ..., n-1).
2. Cualquier circuito ANGLE con **más de 128 qubits es rechazado**.
3. `submission.npz` debe contener:
   - Factorización: `U`, `W`, `H2_I`, `H1_I`, `Hsym_lower`
   - Árbol de Givens: `tree_edges`

## Cómo construir el envío

```bash
# Desde la raíz del proyecto
python submission/build_submission.py \
    --invsqrt benchmarks/fusion_energy/optimized/invsqrt.kmb \
    --dqi benchmarks/combinatorial_optimization/optimized/dqi.kmb \
    --dfthcsos-dir benchmarks/quantum_chemistry/optimized/dfthcsos/ \
    --npz benchmarks/quantum_chemistry/optimized/submission.npz \
    --output submission.zip
```

## Formatos de archivo

- **`.kmb`**: formato binario kickmix (Qualtran)
- **`.kmx`**: formato kickmix alternativo
- **`.npz`**: archivo NumPy comprimido con múltiples arrays

## Verificación previa al envío

Antes de subir, asegúrate de:

1. Todos los archivos `angle_k_*` existen y están numerados secuencialmente desde 0.
2. Ningún circuito ANGLE excede 128 qubits.
3. `submission.npz` contiene todas las claves requeridas (`U`, `W`, `H2_I`, `H1_I`, `Hsym_lower`, `tree_edges`).
4. Los circuitos pasan el simulador kickmix (fuzz testing con inputs aleatorios).
5. Los scratch qubits quedan limpios al final de cada circuito.

## Scoring

El scoring tarda aproximadamente 45 minutos por envío. La puntuación usa la media geométrica de la mejora de cada tarea relativa al baseline.
