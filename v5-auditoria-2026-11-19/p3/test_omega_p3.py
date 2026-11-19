#!/usr/bin/env python3
"""Prueba aislada P3 (Fase 2): Omega emite sus 630 mul/pase como 90 bloques de 7.

Verifica, sin construir el DQI completo:
  1. Estructura: _omega_mul_tasks da 630 tareas/pase (LO=35); _omega_mul_blocks
     da 90 bloques de 7; el orden de tareas == el orden del loop original
     (re-implementado aqui desde los limites del loop, no desde el modulo).
  2. Conteo DINAMICO de muls: monkeypatch sobre D.ixor_kmul durante un build
     Omega aislado (registros dummy) -> 630 llamadas/pase, 1,260 ida+vuelta.
  3. T aislado por pase: 29,085 = 630*42 (mul) + 35*75 (ValueInv); ida+vuelta
     58,170. Q aislado (num_qubits del circuito) se reporta (debe ser << 1,864;
     el pico del DQI completo no lo marca Omega: live_frontera 1,794).
Uso: /home/hatch/workspace/py313/python/bin/python3.13 -u test_omega_p3.py
"""
import sys
# ORDEN: el scratch (p3/src) se inserta AL FINAL para quedar primero en
# sys.path y hacer sombra a los originales (igual que construir_dqi_p3.py).
sys.path.insert(0, "/home/hatch/workspace/qcc-dqi/src")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/kickmix")
sys.path.insert(0, "/home/hatch/workspace/qcc-data/test-dev/espiral-prototipo/p3/src")
import kickmix as km
import dqi_decoder_v1 as D

LO = 35
DEG = 12
print(f"modulo: dqi_decoder_v1={D.__file__}", flush=True)

# --- 1. Estructura: orden de tareas == loop original (referencia independiente) ---
def ref_tasks(adjoint):
    tasks = []
    orden = range(LO) if adjoint else range(LO - 1, -1, -1)
    for i in orden:
        if not adjoint:
            tasks.append(('esc', i, None))
            for j in range(1, i + 1):
                tasks.append(('acc', i, j))
        else:
            for j in range(i, 0, -1):
                tasks.append(('acc', i, j))
            tasks.append(('esc', i, None))
    return tasks

ok_struct = True
for adjoint in (False, True):
    tag = "rev" if adjoint else "fwd"
    tasks = D._omega_mul_tasks(LO, adjoint)
    blocks = D._omega_mul_blocks(LO, adjoint)
    ref = ref_tasks(adjoint)
    n_esc = sum(1 for t in tasks if t[0] == 'esc')
    n_acc = sum(1 for t in tasks if t[0] == 'acc')
    print(f"[{tag}] tareas={len(tasks)} (esc={n_esc} acc={n_acc}) "
          f"esperado 630 = 35 + 595; bloques={len(blocks)} "
          f"tamanos={sorted(set(len(b) for b in blocks))} (esperado 90 x 7)", flush=True)
    print(f"[{tag}] orden == loop original: {tasks == ref}", flush=True)
    print(f"[{tag}] aplanar bloques == tareas: "
          f"{[t for b in blocks for t in b] == tasks}", flush=True)
    ok_struct &= (len(tasks) == 630 and n_esc == 35 and n_acc == 595
                  and len(blocks) == 90 and all(len(b) == 7 for b in blocks)
                  and tasks == ref)

# Per-i: vuelta deshace ida (mismo multiconjunto por i; j asc en ida, desc en vuelta)
fwd, rev = D._omega_mul_tasks(LO, False), D._omega_mul_tasks(LO, True)
per_i_ok = True
for i in range(LO):
    f_i = sorted(t for t in fwd if t[1] == i)
    r_i = sorted(t for t in rev if t[1] == i)
    per_i_ok &= (f_i == r_i)
print(f"[ambos] mismo multiconjunto de tareas por i (ida vs vuelta): {per_i_ok}", flush=True)
ok_struct &= per_i_ok
print("ESTRUCTURA_OK" if ok_struct else "ESTRUCTURA_FAIL", flush=True)

# --- 2+3. Conteo dinamico + T/Q aislado (registros dummy, como contar_omega.py) ---
real_kmul = D.ixor_kmul
counts = {"fwd": 0, "rev": 0}
current = {"dir": None}


def counting_kmul(b, x, y, t):
    counts[current["dir"]] += 1
    return real_kmul(b, x, y, t)


D.ixor_kmul = counting_kmul
b = km.CircuitBuilder()
gf = km.GF2Field(DEG)
S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(70)]
sig = [b.create_quantum_register(DEG, name=f"sig{i}") for i in range(36)]
current["dir"] = "fwd"
D.build_omega_tmp(b, gf, sig, S, LO, adjoint=False)
c_fwd = b.finish_circuit()
t_fwd = int(c_fwd.operation_statistics().num_toffoli_like)
q_fwd = int(c_fwd.num_qubits)
print(f"[aislado fwd] muls={counts['fwd']} (esperado 630); "
      f"T={t_fwd} (esperado 29085 = 630*42 + 35*75); Q={q_fwd}", flush=True)

b = km.CircuitBuilder()
S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(70)]
sig = [b.create_quantum_register(DEG, name=f"sig{i}") for i in range(36)]
current["dir"] = "rev"
D.build_omega_tmp(b, gf, sig, S, LO, adjoint=True)
c_rev = b.finish_circuit()
t_rev = int(c_rev.operation_statistics().num_toffoli_like)
q_rev = int(c_rev.num_qubits)
print(f"[aislado rev] muls={counts['rev']} (esperado 630); "
      f"T={t_rev} (esperado 29085); Q={q_rev}", flush=True)

# ida+vuelta en un solo circuito (contador reseteado: el tercer build volveria
# a sumar 630+630 sobre los conteos anteriores)
counts_fwd_1, counts_rev_1 = counts["fwd"], counts["rev"]
counts["fwd"] = counts["rev"] = 0
b = km.CircuitBuilder()
S = [b.create_quantum_register(DEG, name=f"S{i}") for i in range(70)]
sig = [b.create_quantum_register(DEG, name=f"sig{i}") for i in range(36)]
current["dir"] = "fwd"
D.build_omega_tmp(b, gf, sig, S, LO, adjoint=False)
current["dir"] = "rev"
D.build_omega_tmp(b, gf, sig, S, LO, adjoint=True)
c_both = b.finish_circuit()
t_both = int(c_both.operation_statistics().num_toffoli_like)
q_both = int(c_both.num_qubits)
print(f"[aislado ida+vuelta] muls fwd={counts['fwd']} rev={counts['rev']} "
      f"(esperado 630+630); T={t_both} (esperado 58170); Q={q_both} "
      f"(<< 1864: Omega no marca el pico del DQI)", flush=True)
D.ixor_kmul = real_kmul

ok_med = (counts_fwd_1 == 630 and counts_rev_1 == 630
          and counts["fwd"] == 630 and counts["rev"] == 630
          and t_fwd == 29085 and t_rev == 29085 and t_both == 58170)
print(f"init_and mul/pase: 630 x 42 = {630 * 42} T (ida); ida+vuelta {2 * 630 * 42} T",
      flush=True)
print("MEDICION_OK" if ok_med else "MEDICION_FAIL", flush=True)
print("OMEGA_P3_OK" if (ok_struct and ok_med) else "OMEGA_P3_FAIL", flush=True)
