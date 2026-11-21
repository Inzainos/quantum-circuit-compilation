import sys; sys.path.insert(0,'/home/claude/qcc-local/kickmix')
import kickmix as km, numpy as np
b=km.CircuitBuilder()
q=b.alloc_qubits(3); c=b.create_classical_register(12,name='c'); isb=b.alloc_bits(1)
b.bit_store(isb[0], True, control=c)
b.push_condition(isb[0])
b.init_and(q[0],q[1],q[2]); b.del_and(q[0],q[1],q[2])
b.pop_condition(); b.bit_store(isb,False)
circ=b.finish_circuit()
for k in (None,0,5,11):
    sim=km.Simulator(batch_size=64,debug_print=False,counting_operations=True,seed=1)
    sim.use_same_registers_as(circ)
    v=np.zeros((12,64),dtype=bool)
    if k is not None: v[k,:]=True
    sim.write_across_shots(km.array(list(c)),v) if False else sim.write_across_shots(km.array(c),v)
    sim.do(circ); print(k, sim.operation_statistics().num_toffoli_like)
