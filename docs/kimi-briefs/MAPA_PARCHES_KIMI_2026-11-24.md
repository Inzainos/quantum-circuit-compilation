# Mapa de parches y briefs Kimi — 2026-11-24

**Orden de Elán (2026-11-24 ~11:53):** "Todo eso ya se los había pasado lo de los
parches. Para empezar los perdieron. Mapeen por favor y actualicen GitHub."

**Resultado del mapeo: NADA ESTABA PERDIDO.** Todo estaba en disco; lo que falló fue la
búsqueda por nombre exacto. El parche existe desde el 2026-11-20 12:27 como
`p15_main64d4cec_3_zirx.patch` (sufijo del upload); los briefs buscaban el nombre exacto
`p15_main64d4cec.patch` y concluyeron "NO ESTÁ EN DISCO". Esa conclusión queda SUPERADA.

## 1. El parche P15 — ENCONTRADO (el "perdido")

- **Local:** `~/workspace/user/files/p15_main64d4cec_3_zirx.patch` — 19,301 B, md5 `f3bbb75d35146562a6f8c3196f876cd5`
- **En esta rama:** `docs/kimi-briefs/patches/p15_main64d4cec.patch` (mismo contenido, nombre canónico que usan los briefs)
- **Contenido:** parche completo P15, 9 archivos (`bm_fused.py`, `dqi_decoder_v1.py`, `dqi_kmul42.py`, `dqi_tower_inv.py`, `dqi_tower_inv2.py`, `dqi_tower_inv3.py`, `qf.py`, `tower_inv3_e1d.py`, diff `mainsrc/` → `src_p15/`). Torre 75 T → 66 T; total QF 710,312 → 670,307.
- **No confundir con el hunk aplicado:** `p15_hunk_only.patch` (801 B, md5 `a09968fb…`) es SOLO el hunk de `dqi_tower_inv.py` (@@ -102) que se aplicó para la ruta (a) QF+P15 (Gold PASS, T=670,307). El parche completo de Elán es el de 9 archivos.
- **Referencia en GitHub main:** `docs/QF_P15_AND_2026-11-20.md` y `CHANGELOG.md` (main `457cc742`) ya citan este parche con su md5 `f3bbb75d…`; el ARCHIVO .patch no estaba en GitHub — por eso se sube aquí.

## 2. El parche QF (base del P15)

- **Local:** `~/workspace/user/files/qf_main64d4cec_0_ehz1.patch` — 18,393 B, md5 `d2fdc8694fe5d21af8af08d14b4e9beb`
- **En esta rama:** `docs/kimi-briefs/patches/qf_main64d4cec.patch` (mismo contenido, nombre canónico)
- Mismos 9 archivos, diff `a/` → `b/`. Es la base QF sobre la que aplica el P15.

## 3. Briefs Kimi DQI — ENCONTRADOS (no estaban en GitHub)

- `BRIEFS_KIMI_DQI_V2_2026-11-20.md` — 21,067 B, md5 `f8446fee74194b85d7cfe63dd1fd01c8` (vigente; la v2)
- `BRIEFS_KIMI_DQI_2026-11-20.md` — 15,147 B, md5 `a0fe453f4520bd3d47fea65310c6842f` (v1)
- `ANEXO_CORRECCIONES_BRIEFS_KIMI_2026-11-20.md` — 13,206 B, md5 `8ac1c23faeef80f2604af55de4a05d34`
- **Corrección a la v2 (l.6 y l.157):** "EL PATCH NO ESTÁ EN DISCO — Elán debe re-enviarlo" queda SUPERADO por §1. Elán NO tiene que re-enviar nada. Los números medidos por Elán (670,307 / 8.7154 / 4.9876 / 66 T) siguen vigentes; la aritmética sobre ellos está verificada por Brujo, Datos y Auditor.
- **Búsqueda en GitHub (2026-11-24):** `BRIEFS_KIMI` = 0 resultados en todo el repo; los briefs NO estaban en GitHub — por eso se suben aquí.

## 4. Cadena de verificación (en esta rama)

- `VERIFICACION_BRUJO_BRIEFS_KIMI_V2_2026-11-20.md` — 6,349 B, md5 `9dc292fe527d4f25f0fbce60d534174d`
- `REVISION_AUDITOR_VERIFICACION_BRUJO_BRIEFS_KIMI_V2_2026-11-20.md` — 11,552 B, md5 `815c9421077bb01de66c426097a2a770`

## 5. Mapeado pero NO subido (queda en disco local, con md5)

- `SUPERVISION_DATOS_ANEXO_BRIEFS_KIMI_2026-11-20.md` — 13,364 B, md5 `148cba4bf2e42777f013fcc2df8c01ac` (`qcc-data/test-dev/espiral-prototipo/`)
- `REVISION_AUDITOR_ANEXO_BRIEFS_KIMI_2026-11-20.md` — 10,236 B, md5 `4408235b481a55a7c0ed7287c1474c9f` (`~/workspace/auditoria/`)
- `VERIFICACION_BRUJO_RESPUESTA_KIMI_DQI_2026-11-20.md` — 14,767 B, md5 `5215fd6c69c80326e198a27f464f85d2` (respuesta de Kimi, T1 NO CABE; T2 NO ESTABLECIDO; T3 tau[35] REFUTADO)
- `SUPERVISION_DATOS_RESPUESTA_KIMI_DQI_2026-11-20.md` — 13,890 B, md5 `d4c8ba706c1eb0aa716d4e2a8a2ed838`
- `REVISION_AUDITOR_RESPUESTA_KIMI_DQI_2026-11-20.md` — 18,511 B, md5 `30a5020015f4a25e5d3a69bd221f4941`
- `invsqrt-para-kimi.zip` — 871,465 B, md5 `ba41831075ef299000eceb473308be29` (4 archivos: `invsqrt-public-v34.kmx`, `rotaciones_anf.json`, `intermedios_q28_to_x.json`, `monomios_Qu_thr1e-10.json`). Binario: NO se sube a esta rama snapshot (solo texto). Copias idénticas en `~/workspace/your_files/` y en `~/workspace/goals/quantum-circuit-compilation-competition/files/`.

## 6. Estado en GitHub

- Rama: `local/kimi-briefs-v2-2026-11-24`, desde main `457cc7423a6ef426c1655cbbfae520405efcf559` (PR #36).
- Nada a `main`. Snapshot solo texto, 8 archivos (este mapa + §3 + §4 + §2). Total ~109 KB.
- El tag de GitHub (propuesto `v5-4.90803`) sigue pendiente de confirmación de Elán — no es parte de este snapshot.
