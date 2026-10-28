# src — Optimizadores

Este directorio contiene los scripts de optimización para invsqrt, DQI y
DFTHC-SOS, además de `qubit_temporal_manager.py`, que administra los qubits
temporales de los circuitos. La construcción y verificación de circuitos usa
la biblioteca **kickmix** distribuida con Qualtran.

Los verificadores de referencia están en `verifiers/`; las instrucciones
específicas de cada optimizador se muestran con `--help`.
