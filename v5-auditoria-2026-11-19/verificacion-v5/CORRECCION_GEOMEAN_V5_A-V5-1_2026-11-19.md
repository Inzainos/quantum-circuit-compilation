# Corrección al geomean del ZIP v5 — A-V5-1 (2026-11-19)

## La corrección

El geomean correcto del ZIP v5 es **4.89215**, no 4.88904.

- El reporte `REPORTE_ZIP_V5_2026-11-19.md` (227 l., md5 `760fcfef…`) trae la cifra
  stale **4.88904** en dos lugares:
  - §6, línea 189: "Geomean medido por Datos / verificado por el Auditor: 4.88904"
  - §9, línea 226: descripción sugerida para Kaggle, "expected geomean 4.88904"
- El reporte se conserva tal cual (su md5 está registrado en la cadena); esta nota
  es la corrección documental.

## Por qué

El 4.88904 usó el ratio invsqrt de logshift2 (**5.32499**, stale). El ratio correcto
es el de R1+R5, el circuito que sí va en el ZIP v5:

- R1+R5: 2,076,774 / 389,261.0125451585 = **5.33517083**
- Geomean con 5.33517 = **4.89215242 → 4.89215** (delta +0.0637% vs 4.88904)
- vs adoptado +38.52%, vs g2 +37.74%

## Alcance

- **El ZIP en sí está correcto** — los circuitos no cambian (sha256 `d1392960…`).
  Solo las cifras de §6 y §9 necesitan actualizarse de 4.88904 a **4.89215**.
- La subida a Kaggle del ZIP v5 (ref **58594222**, 2026-11-19 ~22:12 CST) ya usa
  4.89215 en su descripción: "v5: P1P2P3-QF DQI (Q=1857, T=710312) + R1R5 invsqrt
  (Q=139) + seg100@brot13 dfthcsos; expected geomean 4.89215".

## Fuente

- Auditor, `REVISION_AUDITOR_ZIP_V5_2026-11-19.md` §4 (A-V5-1), informe 105 l.,
  md5 `a2a6fee7…` — concurro: el geomean es 4.89215, no 4.88904. El error era del
  Auditor también (en su revisión del seg100@brot13 usó el ratio logshift2).
- Concurre Datos (supervisión, 97 l., md5 `217eee66…`) y el Brujo (verificación,
  57 l., md5 `0057d9d3…`). Cadena completa del ZIP v5: CONCURRO (PASA).
