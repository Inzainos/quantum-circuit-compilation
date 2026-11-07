# Plan de optimización scan_pos con MBU

Objetivo: reducir de 98 Toffoli/posición a ~23 Toffoli/posición, ahorro ≈ -41k Toffoli.

Estado actual:
- Inversión torre 75 Toffoli/posición
- Test cero f=[s==0]: 11 init_and
- Fase g_a = f AND u_a: 12 init_and
Total 98

## Pasos

### 1. Descomputación por medición ya presente
`del_and` en kickmix es HMR + CZ condicionado → 0 Toffoli.
Verificado en:
- src/dqi_tower_inv.py mul6_del
- src/dqi_bm_stage_v1.py _disc_clear
- verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py

Por tanto los 11 del_and de la escalera y los 12 del_and de fase ya son 0 Toffoli.

### 2. Inversión condicional
f=1 solo cuando sigma(r)=0 → probabilidad ≈ 1/4095.
Ideas:
- Computar f
- Hacer HMR de dd y w con medida condicional a f
- Usar `b.push_condition(f)` para envolver TowerInv.forward/undo y fase
Coste estático sube por controles, coste medio cae.

### 3. Compartir scaffolding de inversión
TowerInv crea ancillas por posición. Reutilizar scaffolding entre posiciones:
- Mantener registro `ac` de coords y `R` estáticos
- Solo recalcular N y N^-1
Ahorro de alloc/free y qubits.

### 4. Precomputar pw y src
`pw = [1]` y `src_s/src_u/src_d` se recomputan por posición con bucles Python. Mover a precomputación fuera del bucle con matriz de evaluación de alpha.

### Próxima implementación
1. Modificar `build_scan_inv` para `push_condition(f)` alrededor de:
   - `TI.forward()`
   - computación de `t`
   - fase `init_and(f,u,g)` + `cz`
2. Medir la ganancia con kmx_profile.
3. Si el coste estático sube, probar versión con HMR de `w` condicionado a `f`.

Entregables:
- src/dqi_decoder_v1_opt_mbu.py
- docs/OPTIMIZACION_DQI_SCAN_MBU.md con métricas antes/después
- ZIP actualizado con nuevo dqi.kmb
