"""
Qualtran Bloqs for DQI Decoder - Unified Implementation.

Combines three approaches from Windows downloads:
- v5: Scaffold reuse, BMA, testbench
- motorv15: Adjoint cleanup pipeline (Forney → Chien → BMA → EEA reverse)
- planB: Custom Cirq gates with hardcoded _t_complexity_

Main exports:
- BMABloq: Berlekamp-Massey with Gauss-Jordan (no divisions)
- EEABloq: Extended Euclidean Algorithm with scaffold reuse
- ChienForneyBloq: Chien Search + Forney with log/exp tables
- DQIDecoderBloq: Unified DQI decoder
- DQIMasterPipeline: Full pipeline with adjoint cleanup (motorv15)
- InzainosGaloisMultiplier: Custom Cirq gate for GF(2^12) multiplication
- InzainosGaloisAdder: Custom Cirq gate for GF(2^12) addition
- InzainosGaloisInverse: Custom Cirq gate for GF(2^12) inversion
- VerificadorAislado: Testbench for verification
"""

from qualtran_bloqs.bma_bloq import BMABloq
from qualtran_bloqs.eea_bloq import EEABloq, ScaffoldCache, PolynomialArray, LogExpTables
from qualtran_bloqs.chien_forney_bloq import ChienForneyBloq, LogExpTables as CFLogExpTables, GF2_12
from qualtran_bloqs.dqi_decoder_bloq import DQIDecoderBloq, create_dqi_decoder, estimate_dqi_resources
from qualtran_bloqs.dqi_master_pipeline import DQIMasterPipeline
from qualtran_bloqs.plan_b_gates import (
    InzainosGaloisMultiplier, 
    InzainosGaloisAdder, 
    InzainosGaloisInverse,
    PlanBGaloisMultiplier,
    PlanBGaloisAdder,
    PlanBGaloisInverse,
    GF2_12 as PlanB_GF2_12
)
from qualtran_bloqs.testbench_local import VerificadorAislado, ClassicalDQIDecoder

__all__ = [
    # Main Bloqs
    'BMABloq',
    'EEABloq',
    'ChienForneyBloq',
    'DQIDecoderBloq',
    'DQIMasterPipeline',
    
    # Plan B Gates
    'InzainosGaloisMultiplier',
    'InzainosGaloisAdder',
    'InzainosGaloisInverse',
    'PlanBGaloisMultiplier',
    'PlanBGaloisAdder',
    'PlanBGaloisInverse',
    
    # Utilities
    'ScaffoldCache',
    'PolynomialArray',
    'LogExpTables',
    'VerificadorAislado',
    'ClassicalDQIDecoder',
    
    # Factory functions
    'create_dqi_decoder',
    'estimate_dqi_resources',
]

__version__ = '1.0.0'