import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-worktrees/dqi-1949/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import kickmix as km
import dqi_decoder_v1 as D
from dqi_bm_stage_v1 import BMStageV1
b = km.CircuitBuilder(); gf = km.GF2Field(D.DEG)
S = [b.create_quantum_register(D.DEG, name=f"S{i}") for i in range(70)]
bm = BMStageV1(b, gf, S, 36, 70)
bm.forward()
c = b.finish_circuit()
c.to_file("/home/hatch/workspace/qcc-data/dqi-perfil/bm_forward.kmb", format="kmb")
print("BM forward only: Q=%d T=%d" % (c.num_qubits, c.operation_statistics().num_toffoli_like))
