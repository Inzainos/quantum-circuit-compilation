"""Helpers sin ancillas para productos de torre: formas lineales EN EL SITIO (CX) y Toffoli con fan-out en el objetivo.
Mismo conteo de Toffoli que init_and/del_and (1 por termino), 0 qubits temporales."""
import logging
log = logging.getLogger("qf")


def form_ip(b, form, reg, n):
    """Devuelve (qubit, info). Si la forma es un solo bit, es ese qubit. Si no, la acumula EN EL SITIO en el pivote (CX)."""
    bits = [i for i in range(n) if (form >> i) & 1]
    if len(bits) == 1:
        return reg[bits[0]], None
    p = bits[0]
    for i in bits[1:]:
        b.cx(reg[i], reg[p])
    return reg[p], (reg, p, bits[1:])


def unform_ip(b, info):
    if info is None:
        return
    reg, p, rest = info
    for i in rest:
        b.cx(reg[i], reg[p])


def fan_ccx(b, qx, qy, target, tm, n):
    """target[j] ^= qx & qy para cada bit j de la mascara tm, con UN Toffoli y sin qubit auxiliar."""
    S = [j for j in range(n) if (tm >> j) & 1]
    if not S:
        return
    p = S[0]
    for j in S[1:]:
        b.cx(target[p], target[j])
    b.ccx(qx, qy, target[p])
    for j in S[1:]:
        b.cx(target[p], target[j])


def mul_terms_init(b, terms, nx, ny, x, y, target, nt):
    for fx, fy, tm in terms:
        qx, ix = form_ip(b, fx, x, nx)
        qy, iy = form_ip(b, fy, y, ny)
        fan_ccx(b, qx, qy, target, tm, nt)
        unform_ip(b, iy)
        unform_ip(b, ix)


def mul_terms_phase(b, terms, nx, ny, x, y, m, nt):
    """Para cada termino aplica CZ(fx(x), fy(y)) condicionado a cada bit medido m[j] de la mascara."""
    for fx, fy, tm in terms:
        qx, ix = form_ip(b, fx, x, nx)
        qy, iy = form_ip(b, fy, y, ny)
        for j in range(nt):
            if (tm >> j) & 1:
                b.push_condition(m[j]); b.cz(qx, qy); b.pop_condition()
        unform_ip(b, iy)
        unform_ip(b, ix)
