"""Plan de 15 ANDs para la multiplicacion en GF(64) (base polinomial B de dqi_tower_inv): GF(64)=GF(4)[g]/(cubica),
producto de cuadraticas sobre GF(4) evaluado en P1(GF(4)) = {0,1,w,w^2,inf} (5 puntos) y GF(4) con 3 ANDs c/u: 5*3 = 15 (vs 18 de Karatsuba)."""
import sys, os, itertools
sys.path.insert(0, os.environ['SRCQ']); sys.path.insert(0,'/home/claude/qcc-local/kickmix')
import dqi_tower_inv as T1
mul, B, g = T1.mul, T1.B, T1.g
def val(c):  # coords(6 bits, base B) -> valor
    v=0
    for i in range(6):
        if (c>>i)&1: v^=B[i]
    return v
def crd(v): return T1.coords(v)&63
def m64(a,b): return crd(mul(val(a),val(b)))
w = 1
x = g
# w = elemento de orden 3 en GF(64)* : g^21
def pw(e):
    r=1
    for _ in range(e): r=mul(r,g)
    return r
W = pw(21); assert mul(W,mul(W,W))==1 and W!=1
# F2-base de GF(64): {1,w, g, w g, g^2, w g^2} -> descomposicion (x0,x1,x2) in GF(4)^3, cada xi = a + b w
basis = [1, W, g, mul(W,g), mul(g,g), mul(W,mul(g,g))]
cols = [crd(v) for v in basis]       # columna i = coords de basis[i]
inv = T1._gauss_inv(cols)            # coords c -> coeficientes en 'basis' (bit i = coef de basis[i])
def dec(c):                          # 6 bits coords -> ((a0,b0),(a1,b1),(a2,b2))
    r=0
    for k in range(6):
        if (c>>k)&1: r^=inv[k]
    return [((r>>(2*i))&1, (r>>(2*i+1))&1) for i in range(3)]
# evaluar en eps in GF(4): E(x) = x0 + x1 eps + x2 eps^2  -> como elemento de GF(4)={0,1,W,W^2}; bits (a,b) de a + b W
G4 = {0:(0,0),1:(1,0),W:(0,1),mul(W,W):(1,1)}
def g4mul(u,v):  # u,v en GF(4) como valores de GF(64)
    return mul(u,v)
def lin_form_eval(eps, bit):
    """forma lineal (mascara sobre 6 bits de coords) = bit 'bit' (0:a,1:b) de E_eps(x)."""
    m=0
    for k in range(6):
        d=dec(1<<k)
        # E_eps = sum_i xi eps^i, xi = a_i + b_i W
        e=0
        for i in range(3):
            xi = (1 if d[i][0] else 0) ^ (W if d[i][1] else 0)
            e ^= mul(xi, pw_e(eps,i))
        if G4[e][bit]: m|=1<<k
    return m
def pw_e(eps,i):
    r=1
    for _ in range(i): r=mul(r,eps)
    return r
def lin_form_inf(bit):
    m=0
    for k in range(6):
        d=dec(1<<k); 
        if d[2][bit]: m|=1<<k
    return m
tracks=[]
for eps in (0,1,W,mul(W,W)):
    a=lin_form_eval(eps,0); b=lin_form_eval(eps,1); tracks.append((a,b))
tracks.append((lin_form_inf(0),lin_form_inf(1)))
forms=[]
for a,b in tracks:
    forms += [(a,a),(b,b),(a^b,a^b)]      # p0=u0v0, p1=u1v1, p2=(u0+u1)(v0+v1); fx==fy como mascara (mismo mapeo sobre x e y)
# resolver mascaras de salida: para cada bit de salida k, sum_j m_jk fx_j(x) fy_j(y) == z_k(x,y)
def bil(fx,fy):   # matriz 6x6 como entero de 36 bits: coef de x_a y_b
    r=0
    for a in range(6):
        if (fx>>a)&1:
            for bb in range(6):
                if (fy>>bb)&1: r|=1<<(a*6+bb)
    return r
def zk(k):
    r=0
    for a in range(6):
        for bb in range(6):
            if (m64(1<<a,1<<bb)>>k)&1: r|=1<<(a*6+bb)
    return r
vecs=[bil(fx,fy) for fx,fy in forms]
def solve(target):
    # eliminacion gaussiana sobre F2: target = XOR de subconjunto de vecs
    rows=[(v,1<<j) for j,v in enumerate(vecs)]
    piv={}
    for v,c in rows:
        while v:
            h=v.bit_length()-1
            if h in piv:
                pv,pc=piv[h]; v^=pv; c^=pc
            else:
                piv[h]=(v,c); break
    t=target; c=0
    while t:
        h=t.bit_length()-1
        if h not in piv: return None
        pv,pc=piv[h]; t^=pv; c^=pc
    return c
plan=[]
masks=[0]*len(forms)
for k in range(6):
    c=solve(zk(k))
    assert c is not None, f"bit {k} no representable"
    for j in range(len(forms)):
        if (c>>j)&1: masks[j]|=1<<k
plan=[(fx,fy,m) for (fx,fy),m in zip(forms,masks) if m]
print("terminos", len(plan))
# verificacion exhaustiva
def apply(plan,x,y):
    z=0
    for fx,fy,m in plan:
        if (bin(fx&x).count('1')&1) and (bin(fy&y).count('1')&1): z^=m
    return z
bad=sum(1 for x in range(64) for y in range(64) if apply(plan,x,y)!=m64(x,y))
print("errores", bad)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'plan15.txt'),'w').write(repr(plan))
print(plan)
