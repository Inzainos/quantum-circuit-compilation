"""Mixed-radix Cooley-Tukey iQFT over GF(2^12) for N=4095=9×455.

Uses discrete log/exp tables for GF(2^12) arithmetic.
Multiplication becomes addition of exponents (mod 4095) - much cheaper than gf2_imul.
"""

from __future__ import annotations

from typing import List, Tuple, Sequence
import kickmix as km


class LogExpTables:
    """Precomputed log/exp tables for GF(2^m) arithmetic.
    
    For GF(2^12) with primitive element α:
    - exp_table[k] = α^k for k = 0..4094
    - log_table[x] = k where α^k = x, for x = 1..4095
    - log_table[0] = -1 (undefined)
    
    Operations:
    - mul(a, b) = exp[(log[a] + log[b]) % 4095]
    - div(a, b) = exp[(log[a] - log[b]) % 4095]
    - inv(a) = exp[(4095 - log[a]) % 4095]
    - pow(a, k) = exp[(log[a] * k) % 4095]
    """

    def __init__(self, field: km.GF2Field):
        self.field = field
        self.m = field.degree
        self.N = (1 << self.m) - 1  # 4095
        self.primitive = field.primitive_element
        
        # Build tables
        self._build_tables()
    
    def _build_tables(self) -> None:
        """Build log and exp tables using kickmix field operations."""
        # exp_table[k] = α^k
        self.exp_table = [0] * (self.N + 1)
        self.log_table = [-1] * (1 << self.m)
        
        val = 1
        for k in range(self.N):
            self.exp_table[k] = val
            self.log_table[val] = k
            # Multiply by primitive for next power
            # Use kickmix to compute next power
            val = self.field.pow(self.primitive, k + 1)
        
        # exp_table[N] = exp_table[0] = 1 for convenience
        self.exp_table[self.N] = 1
    
    def log(self, x: int) -> int:
        """Return log_α(x) for x ≠ 0."""
        if x == 0:
            raise ValueError("log(0) undefined")
        return self.log_table[x]
    
    def exp(self, k: int) -> int:
        """Return α^k."""
        return self.exp_table[k % self.N]
    
    def mul(self, a: int, b: int) -> int:
        """Multiply two field elements using log tables."""
        if a == 0 or b == 0:
            return 0
        return self.exp_table[(self.log_table[a] + self.log_table[b]) % self.N]
    
    def div(self, a: int, b: int) -> int:
        """Divide a/b."""
        if a == 0:
            return 0
        if b == 0:
            raise ValueError("Division by zero")
        return self.exp_table[(self.log_table[a] - self.log_table[b]) % self.N]
    
    def inv(self, a: int) -> int:
        """Inverse of a."""
        if a == 0:
            raise ValueError("Inverse of zero undefined")
        return self.exp_table[(self.N - self.log_table[a]) % self.N]
    
    def pow(self, a: int, k: int) -> int:
        """Raise a to power k."""
        if a == 0:
            return 0 if k > 0 else 1  # 0^0 = 1 convention
        return self.exp_table[(self.log_table[a] * k) % self.N]


class CooleyTukeyIQFT:
    """Mixed-radix Cooley-Tukey iQFT over GF(2^12) using log/exp tables.
    
    N = 4095 = 9 × 455 = 3² × 5 × 7 × 13
    Uses DIT (Decimation-In-Time) with log-table arithmetic.
    """

    def __init__(self, builder: km.CircuitBuilder, field: km.GF2Field):
        self.builder = builder
        self.field = field
        self.m = field.degree  # 12
        self.N = (1 << self.m) - 1  # 4095
        self.primitive = field.primitive_element
        
        # Mixed-radix factors
        self.N1 = 9      # 3²
        self.N2 = 455    # 5 × 7 × 13
        assert self.N1 * self.N2 == self.N
        
        # Log/exp tables for fast arithmetic
        self.tables = LogExpTables(field)
        
        # Primitive N-th root of unity ω = α
        self.omega = self.primitive
        # For iQFT, use ω⁻¹
        self.omega_inv = self.tables.exp(self.N - 1)  # α⁻¹
        
        # Roots of unity for sub-transforms
        # ω_N1 = ω^N2 = α^455 (primitive 9th root)
        # ω_N2 = ω^N1 = α^9 (primitive 455th root)
        self.omega_N1 = self.tables.exp(self.N2)
        self.omega_N2 = self.tables.exp(self.N1)
        
        # For iQFT, use inverses
        self.omega_N1_inv = self.tables.exp((self.N1 - 1) * self.N2)  # (α^455)^8
        self.omega_N2_inv = self.tables.exp((self.N2 - 1) * self.N1)  # (α^9)^454
        
        # Precompute DFT roots using log arithmetic
        self._dft9_roots = [[self._dft_root(k, n, self.N1, self.omega_N1_inv) 
                              for n in range(self.N1)] for k in range(self.N1)]
        self._dft455_roots = [[self._dft_root(k, n, self.N2, self.omega_N2_inv) 
                                for n in range(self.N2)] for k in range(self.N2)]
        
        # Precompute twiddle factors: ω^(-k1·n2) = (ω^N2)^(-k1·n2) = ω_N1^(-k1·n2)
        self._twiddle = [[self._dft_root(k1, n2, self.N1, self.omega_N1_inv) 
                           for n2 in range(self.N2)] for k1 in range(self.N1)]

    def _dft_root(self, k: int, n: int, N: int, root: int) -> int:
        """Compute root^(k·n mod N) using log arithmetic."""
        if k == 0 or n == 0:
            return 1
        log_root = self.tables.log(root)
        exp = (log_root * (k * n % N)) % self.N
        return self.tables.exp(exp)

    def _gf2_add_reg(self, target: km.array, source: km.array) -> None:
        self.builder.gf2_iadd(source, target=target, field=self.field)

    def _gf2_mul_reg_const(self, target: km.array, const: int) -> None:
        """Multiply register by constant using kickmix gf2_imul."""
        if const != 1:
            self.builder.gf2_imul(const, target=target, field=self.field)

    def _dft_direct(self, inputs: List[km.array], outputs: List[km.array],
                    roots: List[List[int]], inverse: bool = False) -> None:
        """Direct DFT using precomputed roots with log-table multiplication."""
        n = len(inputs)
        for k in range(n):
            if k == 0:
                # X[0] = Σ x[n]
                self.builder.cx(inputs[0], outputs[k])
                for j in range(1, n):
                    self._gf2_add_reg(outputs[k], inputs[j])
            else:
                temp = self.builder.alloc_qubits(self.m)
                for j in range(n):
                    self.builder.cx(inputs[j], temp)
                    self._gf2_mul_reg_const(temp, roots[k][j])
                    self._gf2_add_reg(outputs[k], temp)
                self.builder.free(temp)

    def _multiply_twiddle(self, reg: km.array, k1: int, n2: int) -> None:
        """Multiply register by twiddle factor using log tables."""
        factor = self._twiddle[k1][n2]
        self._gf2_mul_reg_const(reg, factor)

    def iqft_mixed_radix(self, input_regs: List[km.array], 
                         output_regs: List[km.array]) -> None:
        """Mixed-radix DIT iQFT: N = 9 × 455.
        
        Input: input_regs[n] for n=0..N-1, where n = n1 + 9*n2
        Output: output_regs[k] for k=0..N-1, where k = k2 + 455*k1
        """
        # Step 0: Reorder input to [n1][n2] layout
        stage1 = [[self.builder.alloc_qubits(self.m) for _ in range(self.N2)] 
                  for _ in range(self.N1)]
        
        for n1 in range(self.N1):
            for n2 in range(self.N2):
                n = n1 + self.N1 * n2
                self.builder.cx(input_regs[n], stage1[n1][n2])
        
        # Step 1: N2 DFTs of size N1 (along n1 for each n2)
        stage2 = [[self.builder.alloc_qubits(self.m) for _ in range(self.N1)] 
                  for _ in range(self.N2)]
        
        for n2 in range(self.N2):
            self._dft_direct(
                [stage1[n1][n2] for n1 in range(self.N1)],
                [stage2[n2][k1] for k1 in range(self.N1)],
                self._dft9_roots,
                inverse=False
            )
        
        # Free stage1
        for row in stage1:
            for reg in row:
                self.builder.free(reg)
        
        # Step 2: Multiply by twiddle factors
        for n2 in range(self.N2):
            for k1 in range(self.N1):
                self._multiply_twiddle(stage2[n2][k1], k1, n2)
        
        # Step 3: N1 DFTs of size N2 (along n2 for each k1)
        stage3 = [[self.builder.alloc_qubits(self.m) for _ in range(self.N2)] 
                  for _ in range(self.N1)]
        
        for k1 in range(self.N1):
            self._dft_direct(
                [stage2[n2][k1] for n2 in range(self.N2)],
                [stage3[k1][k2] for k2 in range(self.N2)],
                self._dft455_roots,
                inverse=False
            )
        
        # Free stage2
        for row in stage2:
            for reg in row:
                self.builder.free(reg)
        
        # Step 4: Reorder output to linear layout
        for k1 in range(self.N1):
            for k2 in range(self.N2):
                k = k2 + self.N2 * k1
                self.builder.cx(stage3[k1][k2], output_regs[k])
        
        # Free stage3
        for row in stage3:
            for reg in row:
                self.builder.free(reg)

    def build_iqft(self, coeffs: List[km.array], 
                   evals: List[km.array],
                   pad_to_N: bool = True) -> None:
        """Build iQFT from coefficient array to evaluation array."""
        N = self.N
        if pad_to_N:
            input_regs = []
            for i in range(N):
                reg = self.builder.alloc_qubits(self.m)
                if i < len(coeffs):
                    self.builder.cx(coeffs[i], reg)
                input_regs.append(reg)
        else:
            input_regs = coeffs + [self.builder.alloc_qubits(self.m) for _ in range(N - len(coeffs))]
        
        self.iqft_mixed_radix(input_regs, evals)
        
        for reg in input_regs:
            if pad_to_N or len(coeffs) <= N:
                self.builder.free(reg)


def build_iqft_forney_mbuc(builder: km.CircuitBuilder, field: km.GF2Field,
                           sigma_coeffs: List[km.array],
                           sigma_prime_coeffs: List[km.array],
                           omega_coeffs: List[km.array],
                           error_mbuc: Sequence[km.array],
                           t: int, m: int, degree: int,
                           num_positions: int,
                           is_error: km.array,
                           is_sigma_zero: km.array) -> None:
    """Build complete iQFT + Forney MBUC circuit using mixed-radix Cooley-Tukey."""
    gf = field
    N = (1 << degree) - 1
    iqft = CooleyTukeyIQFT(builder, gf)
    
    # Allocate evaluation arrays
    sigma_evals = [builder.alloc_qubits(degree) for _ in range(N)]
    sigma_prime_evals = [builder.alloc_qubits(degree) for _ in range(N)]
    omega_evals = [builder.alloc_qubits(degree) for _ in range(N)]
    
    # Run iQFT for all three polynomials
    with builder.mark('iqft_sigma'):
        iqft.build_iqft(sigma_coeffs, sigma_evals)
    with builder.mark('iqft_sigma_prime'):
        iqft.build_iqft(sigma_prime_coeffs, sigma_prime_evals)
    with builder.mark('iqft_omega'):
        iqft.build_iqft(omega_coeffs, omega_evals)
    
    # Apply Forney phase at each position
    for j in range(num_positions):
        with builder.mark(f'forney_step_{j}'):
            builder.bit_store(is_error[0], True, control=error_mbuc[j])
            builder.push_condition(is_error[0])
            
            # Check if sigma(α^j) == 0
            builder.flip_if_equal(sigma_evals[j], 0, target=is_sigma_zero)
            
            # Forney phase: e_j = omega(α^j) / sigma_prime(α^j)
            sigma_prime_inv = builder.alloc_qubits(degree)
            located = builder.alloc_qubits(degree)
            
            _, inverse_chain = builder.init_gf2_inverse_with_scaffold(
                sigma_prime_evals[j], target=sigma_prime_inv, field=gf)
            
            builder.init_and(is_sigma_zero, omega_evals[j], located)
            builder.gf2_phase_by_product(located, sigma_prime_inv,
                                         mask=error_mbuc[j], field=gf)
            builder.del_and(is_sigma_zero, omega_evals[j], located)
            
            builder.del_gf2_inverse_with_scaffold(
                sigma_prime_evals[j], target=sigma_prime_inv, scaffold=inverse_chain, field=gf)
            builder.free(inverse_chain)
            builder.free(sigma_prime_inv + located)
            
            builder.pop_condition()
            builder.bit_store(is_error[0], False)
    
    # Free evaluation arrays
    for reg in sigma_evals + sigma_prime_evals + omega_evals:
        builder.free(reg)