# Arquitectura del Proyecto - Documentación

## Estado Actual (2026-10-29)

### Implementaciones PRODUCCIÓN ✅

**invsqrt (Benchmark I - Fusión)**
- Archivo: `src/invsqrt_piecewise.py`
- Arquitectura: Polinomio por tramos + QROM + Horner (sin Newton-Raphson)
- Parámetros: deg=2, j=7, wc=28, dd=13
- Score: 593,733 (Q=185, T=2,993)
- Mejora: -71.3% vs baseline
- Verificado: PASS (64 shots/x + dominio completo)

**dqi (Benchmark II - Optimización)**
- Archivo: `src/dqi_optimized_v10.py`
- Arquitectura: Horner iQFT reemplaza Chien+Forney, contadores 7-bit, active length tracking
- Score: 100.55T (Q=1,888, T=5,708,480)
- Mejora: -0.82% vs baseline
- Verificado: PASS (2,560 shots)

**dfthcsos (Benchmark III - Química)**
- Directorio: `results/dfthcsos_test/brot12_J8/`
- Arquitectura: Brot=12, J=8, 10 angle_k circuitos
- Score: 3.36B
- Verificado: PASS

---

## Prototipos de Investigación ⚠️

### src/qualtran_bloqs/
**ESTADO: PROTOTIPOS NO FUNCIONALES**

Archivos en `src/qualtran_bloqs/` son **prototipos de arquitectura** explorados pero NO implementaciones funcionales:

1. **bma_bloq.py** - BMA con Gauss-Jordan (mock-up, no @bloq)
2. **eea_bloq.py** - Extended Euclidean con scaffold reuse (mock-up)
3. **chien_forney_bloq.py** - Chien Search + Forney (mock-up)
4. **dqi_decoder_bloq.py** - Unified decoder (mock-up)
5. **dqi_master_pipeline.py** - Pipeline adjunto (mock-up)
6. **plan_b_gates.py** - Custom Cirq gates con _t_complexity_ hardcodeado (mock-up)
7. **testbench_local.py** - Verificador clásico (mock-up)

**Por qué son prototipos:**
- Usan `@define` en lugar de `@bloq` decorator de Qualtran
- T-Complexity no implementado correctamente
- Imports duplicados (bma_bloq.py línea 30 y 38)
- Referencias circulares
- No pasan compilación Qualtran

**Uso recomendado:** Referencia arquitectónica únicamente.

---

## Historia de Versiones DQI

| Versión | Archivo | Característica | Estado |
|---------|---------|----------------|--------|
| v2 | dqi_optimized_v2.py | Contadores 7-bit | Obsoleto |
| v10 | dqi_optimized_v10.py | Horner iQFT ✅ | PRODUCCIÓN |
| v11-v15 | dqi_optimized_v*_py | Experimentales | Prototipos |
| v5* | dqi_v5_*.py | Scaffold reuse | Prototipos |

---

## Invsqrt Unificación

**DUPLICIDAD RESUELTA:**
- `src/invsqrt_piecewise.py` → Implementación PRODUCCIÓN
- `src/invsqrt_bloqs.py` → Referencia arquitectónica (prototipo)
- `src/dbhexa_orchestrator.py` → Orquestador (prototipo)

Usar siempre `invsqrt_piecewise.py` para generación de circuitos.

---

## Archivos a Ignorar

Los siguientes son experimentos/archivos de debug no commiteados:
- `src/dqi_optimized_v6.py` a `v9.py`
- `src/dqi_optimized_v11.py` a `v15.py`
- `src/dqi_v5_*`
- `simulate_eea_*.py`
- `workaround.py`, `eee_bkp.py`
- `comentarios.md`

---

## Comandos Producción

```bash
# invsqrt
python src/invsqrt_piecewise.py --deg 2 --j 7 --wc 28 --dd 13 --out invsqrt.kmb

# dqi
python src/dqi_optimized_v10.py /tmp/dqi.kmb --m 4095 --n 70 --degree 12

# Verificar
python verifiers/invsqrt/verify_submission_invsqrt.py invsqrt.kmb
python verifiers/dqi/verify_submission_dqi.py dqi.kmb
```

---

## Inconsistencias Auditadas (2026-10-29)

✅ Resueltas:
- Qualtran Bloqs documentados como prototipos
- Invsqrt unificado en src/invsqrt_piecewise.py
- Imports duplicados documentados
- sys.path modifications dispersos (aceptable para prototipos)

⚠️ Pendiente:
- Eliminar v11-v15 si no aportan valor
- Consolidar TODOs en backlog
