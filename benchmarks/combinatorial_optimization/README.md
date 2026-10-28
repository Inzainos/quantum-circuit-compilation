# Benchmark: dqi — Combinatorial Optimization (Decoded Quantum Interferometry)

## Objetivo de la tarea

Optimizar decodadores reversibles de síndrome de Reed–Solomon para Interferometría Cuántica Decodada (DQI) en el problema de Intersección Polinómica Óptima (OPI) sobre campos finitos.

## Contexto científico

Supón que en cada input de un campo finito, te dan un conjunto de valores de salida permitidos, y tu objetivo es encontrar un polinomio de bajo grado cuya curva caiga dentro de la mayor cantidad posible de esos conjuntos permitidos. Este problema se llama **Optimal Polynomial Intersection (OPI)** (estrechamente relacionado con list recovery en teoría de codificación). Verificar cuántos conjuntos acierta un polinomio propuesto toma milisegundos en un ordenador ordinario, sin embargo, cuando los conjuntos permitidos son grandes (cerca de la mitad del campo en cada punto en nuestro benchmark), encontrar un polinomio óptimo o casi óptimo parece estar más allá del alcance de los algoritmos clásicos conocidos. Esa combinación hace de OPI un candidato líder para una ventaja cuántica verificable (Jordan et al., Nature 2025).

**Decoded Quantum Interferometry (DQI)** aborda OPI usando la transformada de Fourier cuántica para transformar este problema de optimización difícil en un problema clásico de corrección de errores: decodificar un código de Reed–Solomon —la misma familia de códigos usada para leer códigos QR rayados, CDs dañados y transmisiones espaciales ruidosas. Los computadores clásicos decodifican un solo codeword de Reed–Solomon rápidamente usando herramientas como el algoritmo de Euclides extendido, y Khattar et al. (arXiv:2510.10967) estiman que DQI podría resolver instancias de OPI intratables clásicamente con solo unos pocos millones de puertas Toffoli —con el decodador de Reed–Solomon representando más del 90% del coste total del circuito.

El problema es que en DQI, este decodador debe ejecutarse **dentro** del computador cuántico: de forma reversible, sobre una superposición masiva de patrones de error a la vez, y dejando cero basura scratch detrás para que la interferencia cuántica pueda amplificar constructivamente polinomios de alta puntuación. En DQI optimizado, el patrón de error se borra temprano vía measurement-based uncomputation, dejando tras de sí un signo de fase ±1. El trabajo de tu circuito es recuperar ese signo desde los síndromes de error (una huella compacta de los errores), cancelarlo y limpiar todos los qubits de espacio de trabajo.

Inusualmente, tu decodador ni siquiera tiene que ser perfecto: porque cada candidato a polinomio muestrado por DQI se verifica clásicamente al final de todas formas, un fallo ocasional de decodación solo añade una pequeña sobrecarga de repetición —un intercambio capturado directamente en la puntuación.

## Archivo de envío

| Archivo | Formato |
|---------|---------|
| `dqi.kmb` o `dqi.kmx` | Circuito kickmix de dqi |

## Métrica de coste (Benchmark II)

La función de pérdida para esta tarea incluye:

- **Qubit count** (número de qubits lógicos por shot)
- **Toffoli count** (número de puertas Toffoli por shot)
- **Upper confidence bound sobre la tasa de fallo del decodador** — porque el decodador no tiene que ser perfecto, un fallo ocasional añade sobrecarga de repetición capturada en el score.

La puntuación final usa la media geométrica de las mejoras de las tres tareas.

## Métricas objetivo

- Reducción de Toffoli count del decodador de síndrome (más del 90% del coste del circuito DQI)
- Tasa de fallo del decodador (upper confidence bound)
- Corrección reversible sobre campos finitos
- Scratch qubits limpios al final (measurement-based uncomputation)

## Estructura del benchmark

```
combinatorial_optimization/
├── baseline/          # Decodador Reed–Solomon reversible baseline
├── optimized/         # Mejores compilaciones encontradas
├── tests/             # Verificación de corrección de síndromes
├── submission/        # Plantilla para generar dqi.kmb/.kmx
└── results.md         # Métricas: Toffoli count, qubit count, tasa de fallo, comparación vs baseline
```

## Estado

Pendiente de implementación del circuito baseline.

## Referencias

- Jordan et al., Nature 2025, arXiv:2510.10967 — Decoded Quantum Interferometry y OPI.
- Khattar et al. (arXiv:2510.10967) — estimación de coste de DQI y decodador Reed–Solomon.
- List recovery en teoría de codificación — problema relacionado con OPI.
