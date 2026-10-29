#!/usr/bin/env python3
"""
Generador de circuito DQI optimizado (Benchmark II — Combinatorial Optimization).

Implementa el decodador Reed-Solomon MBUC basado en
`verifiers/dqi/dqi_reference_circuit.py` (ProosAndZalkaDecoder, ya verificado)
con las siguientes optimizaciones para reducir Q (qubits):

  1. **Contadores reducidos** (optimizacion 3): n_A, n_B, n_a, n_b usan 7 bits
     (max 73) en vez de 8; n_q usa 8 bits (max 222). counter=2 bits, flag=1 bit,
     halting_counter=8 bits. Total contadores: 5*7 + 1 + 2 + 8 = 46 (vs 51
     baseline). Ahorro: 5 qubits.

  2. **Scaffolds reusables** (optimizacion 2): en `init_gf2_div_with_scaffold`,
     el scaffold se reutiliza entre divisiones consecutivas del EEA en lugar de
     recomputarse. Esto reduce Toffolis (T) sin cambiar Q.

  Nota: Las optimizaciones de reducir `reg_b` (73 registros) y pool de ancillas
  requieren cambios estructurales mayores en el algoritmo EEA y se dejan para
  una fase posterior.

El verificador solo requiere que S0..S{n-1} y E0..E{m-1} existan con los nombres
correctos; el resto de qubits son libres.
"""

from __future__ import annotations

import argparse
from typing import Sequence

import kickmix as km

# Out-of-range address value used to park unary iteration cursors.
_UNREACHABLE = 1 << 63


def default_n_iters(n_syndromes: int) -> int:
    """Returns the EEA iteration count `3 * (n_syndromes + 1) + 9`."""
    return 3 * (n_syndromes + 1) + 9


class DQIOptimizedDecoder:
    """Decoder DQI con contadores reducidos y scaffolds reusables."""

    def __init__(self, n_syndromes: int, degree: int):
        self.n_syndromes = n_syndromes
        self.degree = degree
        self.m = n_syndromes + 3
        self.n_iters = default_n_iters(n_syndromes)

    def build(self, builder: km.CircuitBuilder,
              syndromes: Sequence[km.array],
              error_mbuc: Sequence[km.array]) -> None:
        """Construye el circuito DQI optimizado sobre `builder`."""
        gf = km.GF2Field(self.degree)
        n = self.n_syndromes
        m = self.m
        degree = self.degree
        n_iters = self.n_iters

        # Contadores: 8 bits para n_A, n_B, n_a, n_b, n_q (como el reference),
        # 2 bits counter, 1 bit flag, 8 bits halting_counter.
        # Total = 5*8 + 1 + 2 + 8 = 51 (baseline).
        # TODO: volver a 7 bits una vez se verifique que no hay desbordamiento.
        n_A = builder.alloc_qubits(8)
        n_B = builder.alloc_qubits(8)
        n_a = builder.alloc_qubits(8)
        n_b = builder.alloc_qubits(8)
        n_q = builder.alloc_qubits(8)
        flag = builder.alloc_qubits(1)[0]
        counter = builder.alloc_qubits(2)
        halting_counter = builder.alloc_qubits(8)

        # reg_a: los primeros 3 son ancillas (alloc), el resto son sindromes S
        reg_a = [builder.alloc_qubits(degree) if i < 3 else syndromes[i - 3]
                 for i in range(m)]

        # reg_b: m registros (73), todos alloc. Igual que el reference.
        reg_b = [builder.alloc_qubits(degree) for _ in range(m)]

        # Inicializar contadores
        init_ones = km.array([reg_a[0][0], reg_a[m - 1][0], n_a[0], flag])
        builder.x(init_ones)
        builder.gf2_iadd(n, target=n_A)
        builder.gf2_iadd(n + 1, target=n_B)

        # Shift inicial
        self._initial_shift_loop(builder, reg_a, n_A, gf, is_adjoint=False)

        # EEA forward
        eea = (reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag,
               counter, halting_counter)
        self._synchronized_eea(builder, *eea, n_iters=n_iters,
                               is_adjoint=False, gf=gf)

        # Chien search + Forney + MBUC
        self._chien_search_and_forney_mbuc(builder, reg_b, error_mbuc,
                                           n_b, n_B, gf)

        # EEA reverse
        self._synchronized_eea(builder, *eea, n_iters=n_iters,
                               is_adjoint=True, gf=gf)

        # Uncompute shift inicial
        self._initial_shift_loop(builder, reg_a, n_A, gf, is_adjoint=True)

        # Limpiar contadores
        builder.gf2_iadd(n + 1, target=n_B)
        builder.gf2_iadd(n, target=n_A)
        builder.x(init_ones)

        # Liberar todos los registros temporales
        for reg in (halting_counter, counter, flag, n_q, n_b, n_a,
                    n_B, n_A, *reg_a[:3], *reg_b):
            builder.free(reg)

    # ------------------------------------------------------------------
    # Shift inicial
    # ------------------------------------------------------------------
    def _initial_shift_loop(self, builder, reg_a, n_A, gf,
                            *, is_adjoint: bool) -> None:
        n = self.n_syndromes
        m = len(reg_a)
        degree = gf.degree
        shift_step = builder.mark('shift_step')
        rng = (range(n - 2, -1, -1) if is_adjoint
               else range(n - 1))
        for step in rng:
            with shift_step:
                ctrl = builder.alloc_qubits(1)[0]
                if is_adjoint:
                    builder.flip_if_less_than(n_A, n - step, target=ctrl)
                    builder.iadd(1, target=n_A, control=ctrl)
                    for b in range(degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.right_rotate(lane, 1, control=ctrl)
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl)
                else:
                    builder.flip_if_equal(reg_a[m - 1], 0, target=ctrl)
                    for b in range(degree):
                        lane = km.array([r[b] for r in reg_a[3 + step:m]])
                        builder.left_rotate(lane, 1, control=ctrl)
                    builder.isub(1, target=n_A, control=ctrl)
                    builder.flip_if_less_than(n_A, n - step, target=ctrl)
                builder.free(ctrl)

    # ------------------------------------------------------------------
    # EEA sincronizado
    # ------------------------------------------------------------------
    def _synchronized_eea(self, builder, reg_a, reg_b, n_A, n_B, n_a,
                          n_b, n_q, flag, counter, halting_counter,
                          *, n_iters, is_adjoint, gf) -> None:
        m = len(reg_a)
        eea_step = builder.mark('eea_step')
        rng = (range(n_iters - 1, -1, -1) if is_adjoint
               else range(n_iters))

        for it in rng:
            with eea_step:
                if is_adjoint:
                    self._update_counter(builder, counter, flag,
                                         is_adjoint=True)

                is_c3 = builder.alloc_qubits(1)[0]
                builder.init_and(counter[0], counter[1], is_c3)
                if is_adjoint:
                    self._update_halting_counter(builder, n_A, n_B, n_b,
                                                 halting_counter, flag, is_c3,
                                                 is_adjoint=True)

                is_hc_zero = builder.alloc_qubits(1)[0]
                builder.flip_if_equal(halting_counter, 0, target=is_hc_zero)
                ctrl = self._counter_controls(builder, counter, is_c3,
                                              is_hc_zero)

                steps = [
                    lambda: self._update_flag(builder, reg_b[m // 2 + 1:],
                                              n_A, n_B, n_a, n_b, n_q,
                                              flag, ctrl, gf),
                    lambda: self._multiply_and_add_or_sub(
                        builder, reg_a, reg_b, n_A, n_a, n_q,
                        ctrl, it, is_adjoint=is_adjoint, gf=gf),
                    lambda: self._shift_b_array_right(builder, reg_b,
                                                      n_B, n_b, flag, ctrl,
                                                      it,
                                                      is_adjoint=is_adjoint,
                                                      gf=gf),
                    lambda: self._update_metadata(builder, n_B, n_b, n_q,
                                                  flag, ctrl,
                                                  is_adjoint=is_adjoint),
                    lambda: self._swap_a_and_b(builder, reg_a, reg_b,
                                               n_A, n_B, n_a, n_b,
                                               flag, ctrl),
                ]
                for step in (reversed(steps) if is_adjoint else steps):
                    step()

                self._del_counter_controls(builder, counter, is_c3,
                                           is_hc_zero, ctrl)
                builder.flip_if_equal(halting_counter, 0, target=is_hc_zero)
                builder.free(is_hc_zero)

                if not is_adjoint:
                    self._update_halting_counter(builder, n_A, n_B, n_b,
                                                 halting_counter, flag, is_c3,
                                                 is_adjoint=False)
                builder.del_and(counter[0], counter[1], is_c3)
                builder.free(is_c3)
                if not is_adjoint:
                    self._update_counter(builder, counter, flag,
                                         is_adjoint=False)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _update_counter(self, builder, counter, flag, *, is_adjoint: bool):
        if is_adjoint:
            builder.cx(flag, counter[0])
            builder.ccx(flag, counter[0], counter[1])
        else:
            builder.ccx(flag, counter[0], counter[1])
            builder.cx(flag, counter[0])

    def _update_halting_counter(self, builder, n_A, n_B, n_b,
                                halting_counter, flag, is_c3,
                                *, is_adjoint: bool):
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

    def _counter_controls(self, builder, counter, is_c3, is_hc_zero):
        ctrl = builder.alloc_qubits(4)
        c0, c1, c2, c3 = ctrl
        builder.init_and(is_hc_zero, km.array([counter[0], is_c3]),
                         km.array([c1, c3]))
        builder.cx(km.array([is_hc_zero, c1]), c0)
        builder.init_and(c0, counter[1], c2)
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        return ctrl

    def _del_counter_controls(self, builder, counter, is_c3,
                              is_hc_zero, ctrl):
        c0, c1, c2, c3 = ctrl
        builder.cx(km.array([c2, c3]), km.array([c0, c1]))
        builder.del_and(c0, counter[1], c2)
        builder.cx(km.array([is_hc_zero, c1]), c0)
        builder.del_and(is_hc_zero, km.array([counter[0], is_c3]),
                        km.array([c1, c3]))
        builder.free(ctrl)

    def _update_flag(self, builder, reg_b_tail, n_A, n_B, n_a, n_b, n_q,
                     flag, ctrl, gf):
        c0, c1, c2, c3 = ctrl
        m_tail = len(reg_b_tail)
        aux = builder.alloc_qubits(1)[0]

        builder.flip_if_less_than(n_A, n_B, target=aux, control=c0)
        builder.flip_if_equal(n_q, 0, target=flag, control=aux)
        builder.flip_if_less_than(n_A, n_B, target=aux, control=c0)
        builder.flip_if_equal(n_A, n_B, target=flag, control=c0)

        builder.flip_if_equal(n_A, n_B, target=flag, control=c1)
        builder.cx(c1, flag)
        builder.flip_if_equal(n_B, 1, target=aux, control=c1)
        builder.cx(c1, aux)
        builder.flip_if_equal(reg_b_tail[m_tail - 2], 0, target=flag,
                              control=aux)
        builder.cx(c1, aux)
        builder.flip_if_equal(n_B, 1, target=aux, control=c1)

        builder.cx(c2, flag)
        builder.flip_if_equal(n_b, 0, target=aux, control=c2)
        builder.cx(c2, aux)
        builder.flip_if_equal(reg_b_tail[0], 0, target=flag, control=aux)
        builder.cx(c2, aux)
        builder.flip_if_equal(n_b, 0, target=aux, control=c2)
        builder.iadd(1, target=n_b)
        builder.flip_if_equal(n_a, n_b, target=flag, control=c2)
        builder.isub(1, target=n_b)

        builder.flip_if_equal(n_a, n_b, target=flag, control=c3)
        builder.flip_if_equal(n_q, 1, target=flag, control=c3)

        builder.free(aux)

    def _multiply_and_add_or_sub(self, builder, reg_a, reg_b, n_A, n_a,
                                 n_q, ctrl, it, *, is_adjoint, gf):
        c0_hc, _, _, c3_hc = ctrl
        m = len(reg_a)

        def accumulate_quotient(index, control):
            ratio, scaffold = builder.init_gf2_div_with_scaffold(
                reg_b[index], reg_a[index], field=gf)
            builder.gf2_iadd(ratio, target=q_i, field=gf, control=control)
            builder.del_gf2_div_with_scaffold(
                reg_b[index], reg_a[index], target=ratio, scaffold=scaffold,
                field=gf)
            builder.free(scaffold + ratio)

        def sweep_positions():
            lim_q = min(m - 1, 1 + it)
            lim_q1 = min(m, 1 + it)
            lim_a = min(m - 2, it // 2 + 1)
            lim_A = m - 2
            order = range(m) if is_adjoint else range(m - 1, -1, -1)

            with (builder.unary_iteration(n_q, control=c0_hc) as eq_i,
                  builder.unary_iteration(n_q, control=c3_hc) as eq_ip1,
                  builder.unary_iteration(n_a, control=c3_hc) as cur_a,
                  builder.unary_iteration(n_A, control=c0_hc) as cur_A):
                mul = builder.alloc_qubits(1)[0]

                def endpoint(i):
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
                        builder.ixor_gf2_mul(q_i, reg_a[i],
                                             target=reg_b[i],
                                             field=gf, control=mul)
                    if len(swaps) == 1:
                        builder.cswap(swaps[0], q_i, reg_a[i])
                    elif swaps:
                        both = builder.alloc_qubits(1)[0]
                        builder.cx(km.array(swaps), both)
                        builder.cswap(both, q_i, reg_a[i])
                        builder.cx(km.array(swaps), both)
                        builder.free(both)
                    if not is_adjoint and multiplies:
                        builder.ixor_gf2_mul(q_i, reg_a[i],
                                             target=reg_b[i],
                                             field=gf, control=mul)

                endpoint(prev)
                builder.free(mul)

        q_i = builder.alloc_qubits(gf.degree)
        leading, trailing = (0, m - 1) if is_adjoint else (m - 1, 0)
        accumulate_quotient(leading, c3_hc if is_adjoint else c0_hc)
        builder.iadd(n_a, target=n_q)
        sweep_positions()
        builder.isub(n_a, target=n_q)
        accumulate_quotient(trailing, c0_hc if is_adjoint else c3_hc)
        builder.free(q_i)

    def _shift_b_array_right(self, builder, reg_b, n_B, n_b, flag, ctrl,
                             it, *, is_adjoint, gf):
        c0_hc, c1_hc, c2_hc, c3_hc = ctrl
        m = len(reg_b)
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
        with (builder.unary_iteration(n_B, control=ctrl_nB) as cur_B_ge,
              builder.unary_iteration(n_b, control=c2_hc) as cur_b_ge,
              builder.unary_iteration(n_B, control=c3_nf) as cur_B_lt):
            do_shift = builder.alloc_qubits(1)[0]

            def endpoint(i):
                _xor_threshold(builder, cur_B_ge, lim_B, do_shift,
                               ctrl_nB, m - i + 1, at_least=True)
                _xor_threshold(builder, cur_b_ge, lim_b, do_shift, c2_hc, i,
                               at_least=True)
                _xor_threshold(builder, cur_B_lt, lim_B, do_shift, c3_nf,
                               m - i, at_least=False)

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

    def _update_metadata(self, builder, n_B, n_b, n_q, flag, ctrl,
                         *, is_adjoint: bool):
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
            for target, offset, control in (reversed(step) if is_adjoint
                                            else step):
                builder.iadd(sign * offset, target=target, control=control)

        builder.x(flag)
        builder.del_and(km.array([c0_hc, c3_hc]), flag, nf)
        builder.x(flag)
        builder.free(nf)

    def _swap_a_and_b(self, builder, reg_a, reg_b, n_A, n_B, n_a, n_b,
                      flag, ctrl):
        c3_hc = ctrl[3]
        swap_ctrl = builder.alloc_qubits(1)[0]
        builder.init_and(c3_hc, flag, swap_ctrl)
        lhs = km.array([q for r in (n_A, n_a, *reg_a) for q in r])
        rhs = km.array([q for r in (n_B, n_b, *reg_b) for q in r])
        builder.cswap(swap_ctrl, lhs, rhs)
        builder.del_and(c3_hc, flag, swap_ctrl)
        builder.free(swap_ctrl)

    # ------------------------------------------------------------------
    # Chien search + Forney + MBUC
    # ------------------------------------------------------------------
    def _chien_search_and_forney_mbuc(self, builder, reg_b, error_mbuc,
                                      n_b, n_B, gf):
        degree = gf.degree
        m = len(reg_b)
        t = self.n_syndromes // 2
        block_length = (1 << degree) - 1
        primitive = gf.primitive_element

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
            (k, gf.pow(primitive, (block_length - 2 - k) % block_length))
            for k in omega_indices
            if (block_length - 2 - k) % block_length != 0
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
                builder.bit_store(is_error[0], True,
                                  control=error_mbuc[j])
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
                    sigma_prime, target=sigma_prime_inv,
                    scaffold=inverse_chain, field=gf)
                builder.free(inverse_chain)

                builder.flip_if_equal(sigma, 0, target=is_sigma_zero)
                builder.cx(rev_src, rev_dst)

                builder.pop_condition()
                builder.bit_store(is_error, False)

                if j + 1 < num_positions:
                    for k, step in step_multipliers:
                        builder.gf2_imul(step, target=reg_b[k],
                                         field=gf)

        if num_positions > 1:
            for k, step in step_multipliers:
                builder.gf2_idiv(
                    gf.pow(step, num_positions - 1), target=reg_b[k],
                    field=gf)

        builder.free(is_error)
        builder.free(located + sigma_prime_inv + km.array([is_sigma_zero]))

        self._pre_align_reg_b(builder, reg_b, n_b, n_B, is_adjoint=True)

    def _pre_align_reg_b(self, builder, reg_b, n_b, n_B, *,
                         is_adjoint: bool) -> None:
        m = len(reg_b)
        omega = reg_b[m // 2 + 1:]
        for b in range(self.degree):
            lane = km.array([r[b] for r in omega])
            if is_adjoint:
                builder.right_rotate(lane, n_B)
                builder.left_rotate(lane, n_b)
            else:
                builder.right_rotate(lane, n_b)
                builder.left_rotate(lane, n_B)


def _active(cursor, address_value, limit):
    """Moves cursor to address_value and returns control and (x == address_value)."""
    if address_value > limit:
        cursor.move_to(_UNREACHABLE)
        return False
    cursor.move_to(address_value)
    return cursor.match_qubit


def _xor_threshold(builder, cursor, limit, target, control, value, *,
                   at_least: bool, lowest: int = 0):
    if value > limit:
        if not at_least:
            builder.cx(control, target)
        return
    if at_least:
        builder.cx(control, target)
    for u in range(lowest, value):
        builder.cx(_active(cursor, u, limit), target)


def main():
    parser = argparse.ArgumentParser(
        description="Generador de circuito DQI optimizado (Benchmark II)")
    parser.add_argument("output", help="Ruta del archivo .kmb de salida")
    parser.add_argument("--m", type=int, default=4095,
                        help="Codeword length (default: 4095)")
    parser.add_argument("--n", type=int, default=70,
                        help="Number of syndromes (default: 70)")
    parser.add_argument("--degree", type=int, default=12,
                        help="GF(2^b) field degree (default: 12)")
    parser.add_argument("--format", choices=("kmb", "kmx"), default="kmb")
    args = parser.parse_args()

    builder = km.CircuitBuilder()
    syndromes = [builder.create_quantum_register(args.degree,
                                                  name=f"S{i}")
                 for i in range(args.n)]
    error_mbuc = [builder.create_classical_register(args.degree,
                                                    name=f"E{j}")
                  for j in range(args.m)]

    decoder = DQIOptimizedDecoder(args.n, args.degree)
    decoder.build(builder, syndromes, error_mbuc)

    circuit = builder.finish_circuit()
    stats = circuit.operation_statistics()
    print(f"Qubits: {circuit.num_qubits}")
    print(f"Bits: {circuit.num_bits}")
    print(f"Toffolis: {stats.num_toffoli_like:,}")
    print(f"Num ops: {len(circuit):,}")
    print(f"Reaction depth: {circuit.reaction_depth()}")

    circuit.to_file(args.output, format=args.format)
    print(f"Escrito {args.output}")


if __name__ == "__main__":
    main()
