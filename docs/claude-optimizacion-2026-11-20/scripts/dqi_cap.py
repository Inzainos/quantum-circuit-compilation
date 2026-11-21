import os
REPO=os.environ.get("REPO","."); KICKMIX=os.environ.get("KICKMIX","/home/claude/qcc-local/kickmix")
import sys, os, traceback
sys.path.insert(0,os.environ['SRCQ']); sys.path.insert(0,KICKMIX)
import kickmix as km, dqi_decoder_v1 as D
from bm_fused_e1d import BMStageFusedE1d
cap=int(sys.argv[1]); DEG=12
b=km.CircuitBuilder(); b.set_max_qubits(cap); gf=km.GF2Field(DEG)
S=[b.create_quantum_register(DEG,name=f'S{i}') for i in range(70)]
E=[b.create_classical_register(DEG,name=f'E{j}') for j in range(4095)]
try:
    bm=BMStageFusedE1d(b,gf,S,36,70); bm.forward()
    D.build_omega_tmp(b,gf,bm.sigma,S,35,adjoint=False)
    D.build_scan_inv(b,gf,bm.sigma,S[:35],E,range(2))
    D.build_omega_tmp(b,gf,bm.sigma,S,35,adjoint=True)
    bm.reverse(); b.x(bm.sigma[0][0]); b.x(bm.tau[1][0]); b.x(bm.d[0])
    c=b.finish_circuit(); print('cap',cap,'OK Q',c.num_qubits,'T',int(c.operation_statistics().num_toffoli_like),'(base 306030)')
except Exception as e:
    print('cap',cap,'EXCEDE',repr(e)[:150].replace('\n',' '))
    for f in traceback.extract_tb(sys.exc_info()[2])[-6:]: print('  ',os.path.basename(f.filename),f.lineno,f.name)
