"""Rastreo ANF hacia ATRAS por ventanas cortas (extraccion por capas).

Para cada rotacion Z_POW de fase, se camina hacia atras ~300 lineas
manteniendo la ANF del qubit objetivo en terminos de los qubits que
habia al inicio de la ventana (los intermedios). Es rapido porque la
ventana es corta y solo se sigue el qubit objetivo.

La composicion a x se hace en un segundo paso: cada intermedio se
rastrea igual (ventana corta) hasta llegar a x.
"""
import json
import sys
from collections import defaultdict

MAX_MONOMIALS = 4000
MAX_DEGREE = 6


def parse(line):
    p = line.split()
    if not p:
        return None, []
    op = p[0]
    args = []
    for tok in p[1:]:
        if tok.startswith("q"):
            args.append(tok)
        elif tok == "if":
            break
        elif tok.startswith("b"):
            break
    return op, args


def anf_prod(fa, fb):
    out = set()
    for ma in fa:
        for mb in fb:
            m = frozenset(ma | mb)
            if len(m) <= MAX_DEGREE:
                out ^= {m}
    return out


def trace_back(lines, target, line_no, back=300):
    f = defaultdict(set)
    f[target] = {frozenset([target])}
    for i in range(line_no - 1, max(0, line_no - back) - 1, -1):
        op, args = parse(lines[i])
        if op is None or not args:
            continue
        if op == "X" and len(args) == 1:
            q = args[0]
            if q in f:
                f[q] ^= {frozenset()}
        elif op == "CX" and len(args) == 2:
            a, b = args
            if b in f:
                f[b] ^= f.get(a, {frozenset([a])})
        elif op in ("CCX", "CCZ") and len(args) == 3:
            a, b, c = args
            if c in f:
                fa = f.get(a, {frozenset([a])})
                fb = f.get(b, {frozenset([b])})
                f[c] ^= anf_prod(fa, fb)
        elif op == "CSWAP" and len(args) == 3:
            a, b, c = args
            if b in f or c in f:
                fa = f.get(a, {frozenset([a])})
                fb = f.get(b, {frozenset([b])})
                fc = f.get(c, {frozenset([c])})
                ab = anf_prod(fa, fb)
                ac = anf_prod(fa, fc)
                f[b] ^= ab ^ ac
                f[c] ^= ac ^ ab
        elif op == "SWAP" and len(args) == 2:
            a, b = args
            if a in f or b in f:
                fa = f.get(a, {frozenset([a])})
                fb = f.get(b, {frozenset([b])})
                f[a], f[b] = fb, fa
        elif op in ("R", "HMR") and len(args) >= 1:
            q = args[0]
            for r in list(f.keys()):
                f[r] = {m for m in f[r] if q not in m}
        if len(f.get(target, set())) > MAX_MONOMIALS:
            return f, i, "explosion"
    return f, max(0, line_no - back), "ok"


if __name__ == "__main__":
    path = sys.argv[1]
    lines = open(path).read().splitlines()
    # rotaciones de fase: Z_POW con angulo < 0.3 (excluye las de 1.5/1.0/0.5)
    rots = []
    for i, l in enumerate(lines):
        p = l.split()
        if p and p[0] == "Z_POW" and len(p) >= 3:
            try:
                a = float(p[2])
            except Exception:
                continue
            if a < 0.3:
                rots.append((i, p[1], a))
    print(f"rotaciones de fase: {len(rots)}")
    out = []
    for i, q, a in rots:
        f, start, status = trace_back(lines, q, i, back=300)
        fn = f.get(q, set())
        by_deg = defaultdict(int)
        for m in fn:
            by_deg[len(m)] += 1
        out.append({
            "line": i, "qubit": q, "angle": a,
            "n_monomials": len(fn),
            "by_degree": dict(sorted(by_deg.items())),
            "constant": frozenset() in fn,
            "monomials": [sorted(m) for m in sorted(fn, key=lambda s: (len(s), sorted(s)))],
            "status": status,
        })
        print(f"linea {i} {q} ang={a:.3g}: {len(fn)} monomios, grados {dict(sorted(by_deg.items()))}, {status}")
    with open("rotaciones_anf.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("guardado en rotaciones_anf.json")
