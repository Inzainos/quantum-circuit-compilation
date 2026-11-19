# Verificación Brujo — Circuitos adoptados para v5 (QF + lbfgs)
Fecha: 2026-11-19 ~16:58. Verificador: El Brujo. Alcance: los dos circuitos adoptados que entran al v5 (DQI QF + dfthcsos lbfgs), por orden de Elán (opción elegida 16:47). Método: hash/tamaño de los archivos, Gold log (QF), evaluación local (lbfgs), miembros de los ZIPs por streaming (sin extraer). Nada se construyó ni se modificó.

## 1. DQI — QF (Q=1857, T=710,312)
- Archivo: `~/workspace/qcc-data/test-dev/espiral-prototipo/claude-qf/dqi_qf.kmb`
- Tamaño: 628,685,675 B. sha256: `38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13` — **byte-idéntico al build QF verificado en cadena**.
- Gold log `verify_qf_gold.log` (1,415 B, 19 nov 14:42): status **PASS**; score **2,971,470,537,625.3**; value_errors 5; phase_errors 0; toffoli_count 710,312; num_qubits 1857; reaction_depth 3,154. Todos coinciden con los valores de la cadena QF.
- ZIP v4.1 (`candidato-qf-2026-11-19.zip`): miembro `dqi.kmb` sha256 = `38b9cbf0…` — **el ZIP contiene exactamente el QF**.
- Mínima fricción: formas in-place (`form_ip`/`unform_ip`) + `fan_ccx`; el dato se transforma donde vive, sin copias ni qubits extra: −7 Q, ΔT=0.
- **Veredicto: CONCURRO (PASA). Listo para v5.**

## 2. dfthcsos — lbfgs (65,60,60)
- Archivo: `~/workspace/qcc-data/dfthcsos-refit/lbfgs_rho1e-4_eps17_65_60_60_ep100.npz`
- md5: `81ff3249396c7b9256cca2b1db7c8ee8`. Tamaño: 2,195,394 B. ✓
- ZIPs: miembro `dfthcsos/submission.npz` md5 = `521d53c6d8948720cdb9913f7885bdc9` en **v3 y en v4.1** — el mismo lbfgs en ambos. (El `dqi.kmb` del v3 es swap42, sha `209d53e2…`, distinto del QF, como corresponde.)
- Evaluación local (continua, `evaluate_inputs`, Task 1): error_1 ≈ 0 mHa (8.98e-12, nivel de redondeo); **error_2 16.985 mHa (< 20 mHa, PASA)**; lambda_eff 48.966; E_gap 3.913. El .npz carga y evalúa bien.
- Precisión honesta: la evaluación local continua (Task 1) da error_2 16.985, mientras la evaluación oficial de bits finitos (Task 3, 254,464 shots) dio error_1 3.340 mHa, error_2 19.371 mHa, score 3,336,160,975, PASS. Son evaluaciones distintas; la aceptación se juzga por la de bits finitos (oficial), que **PASÓ**. La local es consistente (pasa) y confirma que el archivo está intacto.
- No reproduje T/Q/score localmente en esta corrida: mi llamada a `resource_costs` pasó circuitos vacíos y levantó `ValueError: circuits must be nonempty` (error mío, no del archivo). Los valores autoritativos T=93,237, Q=730, score 3,336,160,975 son del verificador oficial, ya verificados en cadena. No los re-derivo aquí.
- Mínima fricción: modelo analítico + tabla de ángulos tal cual, sin reestructura.
- **Veredicto: CONCURRO (PASA). Listo para v5.**

## 3. Conclusión
Los dos circuitos adoptados están intactos (hash + miembro de ZIP) y verificados (QF Gold PASS; lbfgs evaluación local PASA + oficial PASS en registro). **QF + lbfgs listos para v5.** Nota: el DQI del v5 será el build combinado P1+P2+P3 sobre código QF (GO dado por Elán, en construcción por Programación); el dfthcsos se queda lbfgs.
