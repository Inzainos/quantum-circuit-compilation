#!/usr/bin/env python3
"""Medir la composicion fina del pico Q en bm_forward (DQI, commit a741cc7).

Replica forward_round paso a paso (mismos metodos internos) y registra
b.num_allocated_qubits despues de cada sub-paso, para ver de donde salen
los 85 transitorios del pico y que se puede recortar. Escala chica (n=6)
para entender la estructura, y escala completa (n=70) para medir el pico real.

Uso: PYTHONPATH=/home/hatch/workspace/qcc-data/kickmix:/home/hatch/workspace/qcc-dqi/src python3 pico_bm_fino.py [n]
"""
import sys, time
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
import kickmix as km
from dqi_bm_stage_v1 import BMStageV1

def log(b, tag, base):
    print(f"  {tag:38s} live={b.num_allocated_qubits} (+{b.num_allocated_qubits-base})", flush=True)

def ronda_fina(bm, b, r, base):
    """Replica forward_round(r) con logging fino. Devuelve live max en la ronda."""
    print(f"--- ronda {r} (base live={base}) ---", flush=True)
    mx = base
    def snap(tag):
        nonlocal mx
        v = int(b.num_allocated_qubits)
        mx = max(mx, v)
        log(b, tag, base)
    p = b.alloc_qubits(1)[0]; t = b.alloc_qubits(1)[0]
    D = b.alloc_qubits(12); X = b.alloc_qubits(12); alpha = b.alloc_qubits(12)
    snap("alloc p,t,D,X,alpha")
    bm._disc(r, D); snap("tras _disc")
    bm._flags(D, p, t, inverse=False); snap("tras _flags")
    b.cx(bm.sigma[0], X); snap("tras cx sigma0->X")
    with b.mark('bm_alpha'):
        P = b.init_gf2_mul(X, D, field=bm.f)
        Pinv = b.alloc_qubits(12)
        scaf = bm._inv_init(P, Pinv)
        bm._alpha_sel(P, Pinv, p, alpha)
    snap("tras alpha (P,Pinv,alpha)")
    with b.mark('bm_swap'):
        for i in range(bm.bu(r) + 1):
            b.cswap(p, bm.sigma[i], bm.tau[i])
    snap("tras swap")
    with b.mark('bm_update'):
        for i in range(bm.bu(r) + 1):
            bm._mul(alpha, bm.tau[i], bm.sigma[i])
    snap("tras update")
    bm._dupd(p, inverse=False); snap("tras _dupd")
    with b.mark('bm_alpha'):
        bm._alpha_sel(P, Pinv, p, alpha)
        bm._inv_del(scaf, P, Pinv)
        b.free(Pinv)
        b.del_gf2_mul(X, D, target=P, field=bm.f); b.free(P)
    snap("tras alpha undo (P,Pinv liberados)")
    bm._xmux(X, p); snap("tras _xmux")
    bm._dclear(D, p, t); snap("tras _dclear")
    b.free(alpha); b.free(X); b.free(D)
    snap("tras free alpha,X,D (fin ronda)")
    bm.tau = [bm.tau[-1]] + bm.tau[:-1]
    bm.flags.append((p, t))
    snap("tras guardar flags p,t")
    return mx

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    DEG = 12
    b = km.CircuitBuilder(); gf = km.GF2Field(DEG)
    S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(n)]
    bm = BMStageV1(b, gf, S, 36 if n == 70 else 6, n)
    base0 = int(b.num_allocated_qubits)
    print(f"n={n} live inicial (S+sigma+tau+d+H) = {base0}", flush=True)
    print(f"  S={n*DEG} sigma={len(bm.sigma)*DEG} tau={len(bm.tau)*DEG} d={len(bm.d)} H={len(bm.H)}", flush=True)
    # rondas normales hasta la penultima
    for r in range(n - 1):
        bm.forward_round(r)
    print(f"tras {n-1} rondas normales live={b.num_allocated_qubits}", flush=True)
    # ultima ronda con logging fino
    base = int(b.num_allocated_qubits)
    mx = ronda_fina(bm, b, n - 1, base)
    c = b.finish_circuit()
    print(f"RESULTADO n={n}: pico_ronda={mx} Q_circuito={c.num_qubits} T={c.operation_statistics().num_toffoli_like}", flush=True)
    print(f"  live final={b.num_allocated_qubits} (base {base} + 2 flags = {base+2})", flush=True)

if __name__ == "__main__":
    main()
