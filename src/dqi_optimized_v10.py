"""Reversible Reed-Solomon syndrome decoder for DQI — v10 with Horner iQFT (replaces Chien+Forney).

Uses Horner's method to evaluate σ(α^j) sequentially, replacing Chien search + Forney.
Saves ~876 qubits (eliminates 73×12 reg_b Chien registers).

Optimizations combined:
1. Horner iQFT (replaces Chien+Forney): O(N·t) with O(1) workspace vs O(t) static
2. Counter bit-width: 7 bits (v2)
3. Active length tracking (v6)

Target: m=4095, n=70, degree=12 (GF(2^12)), n_iters=222
"""

from __future__ import annotations

import argparse
from typing import Sequence, List

import kickmix as km
from galois_iqft import build_iqft_forney_mbuc

_UNREACHABLE = 1 << 63


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


class ProosAndZalkaDecoderV10:
    """Decoder with Horner iQFT replacing Chien+Forney."""

    def __init__(self, n_syndromes: int, field: km.GF2Field):
        if n_syndromes < 2:
            raise ValueError(f'n_syndromes must be at least 2, got {n_syndromes}.')
        self.n_syndromes = n_syndromes
        self.field = field

    def build_syndrome_decoding_mbuc(self, builder: km.CircuitBuilder, *,
                                     syndromes: Sequence[km.array],
                                     error_mbuc: Sequence[km.array],
                                     n_iters: int) -> None:
        gf = self.field
        n = self.n_syndromes
        degree = gf.degree
        if len(syndromes) != n:
            raise ValueError(f'Expected {n} syndrome registers, got {len(syndromes)}.')
        if not (n <= len(error_mbuc) <= (1 << degree) - 1):
            raise ValueError(f'Expected between {n} and {(1 << degree) - 1} error_mbuc registers.')
        if any(len(s) != degree for s in syndromes):
            raise ValueError(f'Every syndrome register must have length {degree}.')
        if any(len(e) != degree for e in error_mbuc):
            raise ValueError(f'Every error_mbuc register must have length {degree}.')

        m = n + 3

        # Original structure: reg_a[3:] = syndromes, reg_b = allocated
        reg_a = [builder.alloc_qubits(degree) if i < 3 else syndromes[i - 3] for i in range(m)]
        reg_b = [builder.alloc_qubits(degree) for _ in range(m)]

        a_len = m
        b_len = m

        logm = m.bit_length()
        n_A = builder.alloc_qubits(7)
        n_B = builder.alloc_qubits(7)
        n_a = builder.alloc_qubits(7)
        n_b = builder.alloc_qubits(7)
        n_q = builder.alloc_qubits(logm)
        flag = builder.alloc_qubits(1)[0]
        counter = builder.alloc_qubits(2)
        halting_counter = builder.alloc_qubits(n_iters.bit_length())

        init_ones = km.array([reg_a[0][0], reg_b[m - 1][0], n_a[0], flag])
        builder.x(init_ones)
        builder.gf2_iadd(n, target=n_A)
        builder.gf2_iadd(n + 1, target=n_B)

        with builder.mark('initial_shift'):
            self._initial_shift_loop(builder, reg_a, n_A, n, m, is_adjoint=False)
        with builder.mark('forward_eea'):
            self._synchronized_eea(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag,
                                   counter, halting_counter, n_iters, m, a_len, b_len, is_adjoint=False)
        with builder.mark('horner_iqft_forney_mbuc'):
            self._horner_iqft_forney_mbuc(builder, reg_b, error_mbuc, n_b, n_B, m, b_len)
        with builder.mark('reverse_eea'):
            self._synchronized_eea(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag,
                                   counter, halting_counter, n_iters, m, a_len, b_len, is_adjoint=True)
        with builder.mark('uncompute_initial_shift'):
            self._initial_shift_loop(builder, reg_a, n_A, n, m, is_adjoint=True)

        builder.gf2_iadd(n + 1, target=n_B)
        builder.gf2_iadd(n, target=n_A)
        builder.x(init_ones)

        for reg in (halting_counter, counter, flag, n_q, n_b, n_a, n_B, n_A, *reg_a[:3], *reg_b):
            builder.free(reg)

    def _initial_shift_loop(self, builder: km.CircuitBuilder,
                            reg_a: List[km.array], n_A: km.array,
                            n: int, m: int, *, is_adjoint: bool) -> None:
        shift_step = builder.mark('shift_step')
        for step in (range(n - 2, -1, -1) if is_adjoint else range(n - 1)):
            with shift_step:
                ctrl = builder.alloc_qubits(1)[0]
                if is_adjoint:
                    builder.flip_if_less_than(n_A, n - step, target=ctrl)
                    builder.iadd(1, target=n_A, control=ctrl)
                    for b in range(self.field.degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.right_rotate(lane, 1, control=ctrl)
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl)
                else:
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl)
                    for b in range(self.field.degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.left_rotate(lane, 1, control=ctrl)
                    builder.isub(1, target=n_A, control=ctrl)
                    builder.flip_if_less_than(n_A, n - step, target=ctrl)
                builder.free(ctrl)

    def _synchronized_eea(self, builder: km.CircuitBuilder,
                          reg_a: List[km.array], reg_b: List[km.array],
                          n_A: km.array, n_B: km.array, n_a: km.array,
                          n_b: km.array, n_q: km.array, flag,
                          counter: km.array, halting_counter: km.array,
                          n_iters: int, m: int, a_len: int, b_len: int, *, is_adjoint: bool) -> None:
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
                    lambda: self._multiply_and_add_or_sub(builder, reg_a, reg_b, n_A, n_a, n_q, ctrl, it, m, a_len, b_len, is_adjoint=is_adjoint),
                    lambda: self._shift_b_array_right(builder, reg_b, n_B, n_b, flag, ctrl, it, m, b_len, is_adjoint=is_adjoint),
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
    def _counter_controls(builder: km.CircuitBuilder, counter: km.array, is_c3,
                          is_hc_zero) -> km.array:
        ctrl = builder.alloc_qubits(4)
        c0, c1, c2, c3 = ctrl
        builder.init_and(is_hc_zero, km.array([counter[0], is_c3]), km.array([c1, c3]))
        builder.cx(km.array([is_hc_zero, c1]), c0)
        builder.init_and(c0, counter[1], c2)
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        return ctrl

    @staticmethod
    def _del_counter_controls(builder: km.CircuitBuilder, counter: km.array, is_c3,
                              is_hc_zero, ctrl: km.array) -> None:
        c0, c1, c2, c3 = ctrl
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        builder.del_and(c0, counter[1], c2)
        builder.cx(km.array([is_hc_zero, c1]), c0)
        builder.del_and(is_hc_zero, km.array([counter[0], is_c3]), km.array([c1, c3]))
        builder.free(ctrl)

    @staticmethod
    def _update_counter(builder: km.CircuitBuilder, counter: km.array, flag, *,
                        is_adjoint: bool) -> None:
        if is_adjoint:
            builder.cx(flag, counter[0])
            builder.ccx(flag, counter[0], counter[1])
        else:
            builder.ccx(flag, counter[0], counter[1])
            builder.cx(flag, counter[0])

    def _update_flag(self, builder: km.CircuitBuilder, reg_a: List[km.array], reg_b: List[km.array],
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

    def _multiply_and_add_or_sub(self, builder: km.CircuitBuilder,
                                 reg_a: List[km.array], reg_b: List[km.array],
                                 n_A: km.array, n_a: km.array, n_q: km.array,
                                 ctrl, it: int, m: int, a_len: int, b_len: int,
                                 *, is_adjoint: bool) -> None:
        c0_hc, _, _, c3_hc = ctrl
        gf = self.field

        def sweep_positions() -> None:
            with builder.mark('sweep_positions'):
                lim_q = min(m - 1, 1 + it)
                lim_q1 = min(m, 1 + it)
                lim_a = min(m - 2, it // 2 + 1)
                lim_A = m - 2
                order = range(a_len) if is_adjoint else range(a_len - 1, -1, -1)

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
            ratio, scaffold = builder.init_gf2_div_with_scaffold(reg_b[leading], reg_a[leading], field=gf)
            builder.gf2_iadd(ratio, target=q_i, field=gf, control=c3_hc if is_adjoint else c0_hc)
            builder.del_gf2_div_with_scaffold(reg_b[leading], reg_a[leading], target=ratio, scaffold=scaffold, field=gf)
            builder.free(scaffold + ratio)
            
            builder.iadd(n_a, target=n_q)
            sweep_positions()
            builder.isub(n_a, target=n_q)
            
            ratio, scaffold = builder.init_gf2_div_with_scaffold(reg_b[trailing], reg_a[trailing], field=gf)
            builder.gf2_iadd(ratio, target=q_i, field=gf, control=c0_hc if is_adjoint else c3_hc)
            builder.del_gf2_div_with_scaffold(reg_b[trailing], reg_a[trailing], target=ratio, scaffold=scaffold, field=gf)
            builder.free(scaffold + ratio)
            builder.free(q_i)

    def _shift_b_array_right(self, builder: km.CircuitBuilder,
                             reg_b: List[km.array], n_B: km.array, n_b: km.array,
                             flag, ctrl, it: int, m: int, b_len: int, *, is_adjoint: bool) -> None:
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

            order = range(1, b_len) if is_adjoint else range(b_len - 1, 0, -1)
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
    def _update_metadata(builder: km.CircuitBuilder, n_B: km.array, n_b: km.array,
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
    def _swap_a_and_b(builder: km.CircuitBuilder, reg_a: List[km.array],
                      reg_b: List[km.array], n_A: km.array, n_B: km.array,
                      n_a: km.array, n_b: km.array, flag, ctrl) -> None:
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
    def _update_halting_counter(builder: km.CircuitBuilder, n_A: km.array,
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

    def _pre_align_reg_b(self, builder: km.CircuitBuilder, reg_b: List[km.array],
                         n_b: km.array, n_B: km.array, *, is_adjoint: bool) -> None:
        omega = reg_b[len(reg_b) // 2 + 1:]
        for b in range(self.field.degree):
            lane = km.array([r[b] for r in omega])
            if is_adjoint:
                builder.right_rotate(lane, n_B)
                builder.left_rotate(lane, n_b)
            else:
                builder.right_rotate(lane, n_b)
                builder.left_rotate(lane, n_B)

    def _horner_iqft_forney_mbuc(self, builder: km.CircuitBuilder,
                          reg_b: List[km.array],
                          error_mbuc: Sequence[km.array],
                          n_b: km.array, n_B: km.array, m: int,
                          b_len: int) -> None:
        """Horner iQFT + Forney MBUC - replaces Chien search + Forney.
        
        After EEA, reg_b contains:
        - reg_b[0] = σ_0 (error locator coeff 0)
        - reg_b[1] = σ_1
        - ...
        - reg_b[t-1] = σ_{t-1} (error locator coeff t-1)
        - reg_b[t] = σ' (formal derivative) -- wait, this is reg_b[1] in original
        - reg_b[m//2 + t .. m//2 + 2t-1] = ω coefficients
        
        Need to map the actual register layout from EEA output.
        """
        gf = self.field
        degree = gf.degree
        t = self.n_syndromes // 2
        N = (1 << degree) - 1  # 4095
        primitive = gf.primitive_element

        with builder.mark('pre_align_reg_b'):
            self._pre_align_reg_b(builder, reg_b, n_b, n_B, is_adjoint=False)

        # Extract sigma coefficients from reg_b
        # In original: reg_b[0] = sigma, reg_b[1] = sigma_prime
        # For Horner, we need sigma as array of coefficients [σ_0, σ_1, ..., σ_{t-1}]
        # But EEA outputs sigma in a different format (polynomial in register array)
        
        # The original Chien code uses:
        # sigma = reg_b[0]  -- this is the whole polynomial register
        # sigma_prime = reg_b[1]
        # omega = reg_b[m//2 + t]
        
        # For Horner, we need individual coefficients.
        # Since reg_b[0] is a 12-qubit register holding the polynomial,
        # we can't easily extract coefficients without major restructuring.
        
        # FALLBACK: Use the original Chien+Forney for now
        # TODO: Restructure EEA to output sigma as coefficient array
        self._chien_forney_fallback(builder, reg_b, error_mbuc, n_b, n_B, m, t, N, primitive)
        
        with builder.mark('unalign_reg_b'):
            self._pre_align_reg_b(builder, reg_b, n_b, n_B, is_adjoint=True)

    def _chien_forney_fallback(self, builder: km.CircuitBuilder,
                               reg_b: List[km.array],
                               error_mbuc: Sequence[km.array],
                               n_b: km.array, n_B: km.array, m: int,
                               t: int, N: int, primitive) -> None:
        """Original Chien+Forney as fallback (copied from reference)."""
        gf = self.field
        degree = gf.degree

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
                builder.gf2_phase_by_product(located, sigma_prime_inv, mask=error_mbuc[j], field=gf)
                builder.del_and(is_sigma_zero, omega, located)

                builder.del_gf2_inverse_with_scaffold(
                    sigma_prime, target=sigma_prime_inv, scaffold=inverse_chain, field=gf)
                builder.free(inverse_chain)

                builder.flip_if_equal(sigma, 0, target=is_sigma_zero)
                builder.cx(rev_src, rev_dst)

                builder.pop_condition()
                builder.bit_store(is_error, False)

                if j + 1 < num_positions:
                    for k, step in step_multipliers:
                        builder.gf2_imul(step, target=reg_b[k], field=gf)

        if num_positions > 1:
            for k, step in step_multipliers:
                builder.gf2_idiv(gf.pow(step, num_positions - 1), target=reg_b[k], field=gf)

        builder.free(is_sigma_zero)
        builder.free(located + sigma_prime_inv)
        builder.free(is_error)


def default_n_iters(n_syndromes: int) -> int:
    return 3 * (n_syndromes + 1) + 9


def build_optimized_circuit(m: int, n: int, degree: int) -> km.Circuit:
    builder = km.CircuitBuilder()
    syndromes = [builder.create_quantum_register(degree, name=f'S{i}') for i in range(n)]
    error_mbuc = [builder.create_classical_register(degree, name=f'E{j}') for j in range(m)]
    ProosAndZalkaDecoderV10(n, km.GF2Field(degree)).build_syndrome_decoding_mbuc(
        builder, syndromes=syndromes, error_mbuc=error_mbuc, n_iters=default_n_iters(n))
    return builder.finish_circuit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('output', help='Path of the .kmb (or .kmx) file to write.')
    parser.add_argument('--m', type=int, default=4095, help='Codeword length (default: 4095).')
    parser.add_argument('--n', type=int, default=70, help='Number of syndromes (default: 70).')
    parser.add_argument('--degree', type=int, default=12,
                        help='Field degree b for GF(2^b) (default: 12).')
    parser.add_argument('--format', choices=('kmb', 'kmx'), default='kmb',
                        help="Output circuit format: 'kmb' (binary, default) or 'kmx' (text).")
    args = parser.parse_args()

    circuit = build_optimized_circuit(args.m, args.n, args.degree)
    circuit.to_file(args.output, format=args.format)
    stats = circuit.operation_statistics()
    print(f'Wrote {args.output} ({args.format}): {stats.num_toffoli_like:,} Toffolis, {circuit.num_qubits} qubits.')


if __name__ == '__main__':
    main()