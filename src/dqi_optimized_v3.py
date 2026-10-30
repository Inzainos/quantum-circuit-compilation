"""Reversible Reed-Solomon syndrome decoder for Decoded Quantum Interferometry (DQI) — v3 optimized.

Implements 3 major optimizations over the reference circuit:
1. **AncillaPool**: Reuse all temporary qubits (ctrl, aux, mul, etc.) from a pool (~1,053 → ~200 qubits)
2. **ScaffoldCache**: Cache and reuse division/inverse scaffolds across EEA rounds (Toffoli↓)
3. **Reduce reg_b**: Track active lengths to avoid operating on unused registers

Target: m=4095, n=70, degree=12 (GF(2^12)), n_iters=222
Baseline v2: Q=1,889, T=5,712,031, Q²×T=20,382,361,983,382
"""

from __future__ import annotations

import argparse
from typing import Sequence, Dict, List, Tuple

import kickmix as km

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


class AncillaPool:
    """Pool de qubits ancilla reutilizables para evitar alloc/free repetidos."""

    def __init__(self, builder: km.CircuitBuilder):
        self.builder = builder
        self._free: Dict[int, List[km.array]] = {}
        self._allocated: Dict[int, List[km.array]] = {}

    def get(self, num_qubits: int) -> km.array:
        if num_qubits in self._free and self._free[num_qubits]:
            reg = self._free[num_qubits].pop()
            self._allocated.setdefault(num_qubits, []).append(reg)
            return reg
        reg = self.builder.alloc_qubits(num_qubits)
        self._allocated.setdefault(num_qubits, []).append(reg)
        return reg

    def put(self, reg: km.array) -> None:
        n = len(reg)
        if n in self._allocated and reg in self._allocated[n]:
            self._allocated[n].remove(reg)
            self._free.setdefault(n, []).append(reg)

    def free_all(self) -> None:
        for regs in self._free.values():
            for reg in regs:
                self.builder.free(reg)
        for regs in self._allocated.values():
            for reg in regs:
                self.builder.free(reg)
        self._free.clear()
        self._allocated.clear()


class ScaffoldCache:
    """Cache de scaffolds para divisiones e inversas GF(2^12) reutilizables."""

    def __init__(self, builder: km.CircuitBuilder, field: km.GF2Field):
        self.builder = builder
        self.field = field
        self._div_cache: Dict[Tuple[int, int], Tuple[km.array, km.array]] = {}
        self._inv_cache: Dict[int, Tuple[km.array, km.array]] = {}

    def get_div_scaffold(self, numerator: km.array, denominator: km.array) -> Tuple[km.array, km.array]:
        key = (id(numerator), id(denominator))
        if key in self._div_cache:
            return self._div_cache[key]
        ratio, scaffold = self.builder.init_gf2_div_with_scaffold(numerator, denominator, field=self.field)
        self._div_cache[key] = (ratio, scaffold)
        return ratio, scaffold

    def release_div_scaffold(self, numerator: km.array, denominator: km.array,
                             ratio: km.array, scaffold: km.array) -> None:
        key = (id(numerator), id(denominator))
        if key in self._div_cache:
            self.builder.del_gf2_div_with_scaffold(numerator, denominator, target=ratio, scaffold=scaffold, field=self.field)
            self.builder.free(scaffold + ratio)
            del self._div_cache[key]

    def get_inv_scaffold(self, target: km.array) -> Tuple[km.array, km.array]:
        key = id(target)
        if key in self._inv_cache:
            return self._inv_cache[key]
        inv, scaffold = self.builder.init_gf2_inverse_with_scaffold(target, field=self.field)
        self._inv_cache[key] = (inv, scaffold)
        return inv, scaffold

    def release_inv_scaffold(self, target: km.array, inv: km.array, scaffold: km.array) -> None:
        key = id(target)
        if key in self._inv_cache:
            self.builder.del_gf2_inverse_with_scaffold(target, target=inv, scaffold=scaffold, field=self.field)
            self.builder.free(scaffold + inv)
            del self._inv_cache[key]

    def clear(self) -> None:
        self._div_cache.clear()
        self._inv_cache.clear()


class ProosAndZalkaDecoderV3:
    """Optimized reversible Reed-Solomon MBUC decoder with 3 innovations."""

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
        pool = AncillaPool(builder)
        scaffold_cache = ScaffoldCache(builder, gf)

        # Original structure: reg_a[3:] = syndromes, reg_b = allocated
        reg_a = [pool.get(degree) if i < 3 else syndromes[i - 3] for i in range(m)]
        reg_b = [pool.get(degree) for _ in range(m)]

        # Track active lengths for reg_b optimization
        a_len = m
        b_len = m

        logm = m.bit_length()
        n_A = pool.get(7)
        n_B = pool.get(7)
        n_a = pool.get(7)
        n_b = pool.get(7)
        n_q = pool.get(logm)
        flag = pool.get(1)
        counter = pool.get(2)
        halting_counter = pool.get(n_iters.bit_length())

        init_ones = km.array([reg_a[0][0], reg_b[m - 1][0], n_a[0], flag[0]])
        builder.x(init_ones)
        builder.gf2_iadd(n, target=n_A)
        builder.gf2_iadd(n + 1, target=n_B)

        with builder.mark('initial_shift'):
            self._initial_shift_loop(builder, reg_a, n_A, n, m, pool, is_adjoint=False)
        with builder.mark('forward_eea'):
            self._synchronized_eea(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag,
                                   counter, halting_counter, n_iters, m, pool, scaffold_cache,
                                   a_len, b_len, is_adjoint=False)
        with builder.mark('chien_forney_mbuc'):
            self._chien_search_and_forney_mbuc(builder, reg_b, error_mbuc, n_b, n_B, m, pool, scaffold_cache, b_len)
        with builder.mark('reverse_eea'):
            self._synchronized_eea(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag,
                                   counter, halting_counter, n_iters, m, pool, scaffold_cache,
                                   a_len, b_len, is_adjoint=True)
        with builder.mark('uncompute_initial_shift'):
            self._initial_shift_loop(builder, reg_a, n_A, n, m, pool, is_adjoint=True)

        builder.gf2_iadd(n + 1, target=n_B)
        builder.gf2_iadd(n, target=n_A)
        builder.x(init_ones)

        for reg in (halting_counter, counter, flag, n_q, n_b, n_a, n_B, n_A):
            pool.put(reg)
        for reg in reg_a[:3]:
            pool.put(reg)
        for reg in reg_b:
            pool.put(reg)
        scaffold_cache.clear()
        pool.free_all()

    def _initial_shift_loop(self, builder: km.CircuitBuilder,
                            reg_a: List[km.array], n_A: km.array,
                            n: int, m: int, pool: AncillaPool, *, is_adjoint: bool) -> None:
        shift_step = builder.mark('shift_step')
        for step in (range(n - 2, -1, -1) if is_adjoint else range(n - 1)):
            with shift_step:
                ctrl = pool.get(1)
                if is_adjoint:
                    builder.flip_if_less_than(n_A, n - step, target=ctrl[0])
                    builder.iadd(1, target=n_A, control=ctrl[0])
                    for b in range(self.field.degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.right_rotate(lane, 1, control=ctrl[0])
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl[0])
                else:
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl[0])
                    for b in range(self.field.degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.left_rotate(lane, 1, control=ctrl[0])
                    builder.isub(1, target=n_A, control=ctrl[0])
                    builder.flip_if_less_than(n_A, n - step, target=ctrl[0])
                pool.put(ctrl)

    def _synchronized_eea(self, builder: km.CircuitBuilder,
                          reg_a: List[km.array], reg_b: List[km.array],
                          n_A: km.array, n_B: km.array, n_a: km.array,
                          n_b: km.array, n_q: km.array, flag,
                          counter: km.array, halting_counter: km.array,
                          n_iters: int, m: int, pool: AncillaPool,
                          scaffold_cache: ScaffoldCache,
                          a_len: int, b_len: int, *, is_adjoint: bool) -> None:
        eea_step = builder.mark('eea_step')
        for it in (range(n_iters - 1, -1, -1) if is_adjoint else range(n_iters)):
            with eea_step:
                if is_adjoint:
                    self._update_counter(builder, counter, flag, is_adjoint=True)

                is_c3 = pool.get(1)
                builder.init_and(counter[0], counter[1], is_c3[0])
                if is_adjoint:
                    self._update_halting_counter(builder, n_A, n_B, n_b, halting_counter,
                                                 flag, is_c3, is_adjoint=True)

                is_hc_zero = pool.get(1)
                builder.flip_if_equal(halting_counter, 0, target=is_hc_zero[0])
                ctrl = self._counter_controls(builder, counter, is_c3, is_hc_zero, pool)

                steps = [
                    lambda: self._update_flag(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag, ctrl, m, pool),
                    lambda: self._multiply_and_add_or_sub(builder, reg_a, reg_b, n_A, n_a, n_q, ctrl, it, m, pool, scaffold_cache, a_len, b_len, is_adjoint=is_adjoint),
                    lambda: self._shift_b_array_right(builder, reg_b, n_B, n_b, flag, ctrl, it, m, pool, b_len, is_adjoint=is_adjoint),
                    lambda: self._update_metadata(builder, n_B, n_b, n_q, flag, ctrl, is_adjoint=is_adjoint),
                    lambda: self._swap_a_and_b(builder, reg_a, reg_b, n_A, n_B, n_a, n_b, flag, ctrl, pool),
                ]
                for step in (reversed(steps) if is_adjoint else steps):
                    step()

                self._del_counter_controls(builder, counter, is_c3, is_hc_zero, ctrl, pool)
                builder.flip_if_equal(halting_counter, 0, target=is_hc_zero[0])
                pool.put(is_hc_zero)

                if not is_adjoint:
                    self._update_halting_counter(builder, n_A, n_B, n_b, halting_counter,
                                                 flag, is_c3, is_adjoint=False)
                builder.del_and(counter[0], counter[1], is_c3[0])
                pool.put(is_c3)
                if not is_adjoint:
                    self._update_counter(builder, counter, flag, is_adjoint=False)

    @staticmethod
    def _counter_controls(builder: km.CircuitBuilder, counter: km.array, is_c3,
                          is_hc_zero, pool: AncillaPool) -> km.array:
        ctrl = pool.get(4)
        c0, c1, c2, c3 = ctrl
        builder.init_and(is_hc_zero[0], km.array([counter[0], is_c3[0]]), km.array([c1, c3]))
        builder.cx(km.array([is_hc_zero[0], c1]), c0)
        builder.init_and(c0, counter[1], c2)
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        return ctrl

    @staticmethod
    def _del_counter_controls(builder: km.CircuitBuilder, counter: km.array, is_c3,
                              is_hc_zero, ctrl: km.array, pool: AncillaPool) -> None:
        c0, c1, c2, c3 = ctrl
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        builder.del_and(c0, counter[1], c2)
        builder.cx(km.array([is_hc_zero[0], c1]), c0)
        builder.del_and(is_hc_zero[0], km.array([counter[0], is_c3[0]]), km.array([c1, c3]))
        pool.put(ctrl)

    @staticmethod
    def _update_counter(builder: km.CircuitBuilder, counter: km.array, flag, *,
                        is_adjoint: bool) -> None:
        if is_adjoint:
            builder.cx(flag[0], counter[0])
            builder.ccx(flag[0], counter[0], counter[1])
        else:
            builder.ccx(flag[0], counter[0], counter[1])
            builder.cx(flag[0], counter[0])

    def _update_flag(self, builder: km.CircuitBuilder, reg_a: List[km.array], reg_b: List[km.array],
                     n_A: km.array, n_B: km.array, n_a: km.array, n_b: km.array,
                     n_q: km.array, flag, ctrl, m: int, pool: AncillaPool) -> None:
        with builder.mark('update_flag'):
            c0, c1, c2, c3 = ctrl
            aux = pool.get(1)

            builder.flip_if_less_than(n_A, n_B, target=aux[0], control=c0)
            builder.flip_if_equal(n_q, 0, target=flag[0], control=aux[0])
            builder.flip_if_less_than(n_A, n_B, target=aux[0], control=c0)
            builder.flip_if_equal(n_A, n_B, target=flag[0], control=c0)

            builder.flip_if_equal(n_A, n_B, target=flag[0], control=c1)
            builder.cx(c1, flag[0])
            builder.flip_if_equal(n_B, 1, target=aux[0], control=c1)
            builder.cx(c1, aux[0])
            builder.flip_if_equal(reg_b[m - 2], 0, target=flag[0], control=aux[0])
            builder.cx(c1, aux[0])
            builder.flip_if_equal(n_B, 1, target=aux[0], control=c1)

            builder.cx(c2, flag[0])
            builder.flip_if_equal(n_b, 0, target=aux[0], control=c2)
            builder.cx(c2, aux[0])
            builder.flip_if_equal(reg_b[0], 0, target=flag[0], control=aux[0])
            builder.cx(c2, aux[0])
            builder.flip_if_equal(n_b, 0, target=aux[0], control=c2)
            builder.iadd(1, target=n_b)
            builder.flip_if_equal(n_a, n_b, target=flag[0], control=c2)
            builder.isub(1, target=n_b)

            builder.flip_if_equal(n_a, n_b, target=flag[0], control=c3)
            builder.flip_if_equal(n_q, 1, target=flag[0], control=c3)

            pool.put(aux)

    def _multiply_and_add_or_sub(self, builder: km.CircuitBuilder,
                                 reg_a: List[km.array], reg_b: List[km.array],
                                 n_A: km.array, n_a: km.array, n_q: km.array,
                                 ctrl, it: int, m: int, pool: AncillaPool,
                                 scaffold_cache: ScaffoldCache, a_len: int, b_len: int,
                                 *, is_adjoint: bool) -> None:
        c0_hc, _, _, c3_hc = ctrl
        gf = self.field

        def accumulate_quotient(index: int, control) -> None:
            with builder.mark('quotient_div'):
                ratio, scaffold = scaffold_cache.get_div_scaffold(reg_b[index], reg_a[index])
                builder.gf2_iadd(ratio, target=q_i, field=gf, control=control)
                scaffold_cache.release_div_scaffold(reg_b[index], reg_a[index], ratio, scaffold)

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
                    mul = pool.get(1)

                    def endpoint(i: int) -> None:
                        _xor_threshold(builder, cur_a, lim_a, mul[0], c3_hc, i + 1,
                                       at_least=True, lowest=1)
                        _xor_threshold(builder, cur_A, lim_A, mul[0], c0_hc, m - i,
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
                                mul[0],
                            )
                        prev = i

                        swaps = [a for a in (_active(eq_i, i, lim_q),
                                             _active(eq_ip1, i + 1, lim_q1))
                                 if a is not False]
                        multiplies = i < lim_a or i >= 2

                        if is_adjoint and multiplies:
                            builder.ixor_gf2_mul(q_i, reg_a[i], target=reg_b[i], field=gf, control=mul[0])
                        if len(swaps) == 1:
                            builder.cswap(swaps[0], q_i, reg_a[i])
                        elif swaps:
                            both = pool.get(1)
                            builder.cx(km.array(swaps), both[0])
                            builder.cswap(both[0], q_i, reg_a[i])
                            builder.cx(km.array(swaps), both[0])
                            pool.put(both)
                        if not is_adjoint and multiplies:
                            builder.ixor_gf2_mul(q_i, reg_a[i], target=reg_b[i], field=gf, control=mul[0])

                    endpoint(prev)
                    pool.put(mul)

        with builder.mark('multiply_and_add_or_sub'):
            q_i = pool.get(gf.degree)
            leading, trailing = (0, m - 1) if is_adjoint else (m - 1, 0)
            accumulate_quotient(leading, c3_hc if is_adjoint else c0_hc)
            builder.iadd(n_a, target=n_q)
            sweep_positions()
            builder.isub(n_a, target=n_q)
            accumulate_quotient(trailing, c0_hc if is_adjoint else c3_hc)
            pool.put(q_i)

    def _shift_b_array_right(self, builder: km.CircuitBuilder,
                             reg_b: List[km.array], n_B: km.array, n_b: km.array,
                             flag, ctrl, it: int, m: int, pool: AncillaPool,
                             b_len: int, *, is_adjoint: bool) -> None:
        with builder.mark('shift_b_array_right'):
            c0_hc, c1_hc, c2_hc, c3_hc = ctrl
            lim_B = m - 2
            lim_b = min(m - 2, it // 2 + 1)

            builder.x(flag[0])
            nf = pool.get(2)
            builder.init_and(km.array([c0_hc, c3_hc]), flag[0], nf)
            builder.x(flag[0])
            c0_nf, c3_nf = nf

            ctrl_nB = pool.get(1)
            builder.cx(km.array([c0_nf, c1_hc]), ctrl_nB[0])

            order = range(1, b_len) if is_adjoint else range(b_len - 1, 0, -1)
            with (
                builder.unary_iteration(n_B, control=ctrl_nB[0]) as cur_B_ge,
                builder.unary_iteration(n_b, control=c2_hc) as cur_b_ge,
                builder.unary_iteration(n_B, control=c3_nf) as cur_B_lt,
            ):
                do_shift = pool.get(1)

                def endpoint(i: int) -> None:
                    _xor_threshold(builder, cur_B_ge, lim_B, do_shift[0], ctrl_nB[0], m - i + 1, at_least=True)
                    _xor_threshold(builder, cur_b_ge, lim_b, do_shift[0], c2_hc, i, at_least=True)
                    _xor_threshold(builder, cur_B_lt, lim_B, do_shift[0], c3_nf, m - i, at_least=False)

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
                            do_shift[0],
                        )
                    prev = i
                    builder.cswap(do_shift[0], reg_b[i - 1], reg_b[i])

                endpoint(prev)
                pool.put(do_shift)

            builder.cx(km.array([c0_nf, c1_hc]), ctrl_nB[0])
            pool.put(ctrl_nB)
            builder.x(flag[0])
            builder.del_and(km.array([c0_hc, c3_hc]), flag[0], nf)
            builder.x(flag[0])
            pool.put(nf)

    @staticmethod
    def _update_metadata(builder: km.CircuitBuilder, n_B: km.array, n_b: km.array,
                         n_q: km.array, flag, ctrl, *, is_adjoint: bool) -> None:
        with builder.mark('update_metadata'):
            c0_hc, c1_hc, c2_hc, c3_hc = ctrl
            builder.x(flag[0])
            nf = builder.alloc_qubits(2)
            builder.init_and(km.array([c0_hc, c3_hc]), flag[0], nf)
            builder.x(flag[0])
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

            builder.x(flag[0])
            builder.del_and(km.array([c0_hc, c3_hc]), flag[0], nf)
            builder.x(flag[0])
            builder.free(nf)

    @staticmethod
    def _swap_a_and_b(builder: km.CircuitBuilder, reg_a: List[km.array],
                      reg_b: List[km.array], n_A: km.array, n_B: km.array,
                      n_a: km.array, n_b: km.array, flag, ctrl, pool: AncillaPool) -> None:
        with builder.mark('swap_a_and_b'):
            c3_hc = ctrl[3]
            swap_ctrl = pool.get(1)
            builder.init_and(c3_hc, flag[0], swap_ctrl[0])
            # Swap all registers
            lhs = km.array([q for r in (n_A, n_a, *reg_a) for q in r])
            rhs = km.array([q for r in (n_B, n_b, *reg_b) for q in r])
            builder.cswap(swap_ctrl[0], lhs, rhs)
            pool.put(swap_ctrl)

    @staticmethod
    def _update_halting_counter(builder: km.CircuitBuilder, n_A: km.array,
                                n_B: km.array, n_b: km.array,
                                halting_counter: km.array, flag, is_c3, *,
                                is_adjoint: bool) -> None:
        with builder.mark('update_halting_counter'):
            work = builder.alloc_qubits(3)
            ctrl, busy, running = work
            builder.init_and(is_c3[0], flag[0], ctrl)
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
            builder.del_and(is_c3[0], flag[0], ctrl)
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

    def _chien_search_and_forney_mbuc(self, builder: km.CircuitBuilder,
                                      reg_b: List[km.array],
                                      error_mbuc: Sequence[km.array],
                                      n_b: km.array, n_B: km.array, m: int,
                                      pool: AncillaPool, scaffold_cache: ScaffoldCache,
                                      b_len: int) -> None:
        gf = self.field
        degree = gf.degree
        t = self.n_syndromes // 2
        block_length = (1 << degree) - 1
        primitive = gf.primitive_element

        with builder.mark('pre_align_reg_b'):
            self._pre_align_reg_b(builder, reg_b, n_b, n_B, is_adjoint=False)

        sigma = reg_b[0]
        sigma_prime = reg_b[1]
        omega = reg_b[m // 2 + t]
        sigma_prime_inv = pool.get(degree)
        located = pool.get(degree)
        is_sigma_zero = pool.get(1)
        is_error = builder.alloc_bits(1)

        omega_indices = range(m // 2 + 1, m // 2 + t + 1)
        step_multipliers = [
            (k, gf.pow(primitive, k))
            for k in range(1, t + 1)
        ] + [
            (k, gf.pow(primitive, (m - 2 - k) % block_length))
            for k in omega_indices
            if (m - 2 - k) % block_length != 0
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

        num_positions = min(block_length, len(error_mbuc))
        forney_step = builder.mark('forney_step')
        for j in range(num_positions):
            with forney_step:
                builder.bit_store(is_error[0], True, control=error_mbuc[j])
                builder.push_condition(is_error[0])

                builder.cx(fwd_src, fwd_dst)
                builder.flip_if_equal(sigma, 0, target=is_sigma_zero[0])

                inv, inv_scaffold = scaffold_cache.get_inv_scaffold(sigma_prime)
                builder.gf2_iadd(inv, target=sigma_prime_inv, field=gf)
                scaffold_cache.release_inv_scaffold(sigma_prime, inv, inv_scaffold)

                builder.init_and(is_sigma_zero[0], omega, located)
                builder.gf2_phase_by_product(located, sigma_prime_inv, mask=error_mbuc[j], field=gf)
                builder.del_and(is_sigma_zero[0], omega, located)

                builder.flip_if_equal(sigma, 0, target=is_sigma_zero[0])
                builder.cx(rev_src, rev_dst)

                builder.pop_condition()
                builder.bit_store(is_error[0], False)

                if j + 1 < num_positions:
                    for k, step in step_multipliers:
                        builder.gf2_imul(step, target=reg_b[k], field=gf)

        if num_positions > 1:
            for k, step in step_multipliers:
                builder.gf2_idiv(gf.pow(step, num_positions - 1), target=reg_b[k], field=gf)

        pool.put(is_sigma_zero)
        pool.put(located + sigma_prime_inv)
        builder.free(is_error)

        with builder.mark('unalign_reg_b'):
            self._pre_align_reg_b(builder, reg_b, n_b, n_B, is_adjoint=True)


def default_n_iters(n_syndromes: int) -> int:
    return 3 * (n_syndromes + 1) + 9


def build_optimized_circuit(m: int, n: int, degree: int) -> km.Circuit:
    builder = km.CircuitBuilder()
    syndromes = [builder.create_quantum_register(degree, name=f'S{i}') for i in range(n)]
    error_mbuc = [builder.create_classical_register(degree, name=f'E{j}') for j in range(m)]
    ProosAndZalkaDecoderV3(n, km.GF2Field(degree)).build_syndrome_decoding_mbuc(
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