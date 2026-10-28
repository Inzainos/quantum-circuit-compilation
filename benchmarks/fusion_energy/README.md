# Benchmark: invsqrt — Fusion Energy (1/√x Phasing)

## Objetivo de la tarea

Comprimir circuitos de raíz cuadrada inversa en punto fijo para interacciones de Coulomb par a par usados para modelar el poder de frenado de partículas alfa en plasmas cálidos densos durante fusión por confinamiento inercial.

## Contexto científico

En fusión por confinamiento inercial, láseres comprimen una pequeña cápsula de combustible a temperaturas y densidades extremas. Si el combustible se ignita depende de qué tan rápido las partículas cargadas rápidas (como las partículas alfa liberadas por reacciones de fusión) depositan su energía en el combustible circundante. Esta tasa se llama **stopping power**. En el camino hacia la ignición, el combustible atraviesa **warm dense matter**, un estado demasiado caliente y denso para teorías estándar y difícil de sondear experimentalmente, lo que hace del stopping power una incertidumbre clave en el diseño del blanco (Rubin et al., PNAS 2024).

Un computador cuántico puede simular los electrones directamente. Almacena la posición de cada electrón en un grid 3D y avanza el tiempo alternando entre actualizaciones de energía cinética y energía potencial. La energía potencial es la repulsión de Coulomb entre cada par de electrones, proporcional a 1/distancia. Para cada par, el circuito calcula la distancia al cuadrado `x`, phases por `1/√x` con aproximadamente 7 dígitos significativos (un error relativo de 2⁻²⁴), y limpia cualquier trabajo scratch. Con 2¹⁸ electrones, hay 23,653 pares por time step, por lo que esta subroutine domina el coste de toda la simulación.

La tarea la aísla: dado `x`, aplica la fase correcta para cada valor posible de `x`.

Puedes reconocer la versión clásica de este problema. El famoso "fast inverse square root" del videojuego Quake III combina una primera conjetura ingeniosa con un paso del método de Newton. La versión cuántica debe ser reversible, usar aritmética en punto fijo, y ser mucho más precisa. El circuito reference sigue la misma receta; eres libre de encontrar uno mejor.

## Archivo de envío

| Archivo | Formato |
|---------|---------|
| `invsqrt.kmb` o `invsqrt.kmx` | Circuito kickmix de invsqrt |

## Métrica de coste (Benchmark I)

La función de pérdida para esta tarea se basa en:

- **Qubit count** (número de qubits lógicos por shot)
- **Toffoli count** (número de puertas Toffoli por shot)

El coste combinado determina la mejora relativa al baseline. La puntuación final usa la media geométrica de las mejoras de las tres tareas.

## Métricas objetivo

- Reducción de conteo de puertas Toffoli (impulsa el tiempo de ejecución)
- Reducción de qubit count lógico (impulsa el tamaño de la máquina)
- Precisión: 7 dígitos significativos, error relativo ≤ 2⁻²⁴
- Circuitos reversibles, aritmética en punto fijo, scratch qubits limpios al final

## Estructura del benchmark

```
fusion_energy/
├── baseline/          # Circuito invsqrt baseline (referencia)
├── optimized/         # Mejores compilaciones encontradas
├── tests/             # Verificación de precisión contra 1/√x
├── submission/        # Plantilla para generar invsqrt.kmb/.kmx
└── results.md         # Métricas: Toffoli count, qubit count, error, comparación vs baseline
```

## Estado

Pendiente de implementación del circuito baseline.

## Referencias

- Rubin et al., PNAS 2024 — stopping power en fusión por confinamiento inercial.
- Khattar et al. (arXiv:2610.23832) — kickmix package y verificación.
- Fast inverse square root (Quake III) — inspiración para la primera conjetura + Newton.
