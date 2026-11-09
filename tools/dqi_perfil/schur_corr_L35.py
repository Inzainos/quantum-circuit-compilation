#!/usr/bin/env python3
"""Relacion entre el convergente [2L] (diagonal [L/L]) y el sigma verdadero a L=35.
Se busca una correccion lineal: sigma = sigma' + c * (algo) ?
Se prueban: sigma' - sigma, sigma'/sigma, y si sigma' = sigma + a*x^L*omega, etc.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/verifiers/dqi")
import numpy as np
import dqi_bm_model as G
from schur_explora_stieltjes import syndrome, schur_stieltjes, convergents, trim

def pmul(a, b):
    if not a or not b:
        return [0]
    out = [0]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] ^= G.mul(x, y)
    return out

def pdivmod(a, b):
    """Division de polinomios en GF(2^12). Devuelve (q, r)."""
    a = list(a); b = list(b)
    while len(a) > 1 and a[-1] == 0: a.pop()
    while len(b) > 1 and b[-1] == 0: b.pop()
    if len(a) < len(b):
        return [0], a
    q = [0]*(len(a)-len(b)+1)
    inv_lead = G.inv(b[-1])
    for i in range(len(a)-len(b), -1, -1):
        coef = G.mul(a[i+len(b)-1], inv_lead)
        q[i] = coef
        for j in range(len(b)):
            a[i+j] ^= G.mul(coef, b[j])
    r = a[:len(b)-1] if len(b) > 1 else [0]
    while len(r) > 1 and r[-1] == 0: r.pop()
    while len(q) > 1 and q[-1] == 0: q.pop()
    return q, r

rng = np.random.default_rng(123)
n = 70
S35 = None
for k_err in range(1, 36):
    S = syndrome(rng, k_err, n)
    if k_err == 35:
        S35 = S
S = S35
stats = {"mac": 0, "div": 0, "cambios": 0}
sig_bm, L_bm = G.bm(S, stats)
L = L_bm
sig = trim(sig_bm)
# omega de BM
prod = pmul(sig, S)
omega = trim(prod[:n])
print(f"L={L}, deg sigma={len(sig)-1}, deg omega={len(omega)-1}")
print(f"sigma={sig}")
print(f"omega={omega}")
# Schur convergente [2L]
gammas, breakdown = schur_stieltjes(S, 2*n+2, n)
conv = convergents(gammas)
p2, q2 = conv[2*L]
inv0 = G.inv(q2[0])
sig_p = trim([G.mul(c, inv0) for c in q2])
ome_p = trim([G.mul(c, inv0) for c in p2])
print(f"\nconv[2L]: deg sigma'={len(sig_p)-1}, deg omega'={len(ome_p)-1}")
print(f"sigma'={sig_p}")
print(f"omega'={ome_p}")
# Diferencia sigma' - sigma (en GF(2) es XOR = suma)
diff = [0]*max(len(sig_p), len(sig))
for i in range(len(diff)):
    a = sig_p[i] if i < len(sig_p) else 0
    b = sig[i] if i < len(sig) else 0
    diff[i] = a ^ b
diff = trim(diff)
print(f"\nsigma' XOR sigma = {diff}  (deg {len(diff)-1})")
# Es la diferencia un multiplo de omega o de sigma? Divide diff entre omega y entre sigma.
q1, r1 = pdivmod(diff, omega)
print(f"diff / omega: q={trim(q1)} r={trim(r1)}")
q2b, r2b = pdivmod(diff, sig)
print(f"diff / sigma: q={trim(q2b)} r={trim(r2b)}")
# Cociente sigma'/sigma ?
q3, r3 = pdivmod(sig_p, sig)
print(f"sigma'/sigma: q={trim(q3)} r={trim(r3)}")
# omega'/omega ?
q4, r4 = pdivmod(ome_p, omega)
print(f"omega'/omega: q={trim(q4)} r={trim(r4)}")
# Es sigma' = sigma + c*x^L ? (un termino monomial de grado L)
# diff deberia ser [0]*L + [c]
print(f"\ndiff es monomial x^L? {diff == [0]*L + [diff[L]] if len(diff)==L+1 else False}")
print(f"diff[L] = {diff[L] if len(diff)>L else None}")
# Es omega' = omega + c'*x^L ?
diff_o = [0]*max(len(ome_p), len(omega))
for i in range(len(diff_o)):
    a = ome_p[i] if i < len(ome_p) else 0
    b = omega[i] if i < len(omega) else 0
    diff_o[i] = a ^ b
diff_o = trim(diff_o)
print(f"omega' XOR omega = {diff_o} (deg {len(diff_o)-1})")
print(f"omega' XOR omega es monomial x^L? {diff_o == [0]*L + [diff_o[L]] if len(diff_o)==L+1 else False}")
