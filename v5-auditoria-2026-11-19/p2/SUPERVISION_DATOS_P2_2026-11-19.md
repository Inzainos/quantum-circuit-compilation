# SUPERVISIÓN DE DATOS — P2 (Fase 2, DQI): CONCURRO (PASA)

**Fecha:** 2026-11-19 ~12:54 CST
**Reporte supervisado:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p2/REPORTE_P2_2026-11-19.md` — **173 l. / md5 `3795109751f890400c77bb8a2135824c`** (medido por mí).
**Verificación del Brujo supervisada:** `~/workspace/qcc-data/test-dev/espiral-prototipo/p2/VERIFICACION_BRUJO_P2_2026-11-19.md` — **122 l. / md5 `13a267ba15248d7293fa668d66fc97c3`** (medido por mí; el Brujo corrigió el md5 en su mensaje de las 12:54 CST — el md5 que él citó coincide exactamente con el medido en disco).
**Constructor:** Programación (subagente constructor P2).
**Diseño:** `FASE2_DQI_2026-11-19.md` §1.2 y §P2.
**Cadena:** Programación ✓ → **Datos ✓ (este informe)** → Brujo ✓ → Auditor → Elán.
**Nada a producción, ZIP, GitHub ni Kaggle sin GO de Elán.**

## Veredicto: CONCURRO (PASA)

P2 cumple el criterio de FASE 2 §P2: los 6 temps de la escalera de
`_t_recon` quedan expuestos como bloque 6×1 canónico
(`_ladder6_alloc` / `_ladder6_free`), con exactamente 6 qubits allocados
una vez por ronda, pico Q sin cambio (1,864) y `_t_recon_del` limpiando
exactamente los 6 qubits (balance 0 medido). El circuito resultante es
**byte-idéntico a swap42** (equivalencia probada por hash y por `cmp`;
el Gold de swap42 lo cubre). Impacto en score: 0, como estima el diseño.
La escalera de `_flags` (10 temps) no se tocó.

## 1. Verificado por cómputo propio

### 1.1 Circuito byte-idéntico a swap42 (la equivalencia central)

Medido por mí en este turno (`sha256sum` + `cmp`):

| Archivo | Tamaño (B) | sha256 |
|---|---|---|
| `dqi_p2.kmb` | 646,811,990 | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |
| `dqi_p2_control.kmb` | 646,811,990 | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |
| `dqi_swap42.kmb` | 646,811,990 | `746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603` |

- `cmp dqi_p2.kmb dqi_swap42.kmb` → **idéntico** (sin diferencias).
- `cmp dqi_p2.kmb dqi_p2_control.kmb` → **idéntico** (sin diferencias).
- La ruta de build es reproducible en esta caja: el control (copia sin
  modificar) reproduce el candidato exacto.

### 1.2 Estadísticas leídas por mí de los tres .kmb (carga directa con `km.Circuit.from_file`)

Script `/tmp/stats_p2_datos2.py` (corrido por mí en este turno;
`operation_statistics()` + `num_qubits` + `num_bits`):

| Variante | Q | T (toffoli_like) | num_bits | num_instructions |
|---|---|---|---|---|
| swap42 (referencia) | 1,864 | 710,312 | 198,813 | 74,182,884 |
| **P2** | **1,864** | **710,312** | **198,813** | **74,182,884** |
| P2 control | 1,864 | 710,312 | 198,813 | 74,182,884 |

Idénticos en los tres. Coinciden con el reporte §5 y con el
`stats_kmb_p2.log` del reporte. (Nota: `operation_statistics()`
devuelve los conteos por puerta; `num_instructions` es la suma,
74,182,884 — igual que en P1/P3.)

### 1.3 Prueba aislada re-corrida por mí (`test_ladder6_p2.py`)

Salida medida por mí en este turno, idéntica a la del reporte (§6.1)
y a la del Brujo (§6):

```
DW=8 lad_len=6 (esperado 6)
allocs _t_recon: n0=1725 n1=1736 delta=11 (esperado 11)
balance tras _t_recon_del: n2=1725 n2-n0=0 (esperado 0)
toffoli_like total=9 (esperado 9: _t_recon 9 T + _t_recon_del 0 T)
num_qubits circuito=1736
LADDER6_OK
```

Aritmética verificada por mí:
- n0 = 840 (S 70×12) + 432 (sigma) + 432 (tau) + 8 (d) + 12 (H)
  + 1 (p) = **1,725** ✓.
- delta = lad 6 + z0, s1, or_out, np_, w (5) = **11** ✓.
- Balance 0 → los 11 transitorios vuelven a 0 ✓.

### 1.4 Diff leído por mí (solo `dqi_bm_stage_v1.py` cambia)

- `src/dqi_bm_stage_v1.py` md5 **`f239e9166287cd032fc975433df437b8`**
  — coincide con el reporte (§2, §8) y con el Brujo (§3).
- `src/construir_dqi_p2.py` md5 **`436f66f521e9a3caa15fa17cb6f9d9d8`**
  — archivo nuevo, sin contraparte en swap42 (coincide con el resumen
  de la cadena; el script vive en `src/`, no en la raíz de `p2/`).
- Métodos nuevos verificados por grep en `src/dqi_bm_stage_v1.py`:
  `_ladder6_alloc` (líneas 151–158, con docstring P2, un solo
  `alloc_qubits(DW - 2)`), `_ladder6_free` (líneas 160–162).
- Líneas cambiadas verificadas por grep: `_t_recon` línea 178
  (`lad = b.alloc_qubits(DW - 2)` → `lad = self._ladder6_alloc()`);
  `_t_recon_del` línea 224 (`b.free(lad)` →
  `self._ladder6_free(lad)`). Nada más cambia en el cómputo ni en el
  descomputo.
- Escalera de `_flags` intacta: línea 112
  (`lad = b.alloc_qubits(DEG - 2); z = b.alloc_qubits(1)[0]; ...`)
  — el `alloc_qubits(DEG - 2)` = 10 temps sigue ahí, sin tocar.

### 1.5 Ruta de producción usa los métodos P2 por herencia

Verificado por grep por mí:
- `bm_fused_e1d.py:21 class BMStageFusedE1d(BMStageFused)`,
  `bm_fused.py:22 class BMStageFused(BMStageV1)` (herencia en cadena,
  igual que en P1).
- Producción: `bm_fused_e1d.py:40` `w = self._t_recon(p)` y `:42`
  `self._t_recon_del(p, w)` — los métodos P2 entran por herencia.
- `BMStageV1._dclear`: `:243` `w = self._t_recon(p)` y `:245`
  `self._t_recon_del(p, w)` — una sola vez cada uno (ver D-P2-1).

### 1.6 `lad` se aloca una vez por ronda (140 llamadas)

- `_dclear` se llama una vez por `forward_round` y una vez por
  `reverse_round` (`dqi_bm_stage_v1.py` líneas 273 y 283, citadas por
  el reporte §6.1 y el Brujo §5) → 70 + 70 = **140 llamadas** en el
  build completo; cada `_dclear` llama `_t_recon` una sola vez
  (línea 243) y cada llamada aloca `lad` una sola vez (un solo
  `alloc_qubits(DW - 2)` en `_ladder6_alloc`).

### 1.7 Build logs leídos en directo

- `build_control.log` (1,071 B): `TOTAL P2 Q=1864 T=710312 en 137s`,
  `live_frontera` 1794/1794/1794/1794/1724, sha `746271d9…`.
- `build_p2.log` (1,063 B): `TOTAL P2 Q=1864 T=710312 en 137s`,
  mismo `live_frontera`, sha `746271d9…`.
- Ambos imprimen ratio DQI 8.16189x / geomean 3.52162x / escalado
  Kaggle 3.53019x — valores del script, ver §2 (D-P1-1).

## 2. Precisiones

### D-P2-1 (del Brujo, menor, cita) — CONCURRO

El reporte §6.1 dice "línea 230 en `BMStageV1._dclear`" para la
llamada a `_t_recon`. Verificado por mí por grep: la línea 230 es el
docstring ("CAMBIO rama-t-eliminada: el control del cswap es w =
_t_recon(p)"); la llamada real es la línea 243
(`w = self._t_recon(p)`) y el descomputo la 245
(`self._t_recon_del(p, w)`). **La afirmación es cierta** (una sola
llamada por `_dclear`); solo la línea citada es la del docstring.
La ruta de producción sí está citada bien: `bm_fused_e1d.py` líneas
40/42 (verificadas por mí, §1.5).

### D-P2-2 (mía, menor, etiqueta de hora) — la ventana de construcción del reporte es UTC, no CST

El encabezado del reporte dice "construcción ~18:25–18:35 CST".
Las mtimes de los archivos (UTC) son: `dqi_p2_control.kmb` 18:28:21,
`dqi_p2.kmb` 18:31:37, `build_p2.log` 18:31:49, reporte 18:33:23 UTC
→ **ventana real ~12:28–12:33 CST**. Es la misma trampa de etiqueta
que D-P1-4 en P1 (UTC etiquetado como CST, 6 h de diferencia). No
cambia ningún número; solo la etiqueta de hora del encabezado.

### Cita D-P1-1 en el reporte §4 — CORRECTA

El §4 cita correctamente la precisión D-P1-1 del reporte P1: los
8.16189x / 3.52162x impresos por el script de build son estimados
(ancla vieja 7.48129 y 5.32 redondeado); los valores Gold son
8.16289x / 3.52286x (verificados exactos por mí en P1:
ratio DQI 8.162890942147493, geomean 3.522859936910316). El Brujo
también lo confirma en su §7. Nada que corregir aquí.

## 3. Gold: PASS por identidad de bytes con swap42 (no se re-corrió)

`~/workspace/qcc-data/dqi-perfil/swap42/verify_swap42_gold.log`,
leído en directo por mí en P1 (md5 `38d9f639d158b3b8044ac05ad3b5efb8`,
sin cambios desde el 14 nov) y citado por el Brujo en su §8:

```
status: PASS, score: 2993914799696.024, verified_shots: 102400
value_errors: 5, phase_errors: 0, repetition_factor: 1.2131052140444296
toffoli_count: 710312, reaction_depth: 19501, num_ops: 74182884
num_qubits: 1864, num_bits: 198813
circuit_sha256: 746271d961a74cf224dcfdc73e76a7c77da3c1803d6e9341b14f805ecf4a2603
exit_gold=0
```

El `.kmb` P2 tiene **el mismo sha256** (ver §1.1) → mismo circuito →
el Gold de swap42 lo cubre. Score recomputado exacto en P1:
R×Q²×T = 1.2131052140444296 × 1,864² × 710,312 =
2,993,914,799,696.024. No se re-corrió el Gold del DQI.

## 4. Criterio FASE 2 §P2 — cumplido

- Bloque 6×1 canónico (`_ladder6_alloc` / `_ladder6_free`): ✓.
- Exactamente 6 qubits allocados una vez por ronda: ✓ (140 llamadas,
  un solo `alloc_qubits(DW - 2)` por llamada).
- Pico Q sin cambio (1,864): ✓ (byte-idéntico; `live_frontera`
  idéntico).
- `_t_recon_del` limpia exactamente los 6 qubits: ✓ (balance 0
  medido; los 11 transitorios vuelven a 0).
- Circuito byte-idéntico a swap42: ✓ (sha256 + `cmp`).
- Gold: ✓ por identidad de bytes (PASS, 102,400 tiros, 5 valor /
  0 fase).
- Escalera de `_flags` (10 temps) no tocada: ✓.

## 5. Lo que NO se tocó (verificado)

- Fuente swap42 local: el `.kmb` sigue en sha `746271d9…`; el diff
  muestra solo el cambio P2 en la copia test-dev.
- Candidato swap42 (ZIP), ZIP Adopted v3, docs de diseño, árboles
  R1/R2/R5, árbol P1: sin cambios en esta tarea.
- Entrenamiento SomeJoint en la Kali: ni mirado.

**P2 PASA. Siguiente: Auditor → Elán.**

**Fase 2 COMPLETA en sus 3 variantes construidas** (P1, P2, P3 — las
tres PASA, las tres byte-idénticas a swap42, impacto en score 0).
Quedan P5 y la combinación P1+P2+P3 sin construir (decisión posterior
de Elán). P4 INVALIDADO (A-F2-1).
