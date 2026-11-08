"""Inventario de ideas del MoE + estimación clásica de multiplicación por ventanas.

Ideas recibidas de los modelos (Willy, ChatGPT, Deamon-X, Claude,
base44 filósofo, Copilot, Meta, Nemotron, Mistral, etc.) y su estado.
Las dos sin probar que quedan: multiplicación por ventanas (radix-4)
y reajuste minimax/Chebyshev de las tablas.

Estimación clásica radix-4: contar ANDs del MAC actual (shift-and-add
con truncamiento) vs radix-4 (ventanas de 2 bits de t) para nuestros
tamaños (t=12 bits b=6, A=28 bits, salida 28 bits, shift 18).
En radix-4 cada ventana de 2 bits de t aporta 0, A, 2A o 3A; 2A es
gratis (desplazamiento), 3A = 2A + A (hay que precalcularlo o sumarlo).

Uso: python inventario_ideas.py
"""
import numpy as np

# MAC actual (shift-and-add con truncamiento, como mac_sub_trunc):
# V -= (A*t) >> shift. A de nA bits, t de nt bits, V de 28 bits.
# Para cada bit i de t: AND de t[i] con A[j] para j en [j0, nA),
# donde j0 = max(0, shift-i), y se suman a V[i+j0-shift : 28].
# ANDs = suma sobre i de (nA - j0) para los i con j0 < nA.
def ands_shift_add(nA, nt, shift, nV=28):
    total = 0
    for i in range(nt):
        j0 = max(0, shift - i)
        if j0 >= nA:
            continue
        total += (nA - j0)
    return total


# Radix-4 (ventanas de 2 bits): nt bits -> nt/2 ventanas.
# Cada ventana w (2 bits) aporta w * (A << 2k) >> shift, w en {0,1,2,3}.
# w=0: nada. w=1: A. w=2: 2A (gratis, desplazamiento). w=3: 3A.
# 3A se precalcula una vez (un sumador A+2A, ~nA ANDs de acarreo...
# en la práctica un iadd de nA bits cuesta ~nA Toffolis por los
# acarreos; lo contamos como nA ANDs).
# Por ventana, los ANDs son los de seleccionar A/2A/3A según w:
# cada bit de la ventana necesita ANDs con A para el mux (2 bits de
# control -> ~2 ANDs por bit de A, aprox). Estimamos 2*nA por ventana
# para el peor caso, pero con truncamiento solo cuentan los bits que
# sobreviven al shift.
# Estimación conservadora: por ventana, ANDs = 2 * (bits de A que
# sobreviven) + (costo de 3A amortizado).
def ands_radix4(nA, nt, shift, nV=28):
    nvent = (nt + 1) // 2
    # Precalcular 3A una vez: ~nA ANDs (acarreo del sumador).
    total = nA
    for k in range(nvent):
        i = 2 * k  # bit bajo de la ventana
        j0 = max(0, shift - i)
        if j0 >= nA:
            continue
        bits = nA - j0
        # Mux de 2 bits de control: ~2 ANDs por bit de A.
        total += 2 * bits
    return total


def main():
    print("Inventario de ideas del MoE (estado):")
    ideas = [
        ("WideLookup (84b, COMBO AGRESIVO)", "HECHO", "~519k con reuso b=6, pasa"),
        ("Barrido de b hacia abajo (filósofo)", "HECHO", "b=6 mejor (~519k); b=5 ~508k margen delgado"),
        ("Fused MAC (Elán)", "HECHO", "full13/14/15, ~716k"),
        ("Truncamiento (full11)", "HECHO", "914k -> 752k"),
        ("Monomios del valor (fase)", "HECHO, FALLA", "acarreo 3.126e-06, 52x tol"),
        ("WideLookup + monomios", "HECHO, FALLA", "mismo acarreo"),
        ("ANDs compartidos t[j]*t[k]", "HECHO", "ahorro 450 T, fase sigue fallando"),
        ("Bandera de acarreo", "HECHO, NO SIRVE", "S_w>=4 en 34%, residual 4.8e-04"),
        ("Dos tuberías ligera/pesada", "HECHO, PASA", "corte -29, ~1.2-1.4M, caro"),
        ("Split lookup + reuso manual", "HECHO", "~519k, mejor WideLookup"),
        ("QROM por bloques + cuadrática", "HECHO", "es logshift2/full15"),
        ("Constant Folding", "NO APLICA", "t/S/C2 son cuánticos, no constantes"),
        ("Phase Gradient / QFT", "NO APLICA", "kickmix no tiene H coherente"),
        ("CSD", "NO APLICA", "S/C2 son registros cuánticos"),
        ("Karatsuba / Toom-Cook", "MUERTO", "crossover 32-64b; nosotros 10-28b"),
        ("Margolus", "EN MAIN CHAT", "se prueba en la torre DQI"),
        ("Minimax/Chebyshev tablas", "SIN PROBAR", "experimento, no certeza"),
        ("Multiplicación por ventanas radix-4", "SIN PROBAR", "estimar aquí"),
    ]
    for nombre, estado, nota in ideas:
        print(f"  {nombre:38s} {estado:14s} {nota}")
    print("\nEstimación clásica de ANDs por MAC (b=6: t=12b, A=28b, shift=18):")
    for (nA, nt, shift, etiqueta) in [
        (28, 12, 18, "MAC1 C2*t (b=6)"),
        (28, 12, 18, "MAC2 t*h  (b=6)"),
        (28, 10, 18, "MAC b=8 (t=10b)"),
        (28, 11, 18, "MAC b=7 (t=11b)"),
    ]:
        sa = ands_shift_add(nA, nt, shift)
        r4 = ands_radix4(nA, nt, shift)
        print(f"  {etiqueta}: shift-and-add={sa} ANDs, radix-4~{r4} ANDs "
              f"(ahorro {sa-r4:+d}, {100.0*(sa-r4)/sa:+.1f}%)")
    print("\nNota: radix-4 ahorra ANDs solo si el mux por ventana es")
    print("barato; con truncamiento el ahorro real es menor porque")
    print("muchos bits ya se truncan en shift-and-add.")


if __name__ == "__main__":
    main()
