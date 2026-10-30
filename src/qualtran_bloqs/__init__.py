"""
Qualtran Bloqs for DQI Decoder - PROTOTYPES.

⚠️  IMPORTANTE: Estos archivos son PROTOTIPOS DE INVESTIGACIÓN, no implementación funcional
⚠️  - No usan el decorator @bloq de Qualtran
⚠️  - No implementan TComplexity correctamente
⚠️  - Son mock-ups para explorar arquitecturas
⚠️  - NO usar en producción

Combines three approaches from Windows downloads:
- v5: Scaffold reuse, BMA, testbench
- motorv15: Adjoint cleanup pipeline (Forney → Chien → BMA → EEA reverse)
- planB: Custom Cirq gates with hardcoded _t_complexity_

ESTADO: Prototipos de investigación (2026-10-29)
- Implementación real DQI: src/dqi_optimized_v10.py
- Implementación real invsqrt: src/invsqrt_piecewise.py
- Estos Bloqs son documentación de arquitectura explorada

RECOMENDACIÓN: Usar src/dqi_optimized_v10.py y src/invsqrt_piecewise.py para producción.
"""

# Prototypes - for architectural reference only
# All imports marked as prototypes
try:
    from qualtran_bloqs.bma_bloq import BMABloq
except ImportError:
    BMABloq = None

try:
    from qualtran_bloqs.eea_bloq import EEABloq, ScaffoldCache, PolynomialArray, LogExpTables
except ImportError:
    EEABloq = ScaffoldCache = PolynomialArray = LogExpTables = None

try:
    from qualtran_bloqs.chien_forney_bloq import ChienForneyBloq
except ImportError:
    ChienForneyBloq = None

try:
    from qualtran_bloqs.dqi_decoder_bloq import DQIDecoderBloq, create_dqi_decoder, estimate_dqi_resources
except ImportError:
    DQIDecoderBloq = create_dqi_decoder = estimate_dqi_resources = None

try:
    from qualtran_bloqs.dqi_master_pipeline import DQIMasterPipeline
except ImportError:
    DQIMasterPipeline = None

try:
    from qualtran_bloqs.plan_b_gates import (
        InzainosGaloisMultiplier, 
        InzainosGaloisAdder, 
        InzainosGaloisInverse,
    )
except ImportError:
    InzainosGaloisMultiplier = InzainosGaloisAdder = InzainosGaloisInverse = None

try:
    from qualtran_bloqs.testbench_local import VerificadorAislado, ClassicalDQIDecoder
except ImportError:
    VerificadorAislado = ClassicalDQIDecoder = None

__all__ = [
    # Main Bloqs (PROTOTYPES)
    'BMABloq',
    'EEABloq',
    'ChienForneyBloq',
    'DQIDecoderBloq',
    'DQIMasterPipeline',
    
    # Plan B Gates (PROTOTYPES)
    'InzainosGaloisMultiplier',
    'InzainosGaloisAdder',
    'InzainosGaloisInverse',
    
    # Utilities (PROTOTYPES)
    'ScaffoldCache',
    'PolynomialArray',
    'LogExpTables',
    'VerificadorAislado',
    'ClassicalDQIDecoder',
    
    # Factory functions (PROTOTYPES)
    'create_dqi_decoder',
    'estimate_dqi_resources',
]

__version__ = '1.0.0-prototype'
__prototype__ = True
__note__ = "Archivos de investigación. No usar en producción."