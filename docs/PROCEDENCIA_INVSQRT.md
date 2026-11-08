# Procedencia del trabajo de invsqrt por polinomios (2026-11-08)

Documento de procedencia. Separa lo que se tomó del circuito público V34 (`invsqrt-public-v34.kmb`) de lo que es propio.
Los datos de V34 los aportó el otro agente del equipo; este documento recoge lo que se declaró, no lo verifica contra la fuente.

## Fuente externa
- Circuito: `invsqrt-public-v34.kmb` (circuito público de otro participante).
- Autoría (declarada por el equipo): circuito de **SomeJoint**; es el circuito de 62 qubits de **yoyobar** con los dos AND merges de **Ehan Mallick**, según lo distribuye **Alex Chilton**.
- Origen: notebook público de SomeJoint (accesible). Dataset de referencia: "33 QCC V8" (busyaprime); la URL directa devuelve 404, **PENDIENTE de confirmar**.
- Licencia del notebook/dataset de origen: **PENDIENTE de confirmar** (las reglas solo aceptan código público con licencia aprobada por la OSI, p. ej. Apache 2.0).
- URL exacta del notebook y fecha de consulta: **PENDIENTE de completar**.
- Medición con el verificador oficial de la competencia (PASS): Q = 62, Toffoli medios = 1,281.66 (máximo estático 1,537), T ≈ 1,191, 41 rotaciones, C (toffoli_equiv) = 1,579.38, Q·C = 97,921. Referencia propia (logshift2): Q·C = 390,005.
- El `.kmb` de V34 **no** está en este repositorio ni en ninguna zip de entrega.

## Tomado de V34
1. El circuito, solo como referencia para verificarlo y obtener sus números.
2. El mecanismo: modo por-bit de fase (monomios agrupados en ANFs que comparten un ángulo de peso binario, una rotación por bit), ANDs sobre ancillas reutilizables, limpieza por HMR con fixup de Z condicionada en lugar de deshacer en espejo.
3. Datos trazados del circuito: ANFs de los 9 intermedios (q23, q25, q26, q27, q40, q41, q50, q51, q57) y 51 rotaciones con sus monomios.
   Conteo: de las 51 trazadas, 10 tienen ángulo exactamente 1/4 (compuerta T, no requiere síntesis); 51 - 10 = 41 = `rotation_count` del verificador. La T media del verificador (11.5) son esas 10 más ~1 T explícita.
   En el repositorio están los de q28: `data/invsqrt-sweep/rotaciones_q28_en_x.json` e `intermedios_q28_to_x.json`.

## Propio
- Tercera tubería (bandera secuencial; q23 por XOR, 0 Toffoli).
- Capa 1 dinámica, caché de ANDs, modos auto/min_c/min_q/fixed (`src/invsqrt_poly.py`).
- Factorización Q(u) y lista de Möbius (2,559 monomios) y su medición (descartada: Q·C = 481,623 sin contar S ni normalización).
- NR, dbhexa, LUT seed, logshift2, DQI, dfthcsos.

## Reglas de la competencia (leídas por el equipo en la página oficial)
- Compartir código en privado entre equipos: prohibido (descalificación).
- Código público con licencia aprobada por la OSI (p. ej. Apache 2.0): permitido. Datos externos permitidos si son públicos y gratuitos.
- La entrega debe ser trabajo original propio y no infringir derechos de terceros. Si el circuito final reproduce V34 función por función: citar la fuente, declarar la derivación y, idealmente, ir más allá de V34.
- El repositorio de GitHub es público: los JSON con datos trazados de V34 ya son públicos.

## Estado frente a las reglas
- Ninguna zip enviada a Kaggle contiene material derivado de V34 (la zip vigente lleva logshift2, sha256 `096c37a6…`).
- **Antes de enviar algo que dependa de datos o estructura de V34**: revisar en las reglas de la competencia qué se permite con código público, si exige citar la fuente y si limita compartir circuitos entre equipos. Citar autor y URL en el README de la zip.
