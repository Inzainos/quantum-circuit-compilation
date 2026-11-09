import numpy as np, sys, itertools, time
sys.path.insert(0,'src'); sys.path.insert(0,'verifiers/invsqrt')
from invsqrt_halfsplit import tabla_mitad, error_relativo
from invsqrt_piecewise import PWSpec
spec=PWSpec(deg=2,j=8,wc=28,dd=13)
def modelo_t(spec, xs, sesgo, ks, dd):
    width,j,d=spec.width,spec.j,spec.deg
    b,w=tabla_mitad(spec,sesgo)
    xs=np.asarray(xs,dtype=np.int64)
    s=(width-(np.floor(np.log2(xs)).astype(np.int64)+1))//2
    xn=xs<<(2*s); mask=(1<<width)-1
    top=(xn>>(width-1))&1; sel=1-top
    rot=np.where(top==1,xn,(xn<<1)&mask)
    f=(rot>>(width-1-j))&((1<<j)-1); addr=f+(sel<<j)
    tab=[np.array(r,dtype=np.int64) for r in b]
    c={i:tab[i][addr] for i in range(d+1)}
    for i in range(d-1,-1,-1):
        k=ks[i]; prod=np.zeros_like(xs)
        for m in range(1,dd+1):
            ctl=(rot>>(width-1-j-m))&1
            prod+=ctl*((c[i+1]>>(m+k))<<k)
        acc=c[i]-prod
        if ((acc<0)|(acc>=2**w[i])).any(): raise OverflowError
        c[i]=acc
    return c[0]<<s
def errtol(xs,sesgo,ks,dd):
    y=modelo_t(spec,xs,sesgo,ks,dd)
    return float(error_relativo(spec,xs,y).max())/2**-24
if __name__=='__main__':
    full=np.arange(1,1<<22,dtype=np.int64)
    sub=full[::13]
    # linea base: buscar sesgo del entregado
    t0=time.time()
    base=[(sg,errtol(sub,sg,(0,0),13)) for sg in range(0,40,4)]
    print('base (k=0,0,dd=13) sesgo->error/tol(sub):',[(a,round(b,3)) for a,b in base], round(time.time()-t0,1),'s')
