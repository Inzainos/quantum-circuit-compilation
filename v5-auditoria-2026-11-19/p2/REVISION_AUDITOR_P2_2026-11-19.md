# REVISIÓN DEL AUDITOR — P2 (PROTOTIPO ESPIRAL, FASE 2, DQI)

**Fecha:** 2026-11-19 ~13:05–13:15 CST
**Orden:** Elán (2026-11-19 ~11:17, vía Coordinador) — prototipo del motor de la espiral; el Brujo coordina.
**Constructor:** Programación (subagente constructor P2).
**Diseño:** `~/workspace/qcc-data/dfthcsos-refit/espiral-rediseno/FASE2_DQI_2026-11-19.md` §1.2 y §P2.
**Reporte revisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p2/REPORTE_P2_2026-11-19.md` — **173 l. / md5 `3795109751f890400c77bb8a2135824c`**.
**Supervisión revisada:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p2/SUPERVISION_DATOS_P2_2026-11-19.md` — **202 l. / md5 `fb5ad3d6…`, CONCURRO (PASA)**.
**Verificación revisada:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p2/VERIFICACION_BRUJO_P2_2026-11-19.md` — **122 l. / md5 `13a267ba15248d7293fa668d66fc97c3`, CONCURRO (PASA)**.
**Cadena:** Programación (construye) → Brujo (verifica, 12:37) → Datos (supervisa, 12:54) → **Auditor (esta revisión)** → Elán (decide). Nota: en P2 el Brujo verificó antes de que Datos supervisara (ver A-P2-1); ambos concurrieron PASA, así que la cadena está completa en cualquier orden.
**Regla 0:** cada número aquí viene de un log leído o de un cómputo propio en python; lo estimado se marca [ESTIMADO]. Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.

## Veredicto: CONCURRO (PASA)

P2 PASA. Los 6 temps de la escalera de `_t_recon` quedan expuestos como bloque 6×1 canónico (`_ladder6_alloc` / `_ladder6_free`), con exactamente 6 qubits allocados una vez por ronda, pico Q sin cambio (1,864) y `_t_recon_del` limpiando exactamente los 6 qubits (balance 0 medido). El circuito resultante es **byte-idéntico a swap42** (sha `746271d9…`, `cmp` confirma). El Gold de swap42 lo cubre por identidad de bytes (PASS, 102,400 tiros, 5 errores de valor / 0 de fase). Impacto en score: 0, como estima el diseño. La escalera de `_flags` (10 temps) no se tocó.

## 1. Circuito byte-idéntico a swap42 — VERIFICADO (la equivalencia central)

Medidos por mí (sha256):
- `dqi_p2.kmb`: **646,811,990 B**, sha256 `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` ✓.
- `dqi_p2_control.kmb`: **646,811,990 B**, mismo sha `746271d9…` ✓.
- `dqi_swap42.kmb` (referencia): **646,811,990 B**, mismo sha `746271d9…` ✓.
- **`cmp` confirma: P2 byte-idéntico a swap42 y al control** ✓ (corrido por mí). La ruta de build es reproducible en esta caja (control Q=1,864 T=710,312 en 137 s, mismo `live_frontera`).

## 2. Estadísticas — VERIFICADAS (carga directa mía de los 3 .kmb)

Cargados por mí con `km.Circuit.from_file`:

| Variante | Q | T | num_bits | num_instructions |
|---|---|---|---|---|
| swap42 | 1,864 | 710,312 | 198,813 | 74,182,884 |
| P2 | 1,864 | 710,312 | 198,813 | 74,182,884 |
| P2 control | 1,864 | 710,312 | 198,813 | 74,182,884 |

**Idénticos en las tres** ✓. Coinciden con el reporte §5, con el `stats_kmb_p2.log` (num_qubits=1864, toffoli_like=710312, num_bits=198813, num_instructions=74182884) y con la supervisión de Datos §1.2.

## 3. Prueba aislada — RE-CORRIDA POR MÍ (LADDER6_OK)

`test_ladder6_p2.py`, salida medida por mí en este turno, idéntica a la del reporte (§6.1), a la del Brujo (§6) y a la de Datos (§1.3):

```
DW=8 lad_len=6 (esperado 6)
allocs _t_recon: n0=1725 n1=1736 delta=11 (esperado 11)
balance tras _t_recon_del: n2=1725 n2-n0=0 (esperado 0)
toffoli_like total=9 (esperado 9: _t_recon 9 T + _t_recon_del 0 T)
num_qubits circuito=1736
LADDER6_OK
```

Aritmética verificada por mí: n0 = 840 (S 70×12) + 432 (sigma) + 432 (tau) + 8 (d) + 12 (H) + 1 (p) = **1,725** ✓; delta = lad 6 + z0, s1, or_out, np_, w (5) = **11** ✓; n1 = 1,725 + 11 = 1,736 = num_qubits del circuito ✓; balance 0 → los 11 transitorios vuelven a 0 ✓.

## 4. Diff — VERIFICADO (solo `dqi_bm_stage_v1.py` difiere)

`diff -rq` entre `p2/src/` y el fuente swap42: entre los archivos presentes en ambos lados, **solo `dqi_bm_stage_v1.py` difiere** (p2 md5 `f239e9166287cd032fc975433df437b8`; swap42 md5 `3ab25965fb85372f6ba42dc7dd82a6a1`) ✓. `construir_dqi_p2.py` es nuevo (md5 `436f66f521e9a3caa15fa17cb6f9d9d8`, coincide con Datos §1.4; el script vive en `src/`, no en la raíz de `p2/`); el resto de `.py` son byte-idénticos. El diff muestra exactamente: dos métodos nuevos (`_ladder6_alloc` líneas 151–158 con docstring P2; `_ladder6_free` líneas 160–162) + dos líneas cambiadas: `_t_recon` línea 178 (`lad = b.alloc_qubits(DW - 2)` → `lad = self._ladder6_alloc()`) y `_t_recon_del` línea 224 (`b.free(lad)` → `self._ladder6_free(lad)`). **Nada más cambia en el cómputo ni en el descomputo** ✓.

**Escalera de `_flags` intacta:** línea 112 (`lad = b.alloc_qubits(DEG - 2); z = b.alloc_qubits(1)[0]; nz = b.alloc_qubits(1)[0]`) **idéntica** en ambos archivos (verificado por mí, línea por línea) ✓.

## 5. Ruta de producción usa los métodos P2 por herencia — VERIFICADO (grep)

- `bm_fused_e1d.py:21 class BMStageFusedE1d(BMStageFused)`, `bm_fused.py:22 class BMStageFused(BMStageV1)`, `dqi_bm_stage_v1.py:27 class BMStageV1` ✓.
- Producción: `bm_fused_e1d.py:40` `w = self._t_recon(p)` y `:42` `self._t_recon_del(p, w)` — los métodos P2 entran por herencia ✓.
- `BMStageV1._dclear`: `:243` `w = self._t_recon(p)` y `:245` `self._t_recon_del(p, w)` — una sola vez cada uno (ver D-P2-1) ✓.

## 6. `lad` se aloca una vez por ronda (140 llamadas) — VERIFICADO

`_dclear` se llama en `forward_round` (línea 273, `self._dclear(D, p)  # D -> 0`) y en `reverse_round` (línea 283, `self._dclear(D, p)  # reconstruye D`) — una vez por ronda cada una ✓. BM = 70 rondas ida + 70 vuelta → 70 + 70 = **140 llamadas**; cada una aloca `lad` una sola vez (un solo `alloc_qubits(DW - 2)` en `_ladder6_alloc`) ✓.

**El pico Q en BM no sube:** el `.kmb` es byte-idéntico → Q pico 1,864 por construcción (mismo valor del Gold de swap42). El `live_frontera` del build P2 es idéntico al de swap42 (1794/1794/1794/1794/1724) ✓.

## 7. Gold: PASS por identidad de bytes con swap42 (no se re-corrió)

`verify_swap42_gold.log` (md5 `38d9f639d158b3b8044ac05ad3b5efb8`, sin cambios desde el 14 nov — verificado por mí; coincide con Datos §3): status PASS, score 2,993,914,799,696.024, verified_shots 102,400, value_errors 5, phase_errors 0, repetition_factor 1.2131052140444296, toffoli_count 710,312, reaction_depth 19,501, num_ops 74,182,884, num_qubits 1,864, num_bits 198,813, circuit_sha256 `746271d9…`, exit_gold=0. Score recomputado exacto en P1: R×Q²×T = 1.2131052140444296 × 1,864² × 710,312 = 2,993,914,799,696.024. El `.kmb` P2 tiene el mismo sha256 → mismo circuito → el Gold de swap42 lo cubre. No se re-corrió el Gold del DQI.

## 8. Build logs — LEÍDOS EN DIRECTO

- `build_control.log` (1,071 B): `TOTAL P2 Q=1864 T=710312 en 137s`, `live_frontera` 1794/1794/1794/1794/1724, sha `746271d9…` ✓.
- `build_p2.log` (1,063 B): `TOTAL P2 Q=1864 T=710312 en 137s`, mismo `live_frontera`, sha `746271d9…` ✓.
- Ambos imprimen ratio DQI 8.16189x / geomean 3.52162x / escalado Kaggle 3.53019x — valores del script, ver D-P1-1 (el §4 del reporte cita correctamente D-P1-1: los valores Gold son 8.16289x / 3.52286x) ✓.

## 9. Precisiones

**D-P2-1 (del Brujo, CONCURRO — verificada por mí):** el reporte §6.1 dice "línea 230 en `BMStageV1._dclear`" para la llamada a `_t_recon`. Verificado por mí por grep: la línea 230 es el docstring ("CAMBIO rama-t-eliminada: el control del cswap es w = _t_recon(p)"); la llamada real es la línea 243 (`w = self._t_recon(p)`) y el descomputo la 245 (`self._t_recon_del(p, w)`). **La afirmación es cierta** (una sola llamada por `_dclear`); solo la línea citada es la del docstring. La ruta de producción sí está citada bien: `bm_fused_e1d.py` líneas 40/42 (verificadas por mí, §5).

**D-P2-2 (de Datos, CONCURRO — verificada por mí):** el encabezado del reporte dice "construcción ~18:25–18:35 CST". Las mtimes son `dqi_p2_control.kmb` 18:28:21 UTC, `dqi_p2.kmb` 18:31:37 UTC, `build_p2.log` 18:31:49 UTC, reporte 18:33:23 UTC → **ventana real ~12:28–12:33 CST**. Misma trampa de etiqueta que D-P1-4 en P1 (UTC etiquetado como CST, 6 h de diferencia). No cambia ningún número; solo la etiqueta de hora del encabezado.

## 10. Precisiones propias (A-P2-1 a A-P2-2, menores)

- **A-P2-1 (menor — el orden de la cadena en P2):** en P2 el Brujo verificó antes de que Datos supervisara (el informe del Brujo dice "Datos (supervisión pendiente)" y la supervisión de Datos dice "Brujo ✓"; fechas 12:37 vs 12:54). El orden usual es Programación → Datos → Brujo → Auditor; aquí fue Programación → Brujo → Datos → Auditor — igual que en P1 (A-P1-2). Ambos concurrieron PASA, así que la cadena está completa en cualquier orden — lo dejo registrado para que el tablero no se confunda.
- **A-P2-2 (menor — el pico de `_dclear` está documentado en el código mismo):** el docstring de `_dclear` (líneas 230–236) dice explícitamente: "el pico de _dclear queda en la inversion, 1,860; w anade 11 transitorios sobre ~1,830 -> 1,841 < 1,860". La afirmación del reporte §6.2 ("el `lad` vive sobre base ~1,830 → 1,841 < 1,860 pico de inversión") no es solo una afirmación del reporte — está documentada en el código que P2 no tocó. Refuerza la confirmación #2.

## 11. Criterio FASE 2 §P2 — CUMPLIDO

- Bloque 6×1 canónico (`_ladder6_alloc` / `_ladder6_free`): ✓.
- Exactamente 6 qubits allocados una vez por ronda: ✓ (140 llamadas, un solo `alloc_qubits(DW - 2)` por llamada).
- Pico Q sin cambio (1,864): ✓ (byte-idéntico; `live_frontera` idéntico).
- `_t_recon_del` limpia exactamente los 6 qubits: ✓ (balance 0 medido; los 11 transitorios vuelven a 0).
- Circuito byte-idéntico a swap42: ✓ (sha256 + `cmp`).
- Gold: ✓ por identidad de bytes (PASS, 102,400 tiros, 5 valor / 0 fase).
- Escalera de `_flags` (10 temps) no tocada: ✓.

## 12. Veredicto y cadena

**CONCURRO (PASA)** — P2 pasa: bloque 6×1 canónico verificado en código, 6 qubits una vez por ronda (140 llamadas), pico Q sin cambio, balance 0 medido, circuito byte-idéntico a swap42 con Gold PASS por identidad. Precisiones: D-P2-1 (línea 230 es el docstring, llamada real 243/245 — concurro), D-P2-2 (ventana UTC etiquetada como CST — concurro) y A-P2-1, A-P2-2 (mías). Ninguna cambia el veredicto.

**Cadena COMPLETA (P2):** Programación ✓ → Brujo ✓ → Datos ✓ → Auditor ✓ (esta revisión: CONCURRO, PASA) → **Elán** (decide).

**Fase 2 COMPLETA en sus 3 variantes construidas** (P1, P2, P3 — las tres PASA, las tres byte-idénticas a swap42, impacto en score 0). Quedan P5 y la combinación P1+P2+P3 sin construir (decisión posterior de Elán). P4 INVALIDADO (A-F2-1).
