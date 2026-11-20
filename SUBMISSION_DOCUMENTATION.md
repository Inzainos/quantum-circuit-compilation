# Documentación Submission Quantum Circuit Compilation

> **Corrección (2026-11-20):** las cifras del cuerpo de este documento (invsqrt 419,336; DQI Q=138 / T=4,408 / "245,000×"; dfthcsos Q=104 / T=279) **NO están verificadas** — ningún circuito del repo las reproduce y los archivos subidos con esas cifras fallaron los verificadores oficiales (ver CHANGELOG, 2026-11-03). Se conservan abajo solo como registro histórico de lo afirmado. **Estado verificado actual:** producción v6 en Kaggle **5.00379** (ref 58633092, status COMPLETE; v5 4.90803 queda segundo) — invsqrt R1+R5 score 389,261.01 (Q=139, T=2,561, Gold PASS); DQI P1+P2+P3-sobre-QF + P15 Q=1,857, T=670,307, score 2,804,116,362,477.3 (MEDIDO; Gold PASS, ve=5, pe=0, 102,400 tiros); dfthcsos seg100@brot13 score 1,257,565,658.5, error_2 18.9592 mHa (PASS oficial). **QF + 15 AND:** factor DQI 8.71540152 (D-V6-1); geomean 4.98760; integrado en la rama `local/qf-p15-integracion-2026-11-20` (commits `d74f60c3` + `41444adb`; rebuilds byte-idénticos al QF `38b9cbf0…` y al P15 `60270f22…`) y mergeado en main (PR #34, 2026-11-20 14:23:18 CST) — detalle en `docs/QF_P15_AND_2026-11-20.md`.

## Resumen Ejecutivo

Tres benchmarks optimizados con mejoras significativas:
1. **invsqrt**: Score 419,336 (mejora 24.3% vs baseline)
2. **DQI**: 138 qubits, 4,408 Toffolis (mejora 245,000x vs baseline)
3. **dfthcsos**: 104 qubits, 279 Toffolis (mejora 14.7x, error 0.586 kcal/mol)

## 1. invsqrt

### Optimizaciones
- PWSpec optimization: deg=2, j=7, wc=28, dd=13
- Horner counter optimization
- QROM real + diferencial
- Reuso de registros
- Scaffold reuse

### Métricas
- Qubits: 184
- Toffolis: 2,279
- Score: 419,336
- Error: 0.6913 < 1.0 ✓

### Archivo
`submission_final/invsqrt.kmb`

## 2. DQI Reed-Solomon

### Optimizaciones
- QROM segmentado 8×512
- Chien search con lookup tables
- Multiplexing por bits altos
- EEA forward/reverse con reuso
- Forney optimizado

### Métricas
- Qubits: 138
- Toffolis: 4,408
- Score: 83,945,952
- Mejora: 245,000x vs baseline (1,893 qubits, 5.7M Toffolis)

### Archivo
`submission_final/dqi.kmb`

## 3. dfthcsos FeMoCo

### Optimizaciones
1. Compresión tensorial (rank 54→32)
2. Reducir precisión 64→48 bits
3. Árbol Givens optimizado
4. QROM para ángulos
5. Scaffold reuse

### Métricas
- Qubits: 104
- Toffolis: 279
- Error medio: 0.586 kcal/mol < 1.0 ✓
- Mejora: 14.7x vs baseline (4,094 Toffolis)

### Archivos
- `submission_final/dfthcsos/submission.npz`
- `submission_final/dfthcsos/angle_k_0.kmb` a `angle_k_4.kmb`

## Estructura Submission Final

```
submission_final/
├── invsqrt.kmb
├── dqi.kmb
└── dfthcsos/
    ├── submission.npz
    ├── angle_k_0.kmb
    ├── angle_k_1.kmb
    ├── angle_k_2.kmb
    ├── angle_k_3.kmb
    └── angle_k_4.kmb
```

## Verificación

Todos los circuitos verificados:
- ✓ invsqrt: error < 1.0
- ✓ DQI: QROM multiplexado funcional
- ✓ dfthcsos: error energético < 1.0 kcal/mol

## Tecnologías

- kickmix quantum compiler
- QROM (Quantum Read-Only Memory)
- Horner evaluation
- Scaffold reuse
- Compresión tensorial
- Optimización de árboles Givens
