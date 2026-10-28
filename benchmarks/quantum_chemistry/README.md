# Benchmark: dfthcsos — Quantum Chemistry & Clean Energy (Hamiltonian Block Encoding)

## Objetivo de la tarea

Co-optimizar factorizaciones tensoriales clásicas, árboles de rotaciones de Givens y tablas de búsqueda cuánticas (QROMs) para simular FeMoCo — el catalizador biológico detrás de la fijación de nitrógeno.

## Contexto científico

La producción industrial de fertilizantes depende del proceso Haber–Bosch, que convierte nitrógeno del aire en amoniaco a alta temperatura y presión. Las bacterias hacen lo mismo a temperatura ambiente usando la enzima nitrogenasa, cuyo sitio activo es un cluster de hierro, molibdeno y azufre conocido como **FeMoCo**. Sus electrones están tan fuertemente correlacionados que los computadores clásicos no pueden predecir fiablemente su química. Un computador cuántico podría calcular la energía de cada paso de la reacción y revelar cómo lo hace la naturaleza (Reiher et al., PNAS 2017).

El algoritmo es **estimación de fase cuántica**, que aplica repetidamente un circuito que codifica el Hamiltoniano de la molécula (el operador que da su energía). El Hamiltoniano se especifica por una tabla enorme de números: para N orbitales, aproximadamente N⁴ de ellos. Los algoritmos más eficientes conocidos (Low et al., PRX 2025) comprimen esta tabla con una factorización tensorial, streaman los datos comprimidos en el computador cuántico con circuitos QROM (quantum read-only memory: tablas de búsqueda que funcionan en una superposición de direcciones a la vez), y lo aplican como secuencias de rotaciones de Givens (rotaciones que mezclan pares de orbitales). Estas búsquedas y rotaciones controladas dominan el conteo de Toffoli.

Esta tarea acopla diseño clásico y cuántico. Tu elección de factorización afecta tanto cuántos datos tienen que cargar los circuitos como cuántas veces la estimación de fase tiene que repetirlos, y debe reproducir las energías de la molécula con precisión. Los circuitos de lookup que cargan los datos de ángulo son tuyos para diseñar, al igual que el árbol clásico de Givens y la precisión en bits. Las puertas de preparación de estado y las rotaciones de Givens, que no son circuitos kickmix, se preciosan con fórmulas analíticas.

## Archivos de envío

| Archivo | Formato |
|---------|---------|
| `dfthcsos/angle_k_0.kmb` o `.kmx` | Circuito ANGLE para k=0 |
| `dfthcsos/angle_k_1.kmb` o `.kmx` | Circuito ANGLE para k=1 |
| … | … |
| `dfthcsos/angle_k_<n-1>.kmb` o `.kmx` | Circuito ANGLE para k=n-1 (último, sin gaps desde 0) |
| `dfthcsos/submission.npz` | Factorización `(U, W, H2_I, H1_I, Hsym_lower)` y árbol de Givens `tree_edges` |

### Reglas importantes

- Los archivos `angle_k_*` deben estar numerados desde **0** con **no gaps**.
- Cualquier circuito ANGLE con **más de 128 qubits es rechazado**.
- `submission.npz` debe contener la factorización `(U, W, H2_I, H1_I, Hsym_lower)` y el árbol de Givens `tree_edges`.

## Métrica de coste (Benchmark III)

La función de pérdida para esta tarea cubre **todo el block encoding**, no solo los circuitos ANGLE enviados. Incluye:

- **Qubit count** y **Toffoli count** (por shot) para todo el block encoding
- Factorización tensorial clásica (afecta cuántos datos cargan los circuitos y cuántas veces se repite la estimación de fase)
- Árbol de rotaciones de Givens
- Circuitos QROM y lookup tables
- Coste analítico de las puertas de preparación de estado y rotaciones de Givens (no son kickmix)

La puntuación final usa la media geométrica de las mejoras de las tres tareas.

## Métricas objetivo

- Reducción de tamaño de QROM (puertas de lookup)
- Optimización de árboles de rotaciones de Givens
- Factorización tensorial clásica óptima (menos datos para cargar, menos repeticiones de estimación de fase)
- Precisión energética química (< 1 kcal/mol típico)
- Circuitos ANGLE ≤ 128 qubits

## Estructura del benchmark

```
quantum_chemistry/
├── baseline/          # Block encoding baseline de FeMoCo
├── optimized/         # Mejores compilaciones encontradas
├── tests/             # Verificación de precisión energética
├── submission/        # Plantilla para generar dfthcsos/ + submission.npz
└── results.md         # Métricas: QROM size, Givens tree, error energético, comparación vs baseline
```

## Estado

Pendiente de implementación del circuito baseline.

## Referencias

- Reiher et al., PNAS 2017 — simulación de FeMoCo / fijación de nitrógeno.
- Low et al., PRX 2025 — block encoding eficiente y QROMs.
- Proceso Haber–Bosch vs. nitrogenasa biológica — contexto de energía y fertilizantes.
