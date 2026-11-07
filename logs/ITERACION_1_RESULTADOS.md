# Iteración 1 - Scan optimizado con reutilización de registros

Fecha: 2026-11-07

## Cambios
- build_scan_inv reutiliza registros s,u,dd,w,t,f,lad,g entre posiciones
- Skeleton MBU en dqi_decoder_v1_opt_mbu.py con precomputación de evaluaciones

## Métricas
DQI:
- Toffoli: 784172
- Qubits: 2016
- scan_pos: 401310 (51.2%)
- bm_update: 150984 (19.25%)

Invsqrt:
- Q: 139
- T: 2561

ZIP: submission/submission_iter1.zip
sha256: 3d840330ac2b3664cfb81834bd82fafdb1f4364313a3b56931e704239b128a2f

## Próximo
Implementar QROM para inversa de 12 bits o control cuántico sobre f para evitar 75 Toffoli/posición en inversión.
