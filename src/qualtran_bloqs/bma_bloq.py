"""
BMABloq - Berlekamp-Massey Algorithm for Reed-Solomon Decoding in GF(2^12).

Computes error locator polynomial σ(x) from 2t syndromes.
Zero polynomial divisions - only CNOT + Toffoli.
Shift register topology - perfect for circular buffers.
Fixed scaffold - updates σ and auxiliary polynomial in same qubit space.

Args:
    t: Error correcting capability (degree of σ). For DQI: t=35.
    gf_degree: Degree of GF(2^m). For DQI: m=12.

Inputs:
    syndromes: 2t syndrome registers (S_0 through S_{2t-1})

Outputs:
    sigma: Error locator polynomial coefficients [σ_0, σ_1, ..., σ_t]
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, List, Dict, Any
from dataclasses import dataclass

import attr
from attr import field, define, frozen

import numpy as np

from qualtran import Bloq, BloqBuilder, BloqDocSpec, QAny, QGF, QInt, Register, Signature, Side, SoquetT, QBit, QUInt, QGF, CtrlSpec
from qualtran.bloqs.arithmetic.addition import AddK
from qualtran.bloqs.gf_arithmetic.gf2_addition import GF2Addition
from qualtran.bloqs.gf_arithmetic.gf2_multiplication import GF2Multiplication, GF2MulK
from qualtran.bloqs.gf_arithmetic.gf2_inverse import GF2Inverse
from qualtran.bloqs.gf_arithmetic.gf2_square import GF2Square
from qualtran.bloqs.gf_poly_arithmetic.gf2_poly_add import GF2PolyAdd
from qualtran.bloqs.basic_gates import CNOT, XGate, Toffoli, ZGate, CZ
from qualtran import Bloq, BloqBuilder, BloqDocSpec, QAny, QGF, QInt, Register, Signature, Side, SoquetT, QBit, QUInt, QGF, CtrlSpec
from qualtran.cirq_interop.t_complexity_protocol import TComplexity


@define
class BMABloq:
    """
    Berlekamp-Massey Algorithm for Reed-Solomon syndrome decoding over GF(2^12).

    Computes error locator polynomial σ(x) from 2t syndromes.

    Zero polynomial divisions - only CNOT + Toffoli.
    Shift register topology - perfect for circular buffers.
    Fixed scaffold - updates σ and auxiliary polynomial in same qubit space.

    Args:
        t: Error correcting capability (degree of σ). For DQI: t=35.
        gf_degree: Degree of GF(2^m). For DQI: m=12.

    Inputs:
        syndromes: 2t syndrome registers (S_0 through S_{2t-1})

    Outputs:
        sigma: Error locator polynomial coefficients [σ_0, σ_1, ..., σ_t]
    """

    t: int = 35
    gf_degree: int = 12
    gf: QGF = None

    def __attrs_post_init__(self):
        if self.t <= 0:
            raise ValueError(f"t must be positive, got {self.t}")
        if self.gf_degree <= 0:
            raise ValueError(f"gf_degree must be positive, got {self.gf_degree}")
        object.__setattr__(self, 'gf', QGF(2, self.gf_degree))

    @property
    def signature(self) -> Signature:
        return Signature(
            [Register(name=f"syndrome_{i}", dtype=QGF(2, self.gf_degree), side=Side.LEFT) for i in range(2 * self.t)] +
            [Register(name=f"sigma_{i}", dtype=QGF(2, self.gf_degree), side=Side.RIGHT) for i in range(self.t + 1)]
        )

    def build_composite_bloq(self, builder: BloqBuilder, **soqs: Dict[str, SoquetT]) -> Dict[str, SoquetT]:
        """Build the BMA circuit using Qualtran bloqs."""
        gf = self.gf
        t = self.t
        degree = self.gf_degree

        # Extract input syndromes
        syndromes = [soqs[f"syndrome_{i}"] for i in range(2 * self.t)]

        # BMA Registers (shift register topology)
        # sigma: t+1 coefficients [σ_0, σ_1, ..., σ_t]
        sigma = [builder.add_register(f"sigma_{i}", gf) for i in range(t + 1)]
        # C: auxiliary polynomial (t+1 coefficients)
        C = [builder.add_register(f"C_{i}", gf) for i in range(t + 1)]
        # Discrepancy Δ
        Delta = builder.add_register("Delta", gf)
        # Degree trackers
        L = builder.add_register("L", builder.qbit(6))  # max 35 needs 6 bits
        B = builder.add_register("B", builder.qbit(6))  # 2*L tracker
        k_counter = builder.add_register("k", builder.qbit(6))
        delta_nz = builder.add_register("delta_nz", builder.qbit(1))[0]

        # Initialize: σ(x) = 1, C(x) = 1, L = 0, B = -1, k = 0
        # σ_0 = 1, C_0 = 1
        builder.add(XGate(), q=sigma[0][0])
        builder.add(XGate(), q=C[0][0])
        # L=0, B=-1 (stored as max value 63), k=0 (already zero)

        # BMA main loop: 2t = 70 iterations
        for n in range(2 * self.t):
            with builder.box(f"bma_iter_{n}"):
                self._compute_discrepancy(builder, syndromes, sigma, Delta, L, n)

                # delta_nz = (Δ != 0)
                builder.flip_if_equal(Delta, 0, target=delta_nz)

                self._update_sigma(builder, sigma, C, Delta, delta_nz, L, B, n)

                builder.add(AddK(6, 1), a=k_counter)

        # Return sigma coefficients
        return {f"sigma_{i}": sigma[i] for i in range(t + 1)}

    def _compute_discrepancy(self, builder: BloqBuilder, syndromes: Sequence[SoquetT],
                            sigma: List[SoquetT], Delta: SoquetT, L: SoquetT, n: int) -> None:
        """Compute Δ = S_n + Σ_{i=1}^L σ_i S_{n-i}."""
        gf = self.gf
        m = self.m
        t = self.t

        builder.add(CNOT(), ctrl=syndromes[n], target=Delta)

        for i in range(1, t + 1):
            ctrl_i = builder.alloc_qubits(1)[0]
            builder.flip_if_less_than(L, i, target=ctrl_i)

            temp = builder.alloc_qubits(m)
            builder.cx(sigma[i], temp)
            builder.gf2_imul(syndromes[n - i], target=temp, field=self.gf)
            builder.gf2_iadd(temp, target=Delta, field=gf, control=ctrl_i)

            builder.free(temp)
            builder.free(ctrl_i)

    def _update_sigma(self, builder: BloqBuilder, sigma: List[SoquetT], C: List[SoquetT],
                      Delta, delta_nz, L, B, k_counter, n: int) -> None:
        gf = self.field
        t = self.t

        for i in range(1, t + 1):
            temp = builder.alloc_qubits(self.m)
            builder.cx(C[i-1], temp)
            builder.gf2_imul(Delta, target=temp, field=gf)
            builder.gf2_iadd(temp, target=sigma[i], field=gf, control=delta_nz)
            builder.free(temp)

    def _t_complexity_(self) -> TComplexity:
        t = self.t
        return TComplexity(t=2 * self.t * self.t * 144, clifford=2 * self.t * self.t * 12)

    def call_classically(self, **kwargs) -> Dict[str, Any]:
        syndromes = [kwargs[f"syndrome_{i}"] for i in range(2 * self.t)]
        sigma = self._classical_bma(syndromes)
        return {f"sigma_{i}": sigma[i] for i in range(self.t + 1)}

    def _classical_bma(self, syndromes: List[int]) -> List[int]:
        gf = GF2_12()
        t = self.t
        N = (1 << 12) - 1
        primitive = 2

        sigma = [0] * (t + 1)
        sigma[0] = 1
        C = [0] * (t + 1)
        C[0] = 1
        L = 0
        B = -1
        k = 0

        for n in range(2 * t):
            delta = syndromes[n]
            for i in range(1, L + 1):
                delta ^= gf.mul(sigma[i], syndromes[n - i])

            delta_nz = delta != 0

            if delta_nz:
                T = sigma[:]
                for i in range(1, t + 1):
                    sigma[i] ^= gf.mul(delta, C[i-1]) if i <= len(C)-1 else 0

                if 2 * L <= n:
                    L = n + 1 - L
                    C = T[:]
                    B = L

        return sigma


class GF2_12:
    """Classical GF(2^12) arithmetic for classical simulation."""

    def __init__(self):
        self.m = 12
        self.N = 4095
        self.primitive = 2
        self._build_tables()

    def _build_tables(self):
        self.exp_table = [0] * 4096
        self.log_table = [-1] * 4096
        val = 1
        for k in range(4095):
            self.exp_table[k] = val
            self.log_table[val] = k
            val = self.mul(val, self.primitive)
        self.exp_table[4095] = 1

    def mul(self, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        return self.exp_table[(self.log_table[a] + self.log_table[b]) % 4095]

    def div(self, a: int, b: int) -> int:
        if a == 0:
            return 0
        if b == 0:
            raise ValueError("Division by zero")
        return self.exp_table[(self.log_table[a] - self.log_table[b]) % 4095]

    def inv(self, a: int) -> int:
        if a == 0:
            raise ValueError("Inverse of zero undefined")
        return self.exp_table[(4095 - self.log_table[a]) % 4095]


if __name__ == '__main__':
    # Test BMA Bloq
    bma = BMABloq(t=35, gf_degree=12)
    print("BMA Bloq created")
    print("Signature:", bma.signature)
    print("T-complexity:", bma._t_complexity_())

    # Test classical simulation
    test_syndromes = [14, 255, 1024, 7, 4095, 33, 12, 8, 9, 21, 44, 99, 105, 300, 2, 0, 11, 4, 1, 5, 8, 9, 13, 27] + [0] * 47
    result = bma.call_classically(**{f"syndrome_{i}": s for i, s in enumerate(test_syndromes)})
    print(f"BMA Classical result: {result}")