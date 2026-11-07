# Análisis de QROM para Inversión GF(2^12) en DQI

Fecha: 2026-11-07
Estado: QROM descartada para permutaciones; TowerInv2 75 Toffoli mantenido

## Resumen
Se probó reemplazar TowerInv2 (75 Toffoli) por QROM de tabla precomputada para la inversión en GF(2^12) y subcampos.

**Resultado**: QROM para permutaciones requiere O(2^n) init_and, peor que circuito aritmético.

## Intentos

### 1. inv8_qrom (GF(8), 8 entradas)
- Patrón angle_k: árbol one-hot con 7 init_and
- Coste real: 6 Toffoli (vs 3 Toffoli nativo con ANF cuadrática)
- **Conclusión**: 2x peor

### 2. inv64_qrom (GF(64), 64 entradas)
- Tabla de inversión en coordenadas internas precomputada
- Patrón angle_k recursivo: 5 niveles, pero tabla es permutación completa
- Cada hoja diferente → sin sharing → 63 init_and
- Coste real: 62 Toffoli (vs 21 Toffoli nativo en TowerInv2)
- **Conclusión**: 3x peor

### 3. Análisis teórico
Para inversión en GF(2^n):
- Circuito aritmético (torre): O(n log n) Toffoli ≈ 75 para n=12
- QROM tabla completa: 2^n - 1 init_and = 4095 para n=12
- QROM solo gana cuando tabla tiene redundancia (muchas entradas iguales)
- En angle_k, ángulos se repiten → sharing en árbol
- En inversión, cada entrada es única → sin sharing → QROM ineficaz

## TowerInv2 actual (75 Toffoli)
- Nivel 12→6: 18 (mul6) + inv6(21) + 36 (mul6) = 75
- Nivel 6→3: usa inv8(3) ANF cuadrática
- ya es near-optimal para circuito reversible estático

## Optimización alternativa: ejecución condicional
Idea: solo ejecutar inversión cuando f=[sigma(r)==0] (≈36/4095 posiciones)
- Ahorro teórico: 75 * 4059/4095 ≈ 74 Toffoli/posición
- Requiere: circuito controlado cuánticamente por f, o circuitos dinámicos
- kickmix estático no soporta branching cuántico eficiente
- Controlar cada init_and en TowerInv2 → CCCX costoso

## Decisión
Mantener TowerInv2 (75 Toffoli) en submission actual.
- DQI total: 784,172 Toffoli
- scan_pos: 401,310 (98/posición)
- Próximos pasos viables:
  1. MBU en phase (ya aplicado: del_and = HMR+CZ)
  2. Reutilización scaffolding entre posiciones
  3. Conditional execution requiere redesign mayor

## Artefactos
- submission/submission_iter1.zip: 784172 Toffoli, Q=2016 (estable)
- src/dqi_decoder_v1.py: reutilización registros
- docs/PLAN_SCAN_OPT_MBU.md: plan condicional