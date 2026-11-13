#!/usr/bin/env python3
"""Medir inverso builtin (init_gf2_inverse_with_scaffold) e Itoh-Tsujii binario: andamios, T, correctitud.

Itoh-Tsujii binario: x^-1 = x^4094, 4094 = 0b111111111110 (11 unos).
  cur = x; acc = 1; por cada bit i=1..11: cur = cur^2 (Frobenius, lineal, 0 T, in situ);
  si bit i set: acc = acc * cur (mul 63 T, target 12).
  11 cuadrados + 10 muls = 630 T. (La cadena de adicion optima baja a ~5 muls = 315 T;
  aun asi >> 75 T de la torre.)
Uso: python3 -u scripts/medir_itoh_builtin.py  (desde la raiz del repo)
"""
import sys, time
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "kickmix"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import numpy as np
import kickmix as km
import dqi_bm_model as G

DEG = 12
gf = km.GF2Field(DEG)
Bn = 4096
vals = np.arange(Bn)
exp = np.array([0 if v == 0 else G.inv(int(v)) for v in vals])


def bits(v):
    return ((v[None, :] >> np.arange(12)[:, None]) & 1) == 1


def verificar(c, nombre, t, q):
    sim = km.Simulator(batch_size=Bn, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(c)
    sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(vals))
    sim.do(c)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
    # layout: a=q0..11, w=q12..23, keep=q24..35, resto aux
    kept = np.zeros(Bn, dtype=np.int64)
    for k in range(12):
        kept |= out[24 + k].astype(np.int64) << k
    sucio = out[12:24].any(axis=0) | out[36:].any(axis=0)
    fase = int(sim.read_phase_flipped_across_shots().sum())
    print(f"[{nombre}] Q={q} (pico sobre base={q - 36}) T={t} | "
          f"correcto={int((kept == exp).sum())}/{Bn} basura={int(sucio.sum())} fase_volteada={fase}", flush=True)


# --- (1) inverso builtin ---
t0 = time.time()
b = km.CircuitBuilder()
a = b.create_quantum_register(12, name='a')
w = b.create_quantum_register(12, name='w')
keep = b.create_quantum_register(12, name='keep')
_, scaf = b.init_gf2_inverse_with_scaffold(a, target=w, field=gf)
live_fwd = int(b.num_allocated_qubits)
for k in range(12):
    b.cx(w[k], keep[k])
b.del_gf2_inverse_with_scaffold(a, target=w, scaffold=scaf, field=gf)
b.free(scaf)
c = b.finish_circuit()
t = int(c.operation_statistics().num_toffoli_like)
q = int(c.num_qubits)
print(f"[builtin] live_tras_fwd={live_fwd} (andamios={live_fwd - 36}) Q={q} T={t} ({time.time()-t0:.1f}s)", flush=True)
verificar(c, 'builtin', t, q)


# --- (2) Itoh-Tsujii binario (exponenciacion x^4094) ---
def _matriz_frob():
    """F: matriz 12x12 (bits) del cuadrado en GF(2^12): F[j] = (X^j)^2 como entero de 12 bits.
    Devuelve (F, Finv) como listas de enteros por fila (fila j = imagen de la base j)."""
    F = [G.mul(1 << j, 1 << j) for j in range(12)]
    # invertir F sobre GF(2): filas F[j], queremos Finv tal que Finv @ F = I (aplicar F luego Finv = identidad).
    # Resolvemos por eliminacion gaussiana sobre la matriz aumentada [F | I] por filas.
    aug = [(F[j] | (1 << (12 + j))) for j in range(12)]
    for col in range(12):
        piv = next(r for r in range(col, 12) if (aug[r] >> col) & 1)
        aug[col], aug[piv] = aug[piv], aug[col]
        for r in range(12):
            if r != col and ((aug[r] >> col) & 1):
                aug[r] ^= aug[col]
    Finv = [(aug[j] >> 12) & 0xFFF for j in range(12)]
    # verificar Finv @ F = I
    for j in range(12):
        acc = 0
        for k in range(12):
            if (Finv[j] >> k) & 1:
                acc ^= F[k]
        assert acc == (1 << j), f"Finv incorrecta en fila {j}"
    return F, Finv


FROB, FROB_INV = _matriz_frob()


def frob_sq(b, reg):
    """reg <- reg^2 en GF(2^12) (Frobenius, lineal, 0 T, in situ)."""
    tmp = b.alloc_qubits(12)
    for j in range(12):
        for k in range(12):
            if (FROB[j] >> k) & 1:
                b.cx(reg[j], tmp[k])
    for k in range(12):
        b.swap(reg[k], tmp[k])
    for j in range(12):
        for k in range(12):
            if (FROB_INV[j] >> k) & 1:
                b.cx(reg[j], tmp[k])
    b.free(tmp)


t0 = time.time()
b = km.CircuitBuilder()
a = b.create_quantum_register(12, name='a')
w = b.create_quantum_register(12, name='w')
keep = b.create_quantum_register(12, name='keep')
# cur = copia de a (12); acc_0 = 1 (12). Cada iteracion deja el acc viejo vivo (intermedio):
# un Itoh-Tsujii reversible con mul de target fresco no puede sobrescribir el acumulador
# sin guardar la historia (Bennett). Se guardan los 11 acc intermedios.
cur = b.alloc_qubits(12)
acc = b.alloc_qubits(12)
for k in range(12):
    b.cx(a[k], cur[k])
b.x(acc[0])  # acc = 1
accs = [acc]
for i in range(1, 12):
    frob_sq(b, cur)  # cur = a^{2^i}
    # P = acc * cur ; mover P a acc2 con SWAP (acc2 en |0⟩): P queda en 0 y se libera sin del.
    # (CX + del NO vale: el CX entrelaza P con acc2 y el del/HMR mide P entrelazado.)
    P = b.init_gf2_mul(acc, cur, field=gf)
    acc2 = b.alloc_qubits(12)
    for k in range(12):
        b.swap(P[k], acc2[k])
    b.free(P)
    acc = acc2
    accs.append(acc)
live_fwd = int(b.num_allocated_qubits)
for k in range(12):
    b.cx(acc[k], w[k])
c = b.finish_circuit()
t = int(c.operation_statistics().num_toffoli_like)
q = int(c.num_qubits)
print(f"[itoh-binario] live_tras_fwd={live_fwd} (andamios={live_fwd - 36}) Q={q} T(ida, sin undo)={t} "
      f"(ida+vuelta ~{2*t}) ({time.time()-t0:.1f}s)", flush=True)
# verificacion: w (q12..23) debe ser a^-1 (acc/cur/accs viejos quedan vivos; solo se chequea w y fase)
sim = km.Simulator(batch_size=Bn, debug_print=False, counting_operations=True, seed=1)
sim.use_same_registers_as(c)
sim.write_across_shots(km.array([km.q(i) for i in range(12)]), bits(vals))
sim.do(c)
out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
kept = np.zeros(Bn, dtype=np.int64)
for k in range(12):
    kept |= out[12 + k].astype(np.int64) << k
fase = int(sim.read_phase_flipped_across_shots().sum())
print(f"[itoh-binario] w correcto={int((kept == exp).sum())}/{Bn} fase_volteada={fase} "
      f"(w=q12..23; intermedios vivos, no se chequea basura)", flush=True)
