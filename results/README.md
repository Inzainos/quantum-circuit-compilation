# results — Mejores compilaciones encontradas

Este directorio almacena los resultados de las optimizaciones ejecutadas.

## Estructura sugerida
```
results/
├── fusion_energy/
│   ├── best_circuit_qasm/
│   └── metrics.json
├── combinatorial_optimization/
│   ├── best_circuit_qasm/
│   └── metrics.json
└── quantum_chemistry/
    ├── best_circuit_qasm/
    └── metrics.json
```

Cada `metrics.json` debería incluir:
- `gate_count` (total, T, CNOT, single-qubit)
- `depth`
- `qubit_count`
- `error` / precisión vs. baseline
- `timestamp`
- `agent_or_method_used`
