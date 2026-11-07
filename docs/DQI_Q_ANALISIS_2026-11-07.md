# DQI: de dónde salen los 2,016 qubits (medido 2026-11-07)

Medido con un proxy del `CircuitBuilder` sobre `src/dqi_decoder_v1.py` (n=70, LS=36, LO=35).

| Concepto | Qubits |
|---|---|
| Registros S (70 síndromes × 12 bits, entrada) | 840 |
| σ (36 × 12) | 432 |
| τ (36 × 12) | 432 |
| d (8) + H (12) | 20 |
| **Base** | **1,724** |
| Flags (p,t) de las 70 rondas, vivos al terminar BM | 140 → 1,864 |
| Temporales del BM (pico en `forward_round` → `_inv_init` → `mul6_init`) | pico 2,005 |
| Temporales del barrido (s,u,dd,w,t,f,lad,g = 95 + torre de inversión ≈57) | pico **2,016** |

Equivalencia de costo: S = R·Q²·T ⇒ 1 qubit ≈ 2/2016 ≈ 0.099 % ≈ **778 Toffoli**.
Los picos del BM (2,005) y del barrido (2,016) están a 11 qubits: recortar solo uno de
los dos rinde ≤ 11 qubits; hay que bajar ambos.

## Palanca descartada: acortar σ/τ (LS)
Prueba con 24,576 tiros (semilla 3, pesos del verificador):

| LS | Toffoli | Qubits | Fallos |
|---|---|---|---|
| 36 (actual) | 784,172 | 2,016 | 0 |
| 35 | 783,536 | 1,992 | 704 / 24,576 (2.9 %) |
| 34 | 777,968 | 1,968 | 2,945 / 24,576 (12 %) |

Cada fallo cuesta ≈0.45 % de R a N=102,400; con 2.9 % de fallos R se dispara. LS=36 es el mínimo.

## Dónde queda margen (sin medir aún)
- Los 70 registros S pesan 840 qubits y los S[35..69] (420) no se tocan en el barrido; sin
  embargo no pueden prestarse como ancilla limpia (contienen datos).
- Flags (140): se podrían codificar en ≈1.58 bits/ronda (−29 qubits) a cambio de lógica extra.
- Torre de inversión: ≈57 qubits vivos por posición; una inversión con menos ancillas pagaría
  Toffoli (presupuesto: 7.6 Toffoli por posición por cada 40 qubits ahorrados).
- Los repos públicos reportan Q≈892 con T≈407k (no verificado): sugiere un esquema que
  reutiliza S en el sitio (≈840 de entrada + ≈50 de ancillas).
