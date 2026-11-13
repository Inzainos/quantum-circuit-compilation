#!/usr/bin/env python3
"""DQI COMPLETO con E1d solo en el bloque alpha: medir Q/T total y geomean.

Replica medir_dqi_fusionado.py pero con BMStageFusedE1d. NO escribe el .kmb.
Esperado: Q=1937 (sin cambio), T=784172+140*6=785012, geomean ~3.3225x (peor por el T extra).
Uso: PYTHONPATH=... python3 -u medir_dqi_e1d.py
"""
import sys, time, math
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/redisenio_inversor")
import kickmix as km
import dqi_decoder_v1 as D
from bm_fused_e1d import BMStageFusedE1d

DEG = 12


def main():
    t0 = time.time()
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f'S{i}') for i in range(70)]
    E = [b.create_classical_register(DEG, name=f'E{j}') for j in range(4095)]
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
    print(f"TOTAL E1d-alpha Q={q} T={t} en {time.time()-t0:.0f}s", flush=True)
    print(f"FUSIONADO (baseline): TOTAL Q=1937 T=784172 geomean=3.3237x", flush=True)
    print(f"Delta Q={q-1937} Delta T={t-784172} (esperado Delta T=+840 = 140 inv alpha x 6 T)", flush=True)
    g = 3.3237 * (1937/q)**(2/3) * (784172/t)**(1/3)
    print(f"geomean estimado = 3.3237 * (1937/{q})^(2/3) * (784172/{t})^(1/3) = {g:.4f}x", flush=True)


if __name__ == "__main__":
    main()
