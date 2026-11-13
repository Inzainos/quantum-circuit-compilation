#!/usr/bin/env python3
"""Construir el DQI COMPLETO con la etapa BM fusionada y medir Q/T total + vivos en fronteras.

Replica build_decoder() de dqi_decoder_v1.py pero con BMStageFused.
Baseline (medido): TOTAL Q=1949 T=784172.

Uso: PYTHONPATH=... python3 medir_dqi_fusionado.py
"""
import sys, time, hashlib
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv")
import kickmix as km
import dqi_decoder_v1 as D
from bm_fused import BMStageFused

DEG = 12

def main():
    t0 = time.time()
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(70)]
    E = [b.create_classical_register(DEG, name=f"E{j}") for j in range(4095)]
    bm = BMStageFused(b, gf, S, 36, 70)
    bm.forward()
    print(f"[bm_forward] live_frontera={int(b.num_allocated_qubits)} (pico medido aparte: 1930)", flush=True)
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
    print(f"TOTAL FUSIONADO Q={q} T={t} en {time.time()-t0:.0f}s", flush=True)
    print(f"BASELINE: TOTAL Q=1949 T=784172", flush=True)
    print(f"Delta Q={q-1949} Delta T={t-784172}", flush=True)
    # geomean: DQI ratio = R*Q^2*T ; geomean escala como (Q_old/Q_new)^(2/3) * (T_old/T_new)^(1/3)
    import math
    g = 3.31 * (1949/q)**(2/3) * (784172/t)**(1/3)
    print(f"geomean estimado = 3.31 * (1949/{q})^(2/3) * (784172/{t})^(1/3) = {g:.4f}x", flush=True)
    c.to_file("/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv/dqi_fusionado.kmb", format="kmb")
    h = hashlib.sha256(open("/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv/dqi_fusionado.kmb","rb").read()).hexdigest()
    print(f"guardado dqi_fusionado.kmb sha256={h}", flush=True)

if __name__ == "__main__":
    main()
