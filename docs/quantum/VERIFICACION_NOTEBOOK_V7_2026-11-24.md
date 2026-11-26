# Verificación en vivo — Notebook v7 es v7 en número pero v5 en contenido

**Fecha de la verificación:** 2026-11-24 ~12:24 CST (consulta en vivo nueva, orden de Elán 12:18)
**Verificado por:** Brujo (Elán pidió la consulta en vivo nueva para resolver la ambigüedad)
**Método:** `get_notebook_info` del conector Kaggle (`bin/client.py call-tool --name get_notebook_info`), kernel 144639626, ref `elnzainoscorona/verifiable-quantum-circuit-compilation`.

## Resultado en vivo

| Campo | Valor |
|---|---|
| `current_version_number` | **7** |
| `is_private` | **false** (público) |
| `last_run_time` | 2026-11-21T18:22:40Z |
| Blob (fuente guardada) | 58,607 caracteres |

## Contenido del blob (la fuente pública actual)

- El encabezado describe la entrega como **"Submission (v5, the current state — see §8 for the full history Adopted v3 → v4 → swap42 → v4.1 → v5)"**.
- **"Kaggle-measured score of this submission: 4.90803"**, geomean 4.89215.
- **Cero menciones** en todo el blob (58,607 caracteres) de: P15 (0), hoist (0), 5.00918 (0), 665,819 (0), 670,307 (0), 5.00379 (0), skip_low (0), D-NB6-1 (0).

## Conclusión

La pública es **v7 en número de versión pero v5 en contenido**. El guardado del 20 nov 10:43 devolvió versión 7, pero subió el contenido viejo: la corrección D-NB6-1 y los números v6/v7 (5.00379 / 5.00918) **no llegaron a la pública**. La ambigüedad que arrastraba la revisión a fondo (save con versión 7 vs get_info con contenido v5, ambos del 20 nov) queda resuelta: no era un problema de caché ni de lectura — el contenido guardado es el v5.

## Qué hace falta

Republicar el notebook con el contenido correcto (el build v6 + la corrección D-NB6-1 + los números v7). **No se republica sin verificar el contenido que se va a subir y sin GO de Elán** (regla vigente). Estado al 2026-11-26: pendiente de su GO.
