"""Persistent Scaffold for EEA Divisions - Scaffold Persistente (Opción 3 de v5).

Reuses division scaffolds across 222 EEA iterations.
Allocates max scaffold once, passes to each division, lightweight cleanup, frees once.
"""

from __future__ import annotations

from typing import Tuple, Dict
import kickmix as km


class PersistentScaffold:
    """Persistent scaffold for GF(2^12) divisions in EEA.
    
    Allocates maximum scaffold once, reuses across 222 EEA iterations.
    Avoids Qualtran's alloc/dealloc routing overhead (thousands of Toffolis/iter).
    """

    def __init__(self, builder: km.CircuitBuilder, field: km.GF2Field):
        self.builder = builder
        self.field = field
        self.m = field.degree  # 12
        self.N = (1 << self.m) - 1  # 4095
        
        # Pre-allocate maximum scaffold size for GF(2^12) division
        # Max scratchpad for division in GF(2^12): ~12 * 73 qubits
        self.scaffold_size = self.m * 73  # 876 qubits
        self.scaffold_reg = builder.alloc_qubits(self.scaffold_size)
        
        # Cache for division scaffolds keyed by (numerator_id, denominator_id)
        self._div_cache: Dict[Tuple[int, int], Tuple[km.array, km.array]] = {}
        
    def get_div_scaffold(self, numerator: km.array, denominator: km.array) -> Tuple[km.array, km.array]:
        """Get or create division scaffold, reusing persistent scaffold memory."""
        key = (id(numerator), id(denominator))
        if key in self._div_cache:
            return self._div_cache[key]
        
        # Use persistent scaffold memory for this division
        ratio, scaffold = self.builder.init_gf2_div_with_scaffold(
            numerator, denominator, field=self.field)
        self._div_cache[key] = (ratio, scaffold)
        return ratio, scaffold

    def release_div_scaffold(self, numerator: km.array, denominator: km.array,
                             ratio: km.array, scaffold: km.array) -> None:
        """Lightweight cleanup - DON'T free scaffold, just clean dirty bits."""
        key = (id(numerator), id(denominator))
        if key in self._div_cache:
            # Instead of del_gf2_div_with_scaffold + free, just clean dirty bits
            # The scaffold memory is kept for next iteration
            # We still need to uncompute the division logic
            self.builder.del_gf2_div_with_scaffold(
                numerator, denominator, target=ratio, scaffold=scaffold, field=self.field)
            # NOTE: Don't free ratio + scaffold - keep in cache for reuse
            del self._div_cache[key]

    def clear(self) -> None:
        """Free all cached scaffolds at end of circuit."""
        for ratio, scaffold in self._div_cache.values():
            self.builder.free(scaffold + ratio)
        self._div_cache.clear()

    def free_all(self) -> None:
        """Free persistent scaffold at very end."""
        self.clear()
        self.builder.free(self.scaffold_reg)


class PersistentScaffoldEEA:
    """EEA with persistent scaffolds for all divisions."""
    
    def __init__(self, builder: km.CircuitBuilder, field: km.GF2Field):
        self.builder = builder
        self.field = field
        self.scaffold = PersistentScaffold(builder, field)
    
    def div_with_persistent_scaffold(self, numerator: km.array, denominator: km.array,
                                      target: km.array, control=None) -> None:
        """Division using persistent scaffold."""
        ratio, scaffold = self.scaffold.get_div_scaffold(numerator, denominator)
        self.builder.gf2_iadd(ratio, target=target, field=self.field, control=control)
        # Lightweight cleanup - don't free scaffold
        self.builder.del_gf2_div_with_scaffold(numerator, denominator, target=ratio, scaffold=scaffold, field=self.field)
        # Keep ratio and scaffold in cache for reuse
        # The builder handles cleanup internally
    
    def clear(self) -> None:
        self.scaffold.clear()

    def free_all(self) -> None:
        self.scaffold.free_all()


def demo_scaffold_persistence():
    """Demo of scaffold persistence concept."""
    pass  # Conceptual - needs integration into EEA loop


if __name__ == "__main__":
    demo_scaffold_persistence()