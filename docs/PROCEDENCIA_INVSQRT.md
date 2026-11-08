# Procedencia del trabajo de invsqrt por polinomios (2026-11-08)

Documento de procedencia. Separa lo que se tomó del circuito público V34 (`invsqrt-public-v34.kmb`) de lo que es propio.
Los datos de V34 los aportó el otro agente del equipo; este documento recoge lo que se declaró, no lo verifica contra la fuente.

## Fuente externa
- Circuito: `invsqrt-public-v34.kmb` (circuito público de otro participante).
- Autor: **PENDIENTE de completar**.
- URL de origen / fecha de descarga: **PENDIENTE de completar**.
- Medición con el verificador oficial de la competencia (PASS): Q = 62, Toffoli medios = 1,281.66 (máximo estático 1,537), T ≈ 1,191, 41 rotaciones, C (toffoli_equiv) = 1,579.38, Q·C = 97,921. Referencia propia (logshift2): Q·C = 390,005.
- El `.kmb` de V34 **no** está en este repositorio ni en ninguna zip de entrega.

## Tomado de V34
1. El circuito, solo como referencia para verificarlo y obtener sus números.
2. El mecanismo: modo por-bit de fase (monomios agrupados en ANFs que comparten un ángulo de peso binario, una rotación por bit), ANDs sobre ancillas reutilizables, limpieza por HMR con fixup de Z condicionada en lugar de deshacer en espejo.
3. Datos trazados del circuito: ANFs de los 9 intermedios (q23, q25, q26, q27, q40, q41, q50, q51, q57) y 51 rotaciones con sus monomios.
   En el repositorio están los de q28: `data/invsqrt-sweep/rotaciones_q28_en_x.json` e `intermedios_q28_to_x.json`.

## Propio
- Tercera tubería (bandera secuencial; q23 por XOR, 0 Toffoli).
- Capa 1 dinámica, caché de ANDs, modos auto/min_c/min_q/fixed (`src/invsqrt_poly.py`).
- Factorización Q(u) y lista de Möbius (2,559 monomios) y su medición (descartada: Q·C = 481,623 sin contar S ni normalización).
- NR, dbhexa, LUT seed, logshift2, DQI, dfthcsos.

## Estado frente a las reglas
- Ninguna zip enviada a Kaggle contiene material derivado de V34 (la zip vigente lleva logshift2, sha256 `096c37a6…`).
- **Antes de enviar algo que dependa de datos o estructura de V34**: revisar en las reglas de la competencia qué se permite con código público, si exige citar la fuente y si limita compartir circuitos entre equipos. Citar autor y URL en el README de la zip.
