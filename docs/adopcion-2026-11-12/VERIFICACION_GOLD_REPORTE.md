# VERIFICACIÓN GOLD-STANDARD DQI FUSIONADO+E1d (102,400 TIROS) — REPORTE

**Fecha:** 2026-11-12 (lanzado 08:59:48 CST, America/Mexico_City)
**Orden de Elán (2026-11-12 ~08:59, palabras exactas, relayada por el Coordinador):** "Pero antes hagan la verificación ya todo fusionado con 102,400 tiros".
**Alcance:** SOLO esta verificación. La publicación del notebook y la subida del ZIP las lanza el agente padre cuando llegue este veredicto.
**Regla 0:** cada número viene de un log citado; lo no medido se dice, no se asume.

## ESTADO: TERMINADO — PASA (09:06:18 CST, ~6.5 min, NO ~65 min)

El verificador terminó a las 09:06:18 CST (lanzado 08:59:48 CST, duración ~6 min 30 s). La estimación de ~65 min era incorrecta: la carga del circuito domina, no la simulación (el costo por tiro es bajo; a 2,560 tiros el run tardó ~90 s, casi todo carga). `exit_gold=0`. El monitor local lo confirmó (chequeo 3, 15:10:14 hora de la caja = 09:10:14 CST: "VERIFICADOR TERMINO (exit_gold presente).").

## 1. Circuito verificado por sha256 antes de correr

- Local `~/workspace/qcc-data/dqi-perfil/verificacion_e1d/dqi_fusionado_e1d.kmb` = `16e06d619230d169866307e1aa1be83343c8f94bd0b99526dc1acd1710383664` (624,877,910 B).
- Kali `/home/deamon/workspace/qcc-data/dqi-perfil/verificacion_e1d/dqi_fusionado_e1d.kmb` = `16e06d619230d169866307e1aa1be83343c8f94bd0b99526dc1acd1710383664` ✓ (medido por SSH, 2026-11-12 ~08:59; mismo sha que el reporte de verificación E1d).
- Kali: 16 CPUs, 7,939 MB RAM total, 6,134 MB disponibles antes del lanzamiento.

## 2. Lanzamiento

- Script: `/home/deamon/workspace/qcc-data/dqi-perfil/verificacion_gold/run_verify_gold.sh` (creado por SSH).
- Log: `/home/deamon/workspace/qcc-data/dqi-perfil/verificacion_gold/verify_gold.log`.
- Comando: `/home/deamon/quantum-circuit-compilation/.venv/bin/python -u /home/deamon/wt_deamonx/quantum-sandbox/verifiers/dqi/verify_submission_dqi.py /home/deamon/workspace/qcc-data/dqi-perfil/verificacion_e1d/dqi_fusionado_e1d.kmb --num-shots 102400 --batch-size 256 --max-workers 1`.
- Lanzado con nohup: pid launcher 2597931, pid verificador 2597935 (confirmado vivo por SSH fresca ~09:00).
- Log inicial (09:00): `=== GOLD FUSIONADO+E1d Q=1934 T=785012 ===`, `Thu Nov 12 08:59:48 AM CST 2026`, sha256 `16e06d61…3664` re-verificado dentro del script.
- Memoria al iniciar: used 1,805 → 3,952 MB (carga del circuito), free 170 MB, available 3,987 MB. (En la verificación a 2,560 tiros el proceso llegó a 6.6 GB RSS, 81% de la Kali; no se subió `--max-workers`.)

## 3. Monitoreo

- Monitor local: `~/workspace/qcc-data/dqi-perfil/verificacion_gold/monitorear_gold.sh` (pid 16756, chequeo cada 300 s por SSH, tolera el hipo SSH exit 255; termina cuando el log contiene `exit_gold=`).
- Log del monitor: `~/workspace/qcc-data/dqi-perfil/verificacion_gold/monitorear_gold.log`.

## 4. Veredicto (medido — run completado 09:06:18 CST)

**PASA el verificador oficial a 102,400 tiros, pero con 2 errores de valor (no 0).** El veredicto del verificador es PASS (status `PASS`, `exit_gold=0`); el conteo de errores es 2, no 0. Se reporta tal cual (regla 0).

```json
{
  "status": "PASS",
  "score": 3527544869510.532,
  "m": 4095, "n": 70, "degree": 12, "r": 2016,
  "verified_shots": 102400,
  "value_errors": 2,
  "phase_errors": 0,
  "empirical_error_rate": 1.953125e-05,
  "effective_error_rate": 0.0009488155716079551,
  "log2_delta": -128.0,
  "repetition_factor": 1.2013880602795501,
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

| Medido | Valor |
|---|---|
| ¿PASA a 102,400 tiros? | **SÍ — status PASS, exit_gold=0** |
| Errores de valor | **2** (no 0) — empírico 2/102,400 = 1.953125e-05 |
| Errores de fase | **0** |
| eps_plus (effective_error_rate) | **0.0009488** (≈0.0009, como se esperaba) |
| R (repetition_factor) | **1.2014** (≈1.19–1.20 esperado; 0.0014 arriba del rango por los 2 errores) |
| Score DQI (R·Q²·T) | **3,527,544,869,510.532** (verificado: R·1934²·785,012 = 3,527,544,869,510.532 exacto) |
| Q / T | 1,934 / 785,012 ✓ |
| Duración | 08:59:48 → 09:06:18 CST (~6.5 min, no ~65 min) |

**Chequeos de consistencia (medidos):**
- CCX/tiro = 76,433,408,000 / 102,400 = **746,420.0** — idéntico al circuito E1d a 2,560 tiros (1,910,835,200 / 2,560 = 746,420) ✓.
- HMR/tiro = 81,085,440,000 / 102,400 = **791,850.0** — idéntico a 2,560 tiros (2,027,136,000 / 2,560 = 791,850) ✓.
- mean_error_weight = 31.046737331746634 — idéntico al run a 2,560 tiros (misma distribución de errores) ✓.
- reaction_depth = 19,185 — idéntica ✓.
- eps_plus (0.000949) < 1/16 (0.0625) = True — el PASS es por el umbral, no por 0 errores ✓.

**Los 2 errores de valor — qué son y por qué no invalidan la adopción:**
- Son errores de decodificación (el BM no corrige el error en 2 de 102,400 tiros), NO errores de fase (phase_errors = 0 — el bug tipo "SIN RUIDO" de fase 0.5 vueltas habría dado errores de fase).
- Son consistentes con la tasa de fallo intrínseca del decodificador BM: el baseline (BM v7, Q=2,016) tuvo **0 fallos en 102,400 tiros a semilla 1 y 2 fallos a semilla 7** (2026-11-07, "same as old"). 2/102,400 ≈ 2e-05 es esa misma tasa.
- El verificador PASA porque eps_plus (0.000949, la cota superior de confianza) está muy por debajo del umbral 1/16. El factor de repetición R = 1.2014 YA incluye esos 2 errores (R se calcula desde eps_plus). El score DQI 3.5275e12 es el score autoritativo con ese R.
- R = 1.2014 está 0.0014 arriba del rango esperado (1.19–1.20) por los 2 errores (con 0 errores habría sido ≈1.19). La diferencia es ~0.1% en el score DQI — no cambia el geomean 3.3289x (calculado) de forma material (el geomean usa los ratios de referencia; R entra en el score DQI absoluto, no en el ratio vs la referencia, que ya usa R≈1.19–1.20).

**Consecuencia:** la adopción (fusión + E1d + lbfgs, ZIP `171d5a81…`, geomean calculado 3.3289x) queda confirmada por el verificador oficial a 102,400 tiros. El notebook y el ZIP pueden publicarse/subirse (decisión de Elán).

## 5. Archivos

Local `~/workspace/qcc-data/dqi-perfil/verificacion_gold/`:
- `VERIFICACION_GOLD_REPORTE.md` — este reporte.
- `monitorear_gold.sh`, `monitorear_gold.log` — monitor local (chequeo 3, 15:10:14 hora de la caja = 09:10:14 CST: "VERIFICADOR TERMINO (exit_gold presente).").
- `verify_gold.log` — copia local del log del verificador (1,349 B, sha256 `bd9a24ca836a1183bdda730e5c40ee9ba33c7b26f0df028c5c1e3dfdd412aac4`).

Kali `/home/deamon/workspace/qcc-data/dqi-perfil/verificacion_gold/`:
- `run_verify_gold.sh`, `verify_gold.log` — lanzador y log del verificador.
