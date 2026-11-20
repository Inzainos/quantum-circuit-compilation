#!/usr/bin/env python3
"""Construir el DQI COMPLETO P1+P2+P3 sobre el codigo QF y GUARDAR el .kmb.

Combinado P1+P2+P3 (Fase 2, espiral) sobre el codigo QF (parche de Claude,
local/claude-qf-minus7-2026-11-19, main 64d4cec). Esperado: BYTE-IDENTICO al
.kmb QF (sha256 38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13,
628,685,675 B), Q=1857, T=710,312.

Uso:
  /home/hatch/workspace/py313/python/bin/python3.13 -u construir_dqi_p1p2p3_qf.py [salida.kmb]
  (por defecto: dqi_p1p2p3_qf.kmb en el workspace p1p2p3-qf/)

Fix D-QF-1 (Brujo): importar dqi_decoder_v1 PRIMERO (antes de los modulos BM)
+ asercion de que TODOS los modulos DQI vienen del scratch. El build log
prueba los __file__ de todos los modulos importados.
"""
import sys, os, time, hashlib
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/fusion_mul_inv")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/dqi-perfil/redisenio_inversor")
# scratch AL FINAL (queda primero en sys.path y hace sombra a los originales)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# dqi_bm_model.py importa verify_submission_dqi via parent.parent/verifiers/dqi;
# el scratch es una copia suelta de src/ sin raiz de repo, asi que esa ruta no
# existe aqui: se agrega el dir real de verificadores (solo para ese import;
# el contenido de dqi_bm_model.py es md5-identico al del repo, f3d8bb0a...).
sys.path.insert(0, "/home/hatch/workspace/qcc-data/verifiers/dqi")
import kickmix as km
import dqi_decoder_v1 as D  # PRIMERO: desde scratch, antes de que las dependencias inserten qcc-dqi/src al frente
import dqi_bm_stage_v1, bm_fused, bm_fused_e1d
from bm_fused_e1d import BMStageFusedE1d
# Asercion: TODOS los modulos del DQI deben venir del scratch combinado
_SCRATCH = os.path.dirname(os.path.abspath(__file__))
for _m in (dqi_bm_stage_v1, bm_fused, bm_fused_e1d, D):
    assert _m.__file__.startswith(_SCRATCH), f"{_m.__name__} vino de {_m.__file__}, no del scratch {_SCRATCH}"
import dqi_kmul42 as _k
assert _k.__file__.startswith(_SCRATCH), f"dqi_kmul42 vino de {_k.__file__}"
print(f"modulos: TODOS desde scratch {_SCRATCH}", flush=True)

DEG = 12
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    "/home/hatch/workspace/qcc-data/test-dev/espiral-prototipo/p1p2p3-qf",
    "dqi_p1p2p3_qf.kmb")


def _check_modulos(tag):
    """Asercion final: todo modulo DQI cargado viene del scratch."""
    import sys as _sys
    _prefijos = ("dqi_", "bm_", "tower_", "qf")
    _mal = []
    for _name, _mod in sorted(_sys.modules.items()):
        if _mod is None or not hasattr(_mod, "__file__") or _mod.__file__ is None:
            continue
        if _name.split(".")[0].startswith(_prefijos) or _name == "qf":
            print(f"modulos[{tag}]: {_name}={_mod.__file__}", flush=True)
            if not _mod.__file__.startswith(_SCRATCH):
                _mal.append(f"{_name}={_mod.__file__}")
    assert not _mal, f"MODULOS FUERA DEL SCRATCH [{tag}]: {_mal}"
    print(f"modulos[{tag}]: TODOS desde scratch", flush=True)


def main():
    print(f"modulos: dqi_bm_stage_v1={dqi_bm_stage_v1.__file__}", flush=True)
    print(f"modulos: bm_fused={bm_fused.__file__}", flush=True)
    print(f"modulos: bm_fused_e1d={bm_fused_e1d.__file__}", flush=True)
    print(f"modulos: dqi_decoder_v1={D.__file__}", flush=True)
    print(f"modulos: dqi_kmul42={sys.modules['dqi_kmul42'].__file__}", flush=True)
    print(f"P1: EMIT_ORDER={_k.EMIT_ORDER} PLAN42_MATRIX={len(_k.PLAN42_MATRIX)}x{len(_k.PLAN42_MATRIX[0])} _iter_plan==PLAN42: {list(_k._iter_plan()) == _k.PLAN42}", flush=True)
    print(f"P2: _ladder6_alloc en BMStageV1: {hasattr(dqi_bm_stage_v1.BMStageV1, '_ladder6_alloc')}", flush=True)
    print(f"P3: N_OMEGA_BLOCK={D.N_OMEGA_BLOCK} bloques/pase ida: {len(D._omega_mul_blocks(35, False))} vuelta: {len(D._omega_mul_blocks(35, True))}", flush=True)
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
    _check_modulos("post-build")
    c = b.finish_circuit()
    q = int(c.num_qubits); t = int(c.operation_statistics().num_toffoli_like)
    print(f"TOTAL P1+P2+P3-QF Q={q} T={t} en {time.time()-t0:.0f}s", flush=True)
    print("REFERENCIA QF: Q=1857 T=710312", flush=True)
    print(f"Delta vs QF: Q={q-1857} T={t-710312} (esperado 0 0)", flush=True)
    c.to_file(OUT, format="kmb")
    h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    print(f"guardado {OUT} sha256={h}", flush=True)
    print("REFERENCIA QF sha256=38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13 (628685675 B)", flush=True)
    print(f"BYTE-IDENTICO al QF: {h == '38b9cbf0e2f552b22bd1b36ccc2a1d781e455a0ae058e78db0b5a95f77a6ae13'}", flush=True)


if __name__ == "__main__":
    main()
