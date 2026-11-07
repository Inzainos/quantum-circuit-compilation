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

## Cambios aplicados (2026-11-07, tarde)
- Barrido: el registro `g` del AND de fase pasa de 12 a 1 qubit (se usaba de a uno). Q 2,016 → **2,009**,
  Toffoli iguales (784,172). Verificado: `dqi_decoder_test` 4,095 posiciones PASA; muestreo 102,400 tiros
  semilla 1: 0 fallos. Nuevo sha del dqi.kmb: `8d6915efe4450025d149a8347931998ffd223b7b59318a05882354b0d5b0acfe`.
  (Efecto en score: −0.7 %.) La zip final NO se ha reconstruido con este cambio.

## Medición del pico del BM (por ronda, 143 qubits temporales + 2 por bandera acumulada)
Pico por paso (ronda 1, sin banderas previas): alloc p,t,D,X → _disc +29 → _flags +38 → inversión
(tower) **+131** → alpha+swap +140 → update **+143**. La torre de inversión retiene 81 qubits desde
`_inv_init` hasta `_inv_del` (a través de swap y update). Deshacerla antes (recomputar al final)
bajaría el pico a 131 pero cuesta +75 Toffoli por ronda y sentido (≈+10.5k, +1.3 %) contra −12
qubits (−1.2 %): neutro. Asignar `alpha` después de la inversión no cambia el pico (se mueve al update).

## Palanca grande (no implementada): EEA/BM en el sitio
σ y τ (864 qubits) viven aparte de S (840). Con normalización σ0=1 el par (σ1..σ35, ω0..ω34) tiene
70 símbolos = los 70 de S: es una biyección sobre los síndromes corregibles. Un algoritmo en el sitio
(EEA sincronizado con grados complementarios, como en los decodificadores sistólicos) llevaría S→(σ,ω)
sin registros aparte; quedarían solo banderas (~140) y temporales (~150): Q≈1,150 en vez de 2,009,
es decir (2009/1150)² ≈ 3× en el componente DQI (≈1.45× en la media geométrica final).
Es un rediseño, no un parche.


## Torre de inversión sin copias (dqi_tower_inv3) y barrido sin t/u — Q 2,009 → 1,949 (mismos 784,172 Toffoli)
Idea (de Capitán): "arquitectura donde los registros fluyan y se cierren sin acumularse". Cambios, todos con 0 Toffoli extra:
- `src/dqi_tower_inv3.py`: N se calcula directo (sin Pn); cambios de base P2C/C2P EN EL SITIO con redes de CX
  (`inplace_ops`); s = a0^a1 se forma temporalmente sobre a0; los productos o0/o1 se acumulan directo en la salida w
  (vía WCOLS) y w se limpia con una sola medición X. El ValueInv3 además cambia a coordenadas en el sitio (sin `ac`).
  Qubits auxiliares de la inversión: 81 → **21**. Autoprueba: 4,096/4,096, 75 Toffoli, sin basura ni fase
  (`tests/test_tower_inv3.py`).
- Barrido: se eliminan los registros `t` y `u` (24 qubits): u_a se forma en un único qubit y la fase se aplica con
  CZ(g_a, w_b) condicionados a E[p][k] (misma fase, menos CX).
- Resultado: Q 2,009 → 1,949; el pico lo fija ahora el BM (≈85 temporales por ronda), el barrido queda en 1,934.
- Verificación: `dqi_decoder_test` 4,095 posiciones PASA; muestreo 102,400 tiros: semilla 1 → 0 fallos,
  semilla 7 → 2 fallos (mismo conteo que el circuito anterior con esa semilla). dqi.kmb nuevo: sha `6108f5c344b995221f3cf57cd357a1742051031cc89929d0ae055a7bb5233dfb`.
- Efecto en score DQI: (2016/1949)² = 1.070× (−6.5 % de costo).

## Nota: por qué no hay "smart scan" por posición
En el verificador (`verify_submission_dqi.py`, líneas ~248-256) los bits clásicos E son resultados de medición
UNIFORMES (mbuc ∈ [0,4095] en las 4,095 posiciones), no el patrón de error disperso; y T es la MEDIA de Toffoli
ejecutados por tiro. Todas las posiciones están activas, así que no se puede saltar ninguna por E[p]=0.
