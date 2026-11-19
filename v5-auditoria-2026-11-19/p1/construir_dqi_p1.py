#!/usr/bin/env python3
"""Construir el DQI COMPLETO con el multiplicador de p1/src y GUARDAR el .kmb.

CONTROL P1: copia fiel de construir_dqi_omega.py (swap42) con el OUT cambiado
a p1/. Si el build es reproducible, el .kmb debe ser byte-identico al swap42
(sha256 746271d9...). Despues del control, dqi_kmul42.py en p1/src se reescribe
con la matriz 6x7 explicita (P1) y se reconstruye como dqi_p1.kmb.
Uso: /home/hatch/workspace/py313/python/bin/python3.13 -u construir_dqi_p1.py
"""
import sys, os, time, hashlib
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/redisenio_inversor")
# scratch AL FINAL (queda primero en sys.path y hace sombra a los originales)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kickmix as km
import dqi_bm_stage_v1, bm_fused, bm_fused_e1d
import dqi_decoder_v1 as D
from bm_fused_e1d import BMStageFusedE1d

DEG = 12
OUT = "/home/hatch/workspace/qcc-data/test-dev/espiral-prototipo/p1/dqi_p1.kmb"


def main():
    print(f"modulos: dqi_bm_stage_v1={dqi_bm_stage_v1.__file__}", flush=True)
    print(f"modulos: bm_fused={bm_fused.__file__}", flush=True)
    print(f"modulos: bm_fused_e1d={bm_fused_e1d.__file__}", flush=True)
    print(f"modulos: dqi_decoder_v1={D.__file__}", flush=True)
    print(f"modulos: dqi_kmul42={sys.modules['dqi_kmul42'].__file__}", flush=True)
    t0 = time.time()
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(70)]
    E = [b.create_classical_register(DEG, name=f"E{j}") for j in range(4095)]
    bm = BMStageFusedE1d(b, gf, S, 36, 70)
    bm.forward()
    print(f"[bm_forward] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    D.build_omega_tmp(b, gf, bm.sigma, S, 35, adjoint=False)
    print(f"[omega_fwd] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    D.build_scan_inv(b, gf, bm.sigma, S[:35], E, None)
    print(f"[scan] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    D.build_omega_tmp(b, gf, bm.sigma, S, 35, adjoint=True)
    print(f"[omega_rev] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    bm.reverse()
    b.x(bm.sigma[0][0]); b.x(bm.tau[1][0]); b.x(bm.d[0])
    print(f"[bm_reverse] live_frontera={int(b.num_allocated_qubits)}", flush=True)
    c = b.finish_circuit()
    q = int(c.num_qubits); t = int(c.operation_statistics().num_toffoli_like)
    print(f"TOTAL P1 Q={q} T={t} en {time.time()-t0:.0f}s", flush=True)
    print(f"PRODUCCION (omega/Karatsuba): Q=1864 T=774932", flush=True)
    print(f"Delta Q={q-1864} Delta T={t-774932} (proyectado Delta Q=0 Delta T=-64620)", flush=True)
    ratio_dqi = 7.48129 * (774932 / t)
    g_calc = (5.32 * ratio_dqi * 1.00583) ** (1/3)
    g_esc = 3.42920 * (774932 / t) ** (1/3)
    print(f"DQI ratio nuevo = {ratio_dqi:.5f}x", flush=True)
    print(f"geomean calculado = {g_calc:.5f}x ; geomean escalando Kaggle 3.42920x = {g_esc:.5f}x", flush=True)
    c.to_file(OUT, format="kmb")
    h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    print(f"guardado {OUT} sha256={h}", flush=True)


if __name__ == "__main__":
    main()
