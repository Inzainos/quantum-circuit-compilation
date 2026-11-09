#!/usr/bin/env python3
"""Perfilado del DQI (decodificador BM v1, commit a741cc7) por etapa.

Reproduce build_decoder() paso a paso y toma una foto (finish_circuit) en cada
frontera de etapa: Q = num_qubits del circuito prefijo (pico de qubits vivos
en ese prefijo, verificado: tras BM forward Q=1949 con live_now=1864) y
T = num_toffoli_like acumulado. T(etapa) = T(acum) - T(acum anterior).
Ademas registra qubits vivos por ronda BM (forward y reverse) para localizar
en que ronda se fija el pico Q=1949.

Uso: PYTHONPATH=.../kickmix:.../src python3 perfil_dqi_etapas.py
Salida: perfil_dqi_etapas.json + resumen en stdout.
"""
import sys, time, json
sys.path.insert(0, "/home/hatch/workspace/qcc-worktrees/dqi-1949/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import kickmix as km
import dqi_decoder_v1 as D
from dqi_bm_stage_v1 import BMStageV1

DEG = D.DEG
OUT = "/home/hatch/workspace/qcc-data/dqi-perfil/perfil_dqi_etapas.json"

def snap(b, label):
    c = b.finish_circuit()
    st = c.operation_statistics()
    return {"label": label, "Q": int(c.num_qubits),
            "T_acum": int(st.num_toffoli_like),
            "live": int(b.num_allocated_qubits)}

def main():
    t0 = time.time()
    res = {"commit": "a741cc7", "fuente": "worktree ~/workspace/qcc-worktrees/dqi-1949"}
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(70)]
    E = [b.create_classical_register(DEG, name=f"E{j}") for j in range(4095)]
    bm = BMStageV1(b, gf, S, 36, 70)
    res["registros"] = {"S": 70 * DEG, "sigma": len(bm.sigma) * DEG,
                        "tau": len(bm.tau) * DEG, "d": len(bm.d),
                        "H": len(bm.H), "banderas_p_t": 0}

    # --- BM forward, por ronda ---
    fwd_live = []
    for r in range(70):
        bm.forward_round(r)
        fwd_live.append(int(b.num_allocated_qubits))
    res["bm_forward_por_ronda_live"] = fwd_live
    res["registros"]["banderas_p_t"] = 2 * len(bm.flags)
    s1 = snap(b, "bm_forward")
    res["etapas"] = [s1]
    print(f"[bm_forward] Q={s1['Q']} T_acum={s1['T_acum']} live={s1['live']} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # --- omega forward ---
    D.build_omega_tmp(b, gf, bm.sigma, S, 35, adjoint=False)
    s2 = snap(b, "omega_fwd")
    res["etapas"].append(s2)
    print(f"[omega_fwd] Q={s2['Q']} T_acum={s2['T_acum']} live={s2['live']} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # --- scan (barrido por posicion) ---
    D.build_scan_inv(b, gf, bm.sigma, S[:35], E, None)
    s3 = snap(b, "scan")
    res["etapas"].append(s3)
    print(f"[scan] Q={s3['Q']} T_acum={s3['T_acum']} live={s3['live']} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # --- omega reverse ---
    D.build_omega_tmp(b, gf, bm.sigma, S, 35, adjoint=True)
    s4 = snap(b, "omega_rev")
    res["etapas"].append(s4)
    print(f"[omega_rev] Q={s4['Q']} T_acum={s4['T_acum']} live={s4['live']} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # --- BM reverse, por ronda ---
    rev_live = []
    for r in reversed(range(70)):
        bm.reverse_round(r)
        rev_live.append({"round": r, "live": int(b.num_allocated_qubits)})
    b.x(bm.sigma[0][0]); b.x(bm.tau[1][0]); b.x(bm.d[0])
    s5 = snap(b, "bm_reverse+final")
    res["etapas"].append(s5)
    res["bm_reverse_por_ronda_live"] = rev_live
    print(f"[bm_reverse] Q={s5['Q']} T_acum={s5['T_acum']} live={s5['live']} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # --- T por etapa (diferencias) ---
    prev = 0
    for s in res["etapas"]:
        s["T_etapa"] = s["T_acum"] - prev
        prev = s["T_acum"]
    res["total_s"] = round(time.time() - t0, 1)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2)
    print("TOTAL Q=%d T=%d en %.1fs -> %s" % (s5["Q"], s5["T_acum"], res["total_s"], OUT))

if __name__ == "__main__":
    main()
