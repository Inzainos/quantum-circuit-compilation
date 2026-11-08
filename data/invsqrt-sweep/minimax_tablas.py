"""Minimax/Chebyshev de las tablas B/S/C2 (idea del MoE, Mistral).

Tablas actuales: Taylor en el borde izquierdo del segmento
  B = g(e), S = -g'(e), C2 = g''(e)/2, con g(y)=y^(-1/2), e=1+seg/nseg.
  Cuantizadas a 28 bits.
Minimax: ajustar el cuadrático B - S*u + C2*u^2 (u=t/2^18, en [0,1/nseg))
  para minimizar el error máximo sobre el segmento, con un ajuste de
  Chebyshev grado 2 (casi-minimax), luego cuantizar a 28 bits.

Se mide el error máximo en V (unidades enteras de 28 bits) sobre todos
los t de todos los segmentos, para Taylor vs minimax, para b=4,5,6.
La fase (vueltas) es proporcional al error en V, así que el cociente
minimax/Taylor es el que importa: se aplica a los errores de fase
medidos (b=6 Taylor: 4.337e-09; b=5 Taylor: 2.221e-08).

Uso: python minimax_tablas.py
"""
import numpy as np
from numpy.polynomial import chebyshev as C

N_VAL = 28
N_MANT = 18


def a_u(v):
    return min(int(round(v * (1 << N_VAL))), (1 << N_VAL) - 1)


def horner_int(B, S, C2, t):
    """V entero como lo hace el circuito (Horner, sin truncar: el
    producto completo y luego el shift es igual al truncado)."""
    h = S - ((C2 * t) >> N_MANT)
    V = B - ((t * h) >> N_MANT)
    return V


def taylor_tables(nseg):
    edges = 1.0 + np.arange(nseg) / nseg
    base_f = edges ** (-0.5)
    slope_f = 0.5 * edges ** (-1.5)
    curv_f = 0.375 * edges ** (-2.5)
    inv = 1.0 / np.sqrt(2.0)
    base, slope, curv = [], [], []
    for seg in range(nseg):
        base.append(a_u(base_f[seg])); slope.append(a_u(slope_f[seg])); curv.append(a_u(curv_f[seg]))
        base.append(a_u(base_f[seg] * inv)); slope.append(a_u(slope_f[seg] * inv)); curv.append(a_u(curv_f[seg] * inv))
    return base, slope, curv


def minimax_tables(nseg):
    """Chebyshev grado 2 por segmento, en u en [0, 1/nseg).
    q(u) = c0 + c1*u + c2*u^2  (potencias). Se pasa a B,S,C2:
    B=c0, S=-c1, C2=c2. Se cuantiza a 28 bits. Hay par e impar
    (impar = par * 1/sqrt(2), igual que Taylor)."""
    base, slope, curv = [], [], []
    inv = 1.0 / np.sqrt(2.0)
    for seg in range(nseg):
        e = 1.0 + seg / nseg
        w = 1.0 / nseg
        # Nodos de Chebyshev en [0, w], muestreo denso para el ajuste.
        xs = np.linspace(0.0, w, 400)
        ys = (e + xs) ** (-0.5)
        # Ajuste Chebyshev grado 2 en el intervalo [0, w].
        ch = C.Chebyshev.fit(xs, ys, 2, domain=[0.0, w])
        # A potencias de u: c0 + c1*u + c2*u^2.
        p = ch.convert(kind=np.polynomial.Polynomial)
        c0, c1, c2 = float(p.coef[0]), float(p.coef[1]), float(p.coef[2])
        # B=c0, S=-c1 (el Horner resta S*u), C2=c2.
        for mult in (1.0, inv):
            base.append(a_u(c0 * mult))
            slope.append(a_u(-c1 * mult))
            curv.append(a_u(c2 * mult))
    return base, slope, curv


def max_err(nseg, base, slope, curv):
    """Error máximo en V (unidades enteras) sobre todos los segmentos
    y todos los t (se muestrean 200 t por segmento para ir rápido,
    más los extremos)."""
    nt = 1 << (N_MANT - int(np.log2(nseg)))
    errs = []
    ts = np.unique(np.concatenate([np.linspace(0, nt - 1, 200).astype(int), [0, nt - 1]]))
    for seg in range(nseg):
        e = 1.0 + seg / nseg
        for parity in (0, 1):
            idx = 2 * seg + parity
            B, S, C2 = base[idx], slope[idx], curv[idx]
            mult = 1.0 if parity == 0 else 1.0 / np.sqrt(2.0)
            for t in ts:
                u = t / (1 << N_MANT)
                y = e + u
                exact = (y ** (-0.5)) * mult * (1 << N_VAL)
                V = horner_int(B, S, C2, int(t))
                errs.append(abs(V - exact))
    return max(errs)


def main():
    print("Minimax/Chebyshev de tablas B/S/C2")
    print("Error máximo en V (unidades enteras de 28 bits).")
    print("Fase medida (Taylor): b=6 -> 4.337e-09, b=5 -> 2.221e-08 vueltas.")
    print("tol 5.96e-08 vueltas. El cociente minimax/Taylor se aplica a la fase.")
    for b in (4, 5, 6):
        nseg = 1 << b
        tb, ts_, tc = taylor_tables(nseg)
        mb, ms, mc = minimax_tables(nseg)
        e_t = max_err(nseg, tb, ts_, tc)
        e_m = max_err(nseg, mb, ms, mc)
        ratio = e_m / e_t if e_t else float("nan")
        print(f"\nb={b} (nseg={nseg}): Taylor max_err_V={e_t:.1f}  "
              f"Minimax max_err_V={e_m:.1f}  cociente={ratio:.3f}")
        # Fase estimada con minimax (aplicando el cociente a la medida Taylor).
        if b == 6:
            print(f"  fase estimada minimax b=6: {4.337e-09 * ratio:.3e} vueltas "
                  f"(margen {5.96e-08 / (4.337e-09 * ratio):.1f}x)")
        if b == 5:
            print(f"  fase estimada minimax b=5: {2.221e-08 * ratio:.3e} vueltas "
                  f"(margen {5.96e-08 / (2.221e-08 * ratio):.1f}x)")
        if b == 4:
            # Taylor b=4: el error escala ~4x el de b=5 (segmento doble).
            # Estimación gruesa de la fase Taylor b=4: 2.221e-08 * 4.
            est_t = 2.221e-08 * 4.0
            print(f"  fase Taylor b=4 (estimada ~4x b=5): {est_t:.3e} "
                  f"(FALLA, tol 5.96e-08)")
            print(f"  fase estimada minimax b=4: {est_t * ratio:.3e} vueltas "
                  f"(margen {5.96e-08 / (est_t * ratio):.1f}x)")


if __name__ == "__main__":
    main()
