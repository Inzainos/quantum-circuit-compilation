# DQI: perfil vigente y auditoria del reporte Schur por bloques (2026-11-08)

Perfil medido (dqi.kmb reconstruido, sha 6108f5c3..., Q=1,949, 784,172 Toffoli; tools/kmx_profile.py):
scan_pos 401,310 (51.2%); BM 298,232 (update 150,984, disc 71,766, swap 33,552, alpha 22,680, dclear 13,860, d 2,100, x 1,680, flags 1,610); omega 84,630 (42,315 x2). BM+omega = 382,862.

Auditoria del REPORTE_SCHUR_BLOQUES (solo lectura; scripts no disponibles aqui, nada reproducido):
1. El eps~0.01 es de la ruta Hankel (solo validacion); el circuito q-d con propagacion rombo acierta 91% (L<=34) y 67% (L=35): eps real ~9-33%. Es el riesgo principal.
2. La vuelta de 274k supone inversas gratis por MBU; recorrer el rombo al reves exige recalcularlas (~75 T) -> vuelta ~ ida. T total ~1,140k, ratio ~22x (no medido).
3. Q=892 asume 52 qubits de trabajo; el barrido actual usa ~70 -> Q~910-930.
Criterio de parada: si eps del q-d rombo con pesos del verificador > ~1% sin forma de absorber los ceros, no baja el score; zip DQI vigente se queda.
Procedencia: el diseno debe ser propio; las cifras del publico son solo referencia.
