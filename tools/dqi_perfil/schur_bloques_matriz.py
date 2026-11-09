#!/usr/bin/env python3
"""q-d MATRICIAL 2x2 (Schur por bloques) para el decodificador BM in-place.

Formulacion even/odd: S(x)=A(y)+x B(y), sigma(x)=C(y)+x D(y),
omega(x)=E(y)+x F(y), y=x^2. La ecuacion clave es la ecuacion matricial
  M(y) . S~(y) = Omega(y)  (mod y^35)
  M=[[C, yD],[D, C]], S~=[[A, yB],[B, A]], Omega=[[E, yF],[F, E]].
La serie matricial S~(y)=sum_j S~_j y^j tiene coeficientes 2x2:
  S~_j = [[S_{2j}, S_{2j-1}],[S_{2j+1}, S_{2j}]]   (S_{-1}=0).
El q-d matricial opera sobre bloques 2x2 (elementos de GF(2^24) en el
sentido de la implementacion: un par (a,b) de GF(2^12)):
  Q_1^(n)   = S~_{n+1} . (S~_n)^{-1}
  E_k^(n)   = Q_k^(n+1) + Q_k^(n) + E_{k-1}^(n+1)      (car 2: - = +)
  Q_{k+1}^(n)= E_k^(n+1) . Q_k^(n+1) . (E_k^(n))^{-1}
La division escalar por e_k^(n) se vuelve INVERSA de matriz 2x2:
una matriz 2x2 puede ser invertible aunque un escalar sea 0 -> el bloque
absorbe el bloque singular (L=35). Los convergentes de la J-fraccion
matricial dan (P, Qmat) con Qmat . S~ = P; Qmat (normalizada) = M,
de donde C, D -> sigma = C(x^2) + x D(x^2).
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G

# --- matrices 2x2 sobre GF(2^12): (a,b,c,d) = [[a,b],[c,d]] ---
def madd(A, B):
    return (A[0]^B[0], A[1]^B[1], A[2]^B[2], A[3]^B[3])
def mmul(A, B):
    a,b,c,d = A; e,f,g,h = B
    return (G.mul(a,e)^G.mul(b,g), G.mul(a,f)^G.mul(b,h),
            G.mul(c,e)^G.mul(d,g), G.mul(c,f)^G.mul(d,h))
def mdet(A):
    a,b,c,d = A
    return G.mul(a,d)^G.mul(b,c)
def minv(A):
    a,b,c,d = A
    det = mdet(A)
    if det == 0:
        return None
    iv = G.inv(det)
    return (G.mul(d,iv), G.mul(b,iv), G.mul(c,iv), G.mul(a,iv))
def mzero():
    return (0,0,0,0)
def meq(A,B):
    return A==B

def trim(a):
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a

def syndrome(rng, k, n):
    pos = rng.choice(4095, size=k, replace=False)
    vals = rng.integers(1, 4096, size=k)
    X = [int(G.EXP[p % 4095]) for p in pos]
    S = []
    for t in range(n):
        s = 0
        for xj, e in zip(X, vals):
            s ^= G.mul(int(e), int(G.EXP[(G.LOG[xj] * t) % 4095]))
        S.append(s)
    return S

def mat_series(S):
    """S~_j = [[S_{2j}, S_{2j-1}],[S_{2j+1}, S_{2j}]] para j=0..34 (n=70)."""
    n = len(S)
    out = []
    for j in range((n+1)//2):
        a = S[2*j] if 2*j < n else 0
        b = S[2*j-1] if 2*j-1 >= 0 else 0
        c = S[2*j+1] if 2*j+1 < n else 0
        d = a
        out.append((a,b,c,d))
    return out

def qd_mat_col0(St, kmax):
    """Columna n=0 del q-d matricial hasta k=kmax. Devuelve (Q0,E0,info)
    o (None,None,razon). Cuenta ops de campo GF(2^12) (muls+invs)."""
    N = len(St)
    nmul = [0]; ninv = [0]
    def mmul_c(A,B):
        nmul[0]+=8
        return mmul(A,B)
    def minv_c(A):
        ninv[0]+=1; nmul[0]+=2
        return minv(A)
    Q = {}; E = {}
    def getQ(k,n): return Q.get((k,n))
    def getE(k,n):
        if k==0: return mzero()
        return E.get((k,n))
    # Q_1^(n) = S~_{n+1} . inv(S~_n), n=0..min(N-2, 2*kmax)
    nmax_q1 = min(N-2, 2*kmax)
    for n in range(nmax_q1+1):
        iv = minv_c(St[n])
        if iv is None:
            return None, None, ("Q1", n, "S~_singular det=0")
        Q[(1,n)] = mmul_c(St[n+1], iv)
    for k in range(1, kmax+1):
        nmax_e = min(N-2*k-1, 2*(kmax-k))
        for n in range(nmax_e+1):
            qkn1=getQ(k,n+1); qkn=getQ(k,n); ekm1=getE(k-1,n+1)
            if qkn1 is None or qkn is None or ekm1 is None:
                return None, None, ("E",k,n,"sin_coefs")
            E[(k,n)] = madd(madd(qkn1,qkn),ekm1)
        if k < kmax:
            nmax_q = min(N-2*(k+1), 2*(kmax-k)-1)
            for n in range(nmax_q+1):
                ekn1=getE(k,n+1); qkn1=getQ(k,n+1); ekn=getE(k,n)
                if ekn1 is None or qkn1 is None or ekn is None:
                    return None, None, ("Q",k+1,n,"sin_coefs")
                iv = minv_c(ekn)
                if iv is None:
                    return None, None, ("Q",k+1,n,"E_singular det=0")
                Q[(k+1,n)] = mmul_c(mmul_c(ekn1,qkn1), iv)
    Q0=[None]; E0=[None]
    for kk in range(1,kmax+1):
        vq=getQ(kk,0); ve=getE(kk,0)
        if vq is None:
            return None,None,("col0",kk,"Q_falta")
        Q0.append(vq); E0.append(ve if ve is not None else mzero())
    return Q0,E0,("ok",nmul[0],ninv[0])

def jfrac_mat_conv(S0, Q0, E0, nconv):
    """Convergentes de la J-fraccion matricial.
    f = 0 + S0 / (1 + (-Q_1 y)/(1 + (-E_1 y)/(1 + (-Q_2 y)/(...)))).
    B_1=S0 (matriz), B_{2k}=-Q_k y, B_{2k+1}=-E_k y.
    p_k = p_{k-1} + B_k . p_{k-2}; q_k = q_{k-1} + B_k . q_{k-2}
    (A_k=1). p,q son matrices 2x2 de polinomios en y (listas de matrices)."""
    def padd(P, Qm):
        n=max(len(P),len(Qm))
        out=[mzero()]*n
        for i,M in enumerate(P): out[i]=madd(out[i],M)
        for i,M in enumerate(Qm): out[i]=madd(out[i],M)
        # trim ceros finales
        while len(out)>1 and out[-1]==mzero(): out.pop()
        return out
    def B(k):
        if k==1: return [S0]
        if k%2==0: return [mzero(), Q0[k//2]]
        return [mzero(), E0[(k-1)//2]]
    def bmul(Bk, P):
        # Bk es [matriz] (const) o [0, matriz] (por y)
        if len(Bk)==1:
            return [mmul(Bk[0], M) for M in P]
        return [mzero()]+[mmul(Bk[1], M) for M in P]
    p_prev2=[[ (1,0,0,1) ]]; p_prev1=[[mzero()]]
    q_prev2=[[mzero()]];     q_prev1=[[ (1,0,0,1) ]]
    conv=[]
    for k in range(1,nconv+1):
        Bk=B(k)
        pk=padd(list(p_prev1), bmul(Bk,p_prev2))
        qk=padd(list(q_prev1), bmul(Bk,q_prev2))
        conv.append((pk,qk))
        p_prev2,p_prev1=p_prev1,pk
        q_prev2,q_prev1=q_prev1,qk
    return conv

def pmul(a,b):
    if not a or not b: return [0]
    out=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            out[i+j]^=G.mul(x,y)
    return out

def mat_to_sigma(Qmat):
    """Qmat = lista de matrices 2x2 (coefs en y). Normaliza por (1,1)[0]
    y extrae C(y)=Qmat[1,1], D(y)=Qmat[2,1]; sigma(x)=C(x^2)+x D(x^2)."""
    # Qmat[k] es la matriz coef de y^k: (a,b,c,d) = [[a,b],[c,d]]
    # C(y) = sum a_k y^k ; D(y) = sum c_k y^k
    a0 = Qmat[0][0]
    if a0==0: return None
    iv=G.inv(a0)
    C=[G.mul(M[0],iv) for M in Qmat]
    D=[G.mul(M[2],iv) for M in Qmat]
    # sigma(x) = C(x^2) + x D(x^2): coef x^{2j}=C_j, x^{2j+1}=D_j
    sig=[0]*(2*len(C))
    for j,c in enumerate(C): sig[2*j]=c
    for j,d in enumerate(D): sig[2*j+1]=d
    return trim(sig)

rng = np.random.default_rng(7)
print("=== q-d MATRICIAL 2x2 + J-fraccion vs BM ===")
for (k_err, n) in [(2,6),(2,10),(5,20),(3,70),(8,70),(12,70),(20,70),(34,70),(35,70)]:
    S = syndrome(rng, k_err, n)
    stats={"mac":0,"div":0,"cambios":0}
    sig_bm, L_bm = G.bm(S, stats)
    if L_bm==0:
        print(f"k={k_err} n={n}: L=0, salto"); continue
    L=L_bm
    St = mat_series(S)
    # La serie matricial tiene N'=(n+1)//2 coefs; el grado en y es ~L/2.
    # kmax en y: el convergente que da sigma tiene deg_y ~ ceil(L/2).
    kmax = (L+1)//2 + 1
    Q0,E0,info = qd_mat_col0(St, kmax)
    if Q0 is None:
        print(f"k={k_err} n={n} L={L}: q-d MATRICIAL BREAKDOWN en {info}")
        continue
    nconv = 2*kmax+1
    conv = jfrac_mat_conv(St[0], Q0, E0, nconv)
    found=None
    for k,(p,qm) in enumerate(conv):
        sig = mat_to_sigma(qm)
        if sig is not None and trim(sig)==trim(sig_bm):
            found=(k,p,qm,sig); break
    if found is None:
        print(f"k={k_err} n={n} L={L}: ningun convergente matricial da sigma. qd={info}")
        continue
    k,p,qm,sig = found
    # ecuacion clave sigma.S = omega (mod x^n)
    prod = pmul(sig, S)
    lhs = trim(prod[:n])
    # omega = numerador p: P es matriz de polinomios; omega(x)=E(x^2)+xF(x^2)
    # con E=P[1,1], F=P[2,1] (normalizados por el mismo factor que sigma)
    a0 = qm[0][0]; iv = G.inv(a0) if a0!=0 else None
    if iv is None:
        print(f"k={k_err} n={n} L={L}: a0=0 no normalizable"); continue
    Epoly=[G.mul(M[0],iv) for M in p]
    Fpoly=[G.mul(M[2],iv) for M in p]
    om=[0]*(2*len(Epoly))
    for j,c in enumerate(Epoly): om[2*j]=c
    for j,d in enumerate(Fpoly): om[2*j+1]=d
    om=trim(om)
    ok_key = (lhs==om)
    print(f"k={k_err} n={n} L={L}: convergente MATRICIAL J[{k}] q==sigma_BM! ec_clave={ok_key} qd={info}")
