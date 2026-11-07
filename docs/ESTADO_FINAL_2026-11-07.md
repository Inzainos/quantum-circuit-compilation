# Estado Final - Google Verifiable Quantum Circuit Competition
## Entrega validada: submission/submission_final.zip

**Fecha:** 2026-11-07  
**Branch:** local/quantum-dqi-v2.0.0  
**Commit HEAD:** cde4a38 (docs: análisis QROM inversión - descartada para permutaciones)

---

## 1. Resumen de la entrega

| Benchmark | Archivo | Qubits | Toffoli | SHA256 |
|-----------|---------|--------|---------|--------|
| invsqrt (Fusion Energy) | invsqrt.kmb | 139 | 2,561 | 7e842bbfba8fb40d32c05b3b195073cf368981a92de77197ed22bd3a3f3faf79 |
| dqi (Combinatorial Opt.) | dqi.kmb | 2,016 | 784,172 | 2b9eb49fd404d5cc81516f1c3b8271229c16c45506f3e84c73e70df78a06dbec |
| dfthcsos (FeMoCo) | angle_k_0..9.kmx + submission.npz | 119 c/u | 3,974 c/u | desde commit fb4e95b |

**Tamaño ZIP:** 59 MB  
**Estructura:** ✓ invsqrt.kmb, dqi.kmb, dfthcsos/angle_k_0..9.kmx, dfthcsos/submission.npz (sin gaps)

---

## 2. Perfil DQI (benchmark II) - kmx_profile estático

```
TOTAL: 784,172 Toffoli (0 condicionados)
├── scan_pos:       401,310 (51.18%)  ← 98 Toffoli/posición × 4,095
├── bm_update:      150,984 (19.25%)
├── bm_disc:         71,766 (9.15%)
├── omega_fwd:       42,315 (5.40%)
└── omega_rev:       42,315 (5.40%)
```

**Descomposición scan_pos/posición (teórica):**
- Inversión torre GF(2¹²): 75 Toffoli
- Test cero f=[s==0]: 11 init_and + 11 del_and (MBU) = 11 Toffoli
- Fase g_a = f AND u_a + CZ: 12 init_and + 12 del_and (MBU) = 12 Toffoli
- **Total: 98 Toffoli/posición** (con MBU en del_and = HMR+CZ, 0 Toffoli uncompute)

---

## 3. Optimizaciones aplicadas y verificación

### 3.1 Reutilización de registros (commit 49ca352)
```python
# Antes: alloc/free dentro del bucle (4095 veces)
for p in positions:
    s = b.alloc_qubits(DEG); ...

# Después: alloc una vez, reuse
s = b.alloc_qubits(DEG); u = b.alloc_qubits(DEG); dd = b.alloc_qubits(DEG); ...
for p in positions:
    ...
for q in (s, u, dd, w, t, lad, g): b.free(q)
```
**Impacto:** Elimina presión temporal de qubits, sin cambio en Toffoli estático.

### 3.2 MBU (Measurement-Based Uncomputation) - Nativo en kickmix
- `del_and` = HMR (Hadamard-Measure-Reset) + CZ condicionado
- **0 Toffoli** para descomputar ANDs
- Verificado en: `dqi_tower_inv.py::mul6_del`, `dqi_bm_stage_v1.py::_disc_clear`, `angle_k_reference_circuit.py`

### 3.3 TowerInv2 - Inversión GF(2¹²) en 75 Toffoli
```
Nivel 12→6: a = a0 + a1·y, N = a0² + a0·a1 + ν·a1², a⁻¹ = N⁻¹·((a0+a1) + a1·y)
  18 (mul6) + inv6(21) + 36 (mul6) = 75 Toffoli
Nivel 6→3: idem con ν'; inv3 = función cuadrática 3 bits (3 AND, sin mult.) = 21 Toffoli
```
**Near-optimal** para circuito aritmético reversible estático.

---

## 4. Optimizaciones evaluadas y descartadas

### 4.1 QROM para inversión (docs/INVERSION_QROM_ANALYSIS.md)

| QROM | Entradas | Toffoli | Nativo | Ratio | Veredicto |
|------|----------|---------|--------|-------|-----------|
| inv8_qrom (angle_k style) | 8 | 6 | 3 (ANF) | 2× peor | ❌ |
| inv64_qrom (tabla completa) | 64 | 62 | 21 (TowerInv2 L6) | 3× peor | ❌ |

**Causa raíz:** Inversión en GF(2ⁿ) es **permutación completa** (cada entrada única) → sin sharing en árbol one-hot QROM.  
**angle_k QROM funciona** porque ángulos se repiten (muchas entradas iguales).

### 4.2 Ejecución condicional con `push_condition(f)`

| Enfoque | Toffoli estático | Funciona |
|---------|------------------|----------|
| `b.push_condition(f_bit_clasico)` + HMR de f | 784,172 (sin cambio) | ✓ compila, no reduce |
| `b.push_condition(f_qubit)` | `TypeError: Expected km.b` | ✗ no soportado |
| Controlar cada `init_and` en TowerInv con f | Requiere CCCX → +coste | ✗ peor |

**Conclusión:** kickmix **compila ambas ramas estáticamente**. `push_condition` solo anota operaciones para el verificador, no reduce el conteo estático de Toffoli que usa la métrica de competición. La probabilidad `f=1 ≈ 1/4095` no se traduce en ahorro estático.

### 4.3 EEA (Extended Euclidean Algorithm) - Reference decoder
- **5.7M Toffoli** (vs 784k BM v7) - descartado por coste

---

## 5. Tests de verificación

```bash
$ .venv/bin/python -m pytest tests/ -q
33 passed, 1 warning in 4.68s
```

**Verificadores kickmix:**
- invsqrt: fuzz testing pasa (error < 1.0)
- dqi: fuzz testing pasa (error < 1.0)  
- dfthcsos: factorización válida, circuitos < 128 qubits

---

## 6. Archivos clave del repositorio

### Código principal
```
src/
├── dqi_decoder_v1.py          # BM decoder v7 con register reuse (784k Toffoli)
├── dqi_tower_inv2.py          # TowerInv2 (75 Toffoli) - autoritativo
├── dqi_tower_inv_qrom.py      # QROM inv8/inv64 (descartado, 6/62 Toffoli)
├── dqi_bm_stage_v1.py         # Berlekamp-Massey stage
├── dqi_omega_stage.py         # Omega in-place
├── dqi_scan_stage.py          # Scan stage original (referencia)
├── invsqrt_logshift2.py       # invsqrt optimizado (log-shift2)
└── submission/
    └── rebuild_valid_zip.py   # Reconstruye ZIP final
```

### Documentación
```
docs/
├── OPTIMIZACION_DQI_SCAN.md        # Hot-spot map y registro reuse
├── PLAN_SCAN_OPT_MBU.md            # Plan condicional (no reduce estático)
├── INVERSION_QROM_ANALYSIS.md      # Análisis QROM descartada
├── ESTADO_FINAL_2026-11-07.md      # Este archivo
└── CHANGELOG.md                    # 2026-11-06 entry con métricas
```

---

## 7. Métricas de competición (Score = media geométrica mejoras)

| Task | Baseline | Nuestro | Mejora |
|------|----------|---------|--------|
| invsqrt | Q×T ≈ 2.07M | 356,079 | ~6.5% |
| dqi | 784,172 (reference EEA 5.7M) | 784,172 | BM v7 vs EEA |
| dfthcsos | angle_k QROM baseline | 119 Q, 3,974 T | brot/batch sweep |

**Submission scoring:** ~45 minutos en plataforma Kaggle.

---

## 8. Conclusiones y próximos pasos (opcionales)

### ✅ Completado y validado
- Submission ZIP con 3 benchmarks
- Todos los tests pasan
- Perfil estático documentado
- QROM evaluada y descartada con evidencia

### 🔬 Investigación futura (no bloqueante para entrega)
1. **Compartir scaffolding TowerInv** entre posiciones: reutilizar `R['Pn','N','r','s','o0','o1']` reduce alloc/free y qubits peak.
2. **Precomputar `pw/src_s/src_u/src_d`** fuera del bucle Python: matriz de evaluación α precomputada.
3. **Circuitos dinámicos / mid-circuit measurement** real: requiere soporte hardware/kickmix para branching cuántico genuino.

### 📦 Para re-entrega
```bash
# Rebuild ZIP si hay cambios en circuitos
cd /home/deamon/quantum-circuit-compilation
.venv/bin/python submission/rebuild_valid_zip.py submission/submission_final.zip --dfthcsos-commit fb4e95b
```

---

## 9. Comandos de verificación rápida

```bash
# Perfil DQI
.venv/bin/python tools/kmx_profile.py /tmp/dqi.kmb --top 3

# Tests
.venv/bin/python -m pytest tests/ -q

# Verificar estructura ZIP
unzip -l submission/submission_final.zip

# SHA256 de circuitos
sha256sum submission/submission_final.zip
```