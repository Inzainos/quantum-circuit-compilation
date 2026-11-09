# Recorte del Horner de logshift2 — resultado negativo (2026-11-08)

Objetivo: usar la holgura de tolerancia para recortar anchos de fila (ks) y filas de u (dd) en el Horner y bajar Q·C (base 390,005).
Método: modelo de error sobre todo el dominio 1..2^22-1 (lee ~0.89 donde el verificador oficial lee 0.792), mejor sesgo 0..3. Criterio: error/tol < 1.

| Configuración | error/tol (modelo) | Toffoli (sesgo=1) |
|---|---|---|
| Base (ks 0,0; dd 13) | 0.862 | 2,561 |
| ks=(1,0) | 1.757 | — |
| ks=(0,1) | 1.464 | 2,487 |
| ks=(1,1) | 1.725 | — |
| ks=(2,2) | 4.474 | (1,2): 2,367 |
| dd=12 | 4.345 | (2,3): 2,195 |
| dd=11 | 12.197 | — |

Conclusión: la holgura real es ~14%, no 20%; un bit de recorte ya la excede. Ninguna variante recortada es válida; no se construyó circuito. Zip vigente sin cambios.
Siguiente vía: rediseñar la aritmética del Horner (no recortarla).
Scripts: tools/horner_trunc/ (busca_trunc.py, horner_trunc.py; scratch, rutas de import ajustar).
