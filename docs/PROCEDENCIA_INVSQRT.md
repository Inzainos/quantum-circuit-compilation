# Procedencia del trabajo de invsqrt por polinomios (2026-11-08)

Documento de procedencia. Separa lo que se tomó del circuito público V34 (`invsqrt-public-v34.kmb`) de lo que es propio.
Los datos de V34 los aportó el otro agente del equipo; este documento recoge lo que se declaró, no lo verifica contra la fuente.

## Fuente externa
- Circuito: `invsqrt-public-v34.kmb` (circuito público de otro participante).
- Autoría (declarada por el equipo): circuito de 62 qubits de **yoyobar** con los dos AND merges de **Ehan Mallick**, distribuido por **Alex Chilton** y publicado por **SomeJoint** (Agniv Banerjee).
- Notebook público de origen: "Quantum Circuits | 24.65 Local GM: Chem Refit", versión 36, score público 24.65393, autor SomeJoint.
- Licencia del notebook (texto de su página): "This Notebook has been released under the Apache 2.0 open source license." (aprobada por la OSI).
- Archivo del circuito V34 (sha256 `af469847…`): dataset **"QCC ladder parts"** de SomeJoint, subcarpeta `invsqrt-af469847`. (El slug "33-qcc-v8" da 404; el correcto es "33-qcc-v8-members", pero no es entrada de ese notebook.)
- Licencia del dataset "QCC ladder parts" (barra lateral y metadatos, según el equipo): **Apache 2.0**. Confirmado también ahí el circuito V34 en `invsqrt-af469847`.
- URL exacta del notebook y del dataset, y fecha de consulta: **PENDIENTE de completar**.
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

## Obligaciones de Apache 2.0 (si se redistribuye material derivado)
- Incluir copia de la licencia y conservar los avisos de autoría/atribución del material original.
- Indicar de forma visible qué archivos se modificaron respecto al original.
- Citar la fuente (autores, notebook, dataset) en el README de la zip.

## Estado frente a las reglas
- Ninguna zip enviada a Kaggle contiene material derivado de V34 (la zip vigente lleva logshift2, sha256 `096c37a6…`).
- Licencia del notebook confirmada (Apache 2.0): el uso derivado es permitido por las reglas, citando la fuente y declarando la derivación. Licencia del dataset también confirmada (Apache 2.0).
- Pendiente antes de enviar: cumplir las obligaciones de Apache 2.0 (arriba), citar a SomeJoint, yoyobar y Ehan Mallick, medir qué fracción del circuito final es propia y qué fracción es V34 reescrito, y declararlo en el README de la zip.
