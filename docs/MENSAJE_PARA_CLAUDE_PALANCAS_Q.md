# Mensaje de relevo para Claude (auditor del DQI)

Capitán, pásale esto a Claude cuando vuelva. Es el resultado medido de las
palancas baratas de Q que propuso, y lo que necesita auditar.

---

Claude, ya medí las dos palancas baratas de Q que propusiste. Resultado:

**1. Las flags de −29 qubits: no son identificables. No toqué ninguna flag.**

Busqué en todo el camino activo del DQI (`dqi_bm_stage_v1.py` +
`dqi_decoder_v1.py`, commit a741cc7) todas las menciones de "flag" y todas
las alocaciones de 1 qubit. Las únicas flags son las p/t (140 qubits,
2 por ronda × 70), que ya están probadas necesarias por dependencia
circular (reporte `REPORTE_BANDERAS_RECOMPUTO.md`). Las demás alocaciones
de 1 qubit (`z`, `nz` en `_flags`; `tmp`, `f`, `g` en el scan) son
transitorias, se liberan dentro de su ámbito y no contribuyen al pico.
Los registros vivos (S 840, sigma 432, tau 432, d 8, H 12) no suman 29
en ninguna combinación (d+H = 20).

Si tienes una identificación concreta de esos −29 qubits (archivo, línea,
registro), especifícala. Sin ella, la palanca no existe y no hay nada que
quitar. La aritmética del +1% al geomean es correcta para −29 qubits, pero
como no son localizables, el efecto medido es 0.

**2. Pico del BM: medido con composición fina. Q=1,949, sin cambio.**

Script `pico_bm_fino.py` (en el repo, se subirá con el reporte). Medido a
escala completa (n=70):
- Base antes de la ronda 69: 1,862 vivos (S 840 + sigma 432 + tau 432 +
  d 8 + H 12 + flags p/t 138).
- Pico vivos simultáneos en la ronda 69: **1,942** (base + 80 transitorios).
- Q del circuito: **1,949** (7 más que el pico de vivos; sobrecarga del pool).
- T de bm_forward: 185,034 (coincide con el perfil).

Composición de los 80 transitorios del pico: p,t (2) + D (12) + X (12) +
alpha (12) + P (12) + Pinv (12) + andamios de mul/inv (18). Los 80 son
genuinamente necesarios a la vez en el bloque alpha. Los temporales de
`_flags` (lad 10 + z 1 + nz 1) y de `_dclear` (u 12) no contribuyen al
pico: se liberan antes de que se aloque el bloque alpha.

La palanca real del pico es el bloque alpha (42 qubits: P + Pinv +
andamios). Reducirlo exige fusionar mul+inv, que es un cambio algorítmico,
no una eliminación de flags. No lo intenté; queda como trabajo futuro.

**3. Integridad:** no toqué main ni el ZIP. El clon está limpio
(HEAD a40a82f), `dqi-1949.kmb` sigue en sha 6108f5c3…, Q=1,949,
T=784,172. Todo el trabajo es scratch en `~/workspace/qcc-data/dqi-perfil/`
(`pico_bm_fino.py`, `REPORTE_PALANCAS_Q_DQI.md`).

**Lo que te pido auditar cuando vuelvas (con el verificador oficial):**
- Que las flags p/t (140) son las únicas flags del camino activo y que no
  hay un conjunto de 29 qubits-flag que yo haya pasado por alto. Si lo hay,
  dime dónde.
- Que el pico Q=1,949 con la composición medida (1,942 vivos, 80
  transitorios, bloque alpha 42) es correcto.
- La ruta q-d/Schur sigue muerta (tu medición del ~21% con pesos reales);
  no se retomó.

— Mole (la raíz)
