# VERIFICACIÓN DQI CON E1d (y DQI FUSIONADO) — REPORTE

**Fecha:** 2026-11-12 (02:00–02:27 CST, America/Mexico_City)
**Alcance:** SOLO verificación. La adopción y el notebook los lanza el agente padre cuando llegue este veredicto.
**Regla 0:** cada número viene de un log citado; lo no medido se dice, no se asume.

## VEREDICTO

| Circuito | Sim n=6 (Tests A–C) | Verificador oficial (Kali) | Veredicto |
|---|---|---|---|
| DQI fusionado+E1d (Q=1,934, T=785,012) | **PASA** (los 3 tests) | **PASA** (2,560 tiros, 0 errores) | **ADOPTABLE** |
| DQI fusionado (Q=1,937, T=784,172) | PASA (desde la fusión) | **PASA** (2,560 tiros, 0 errores) | **PASA** |

**Consecuencia (secuencia de Elán 2026-11-12 ~01:27):** el rediseño SÍ dio ganancia y la integración SÍ pasa la verificación → la adopción es **fusión + E1d + lbfgs dfthcsos −0.58% → ~3.332x** (geomean DQI 3.3259x). La verificación oficial del fusionado, pendiente desde la fusión, queda cerrada: PASA.

**Main y ZIP intactos.** Todo el trabajo en scratch (local `~/workspace/qcc-data/dqi-perfil/verificacion_e1d/` y Kali `/home/deamon/workspace/qcc-data/dqi-perfil/verificacion_e1d/`). Nada a Kaggle, nada a main.

---

## 1. Construir y re-medir el DQI con E1d

Script: `construir_dqi_e1d.py` (usa `bm_fused_e1d.py` / `tower_inv3_e1d.py` de `~/workspace/qcc-data/dqi-perfil/redisenio_inversor/`).
Log: `construir_dqi_e1d.log`.

```
[bm_forward] live_frontera=1864
[omega_fwd]   live_frontera=1864
[scan]        live_frontera=1864
[omega_rev]   live_frontera=1864
[bm_reverse]  live_frontera=1724
TOTAL E1d-alpha Q=1934 T=785012 en 108s
FUSIONADO (baseline): TOTAL Q=1937 T=784172 geomean=3.3237x
Delta Q=-3 Delta T=840 (esperado Delta Q=-3 Delta T=+840 = 140 inv alpha x 6 T)
geomean estimado = 3.3237 * (1937/1934)^(2/3) * (784172/785012)^(1/3) = 3.3259x
guardado /home/hatch/workspace/qcc-data/dqi-perfil/verificacion_e1d/dqi_fusionado_e1d.kmb
sha256=16e06d619230d169866307e1aa1be83343c8f94bd0b99526dc1acd1710383664
```

**Confirmado:** Q=1,934, T=785,012 — coinciden exactamente con lo reportado por el rediseño (ΔQ=−3, ΔT=+840 = 140 inversiones alpha × 6 T). El piso Q=1,934 lo fija el pico del scan (live_frontera=1,864 en scan; el Q total 1,934 = base + pico).

**Re-medición independiente al cargar el .kmb en la Kali** (antes de verificar, `km.Circuit.from_file`, venv del proyecto):
- `dqi_fusionado_e1d.kmb`: Q=1934, T=785012, regs=4165 (70 S + 4,095 E = 4,165 ✓)
- `dqi_fusionado.kmb`: Q=1937, T=784172, regs=4165 ✓

**Copias verificadas por sha256 antes de correr el verificador:**
- Local `dqi_fusionado_e1d.kmb` = Kali `dqi_fusionado_e1d.kmb` = `16e06d619230d169866307e1aa1be83343c8f94bd0b99526dc1acd1710383664` ✓
- Local `dqi_fusionado.kmb` = Kali `dqi_fusionado.kmb` = `7a5815f4b36eb67bdb93b89bcb66c0acd6b7497e865bbde58b3ac8d87dc463cd` ✓ (coincide con el sha reportado en la fusión)

---

## 2. Simulador a n=6 — Tests A–C (como la fusión)

Script: `verificar_e1d.py` (plantilla `verificar_fusion.py` de `~/workspace/qcc-data/dqi-perfil/fusion_mul_inv/`).
Log: `verificar_e1d.log`.

Layout: `S@0 sigma@72 tau@144 d@216 H@224 (nq base=236)`.

- **Forward solo:** fusionada Q=321 T=4,302 ; fusionada+E1d Q=318 T=4,338. Fase volteada: 0 en ambas.
- **Test A (forward idéntico, S/sigma/tau/d/H): PASA.** Los 5 registros idénticos entre fusionada y fusionada+E1d (ej. S = [3581221697895681822, −9016480751880562176, −5309259669920220430, 6163843853690424923] en ambas; d = [1 1 1 1] en ambas; H = [0 0 0 0] en ambas).
- **Test B (ida+vuelta restaura el estado inicial): PASA.** Con E1d: Q=318 T=7,752, fase volteada 0, restaura el estado inicial = True.
- **Test C (fusionada ida+vuelta == fusionada+E1d ida+vuelta, registros persistentes): PASA.** True.
- **VEREDICTO: TODOS PASAN.**

Nota: el forward a n=6 baja Q 321→318 (−3, los 3 qubits N' liberados) y sube T 4,302→4,338 (+36 = 6 inversiones alpha a n=6 × 6 T). Coherente con el diseño de E1d.

---

## 3. Verificador oficial en la Kali

Verificador: `/home/deamon/wt_deamonx/quantum-sandbox/verifiers/dqi/verify_submission_dqi.py` (worktree `quantum-sandbox` @ 4ac3d45).
Intérprete: `/home/deamon/quantum-circuit-compilation/.venv/bin/python` (3.13; el python del sistema 3.14.7 NO carga kickmix.so).
Lanzador: `run_verify_kali.sh`. Log: `verify_kali.log` (copia local del log de la Kali).
Flags: `--num-shots 2560 --batch-size 256 --max-workers 1` (muestreo; el verificador DQI completo a 102,400 tiros NO se corrió — ver §3.3).
Tiempos (Kali, CST): fusionado 02:19:46→02:21:24 (~98 s); E1d 02:21:24→02:22:51 (~87 s). FIN 02:22:51.

### 3.1 DQI fusionado (Q=1,937) — PASS

```json
{
  "status": "PASS",
  "score": 14539292783773.22,
  "m": 4095, "n": 70, "degree": 12, "r": 2016,
  "verified_shots": 2560,
  "value_errors": 0,
  "phase_errors": 0,
  "empirical_error_rate": 0.0,
  "effective_error_rate": 0.03406367107515445,
  "log2_delta": -128.0,
  "repetition_factor": 4.941658272957928,
  "mean_error_weight": 31.046737331746634,
  "toffoli_count": 784172.0,
  "max_toffoli_count": 784172,
  "reaction_depth": 19185,
  "num_ops": 71657404,
  "num_qubits": 1937,
  "num_bits": 198393,
  "circuit_sha256": "7a5815f4b36eb67bdb93b89bcb66c0acd6b7497e865bbde58b3ac8d87dc463cd"
}
```
`exit_fusionado=0`.

### 3.2 DQI fusionado+E1d (Q=1,934) — PASS

```json
{
  "status": "PASS",
  "score": 14509817322132.195,
  "m": 4095, "n": 70, "degree": 12, "r": 2016,
  "verified_shots": 2560,
  "value_errors": 0,
  "phase_errors": 0,
  "empirical_error_rate": 0.0,
  "effective_error_rate": 0.03406367107515445,
  "log2_delta": -128.0,
  "repetition_factor": 4.941658272957928,
  "mean_error_weight": 31.046737331746634,
  "toffoli_count": 785012.0,
  "max_toffoli_count": 785012,
  "reaction_depth": 19185,
  "num_ops": 71675744,
  "num_qubits": 1934,
  "num_bits": 198813,
  "circuit_sha256": "16e06d619230d169866307e1aa1be83343c8f94bd0b99526dc1acd1710383664"
}
```
`exit_e1d=0`.

### 3.3 Caveats — leer antes de usar los números

1. **El PASS es el veredicto; el score absoluto NO es el score de competencia.** Con 2,560 tiros y 0 errores, el verificador calcula eps_plus = −expm1(log(2^−128)/2560) ≈ 0.0341 y R = 4.94. Ese R está inflado por el tamaño de muestra. Con el muestreo completo (102,400 tiros, 0 errores) R sería ≈1.19–1.20, como en la calibración del baseline DQI (2026-11-07). Los scores ~1.45e13 de arriba usan R=4.94 y NO deben citarse como score DQI.
2. **La comparación RELATIVA sí es válida.** Ambos circuitos se verificaron con los mismos 2,560 tiros, el mismo R=4.94 y 0 errores en ambos (semillas distintas por Fiat-Shamir — la semilla se deriva del sha256 del circuito —, así que son dos muestras independientes). E1d/fusionado = (1934/1937)² × (785012/784172) = 0.99797 → **E1d es 0.203% mejor en score DQI**. En geomean (DQI es 1 de 3 tareas): ×(1.002026)^(1/3) = ×1.000675 → **3.3237x → 3.3259x** ✓ (coincide con el estimado de la build).
3. **Chequeos de consistencia internos (E1d vs fusionado, por tiro):**
   - CCX: 1,908,684,800 → 1,910,835,200. Δ = +2,150,400 = 840 Toffoli × 2,560 tiros ✓ exacto.
   - HMR: 2,023,910,400 → 2,027,136,000. Δ = +3,225,600 = 1,260 × 2,560 ✓ (el recompute usa MBU/del).
   - num_bits: 198,393 → 198,813. Δ = +420 = 140 inv alpha × 3 bits (N' liberado/recomputado) ✓.
   - reaction_depth idéntica: 19,185 en ambos (E1d no alarga la profundidad de reacción).
   - mean_error_weight idéntico: 31.046737331746634 (misma distribución de errores decodificada).
4. **Memoria al borde, sin OOM.** El proceso del verificador llegó a 6.6 GB RSS (81% de los 7 GB de la Kali) durante la carga/simulación; `free` mostró 0 disponible en ese momento. No hubo bad_alloc ni Killed: ambos runs completaron. El peso es el circuito en memoria (~625 MB en disco → ~6.6 GB en RAM). **No subir `--max-workers` sin medir:** 1 worker ya usa 6.6 GB.
5. **Sensibilidad del muestreo.** 2,560 tiros con 0 errores descartan cualquier modo de fallo sistemático frecuente (un bug que corrompiera ≥1% de los tiros daría ~25 errores; uno de 0.1% daría ~2–3). Un modo de fallo rarísimo (<~0.1%) no se descarta con esta muestra. Combinado con los Tests A–C exactos a n=6 (que verifican la lógica del BM determinísticamente) y con que el bug tipo "SIN RUIDO" (fase 0.5 vueltas) fallaría una fracción grande de tiros, la evidencia es sólida para adoptar. **Opción no corrida:** verificación completa a 102,400 tiros en la Kali (misma carga de memoria por batch; tiempo estimado ~65 min por circuito a 1 worker). Queda como confirmación gold-standard opcional antes o después de la adopción, a decisión de Elán.

---

## 4. Números finales (medidos)

| | Baseline DQI | Fusionado | Fusionado+E1d |
|---|---|---|---|
| Q | 1,949 | 1,937 | **1,934** |
| T | 784,172 | 784,172 | **785,012** |
| Geomean (est.) | 3.31949 (Kaggle) | 3.3237x | **3.3259x** |
| Verificador oficial (Kali) | PASS (2026-11-07, 102,400 tiros) | **PASS (2,560 tiros, 0 err)** | **PASS (2,560 tiros, 0 err)** |

Adopción (fusión + E1d + lbfgs dfthcsos −0.58%): geomean ≈ **3.332x**.

---

## 5. Archivos

Local `~/workspace/qcc-data/dqi-perfil/verificacion_e1d/`:
- `VERIFICACION_E1D_REPORTE.md` — este reporte.
- `dqi_fusionado_e1d.kmb` — 624,877,910 B, sha256 `16e06d619230d169866307e1aa1be83343c8f94bd0b99526dc1acd1710383664`.
- `construir_dqi_e1d.py`, `construir_dqi_e1d.log` — build + Q/T.
- `verificar_e1d.py`, `verificar_e1d.log` — sim n=6, Tests A–C.
- `run_verify_kali.sh`, `verify_kali.log` — verificador oficial en la Kali (copia local del log).

Kali `/home/deamon/workspace/qcc-data/dqi-perfil/verificacion_e1d/`:
- `dqi_fusionado_e1d.kmb`, `dqi_fusionado.kmb` (copias verificadas por sha256), `run_verify_kali.sh`, `verify_kali.log`.

El `dqi_fusionado.kmb` original sigue en `~/workspace/qcc-data/dqi-perfil/fusion_mul_inv/` (sha256 `7a5815f4b36eb67bdb93b89bcb66c0acd6b7497e865bbde58b3ac8d87dc463cd`).

## 6. Pendientes (no son de esta verificación)

- Adopción (la lanza el agente padre): meter lbfgs dfthcsos en entrega, rebuild del ZIP, verificar el ZIP completo, decisión de Elán para Kaggle/main.
- Opcional: verificación completa a 102,400 tiros en la Kali (~65 min/circuito, 1 worker) como confirmación gold-standard.
- Pendientes de pie del chat (sin cambio): verificación oficial de `invsqrt_mushroom_kingdom.kmb` en la Kali; M6 full; `docs/PROCEDENCIA_INVSQRT.md`; §7 de `docs/ESTADO_FINAL_2026-11-07.md`.
