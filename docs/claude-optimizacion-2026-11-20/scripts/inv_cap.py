import os
REPO=os.environ.get("REPO","."); KICKMIX=os.environ.get("KICKMIX","/home/claude/qcc-local/kickmix")
import sys, os, traceback, logging
sys.path.insert(0,REPO); sys.path.insert(0,KICKMIX); sys.path.insert(0,os.path.join(REPO,'verifiers','invsqrt'))
logging.disable(logging.CRITICAL)
import kickmix as km
cap=int(sys.argv[1])
Real=km.CircuitBuilder
def mk():
    b=Real(); b.set_max_qubits(cap); return b
km.CircuitBuilder=mk
from src.invsqrt_logshift2 import PipelineLog2
from src.invsqrt_halfsplit import PWSpec
P=PipelineLog2(PWSpec(deg=2,j=8,wc=28,dd=13),1)
try:
    c=P.construye(); print('cap',cap,'OK Q',c.num_qubits,'T',c.operation_statistics().num_toffoli_like,'ops',len(c)); import hashlib; c.to_file(f'inv_cap{cap}.kmb',format='kmb')
except Exception as e:
    print('cap',cap,'EXCEDE',repr(e)[:120])
    for f in traceback.extract_tb(sys.exc_info()[2])[-7:]: print('  ',os.path.basename(f.filename),f.lineno,f.name)
