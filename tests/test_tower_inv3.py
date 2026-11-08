"""Torre de inversion GF(2^12) lean (dqi_tower_inv3): correcta en los 4096 valores, 75 Toffoli, sin basura ni fase."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
km = pytest.importorskip("kickmix")
import dqi_bm_model as G  # noqa: E402
import dqi_tower_inv3 as T3  # noqa: E402


def _bits(v):
    return ((v[None, :] >> np.arange(12)[:, None]) & 1) == 1


def test_value_inv3_en_el_sitio():
    Bn = 4096
    vals = np.arange(Bn)
    b = km.CircuitBuilder()
    a = b.create_quantum_register(12, name="a"); w = b.create_quantum_register(12, name="w")
    keep = b.create_quantum_register(12, name="keep")
    vi = T3.ValueInv3(b, a, w).forward()
    for k in range(12):
        b.cx(w[k], keep[k])
    vi.undo()
    c = b.finish_circuit()
    sim = km.Simulator(batch_size=Bn, debug_print=False, counting_operations=True, seed=1)
    sim.use_same_registers_as(c)
    sim.write_across_shots(km.array([km.q(i) for i in range(12)]), _bits(vals)); sim.do(c)
    out = sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)]))
    kept = np.zeros(Bn, dtype=np.int64)
    for k in range(12):
        kept |= out[24 + k].astype(np.int64) << k
    exp = np.array([0 if v == 0 else G.inv(int(v)) for v in vals])
    assert (kept == exp).all()
    assert all((out[k].astype(np.int64) == ((vals >> k) & 1)).all() for k in range(12))   # a restaurado
    assert not out[12:24].any() and not out[36:].any()                                    # w y ancillas limpios
    assert int(sim.read_phase_flipped_across_shots().sum()) == 0
    assert c.operation_statistics().num_toffoli_like == 75
    assert c.num_qubits - 36 <= 21                                                         # <= 21 qubits auxiliares
