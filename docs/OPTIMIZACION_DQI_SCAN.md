# Optimización DQI Scan Stage – Berlekamp-Massey v7

Fecha: 2026-11-06
Estado: Implementado registro-reuse, ZIP reconstruido

## Resumen
Decodificador DQI v7 Berlekamp-Massey con 784 172 Toffoli, Q=2016.
Perfil estático kmx_profile:
- scan_pos 401 310 Toffoli 51.18%
- bm_update 150 984 Toffoli 19.25%
- bm_disc 71 766 Toffoli 9.15%
- omega_fwd/rev 42 315 Toffoli 5.4% c/u

Coste por posición: 401 310 / 4 095 ≈ 98 Toffoli/posición
Descomposición teórica:
- Inversión torre GF(2^12): 75 Toffoli
- Test cero s==0: 11 init_and + 11 del_and = 22 Toffoli
- Fase g_a = f AND u_a + CZ: 12 init_and + 12 del_and = 24 Toffoli
- Total ≈ 121 Toffoli con uncomputo completo; con optimizaciones actuales ≈ 98.

## Cambios aplicados

### 1. Reutilización de registros en build_scan_inv
Archivo: `src/dqi_decoder_v1.py`
Commit: 49ca352 `opt: reuse scan registers across positions (dqi_decoder_v1)`

Antes:
```python
for p in positions:
    s = b.alloc_qubits(DEG); ...
    ...
    b.free(s); ...
```

Después:
```python
s = b.alloc_qubits(DEG); u = b.alloc_qubits(DEG); dd = b.alloc_qubits(DEG); w = b.alloc_qubits(DEG)
t = b.alloc_qubits(DEG); f = b.alloc_qubits(1)[0]; lad = b.alloc_qubits(DEG - 2); g = b.alloc_qubits(DEG)
for p in positions:
    ...
for q in (...): b.free(q)
```

Impacto: elimina 4 095 alloc/free, reduce presión temporal de qubits, sin cambio en Toffoli estático.

### 2. Reconstrucción del ZIP de envío
Script: `submission/rebuild_valid_zip.py`
- invsqrt: `src/invsqrt_logshift2.py --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1`
  Q=139, T=2561, sha256 7e842bbfba8fb40d32c05b3b195073cf368981a92de77197ed22bd3a3f3faf79
- dqi: `src/dqi_decoder_v1.py`
  Toffoli=784172, qubits=2016, sha256 2b9eb49fd404d5cc81516f1c3b8271229c16c45506f3e84c73e70df78a06dbec
- dfthcsos: extraído de commit fb4e95b

Salida: `submission/submission.zip` 57 MB con estructura requerida:
```
invsqrt.kmb
dqi.kmb
dfthcsos/angle_k_0.kmx ...
dfthcsos/submission.npz
```

## Próximas optimizaciones previstas

Objetivo: -10 Toffoli/posición ≈ -41 k total

1. Descomputación por medición del test de cero
   - Ladder AND para f=[s==0] actualmente 11 init_and + 11 del_and
   - Con HMR + medición se eliminan los 11 del_and → ahorro 11 Toffoli/posición

2. Descomputación por medición de fase
   - g_a = f AND u_a usado solo para CZ(g_a, t_a)
   - Medir g_a tras CZ permite eliminar del_and → ahorro 12 Toffoli/posición
   - Combinado con 1. → ~23 Toffoli/posición teóricos vs 98 actuales

3. Inversión condicional
   - f=1 ocurre ~1/4095 de las posiciones
   - Controlar TowerInv con f reduce costo medio de inversión de 75 → ~0.018 Toffoli/posición efectivo
   - Requiere push_condition controlado y recomputación cuidadosa

## Verificación
- kmx_profile estático confirma 784172 Toffoli, sin condicionados
- Estructura ZIP valida según README
- Ramas locales podadas: todas las features ya mergeadas en local/quantum-dqi-v2.0.0
