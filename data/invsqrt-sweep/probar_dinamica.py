"""Prueba la capa 1 dinamica con el simulador kickmix (como el otro agente).
- Construye la capa 1 (mode='auto', Q base 38, C base 1345) sobre x aleatoria.
- Verifica: x restaurada, cada intermedio == su valor ANF clasico,
  scratch limpios, y costo medido (Toffoli medios, Q).
Uso: python3.13 probar_dinamica.py [--tiros N]
"""
import json, sys, argparse
import os as _os, pathlib as _pl
_R = _pl.Path(__file__).resolve().parents[2]  # raiz del repo
sys.path.insert(0, str(_R / 'src'))
if _os.environ.get('KICKMIX_PATH'):  # opcional: ruta del paquete kickmix si no esta instalado
    sys.path.insert(0, _os.environ['KICKMIX_PATH'])
sys.path.insert(0, str(_R / 'verifiers' / 'invsqrt'))
import numpy as np
import kickmix as km
from invsqrt_poly import PolyPhaseBuilder, build_layer1_dynamic

BASE = str(_R / 'data' / 'invsqrt-sweep')
ap = argparse.ArgumentParser()
ap.add_argument('--tiros', type=int, default=1024)
a = ap.parse_args()

inter = json.load(open(f'{BASE}/intermedios_q28_to_x.json'))
inter_anf = {q: v['monomials'] for q, v in inter.items()}
# q24 entra como entrada (su ANF no esta en el JSON); su valor clasico para
# la verificacion se toma como 0 (no se verifica q24, solo su uso en q25).
INTERS = ['q23','q25','q26','q27','q40','q41','q50','q51','q57']

b = km.CircuitBuilder()
x = b.create_quantum_register(22, name="x")
n2q = {f'q{i}': x[i] for i in range(22)}
for q in ['q23','q24','q25','q26','q27','q40','q41','q50','q51','q57']:
    n2q[q] = b.create_quantum_register(1, name=q)[0]
scratch = b.create_quantum_register(4, name="scratch")
em = PolyPhaseBuilder(b, x, None, scratch)
n_and, n_cache, seqs = build_layer1_dynamic(em, inter_anf, n2q, mode="auto", q_base=38, c_base=1345)
print(f"capa 1 dinamica (auto): ANDs={n_and} cache={n_cache} secuenciales={seqs}")
circ = b.finish_circuit()
print(f"qubits del circuito: {circ.num_qubits}")

# simular con x aleatoria
rng = np.random.default_rng(1)
xs = rng.integers(0, 1 << 22, size=a.tiros, dtype=np.int64)
sim = km.Simulator(batch_size=a.tiros, debug_print=False, counting_operations=True, seed=3)
sim.use_same_registers_as(circ)
bits = ((xs[None, :] >> np.arange(22)[:, None]) & 1) == 1
sim.write_across_shots(km.array([km.q(i) for i in range(22)]), bits)
sim.do(circ)
out = sim.read_across_shots(km.array([km.q(i) for i in range(circ.num_qubits)]))
# x restaurada (primeros 22 qubits)
restaurado = bool((out[:22] == bits).all())
print(f"x restaurada: {restaurado}")
# valor clasico de cada intermedio (ANF sobre los bits de x; q24 se toma 0,
# y q23 se calcula por su ANF sin el termino propio + el estado anterior 0:
# q23 = 1 ^ q20 ^ q21 ^ q23_prev, con q23_prev=0 al inicio)
def anf_val(monos, xbits, extra=None):
    # xbits: dict nombre->bool array; extra: dict nombre->bool array (intermedios ya calculados)
    v = np.zeros(a.tiros, dtype=bool)
    for m in monos:
        t = np.ones(a.tiros, dtype=bool)
        for q in m:
            if q in xbits:
                t &= xbits[q]
            elif extra is not None and q in extra:
                t &= extra[q]
            else:
                t &= np.zeros(a.tiros, dtype=bool)
        v ^= t
    return v
xbits = {f'q{i}': bits[i] for i in range(22)}
# orden de los qubits en el circuito: x(0..21), luego intermedios en el orden
# en que se crearon (q23,q24,q25,q26,q27,q40,q41,q50,q51,q57), luego scratch(4),
# luego cache (n_cache). Los indices de los intermedios:
idx = {}
pos = 22
for q in ['q23','q24','q25','q26','q27','q40','q41','q50','q51','q57']:
    idx[q] = pos; pos += 1
# scratch: 4 qubits despues
scratch_idx = list(range(pos, pos+4)); pos += 4
cache_idx = list(range(pos, pos+n_cache))
# valores clasicos (en orden topologico; q23 primero con estado previo 0)
extra = {}
ok = True
for q in ['q23','q25','q26','q27','q40','q41','q50','q51','q57']:
    monos = inter_anf[q]
    if q == 'q23':
        # sin el termino propio (estado previo 0): 1 ^ q20 ^ q21
        monos2 = [m for m in monos if m != ['q23']]
        val = anf_val(monos2, xbits, extra)
    else:
        val = anf_val(monos, xbits, extra)
    extra[q] = val
    got = out[idx[q]]
    match = bool((got == val).all())
    print(f"  {q}: correcto={match}")
    ok = ok and match
print(f"intermedios correctos: {ok}")
# scratch limpios (los 4 de scratch deben estar en 0)
scratch_limpio = not out[scratch_idx].any()
print(f"scratch limpios: {scratch_limpio}")
st = sim.operation_statistics()
print(f"Toffoli medios por tiro: {st.num_toffoli_like / a.tiros:.1f} (estatico {circ.operation_statistics().num_toffoli_like})")
print(f"qubits: {circ.num_qubits}")
print(f"\nVEREDICTO: {'PASA' if (restaurado and ok and scratch_limpio) else 'FALLA'}")
