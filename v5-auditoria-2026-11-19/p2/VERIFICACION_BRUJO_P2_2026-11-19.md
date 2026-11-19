# VERIFICACIÓN DEL BRUJO — P2 (Fase 2, DQI): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~12:37 CST
**Reporte verificado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p2/REPORTE_P2_2026-11-19.md` (173 l. / md5 `37951097…`)
**Constructor:** Programación (subagente constructor P2)
**Diseño:** `FASE2_DQI_2026-11-19.md` §1.2 y §P2
**Cadena:** Programación ✓ → **Datos (supervisión pendiente)** → **Brujo ✓ (este informe)** → Auditor → Elán
**Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.**

## Veredicto: CONCURRO (PASA)

P2 cumple el criterio de FASE 2 §P2: los 6 temps de la escalera de
`_t_recon` quedan expuestos como bloque 6×1 canónico
(`_ladder6_alloc` / `_ladder6_free`), con exactamente 6 qubits allocados
una vez por ronda, pico Q sin cambio (1,864) y `_t_recon_del` limpiando
exactamente los 6 qubits (balance 0 medido). El circuito resultante es
**byte-idéntico a swap42** (equivalencia probada por hash; el Gold de
swap42 lo cubre). Impacto en score: 0, como estima el diseño. La escalera
de `_flags` (10 temps) no se tocó.

## Verificado por cómputo propio

### 1. Circuito byte-idéntico a swap42 (la equivalencia central)
- `dqi_p2.kmb` sha256 calculado por mí: `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` (646,811,990 B).
- `dqi_swap42.kmb` sha256: mismo `746271d9…` — **idéntico**.
- `dqi_p2_control.kmb` sha256: mismo `746271d9…` — la ruta de build es reproducible en esta caja.

### 2. Estadísticas leídas por mí del .kmb P2 (carga directa con `km.Circuit.from_file`)
- P2: Q=1,864, T=710,312, num_bits=198,813, num_instructions=74,182,884.
- Idénticos a swap42 (y a P1). El `stats_kmb_p2.log` del reporte dice lo mismo.

### 3. Mecanismo confirmado en el código (diff leído)
- `diff -rq` p2/src vs swap42: entre los `.py` **solo `dqi_bm_stage_v1.py`
  difiere** (más el script nuevo `construir_dqi_p2.py`). md5
  `dqi_bm_stage_v1.py`: `f239e9166287cd032fc975433df437b8` — coincide con
  el reporte.
- El diff muestra exactamente: dos métodos nuevos (`_ladder6_alloc`
  líneas 151–158 con docstring P2; `_ladder6_free` líneas 160–162) +
  dos líneas cambiadas: `_t_recon` línea 178
  (`lad = b.alloc_qubits(DW - 2)` → `lad = self._ladder6_alloc()`) y
  `_t_recon_del` línea 224 (`b.free(lad)` →
  `self._ladder6_free(lad)`). **Nada más cambia en el cómputo ni en el
  descomputo.**
- Escalera de `_flags` intacta: línea 112
  (`lad = b.alloc_qubits(DEG - 2)`) **idéntica** en ambos archivos.

### 4. Ruta de producción usa los métodos P2 por herencia
- `BMStageFusedE1d(BMStageFused)`, `BMStageFused(BMStageV1)` — verificado
  en los tres archivos.
- `bm_fused_e1d.py` línea 40: `w = self._t_recon(p)`; línea 42:
  `self._t_recon_del(p, w)` — los métodos P2 entran por herencia.
- `BMStageV1._dclear` línea 243: `w = self._t_recon(p)`; línea 245:
  `self._t_recon_del(p, w)` — una sola vez cada uno.

### 5. `lad` se aloca una vez por ronda (140 llamadas)
- `_dclear` se llama en `forward_round` (línea 273) y en
  `reverse_round` (línea 283) — una vez por ronda cada una.
- BM = 70 rondas ida + 70 vuelta → 70 + 70 = **140 llamadas**; cada una
  aloca `lad` una sola vez (un solo `alloc_qubits(DW - 2)` en
  `_ladder6_alloc`).

### 6. Prueba aislada re-corrida por mí (`test_ladder6_p2.py`)
- Salida medida por mí, idéntica a la del reporte:
  `DW=8 lad_len=6 (esperado 6)`,
  `allocs _t_recon: n0=1725 n1=1736 delta=11 (esperado 11)`,
  `balance tras _t_recon_del: n2=1725 n2-n0=0 (esperado 0)`,
  `toffoli_like total=9 (esperado 9)`, `num_qubits circuito=1736`,
  `LADDER6_OK`.
- Aritmética verificada: n0 = 840 (S 70×12) + 432 (sigma) + 432 (tau) +
  8 (d) + 12 (H) + 1 (p) = **1,725** ✓; delta = lad 6 + z0, s1, or_out,
  np_, w (5) = **11** ✓; balance 0 → los 11 transitorios vuelven a 0 ✓.

### 7. Build logs leídos en directo
- `build_control.log`: `TOTAL P2 Q=1864 T=710312 en 137s`,
  `live_frontera` 1794/1794/1794/1794/1724, sha `746271d9…`.
- `build_p2.log`: `TOTAL P2 Q=1864 T=710312 en 137s`, mismo
  `live_frontera`, sha `746271d9…`.
- El §4 del reporte cita correctamente la precisión D-P1-1 (los 8.16189x
  / 3.52162x impresos son estimados del script; los valores Gold son
  8.16289x / 3.52286x).

### 8. Gold de swap42 (cubre a P2 por identidad de bytes)
- Leído en directo (verificado ya en P1):
  `verify_swap42_gold.log`: `status: PASS`,
  `score: 2993914799696.024`, `verified_shots: 102400`,
  `value_errors: 5`, `phase_errors: 0`,
  `repetition_factor: 1.2131052140444296`, `toffoli_count: 710312`,
  `reaction_depth: 19501`, `num_ops: 74182884`, `num_qubits: 1864`,
  `num_bits: 198813`, `circuit_sha256: 746271d9…`, `exit_gold=0`.
- El `.kmb` P2 tiene el mismo sha256 → mismo circuito → el Gold lo cubre.

## Precisiones

### D-P2-1 (menor, cita): la llamada en `BMStageV1._dclear` está en la línea 243, no en la 230
- El reporte §6.1 dice "línea 230 en `BMStageV1._dclear`" para la llamada
  a `_t_recon`. La línea 230 es el docstring ("CAMBIO
  rama-t-eliminada: el control del cswap es w = _t_recon(p)"); la llamada
  real es la línea 243 (`w = self._t_recon(p)`) y el descomputo la 245
  (`self._t_recon_del(p, w)`). **La afirmación es cierta** (una sola
  llamada por `_dclear`); solo la línea citada es la del docstring.
- La ruta de producción sí está citada bien: `bm_fused_e1d.py` líneas
  40/42 (verificadas).

## Lo que NO se tocó (verificado)
- Fuente swap42 local: el `.kmb` sigue en sha `746271d9…`; el diff muestra
  solo el cambio P2 en la copia test-dev.
- Candidato swap42 (ZIP), ZIP Adopted v3, docs de diseño, árboles R1/R2/R5,
  árbol P1: sin cambios en esta tarea.
- Entrenamiento SomeJoint en la Kali: ni mirado.

## Criterio FASE 2 §P2 — cumplido
- Bloque 6×1 canónico (`_ladder6_alloc` / `_ladder6_free`): ✓.
- Exactamente 6 qubits allocados una vez por ronda: ✓ (140 llamadas,
  un solo `alloc_qubits(DW - 2)` por llamada).
- Pico Q sin cambio (1,864): ✓ (byte-idéntico; `live_frontera` idéntico).
- `_t_recon_del` limpia exactamente los 6 qubits: ✓ (balance 0 medido;
  los 11 transitorios vuelven a 0).
- Circuito byte-idéntico a swap42: ✓ (sha256).
- Gold: ✓ por identidad de bytes (PASS, 102,400 tiros, 5 valor / 0 fase).
- Escalera de `_flags` (10 temps) no tocada: ✓.

**P2 PASA. Siguiente: Datos (supervisión) → Auditor → Elán.**
