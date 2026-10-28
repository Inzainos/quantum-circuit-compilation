# Baseline invsqrt — Benchmark I (Fusion Energy)

## Circuito de referencia

- Archivo: `benchmarks/fusion_energy/baseline/invsqrt_ref.kmb`
- Generado con: `verifiers/invsqrt/nr_reference_circuit.py --n-p 10 --format kmb`
- Algoritmo: Newton-Raphson de 3 pasos (normalización → polinomio cúbico por trozos → iteración NR) + phase por bits con Z_POW + uncompute inversa

## Métricas de verificación (baseline)

| Métrica | Valor | Notas |
|---------|-------|-------|
| Status | PASS | Verificado con `--max-x 10000 --shots-per-x 64` |
| Score (Q × C) | 2,070,563 | Objetivo: minimizar |
| Q (num_qubits) | 260 | Registro `x` (22) + scratch (238) |
| Toffoli count | 7,735 | Mean Toffoli-like gates per shot |
| T count | 1.0 | Puertas T puras |
| Rotation count | 37 | Rotaciones Z_POW no-Clifford |
| Rotation eps | 3.74e-11 | Error de síntesis de rotaciones |
| C (toffoli_equivalent) | 7,963.70 | Toffolis + T/4 |
| Num ops | 62,160 | Total de operaciones en el circuito |
| Reaction depth | 4,005 | Profundidad del circuito |
| Verified shots | 640,000 | 10,000 valores × 64 shots |
| Worst error/tolerance | 0.43 | x=729, margen de seguridad |
| Circuit SHA-256 | e2bf8eb6... | Identificador del circuito |

## Circuito optimizado dbhexa

- Archivo: `benchmarks/fusion_energy/optimized/invsqrt_dbhexa_opt2.kmb`
- Generado con: `verifiers/invsqrt/nr_reference_circuit.py --n-p 10 --format kmb` con precisión reducida
- Optimización: `result_bits=28 → 27` (reduce Q en 1 y Toffolis en 88)

## Métricas de verificación (dbhexa optimizado)

| Métrica | Valor | Mejora vs baseline |
|---------|-------|-------------------|
| Status | PASS | Verificado con `--max-x 10000 --shots-per-x 64` |
| Score (Q × C) | 1,880,870 | **−9.1%** |
| Q (num_qubits) | 254 | −6 (−2.3%) |
| Toffoli count | 7,405 | −330 (−4.3%) |
| T count | 1.0 | sin cambio |
| Rotation count | 35 | −2 |
| Rotation eps | 5.91e-11 | similar |
| C (toffoli_equivalent) | 7,618.12 | −345 (−4.3%) |
| Num ops | 59,598 | −2,562 |
| Reaction depth | 3,840 | −165 |
| Verified shots | 640,000 | mismo |
| Worst error/tolerance | 0.70 | x=182, margen aceptable |
| Circuit SHA-256 | ed464ced... | Identificador del circuito |

## Especificación del problema (invsqrt)

| Parámetro | Valor |
|-----------|-------|
| n_p | 10 bits por componente de momento |
| width | 22 qubits (registro `x`) |
| max_x | 3,133,452 |
| beta | 1 |
| precision_bits | 24 |
| shots_per_x | 64 (benchmark completo) |
| Tol(x) | 2^-24 × beta / sqrt(x) |

## Parámetros de precisión dbhexa optimizados

| Parámetro | Baseline | dbhexa optimizado |
|-----------|----------|-------------------|
| delta_bits | 14 | 14 (sin cambio — crítico para precisión) |
| coef_bits | 17 | 17 (sin cambio) |
| square_bits | 28 | 27 (−1 bit) |
| product_bits | 28 | 27 (−1 bit) |
| result_bits | 29 | 27 (−2 bits) |

## Plan de optimización adicional

Para reducir aún más el score (objetivo: <1.5M):

1. **Reducir más bits de precisión**: `result_bits=26` ya falla (overflow o error demasiado grande). `square_bits=26` o `product_bits=26` también fallan. Llegamos al límite de precisión con esta arquitectura.

2. **Reducir Toffoli count**: 7,405 por shot. Oportunidades:
   - Mejor aproximación inicial (menos iteraciones Newton)
   - Multiplicadores truncados más agresivos
   - Compartir subexpresiones entre etapas

3. **Reducir rotaciones**: 35 rotaciones Z_POW. Cada una añade coste T vía `rotation_t_count(eps)`.

## Verificadores disponibles

- `verifiers/invsqrt/verify_submission_invsqrt.py` — verificador oficial
- `verifiers/invsqrt/nr_reference_circuit.py` — circuito de referencia Newton-Raphson

## Comandos útiles

```bash
# Generar circuito de referencia
.venv/bin/python verifiers/invsqrt/nr_reference_circuit.py invsqrt.kmb --n-p 10

# Verificar (rápido, subset)
.venv/bin/python verifiers/invsqrt/verify_submission_invsqrt.py invsqrt.kmb --n-p 10 --max-x 1000 --shots-per-x 64

# Verificar (completo, ~200M shots)
.venv/bin/python verifiers/invsqrt/verify_submission_invsqrt.py invsqrt.kmb --n-p 10

# Ver métricas del circuito
.venv/bin/python -c "
import kickmix as km
c = km.Circuit.from_file('invsqrt.kmb')
print('Qubits:', c.num_qubits)
print('Toffolis:', c.operation_statistics().num_toffoli_like)
print('Ops:', len(c))
"
```
