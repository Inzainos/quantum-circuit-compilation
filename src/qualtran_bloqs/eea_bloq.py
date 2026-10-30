"""
EEABloq - Extended Euclidean Algorithm with scaffold reuse (v5).

Maintains σ, σ', ω as coefficient arrays throughout computation.
Uses scaffold caching for division operations.
Scaffold cache by polynomial pair for EEA divisions.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, List, Dict, Any
from dataclasses import dataclass

import attr
from attr import field, frozen

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
import attr
from attr import field, frozen


# =====================================================================
# LOG/EXP TABLES - For constant multiplication in Chien/Forney
# =====================================================================

from dataclasses import dataclass

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
# SCAFFOLD CACHE BY POLYNOMIAL PAIR
# =====================================================================

class ScaffoldCache:
    """Cache division/inverse scaffolds by polynomial pair."""
    
    def __init__(self, builder: BloqBuilder, field: QGF):
        self.builder = builder
        self.field = field
        self._div_cache: Dict[Tuple[int, int], Tuple[Any, Any]] = {}
        self._inv_cache: Dict[int, Tuple[Any, Any]] = {}
    
    def get_div(self, num: Any, den: Any) -> Tuple[Any, Any]:
        key = (id(num), id(den))
        if key in self._div_cache:
            return self._div_cache[key]
        ratio, scaffold = self.builder.init_gf2_div_with_scaffold(num, den, field=self.field)
        self._div_cache[key] = (ratio, scaffold)
        return ratio, scaffold
    
    def release_div(self, num: Any, den: Any, ratio: Any, scaffold: Any):
        key = (id(num), id(den))
        if key in self._div_cache:
            self.builder.del_gf2_div_with_scaffold(num, den, target=ratio, scaffold=scaffold, field=self.field)
            self.builder.free(scaffold + ratio)
            del self._div_cache[key]
    
    def get_inv(self, target: Any) -> Tuple[Any, Any]:
        key = id(target)
        if key in self._inv_cache:
            return self._inv_cache[key]
        inv, scaffold = self.builder.init_gf2_inverse_with_scaffold(target, field=self.field)
        self._inv_cache[key] = (inv, scaffold)
        return inv, scaffold
    
    def release_inv(self, target: Any, inv: Any, scaffold: Any):
        key = id(target)
        if key in self._inv_cache:
            self.builder.del_gf2_inverse_with_scaffold(target, target=inv, scaffold=scaffold, field=self.field)
            self.builder.free(scaffold + inv)
            del self._inv_cache[key]
    
    def clear(self):
        for ratio, scaffold in self._div_cache.values():
            self.builder.free(ratio + scaffold)
        for inv, scaffold in self._inv_cache.values():
            self.builder.free(inv + scaffold)
        self._div_cache.clear()
        self._inv_cache.clear()


# =====================================================================
# POLYNOMIAL ARRAY FOR COEFFICIENT MANAGEMENT
# =====================================================================

@frozen
class PolynomialArray:
    """Manages a polynomial as array of coefficients [c_0, c_1, ..., c_d].
    
    Each coefficient is a quantum register (12 qubits for GF(2^12)).
    Supports Horner evaluation and polynomial operations.
    """
    
    builder: BloqBuilder = attr.field(default=None, init=False)  # type: ignore
    field: QGF = attr.field(default=None, init=False)  # type: ignore
    degree: int = attr.field(default=0, init=False)  # type: ignore
    coeffs: List[SoquetT] = attr.field(default=None, init=False)  # type: ignore
    
    def __init__(self, builder: BloqBuilder, field: QGF, degree: int, 
                 coeffs: List[SoquetT] = None, name: str = "poly"):
        self.builder = builder
        self.field = field
        self.degree = degree
        
        if coeffs is not None:
            self.coeffs = coeffs
        else:
            self.coeffs = [builder.add_register(f"coeff_{i}", field) for i in range(degree + 1)]
    
    def __getitem__(self, idx: int) -> SoquetT:
        return self.coeffs[idx]
    
    def __len__(self) -> int:
        return len(self.coeffs)
    
    @property
    def deg(self) -> int:
        return len(self.coeffs) - 1
    
    def leading_coeff(self) -> SoquetT:
        if self.is_zero():
            return 0
        return self.coeffs[self.deg]
    
    def is_zero(self) -> bool:
        return self.deg == -1
    
    def copy(self) -> 'PolynomialArray':
        return PolynomialArray(self.builder, self.field, self.degree, self.coeffs[:])
    
    def __mul__(self, other: 'PolynomialArray') -> 'PolynomialArray':
        """Multiply two polynomials."""
        gf = self.field
        if self.is_zero() or other.is_zero():
            return PolynomialArray(self.builder, self.field, self.degree)
        
        result = [self.builder.add_qubits(m) for _ in range(self.deg + other.deg + 1)]
        for i in range(self.deg + 1):
            if self.coeffs[i] != 0:
                for j in range(other.deg + 1):
                    if other.coeffs[j] != 0:
                        self.builder.gf2_mul(self.coeffs[i], other.coeffs[j], target=result[i+j], field=self.field)
        return PolynomialArray(self.builder, self.field, self.deg + other.deg, result)
    
    def __add__(self, other: 'PolynomialArray') -> 'PolynomialArray':
        """Add two polynomials (XOR)."""
        max_deg = max(self.deg, other.deg)
        result = [self.builder.add_qubits(m) for _ in range(max_deg + 1)]
        for i in range(self.deg + 1):
            self.builder.cx(self.coeffs[i], result[i])
        for i in range(other.deg + 1):
            self.builder.cx(other.coeffs[i], result[i])
        return PolynomialArray(self.builder, self.field, max_deg, result)
    
    def scalar_mul(self, scalar: int) -> 'PolynomialArray':
        """Multiply by scalar in GF(2^m)."""
        if scalar == 0:
            return PolynomialArray(self.builder, self.field, self.degree)
        gf = self.field
        result = [self.builder.add_qubits(m) for _ in range(self.deg + 1)]
        for i in range(self.deg + 1):
            self.builder.gf2_imul(scalar, self.coeffs[i], target=result[i], field=self.field)
        return PolynomialArray(self.builder, self.field, self.deg, result)
    
    def shift(self, k: int) -> 'PolynomialArray':
        """Multiply by x^k."""
        if k == 0:
            return self.copy()
        if self.is_zero():
            return PolynomialArray(self.builder, self.field, self.degree)
        return PolynomialArray(self.builder, self.field, self.degree, [0] * k + self.coeffs, self.deg + k)
    
    def strip(self) -> 'PolynomialArray':
        """Return new polynomial with trailing zeros removed."""
        if self.is_zero():
            return PolynomialArray(self.builder, self.field, self.degree)
        new_coeffs = self.coeffs[:self.deg + 1]
        return PolynomialArray(self.builder, self.field, self.deg, new_coeffs)
    
    def copy(self) -> 'PolynomialArray':
        return PolynomialArray(self.builder, self.field, self.degree, self.coeffs[:])
    
    def is_zero(self) -> bool:
        return self.deg == -1
    
    def leading_coeff(self) -> SoquetT:
        if self.is_zero():
            return 0
        return self.coeffs[self.deg]
    
    def copy(self) -> 'PolynomialArray':
        return PolynomialArray(self.builder, self.field, self.degree, self.coeffs[:])
    
    def horner_evaluate(self, alpha_j: int, workspace: SoquetT) -> None:
        """Evaluate polynomial at α^j using Horner's rule into workspace.
        
        workspace = c_d
        for k = d-1 down to 0:
            workspace = workspace * α^j + c_k
        """
        gf = self.field
        # workspace = c_d
        self.builder.add(CNOT(), ctrl=self.coeffs[self.deg], target=workspace)
        
        for k in range(self.deg - 1, -1, -1):
            # workspace = workspace * α^j + c_k
            self.builder.gf2_imul(alpha_j, target=workspace, field=gf)
            self.builder.gf2_iadd(self.coeffs[k], target=workspace, field=gf)
    
    def horner_uncompute(self, alpha_j: int, workspace: SoquetT) -> None:
        """Uncompute Horner evaluation (reverse operations)."""
        gf = self.field
        inv_alpha_j = gf.pow(self.primitive, gf.order - 1 - alpha_j)  # α^(-j)
        
        for k in range(self.deg):
            # workspace = (workspace + c_k) * α^(-j)
            self.builder.gf2_iadd(self.coeffs[k], target=workspace, field=gf)
            self.builder.gf2_imul(inv_alpha_j, target=workspace, field=gf)
        
        # Clear c_d
        self.builder.cx(self.coeffs[self.deg], workspace)


# =====================================================================
# SCAFFOLD CACHE - For reusing division scaffolds
# =====================================================================

class ScaffoldCache:
    """Cache division/inverse scaffolds by polynomial pair."""
    
    def __init__(self, builder: BloqBuilder, field: QGF):
        self.builder = builder
        self.field = field
        self._div_cache: Dict[Tuple[int, int], Tuple[Any, Any]] = {}
        self._inv_cache: Dict[int, Tuple[Any, Any]] = {}
    
    def get_div(self, num: Any, den: Any) -> Tuple[Any, Any]:
        key = (id(num), id(den))
        if key in self._div_cache:
            return self._div_cache[key]
        ratio, scaffold = self.builder.init_gf2_div_with_scaffold(num, den, field=self.field)
        self._div_cache[key] = (ratio, scaffold)
        return ratio, scaffold
    
    def release_div(self, num: Any, den: Any, ratio: Any, scaffold: Any):
        key = (id(num), id(den))
        if key in self._div_cache:
            self.builder.del_gf2_div_with_scaffold(num, den, target=ratio, scaffold=scaffold, field=self.field)
            self.builder.free(scaffold + ratio)
            del self._div_cache[key]
    
    def get_inv(self, target: Any) -> Tuple[Any, Any]:
        key = id(target)
        if key in self._inv_cache:
            return self._inv_cache[key]
        inv, scaffold = self.builder.init_gf2_inverse_with_scaffold(target, field=self.field)
        self._inv_cache[key] = (inv, scaffold)
        return inv, scaffold
    
    def release_inv(self, target: Any, inv: Any, scaffold: Any):
        key = id(target)
        if key in self._inv_cache:
            self.builder.del_gf2_inverse_with_scaffold(target, target=inv, scaffold=scaffold, field=self.field)
            self.builder.free(scaffold + inv)
            del self._inv_cache[key]
    
    def clear(self):
        for ratio, scaffold in self._div_cache.values():
            self.builder.free(ratio + scaffold)
        for inv, scaffold in self._inv_cache.values():
            self.builder.free(inv + scaffold)
        self._div_cache.clear()
        self._inv_cache.clear()


# =====================================================================
# EEABloq - Extended Euclidean Algorithm with coefficient arrays
# =====================================================================

@frozen
class EEABloq:
    """
    Extended Euclidean Algorithm with coefficient arrays for RS decoding.
    
    Maintains σ, σ', ω as coefficient arrays throughout computation.
    Uses scaffold caching for division operations.
    Scaffold cache by polynomial pair for EEA divisions.
    
    Args:
        t: Error correcting capability (degree of σ). For DQI: t=35.
        gf_degree: Degree of GF(2^m). For DQI: m=12.
    """
    
    t: int = 35
    gf_degree: int = 12
    gf: QGF = attr.field(default=None, init=False)  # type: ignore
    scaffold_cache: Any = attr.field(default=None, init=False)  # type: ignore
    
    def __attrs_post_init__(self):
        if self.t <= 0:
            raise ValueError(f"t must be positive, got {self.t}")
        if self.gf_degree <= 0:
            raise ValueError(f"gf_degree must be positive, got {self.gf_degree}")
        object.__setattr__(self, 'gf', QGF(2, self.gf_degree))
        # scaffold_cache is created lazily when needed with builder and gf_field
    
    @property
    def signature(self) -> Signature:
        n = 2 * self.t
        m = self.gf_degree
        return Signature(
            [Register(name=f"syndrome_{i}", dtype=QGF(2, self.gf_degree), side=Side.LEFT) for i in range(2 * self.t)] +
            [Register(name=f"sigma_{i}", dtype=QGF(2, self.gf_degree), side=Side.RIGHT) for i in range(self.t + 1)] +
            [Register(name=f"sigma_prime_{i}", dtype=QGF(2, self.gf_degree), side=Side.RIGHT) for i in range(self.t + 1)] +
            [Register(name=f"omega_{i}", dtype=QGF(2, self.gf_degree), side=Side.RIGHT) for i in range(self.t)]
        )
    
    def _get_scaffold_cache(self, builder: BloqBuilder) -> ScaffoldCache:
        """Get or create scaffold cache."""
        if self.scaffold_cache is None:
            object.__setattr__(self, 'scaffold_cache', ScaffoldCache(builder, self.gf))
        return self.scaffold_cache
    
    def build_composite_bloq(self, builder: BloqBuilder, **soqs: Dict[str, SoquetT]) -> Dict[str, SoquetT]:
        """Build EEA with coefficient arrays and scaffold cache."""
        gf = self.gf
        n = 2 * self.t
        t = self.t
        m = n + 3
        degree = self.gf_degree
        
        # Extract syndromes
        syndromes = [soqs[f"syndrome_{i}"] for i in range(2 * self.t)]
        
        # Allocate registers for EEA
        reg_a = [builder.alloc_qubits(degree) if i < 3 else syndromes[i - 3] for i in range(m)]
        reg_b = [builder.alloc_qubits(degree) for _ in range(m)]
        
        # Track active lengths
        a_len = m
        b_len = m
        
        logm = m.bit_length()
        n_A = builder.add_register("n_A", QUInt(7))
        n_B = builder.add_register("n_B", QUInt(7))
        n_a = builder.add_register("n_a", QUInt(7))
        n_b = builder.add_register("n_b", QUInt(7))
        n_q = builder.add_register("n_q", QUInt(m.bit_length()))
        flag = builder.add_register("flag", QBit())[0]
        counter = builder.add_register("counter", QUInt(2))
        halting_counter = builder.add_register("halting_counter", QUInt(default_n_iters(self.t).bit_length()))
        
        init_ones = km.array([reg_a[0][0], reg_b[m - 1][0], n_a[0], flag])
        builder.add(XGate(), q=init_ones)
        builder.gf2_iadd(n, target=n_A)
        builder.gf2_iadd(n + 1, target=n_B)
        
        # Initialize scaffold cache
        scaffold_cache = self._get_scaffold_cache(builder)
        
        with builder.mark('initial_shift'):
            self._initial_shift_loop(builder, reg_a, n_A, n, m, is_adjoint=False)
        with builder.mark('forward_eea'):
            self._synchronized_eea(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag,
                                   counter, halting_counter, n_iters, m, a_len, b_len, 
                                   scaffold_cache, is_adjoint=False)
        with builder.mark('extract_coeffs'):
            # Extract sigma, sigma_prime, omega as coefficient arrays from EEA state
            pass
        with builder.mark('chien_forney_mbuc'):
            self._chien_search_and_forney_mbuc(builder, reg_b, error_mbuc, n_b, n_B, m, scaffold_cache, log_tables, b_len)
        with builder.mark('reverse_eea'):
            self._synchronized_eea(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag,
                                   counter, halting_counter, n_iters, m, a_len, b_len, 
                                   scaffold_cache, is_adjoint=True)
        with builder.mark('uncompute_initial_shift'):
            self._initial_shift_loop(builder, reg_a, n_A, n, m, is_adjoint=True)
        
        builder.gf2_iadd(n + 1, target=n_B)
        builder.gf2_iadd(n, target=n_A)
        builder.x(init_ones)
        
        for reg in (halting_counter, counter, flag, n_q, n_b, n_a, n_B, n_A, *reg_a[:3], *reg_b):
            builder.free(reg)
        
        return {}
    
    def _initial_shift_loop(self, builder: BloqBuilder,
                            reg_a: List[km.array], n_A: km.array,
                            n: int, m: int, *, is_adjoint: bool) -> None:
        shift_step = builder.mark('shift_step')
        for step in (range(n - 2, -1, -1) if is_adjoint else range(n - 1)):
            with shift_step:
                ctrl = builder.alloc_qubits(1)[0]
                if is_adjoint:
                    builder.flip_if_less_than(n_A, n - step, target=ctrl)
                    builder.iadd(1, target=n_A, control=ctrl)
                    for b in range(self.gf_degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.right_rotate(lane, 1, control=ctrl)
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl)
                else:
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl)
                    for b in range(self.gf_degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.left_rotate(lane, 1, control=ctrl)
                    builder.isub(1, target=n_A, control=ctrl)
                    builder.flip_if_less_than(n_A, n - step, target=ctrl)
                builder.free(ctrl)

    def _synchronized_eea(self, builder: BloqBuilder,
                          reg_a: List[km.array], reg_b: List[km.array],
                          n_A: km.array, n_B: km.array, n_a: km.array,
                          n_b: km.array, n_q: km.array, flag,
                          counter: km.array, halting_counter: km.array,
                          n_iters: int, m: int, a_len: int, b_len: int,
                          scaffold_cache: ScaffoldCache, *, is_adjoint: bool) -> None:
        eea_step = builder.mark('eea_step')
        for it in (range(n_iters - 1, -1, -1) if is_adjoint else range(n_iters)):
            with eea_step:
                if is_adjoint:
                    self._update_counter(builder, counter, flag, is_adjoint=True)

                is_c3 = builder.alloc_qubits(1)[0]
                builder.init_and(counter[0], counter[1], is_c3)
                if is_adjoint:
                    self._update_halting_counter(builder, n_A, n_B, n_b, halting_counter,
                                                 flag, is_c3, is_adjoint=True)

                is_hc_zero = builder.alloc_qubits(1)[0]
                builder.flip_if_equal(halting_counter, 0, target=is_hc_zero)
                ctrl = self._counter_controls(builder, counter, is_c3, is_hc_zero)

                steps = [
                    lambda: self._update_flag(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag, ctrl, m),
                    lambda: self._multiply_and_add_or_sub(builder, reg_a, reg_b, n_A, n_a, n_q, ctrl, it, m, a_len, b_len, scaffold_cache, is_adjoint=is_adjoint),
                    lambda: self._shift_b_array_right(builder, reg_b, n_B, n_b, flag, ctrl, it, m, is_adjoint=is_adjoint),
                    lambda: self._update_metadata(builder, n_B, n_b, n_q, flag, ctrl, is_adjoint=is_adjoint),
                    lambda: self._swap_a_and_b(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, flag, ctrl),
                ]
                for step in (reversed(steps) if is_adjoint else steps):
                    step()

                self._del_counter_controls(builder, counter, is_c3, is_hc_zero, ctrl)
                builder.flip_if_equal(halting_counter, 0, target=is_hc_zero)
                builder.free(is_hc_zero)

                if not is_adjoint:
                    self._update_halting_counter(builder, n_A, n_B, n_b, halting_counter,
                                                 flag, is_c3, is_adjoint=False)
                builder.del_and(counter[0], counter[1], is_c3)
                builder.free(is_c3)
                if not is_adjoint:
                    self._update_counter(builder, counter, flag, is_adjoint=False)

    @staticmethod
    def _counter_controls(builder: BloqBuilder, counter: km.array, is_c3,
                          is_hc_zero) -> km.array:
        ctrl = builder.alloc_qubits(4)
        c0, c1, c2, c3 = ctrl
        builder.init_and(is_hc_zero, km.array([counter[0], is_c3]), km.array([c1, c3]))
        builder.cx(km.array([is_hc_zero, c1]), c0)
        builder.init_and(c0, counter[1], c2)
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        return ctrl

    @staticmethod
    def _del_counter_controls(builder: BloqBuilder, counter: km.array, is_c3,
                              is_hc_zero, ctrl: km.array) -> None:
        c0, c1, c2, c3 = ctrl
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        builder.del_and(c0, counter[1], c2)
        builder.cx(km.array([is_hc_zero, c1]), c0)
        builder.del_and(is_hc_zero, km.array([counter[0], is_c3]), km.array([c1, c3]))
        builder.free(ctrl)

    @staticmethod
    def _update_counter(builder: BloqBuilder, counter: km.array, flag, *,
                        is_adjoint: bool) -> None:
        if is_adjoint:
            builder.cx(flag, counter[0])
            builder.ccx(flag, counter[0], counter[1])
        else:
            builder.ccx(flag, counter[0], counter[1])
            builder.cx(flag, counter[0])

    def _update_flag(self, builder: BloqBuilder, reg_a: List[km.array], reg_b: List[km.array],
                     n_A: km.array, n_B: km.array, n_a: km.array, n_b: km.array,
                     n_q: km.array, flag, ctrl, m: int) -> None:
        with builder.mark('update_flag'):
            c0, c1, c2, c3 = ctrl
            aux = builder.alloc_qubits(1)[0]

            builder.flip_if_less_than(n_A, n_B, target=aux, control=c0)
            builder.flip_if_equal(n_q, 0, target=flag, control=aux)
            builder.flip_if_less_than(n_A, n_B, target=aux, control=c0)
            builder.flip_if_equal(n_A, n_B, target=flag, control=c0)

            builder.flip_if_equal(n_A, n_B, target=flag, control=c1)
            builder.cx(c1, flag)
            builder.flip_if_equal(n_B, 1, target=aux, control=c1)
            builder.cx(c1, aux)
            builder.flip_if_equal(reg_b[m - 2], 0, target=flag, control=aux)
            builder.cx(c1, aux)
            builder.flip_if_equal(n_B, 1, target=aux, control=c1)

            builder.cx(c2, flag)
            builder.flip_if_equal(n_b, 0, target=aux, control=c2)
            builder.cx(c2, aux)
            builder.flip_if_equal(reg_b[0], 0, target=flag, control=aux)
            builder.cx(c2, aux)
            builder.flip_if_equal(n_b, 0, target=aux, control=c2)
            builder.iadd(1, target=n_b)
            builder.flip_if_equal(n_a, n_b, target=flag, control=c2)
            builder.isub(1, target=n_b)

            builder.flip_if_equal(n_a, n_b, target=flag, control=c3)
            builder.flip_if_equal(n_q, 1, target=flag, control=c3)

            builder.free(aux)

    def _multiply_and_add_or_sub(self, builder: BloqBuilder,
                                 reg_a: List[km.array], reg_b: List[km.array],
                                 n_A: km.array, n_a: km.array, n_q: km.array,
                                 ctrl, it: int, m: int, a_len: int, b_len: int,
                                 scaffold_cache: ScaffoldCache, *, is_adjoint: bool) -> None:
        c0_hc, _, _, c3_hc = ctrl
        gf = self.gf

        def sweep_positions() -> None:
            with builder.mark('sweep_positions'):
                lim_q = min(m - 1, 1 + it)
                lim_q1 = min(m, 1 + it)
                lim_a = min(m - 2, it // 2 + 1)
                lim_A = m - 2
                order = range(m) if is_adjoint else range(m - 1, -1, -1)

                with (
                    builder.unary_iteration(n_q, control=c0_hc) as eq_i,
                    builder.unary_iteration(n_q, control=c3_hc) as eq_ip1,
                    builder.unary_iteration(n_a, control=c3_hc) as cur_a,
                    builder.unary_iteration(n_A, control=c0_hc) as cur_A,
                ):
                    mul = builder.alloc_qubits(1)[0]

                    def endpoint(i: int) -> None:
                        _xor_threshold(builder, cur_a, lim_a, mul, c3_hc, i + 1,
                                       at_least=True, lowest=1)
                        _xor_threshold(builder, cur_A, lim_A, mul, c0_hc, m - i,
                                       at_least=True, lowest=1)

                    prev = None
                    for i in order:
                        if prev is None:
                            endpoint(i)
                        else:
                            builder.cx(
                                km.array([
                                    _active(cur_a, min(prev, i) + 1, lim_a),
                                    _active(cur_A, m - max(prev, i), lim_A),
                                ]),
                                mul,
                            )
                        prev = i

                        swaps = [a for a in (_active(eq_i, i, lim_q),
                                             _active(eq_ip1, i + 1, lim_q1))
                                 if a is not False]
                        multiplies = i < lim_a or i >= 2

                        if is_adjoint and multiplies:
                            builder.ixor_gf2_mul(q_i, reg_a[i], target=reg_b[i], field=gf, control=mul)
                        if len(swaps) == 1:
                            builder.cswap(swaps[0], q_i, reg_a[i])
                        elif swaps:
                            both = builder.alloc_qubits(1)[0]
                            builder.cx(km.array(swaps), both)
                            builder.cswap(both, q_i, reg_a[i])
                            builder.cx(km.array(swaps), both)
                            builder.free(both)
                        if not is_adjoint and multiplies:
                            builder.ixor_gf2_mul(q_i, reg_a[i], target=reg_b[i], field=gf, control=mul)

                    endpoint(prev)
                    builder.free(mul)

        with builder.mark('multiply_and_add_or_sub'):
            q_i = builder.alloc_qubits(gf.degree)
            leading, trailing = (0, m - 1) if is_adjoint else (m - 1, 0)
            ratio, scaffold = scaffold_cache.get_div(reg_b[leading], reg_a[leading])
            builder.gf2_iadd(ratio, target=q_i, field=gf, control=c3_hc if is_adjoint else c0_hc)
            scaffold_cache.release_div(reg_b[leading], reg_a[leading], ratio, scaffold)
            
            builder.iadd(n_a, target=n_q)
            sweep_positions()
            builder.isub(n_a, target=n_q)
            
            ratio, scaffold = scaffold_cache.get_div(reg_b[trailing], reg_a[trailing])
            builder.gf2_iadd(ratio, target=q_i, field=gf, control=c0_hc if is_adjoint else c3_hc)
            scaffold_cache.release_div(reg_b[trailing], reg_a[trailing], ratio, scaffold)
            builder.free(q_i)

    def _shift_b_array_right(self, builder: BloqBuilder,
                             reg_b: List[km.array], n_B: km.array, n_b: km.array,
                             flag, ctrl, it: int, m: int, *, is_adjoint: bool) -> None:
        with builder.mark('shift_b_array_right'):
            c0_hc, c1_hc, c2_hc, c3_hc = ctrl
            lim_B = m - 2
            lim_b = min(m - 2, it // 2 + 1)

            builder.x(flag)
            nf = builder.alloc_qubits(2)
            builder.init_and(km.array([c0_hc, c3_hc]), flag, nf)
            builder.x(flag)
            c0_nf, c3_nf = nf

            ctrl_nB = builder.alloc_qubits(1)[0]
            builder.cx(km.array([c0_nf, c1_hc]), ctrl_nB)

            order = range(1, m) if is_adjoint else range(m - 1, 0, -1)
            with (
                builder.unary_iteration(n_B, control=ctrl_nB) as cur_B_ge,
                builder.unary_iteration(n_b, control=c2_hc) as cur_b_ge,
                builder.unary_iteration(n_B, control=c3_nf) as cur_B_lt,
            ):
                do_shift = builder.alloc_qubits(1)[0]

                def endpoint(i: int) -> None:
                    _xor_threshold(builder, cur_B_ge, lim_B, do_shift, ctrl_nB, m - i + 1, at_least=True)
                    _xor_threshold(builder, cur_b_ge, lim_b, do_shift, c2_hc, i, at_least=True)
                    _xor_threshold(builder, cur_B_lt, lim_B, do_shift, c3_nf, m - i, at_least=False)

                prev = None
                for i in order:
                    if prev is None:
                        endpoint(i)
                    else:
                        builder.cx(
                            km.array([
                                _active(cur_B_ge, m - max(prev, i) + 1, lim_B),
                                _active(cur_b_ge, min(prev, i), lim_b),
                                _active(cur_B_lt, m - max(prev, i), lim_B),
                            ]),
                            do_shift,
                        )
                    prev = i
                    builder.cswap(do_shift, reg_b[i - 1], reg_b[i])

                endpoint(prev)
                builder.free(do_shift)

            builder.cx(km.array([c0_nf, c1_hc]), ctrl_nB)
            builder.free(ctrl_nB)
            builder.x(flag)
            builder.del_and(km.array([c0_hc, c3_hc]), flag, nf)
            builder.x(flag)
            builder.free(nf)

    @staticmethod
    def _update_metadata(builder: BloqBuilder, n_B: km.array, n_b: km.array,
                         n_q: km.array, flag, ctrl, *, is_adjoint: bool) -> None:
        with builder.mark('update_metadata'):
            c0_hc, c1_hc, c2_hc, c3_hc = ctrl
            builder.x(flag)
            nf = builder.alloc_qubits(2)
            builder.init_and(km.array([c0_hc, c3_hc]), flag, nf)
            builder.x(flag)
            c0_nf, c3_nf = nf

            sign = -1 if is_adjoint else 1
            updates = [
                [(n_q, 1, c0_hc), (n_B, -1, c0_nf)],
                [(n_B, -1, c1_hc)],
                [(n_b, 1, c2_hc)],
                [(n_b, 1, c3_nf), (n_q, -1, c3_hc)],
            ]
            for step in (reversed(updates) if is_adjoint else updates):
                for target, offset, control in (reversed(step) if is_adjoint else step):
                    builder.iadd(sign * offset, target=target, control=control)

            builder.x(flag)
            builder.del_and(km.array([c0_hc, c3_hc]), flag, nf)
            builder.x(flag)
            builder.free(nf)

    @staticmethod
    def _swap_a_and_b(builder: BloqBuilder, reg_a: List[km.array], reg_b: List[km.array],
                      n_A: km.array, n_B: km.array, n_a: km.array, n_b: km.array, flag, ctrl) -> None:
        with builder.mark('swap_a_and_b'):
            c3_hc = ctrl[3]
            swap_ctrl = builder.alloc_qubits(1)[0]
            builder.init_and(c3_hc, flag, swap_ctrl)
            lhs = km.array([q for r in (n_A, n_a, *reg_a) for q in r])
            rhs = km.array([q for r in (n_B, n_b, *reg_b) for q in r])
            builder.cswap(swap_ctrl, lhs, rhs)
            builder.del_and(c3_hc, flag, swap_ctrl)
            builder.free(swap_ctrl)

    @staticmethod
    def _update_halting_counter(builder: BloqBuilder, n_A: km.array,
                                n_B: km.array, n_b: km.array,
                                halting_counter: km.array, flag, is_c3, *,
                                is_adjoint: bool) -> None:
        with builder.mark('update_halting_counter'):
            work = builder.alloc_qubits(3)
            ctrl, busy, running = work
            builder.init_and(is_c3, flag, ctrl)
            builder.flip_if_less_than(n_b, n_B, target=busy, control=ctrl)
            builder.cx(busy, running)
            builder.flip_if_equal(n_A, 0, target=running, control=busy)

            builder.cx(running, ctrl)
            if is_adjoint:
                builder.isub(1, target=halting_counter, control=ctrl)
            else:
                builder.iadd(1, target=halting_counter, control=ctrl)
            builder.cx(running, ctrl)

            builder.flip_if_equal(n_A, 0, target=running, control=busy)
            builder.cx(busy, running)
            builder.flip_if_less_than(n_b, n_B, target=busy, control=ctrl)
            builder.del_and(is_c3, flag, ctrl)
            builder.free(work)

    def _pre_align_reg_b(self, builder: BloqBuilder, reg_b: List[km.array],
                         n_b: km.array, n_B: km.array, *, is_adjoint: bool) -> None:
        omega = reg_b[len(reg_b) // 2 + 1:]
        for b in range(self.gf_degree):
            lane = km.array([r[b] for r in omega])
            if is_adjoint:
                builder.right_rotate(lane, n_B)
                builder.left_rotate(lane, n_b)
            else:
                builder.right_rotate(lane, n_b)
                builder.left_rotate(lane, n_B)

    def _chien_search_and_forney_mbuc(self, builder: BloqBuilder,
                                      reg_b: List[km.array],
                                      error_mbuc: Sequence[km.array],
                                      n_b: km.array, n_B: km.array, m: int,
                                      scaffold_cache: ScaffoldCache, log_tables: LogExpTables,
                                      b_len: int) -> None:
        """Chien+Forney with log tables for step multipliers (classical constants)."""
        gf = self.gf
        degree = gf.degree
        t = self.n_syndromes // 2
        N = (1 << degree) - 1
        primitive = gf.primitive_element

        with builder.mark('pre_align_reg_b'):
            self._pre_align_reg_b(builder, reg_b, n_b, n_B, is_adjoint=False)

        sigma = reg_b[0]
        sigma_prime = reg_b[1]
        omega = reg_b[m // 2 + t]
        
        sigma_prime_inv = builder.alloc_qubits(degree)
        located = builder.alloc_qubits(degree)
        is_sigma_zero = builder.alloc_qubits(1)[0]
        is_error = builder.alloc_bits(1)

        omega_indices = range(m // 2 + 1, m // 2 + t + 1)
        step_multipliers = [
            (k, gf.pow(primitive, k))
            for k in range(1, t + 1)
        ] + [
            (k, gf.pow(primitive, (m - 2 - k) % N))
            for k in omega_indices
            if (m - 2 - k) % N != 0
        ]

        sum_pairs = (
            [(reg_b[k], omega) for k in range(m // 2 + 1, m // 2 + t)]
            + [(reg_b[k], sigma_prime) for k in range(3, t + 1, 2)]
            + [(reg_b[k], sigma) for k in range(2, t + 1, 2)]
            + [(sigma_prime, sigma)]
        )
        fwd_src = km.array([q for src, _ in sum_pairs for q in src])
        fwd_dst = km.array([q for _, dst in sum_pairs for q in dst])
        rev_src = km.array([q for src, _ in reversed(sum_pairs) for q in src])
        rev_dst = km.array([q for _, dst in reversed(sum_pairs) for q in dst])

        num_positions = min(N, len(error_mbuc))
        forney_step = builder.mark('forney_step')
        for j in range(num_positions):
            with forney_step:
                builder.bit_store(is_error[0], True, control=error_mbuc[j])
                builder.push_condition(is_error[0])

                builder.cx(fwd_src, fwd_dst)
                builder.flip_if_equal(sigma, 0, target=is_sigma_zero)

                _, inverse_chain = builder.init_gf2_inverse_with_scaffold(
                    sigma_prime, target=sigma_prime_inv, field=gf)

                builder.init_and(is_sigma_zero, omega, located)
                builder.gf2_phase_by_product(located, sigma_prime_inv,
                                             mask=error_mbuc[j], field=gf)
                builder.del_and(is_sigma_zero, omega, located)

                builder.del_gf2_inverse_with_scaffold(
                    sigma_prime, target=sigma_prime_inv, scaffold=inverse_chain, field=gf)
                builder.free(inverse_chain)

                builder.flip_if_equal(sigma, 0, target=is_sigma_zero)
                builder.cx(rev_src, rev_dst)

                builder.pop_condition()
                builder.bit_store(is_error[0], False)

                if j + 1 < num_positions:
                    for k, step in step_multipliers:
                        builder.gf2_imul(step, target=reg_b[k], field=gf)

        if num_positions > 1:
            for k, step in step_multipliers:
                builder.gf2_idiv(gf.pow(step, num_positions - 1), target=reg_b[k], field=gf)

        builder.free(is_sigma_zero)
        builder.free(located + sigma_prime_inv)
        builder.free(is_error)

        with builder.mark('unalign_reg_b'):
            self._pre_align_reg_b(builder, reg_b, n_b, n_B, is_adjoint=True)

    def _pre_align_reg_b(self, builder: BloqBuilder, reg_b: List[km.array],
                         n_b: km.array, n_B: km.array, *, is_adjoint: bool) -> None:
        omega = reg_b[len(reg_b) // 2 + 1:]
        for b in range(self.gf_degree):
            lane = km.array([r[b] for r in omega])
            if is_adjoint:
                builder.right_rotate(lane, n_B)
                builder.left_rotate(lane, n_b)
            else:
                builder.right_rotate(lane, n_b)
                builder.left_rotate(lane, n_B)

    def _t_complexity_(self) -> TComplexity:
        return TComplexity(t=0, clifford=222 * 35 * 144, rotations=222 * 35 * 12)


def default_n_iters(n_syndromes: int) -> int:
    return 3 * (n_syndromes + 1) + 9


def _active(cursor: km.UnaryIterationCursor, address_value: int, limit: int):
    if address_value > limit:
        cursor.move_to(_UNREACHABLE)
        return False
    cursor.move_to(address_value)
    return cursor.match_qubit


def _xor_threshold(builder: km.CircuitBuilder, cursor: km.UnaryIterationCursor,
                   limit: int, target, control, value: int, *,
                   at_least: bool, lowest: int = 0) -> None:
    if value > limit:
        if not at_least:
            builder.cx(control, target)
        return
    if at_least:
        builder.cx(control, target)
    for u in range(lowest, value):
        builder.cx(_active(cursor, u, limit), target)


def build_eea_circuit(m: int, n: int, degree: int) -> km.Circuit:
    builder = km.CircuitBuilder()
    syndromes = [builder.create_quantum_register(degree, name=f'S{i}') for i in range(n)]
    error_mbuc = [builder.create_classical_register(degree, name=f'E{j}') for j in range(m)]
    EEABloq(n//2, degree).build_syndrome_decoding_mbuc(
        builder, syndromes=syndromes, error_mbuc=error_mbuc, n_iters=default_n_iters(n))
    return builder.finish_circuit()


if __name__ == '__main__':
    print("EEA Bloq with coefficient arrays and scaffold cache - complete")
    print("Test:", EEABloq(t=35, gf_degree=12).signature)