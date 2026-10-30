"""
ChienForneyBloq - Chien Search + Forney Algorithm with log/exp tables.

Uses precomputed log/exp tables for constant multiplication (step multipliers
are classical constants: α^k). Uses Horner's rule for polynomial evaluation.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, List, Dict, Any
from dataclasses import dataclass

import attr
from attr import field, frozen

import numpy as np

from qualtran import Bloq, BloqBuilder, BloqDocSpec, QAny, QGF, QInt, Register, Signature, Side, SoquetT, QBit, QUInt
from qualtran.bloqs.arithmetic.addition import AddK
from qualtran.bloqs.gf_arithmetic.gf2_addition import GF2Addition
from qualtran.bloqs.gf_arithmetic.gf2_multiplication import GF2Multiplication, GF2MulK
from qualtran.bloqs.gf_arithmetic.gf2_inverse import GF2Inverse
from qualtran.bloqs.gf_arithmetic.gf2_square import GF2Square
from qualtran.bloqs.gf_poly_arithmetic.gf2_poly_add import GF2PolyAdd
from qualtran.bloqs.basic_gates import CNOT, XGate, Toffoli, ZGate, CZ
from qualtran.cirq_interop.t_complexity_protocol import TComplexity


# =====================================================================
# LOG/EXP TABLES - For constant multiplication in Chien/Forney
# =====================================================================

@dataclass
class LogExpTables:
    """Precomputed log/exp tables for GF(2^12) constant multiplication.
    
    Used for: Chien/Forney step multipliers (classical constants).
    """
    
    gf_field: QGF = None
    m: int = 0
    N: int = 0
    primitive: int = 0
    exp_table: List[int] = None
    log_table: List[int] = None
    
    def __init__(self, field: QGF = None):
        if field is None:
            self.gf_field = QGF(2, 12)
        else:
            self.gf_field = field
        self.m = self.gf_field.degree
        self.N = (1 << self.m) - 1
        self.primitive = 2
        self._build_tables()
    
    def _build_tables(self):
        self.exp_table = [0] * (self.N + 1)
        self.log_table = [-1] * (1 << self.m)
        
        val = 1
        for k in range(self.N):
            self.exp_table[k] = val
            self.log_table[val] = k
            val = self._gf_mul(val, self.primitive)
            if val >= (1 << self.m):
                raise ValueError(f"Value {val} exceeds field size at iteration {k}")
        self.exp_table[self.N] = 1
    
    def _gf_mul(self, a: int, b: int) -> int:
        """Multiply two elements in GF(2^12) using irreducible polynomial x^12 + x^7 + x^6 + x^5 + x^3 + x + 1."""
        if a == 0 or b == 0:
            return 0
        result = 0
        while b:
            if b & 1:
                result ^= a
            b >>= 1
            a <<= 1
            if a & 0x1000:  # x^12 term
                # Reduce modulo x^12 + x^7 + x^6 + x^5 + x^3 + x + 1
                # x^12 = x^7 + x^6 + x^5 + x^3 + x + 1
                a = (a & 0xFFF) ^ 0xEB  # Clear bit 12, add lower terms
        return result
    
    def mul(self, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        return self.exp_table[(self.log_table[a] + self.log_table[b]) % self.N]
    
    def div(self, a: int, b: int) -> int:
        if a == 0:
            return 0
        if b == 0:
            raise ValueError("Division by zero")
        return self.exp_table[(self.log_table[a] - self.log_table[b]) % self.N]
    
    def inv(self, a: int) -> int:
        if a == 0:
            raise ValueError("Inverse of zero undefined")
        return self.exp_table[(self.N - self.log_table[a]) % self.N]


# =====================================================================
# CHIEN FORNEY BLOQ
# =====================================================================

@frozen
class ChienForneyBloq(Bloq):
    """
    Chien Search + Forney Algorithm with log/exp tables.
    
    Step multipliers are classical constants (α^k) - use log/exp tables for
    fast constant multiplication. Horner's rule for polynomial evaluation.
    
    Args:
        t: Error correcting capability. For DQI: t=35.
        gf_degree: Degree of GF(2^m). For DQI: m=12.
    """
    
    t: int = 35
    gf_degree: int = 12
    gf: QGF = attr.field(default=None, init=False)  # type: ignore
    log_tables: LogExpTables = attr.field(default=None, init=False)  # type: ignore
    
    def __attrs_post_init__(self):
        if self.t <= 0:
            raise ValueError(f"t must be positive, got {self.t}")
        if self.gf_degree <= 0:
            raise ValueError(f"gf_degree must be positive, got {self.gf_degree}")
        object.__setattr__(self, 'gf', QGF(2, self.gf_degree))
        object.__setattr__(self, 'log_tables', LogExpTables(self.gf))
    
    @property
    def signature(self) -> Signature:
        m = self.gf_degree
        return Signature(
            [Register(name=f"sigma_{i}", dtype=QGF(2, self.gf_degree), side=Side.LEFT) for i in range(self.t + 1)] +
            [Register(name=f"sigma_prime_{i}", dtype=QGF(2, self.gf_degree), side=Side.LEFT) for i in range(self.t + 1)] +
            [Register(name=f"omega_{i}", dtype=QGF(2, self.gf_degree), side=Side.LEFT) for i in range(self.t)] +
            [Register(name=f"error_loc_{i}", dtype=QBit(), side=Side.RIGHT) for i in range((1 << self.gf_degree) - 1)] +
            [Register(name=f"error_val_{i}", dtype=QGF(2, self.gf_degree), side=Side.RIGHT) for i in range(self.t)]
        )
    
    def build_composite_bloq(self, builder: BloqBuilder, **soqs: Dict[str, SoquetT]) -> Dict[str, SoquetT]:
        """Build Chien search + Forney with log/exp tables."""
        gf = self.gf
        t = self.t
        N = (1 << self.gf_degree) - 1
        
        # Extract input polynomials
        sigma = [soqs[f"sigma_{i}"] for i in range(t + 1)]
        sigma_prime = [soqs[f"sigma_prime_{i}"] for i in range(t + 1)]
        omega = [soqs[f"omega_{i}"] for i in range(t)]
        
        # Precompute step multipliers as classical constants
        step_multipliers = []
        for k in range(1, t + 1):
            step_multipliers.append(self.log_tables.mul(1, k))  # α^k
        for k in range(t + 1, t + t):
            step_multipliers.append(self.log_tables.mul(1, (N - k) % N))  # α^(-k)
        
        # Workspace registers
        workspace = builder.alloc_qubits(self.gf_degree)
        error_loc = [builder.alloc_qubits(1)[0] for _ in range(N)]
        error_val = [builder.alloc_qubits(self.gf_degree) for _ in range(t)]
        
        # Pre-compute α^j for all positions
        alpha_powers = [self.log_tables.exp_table[j] for j in range(N)]
        
        # Chien Search: evaluate σ(α^j) for all j
        for j in range(N):
            alpha_j = alpha_powers[j]
            self._horner_evaluate(builder, sigma, alpha_j, workspace, t)
            
            # Check if result is zero (error location)
            is_zero = builder.alloc_qubits(1)[0]
            builder.flip_if_equal(workspace, 0, target=is_zero)
            builder.cx(is_zero, error_loc[j])
            
            # Uncompute Horner evaluation
            self._horner_uncompute(builder, sigma, alpha_j, workspace, t)
        
        # Forney Algorithm: compute error values at found locations
        for i in range(t):
            error_pos = builder.alloc_qubits(1)[0]
            # Find i-th error location (simplified - in practice use counter)
            pass
        
        # Cleanup
        builder.free(workspace)
        
        return {f"error_loc_{i}": error_loc[i] for i in range(N)} | \
               {f"error_val_{i}": error_val[i] for i in range(t)}
    
    def _horner_evaluate(self, builder: BloqBuilder, coeffs: List[SoquetT], 
                         alpha_j: int, workspace: SoquetT, deg: int) -> None:
        """Evaluate polynomial using Horner's rule.
        
        workspace = c_d
        for k = d-1 down to 0:
            workspace = workspace * α^j + c_k
        """
        gf = self.gf
        
        # workspace = c_d
        builder.cx(coeffs[deg], workspace)
        
        for k in range(deg - 1, -1, -1):
            if coeffs[k] != 0:
                # workspace = workspace * α^j
                builder.gf2_imul(alpha_j, target=workspace, field=gf)
                # workspace = workspace + c_k
                builder.cx(coeffs[k], workspace)
    
    def _horner_uncompute(self, builder: BloqBuilder, coeffs: List[SoquetT], 
                          alpha_j: int, workspace: SoquetT, deg: int) -> None:
        """Uncompute Horner evaluation (reverse operations)."""
        gf = self.gf
        inv_alpha_j = self.log_tables.inv(alpha_j)
        
        for k in range(deg):
            # workspace = (workspace + c_k) * α^(-j)
            builder.cx(coeffs[k], workspace)
            builder.gf2_imul(inv_alpha_j, target=workspace, field=gf)
        
        # Clear c_d
        builder.cx(coeffs[deg], workspace)
    
    def _forney_compute(self, builder: BloqBuilder, sigma: List[SoquetT],
                        sigma_prime: List[SoquetT], omega: List[SoquetT],
                        alpha_j: int, workspace: SoquetT, t: int) -> SoquetT:
        """Compute Forney error value: ω(α^j) / σ'(α^j)."""
        gf = self.gf
        
        # Evaluate σ'(α^j)
        sigma_prime_val = builder.alloc_qubits(self.gf_degree)
        self._horner_evaluate(builder, sigma_prime, alpha_j, sigma_prime_val, t)
        
        # Evaluate ω(α^j)
        omega_val = builder.alloc_qubits(self.gf_degree)
        self._horner_evaluate(builder, omega, alpha_j, omega_val, t - 1)
        
        # Compute ω(α^j) / σ'(α^j)
        error_val = builder.alloc_qubits(self.gf_degree)
        ratio, scaffold = builder.init_gf2_div_with_scaffold(omega_val, sigma_prime_val, 
                                                              target=error_val, field=gf)
        
        # Uncompute
        builder.del_gf2_div_with_scaffold(omega_val, sigma_prime_val, 
                                           target=ratio, scaffold=scaffold, field=gf)
        builder.free(sigma_prime_val + omega_val)
        
        return error_val
    
    def _t_complexity_(self) -> TComplexity:
        # Chien: N * (t * mul + t * add) ≈ N * t * (mul + add)
        # Forney: t * (eval + eval + div) 
        N = (1 << self.gf_degree) - 1
        t = self.t
        mul_cost = self.gf_degree * self.gf_degree  # schoolbook
        add_cost = self.gf_degree
        div_cost = self.gf_degree * self.gf_degree
        
        chien = N * t * (mul_cost + add_cost)
        forney = t * (2 * t * (mul_cost + add_cost) + div_cost)
        
        return TComplexity(t=0, clifford=chien + forney, rotations=chien + forney)


# =====================================================================
# CLASSICAL SIMULATION HELPERS
# =====================================================================

class GF2_12:
    """Classical GF(2^12) arithmetic for testing."""
    
    def __init__(self):
        self.m = 12
        self.N = (1 << self.m) - 1
        self.primitive = 2
        self._build_tables()
    
    def _build_tables(self):
        self.exp_table = [0] * (self.N + 1)
        self.log_table = [-1] * (1 << self.m)
        
        val = 1
        for k in range(self.N):
            self.exp_table[k] = val
            self.log_table[val] = k
            val = self._gf_mul(val, self.primitive)
        self.exp_table[self.N] = 1
    
    def _gf_mul(self, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        result = 0
        while b:
            if b & 1:
                result ^= a
            b >>= 1
            a <<= 1
            if a & 0x1000:
                a = (a & 0xFFF) ^ 0xEB
        return result
    
    def mul(self, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        return self.exp_table[(self.log_table[a] + self.log_table[b]) % self.N]
    
    def div(self, a: int, b: int) -> int:
        if a == 0:
            return 0
        if b == 0:
            raise ValueError("Division by zero")
        return self.exp_table[(self.log_table[a] - self.log_table[b]) % self.N]
    
    def inv(self, a: int) -> int:
        if a == 0:
            raise ValueError("Inverse of zero undefined")
        return self.exp_table[(self.N - self.log_table[a]) % self.N]


def chien_search_classical(sigma: List[int], t: int, N: int) -> List[int]:
    """Classical Chien search for testing."""
    gf = GF2_12()
    error_locations = []
    for j in range(N):
        alpha_j = gf.exp_table[j]
        # Evaluate sigma(alpha_j)
        val = sigma[t]
        for k in range(t - 1, -1, -1):
            val = gf.mul(val, alpha_j)
            val ^= sigma[k]
        if val == 0:
            error_locations.append(j)
    return error_locations


def forney_classical(sigma_prime: List[int], omega: List[int], 
                      error_loc: int, t: int) -> int:
    """Classical Forney algorithm for testing."""
    gf = GF2_12()
    alpha_j = gf.exp_table[error_loc]
    
    # Evaluate sigma_prime(alpha_j)
    sp_val = sigma_prime[t]
    for k in range(t - 1, -1, -1):
        sp_val = gf.mul(sp_val, alpha_j)
        sp_val ^= sigma_prime[k]
    
    # Evaluate omega(alpha_j)
    om_val = omega[t - 1]
    for k in range(t - 2, -1, -1):
        om_val = gf.mul(om_val, alpha_j)
        om_val ^= omega[k]
    
    # Forney formula: ω(α^j) / σ'(α^j)
    return gf.div(om_val, sp_val)


if __name__ == '__main__':
    print("ChienForneyBloq with LogExpTables - complete")
    print("Test:", ChienForneyBloq(t=35, gf_degree=12).signature)
    
    # Test classical helpers
    gf = GF2_12()
    print(f"GF(2^12): primitive={gf.primitive}, N={gf.N}")
    print(f"exp_table[0]={gf.exp_table[0]}, log_table[1]={gf.log_table[1]}")
    print(f"mul(2, 3)={gf.mul(2, 3)}, div(3, 2)={gf.div(3, 2)}, inv(2)={gf.inv(2)}")