# Regla — Los parches P15 y QF no se le vuelven a pedir a Elán (2026-11-24)

**Orden de Elán, 2026-11-24 ~12:00 CST (principal):** "Tenemos cuatro días con el parche
y me lo siguen pidiendo todavía."

## Lo que pasó

El parche P15 existe desde el 2026-11-20 12:27 CST como
`p15_main64d4cec_3_zirx.patch` (19,301 B, md5 `f3bbb75d…`). Se lo siguieron pidiendo
porque los briefs buscaban el nombre exacto `p15_main64d4cec.patch` y concluyeron que
no estaba en disco. La conclusión de los briefs v2 (l.6, l.157) — "EL PATCH NO ESTÁ EN
DISCO — Elán debe re-enviarlo" — **queda superada y es incorrecta**. Elán no tiene que
re-enviar nada.

## La regla

**Nadie le vuelve a pedir a Elán que re-envíe el P15 ni el QF** — ni nosotros, ni Kimi.
Quien los necesite los toma de GitHub o del disco:

- **GitHub (esta rama):** `docs/kimi-briefs/patches/p15_main64d4cec.patch`
  (contenido = `p15_main64d4cec_3_zirx.patch`, md5 `f3bbb75d…`) y
  `docs/kimi-briefs/patches/qf_main64d4cec.patch`
  (contenido = `qf_main64d4cec_0_ehz1.patch`, md5 `d2fdc869…`).
- **Disco:** `~/workspace/user/files/p15_main64d4cec_3_zirx.patch` y
  `~/workspace/user/files/qf_main64d4cec_0_ehz1.patch`.
- **Mapa completo:** `docs/kimi-briefs/MAPA_PARCHES_KIMI_2026-11-24.md`.

## Para los briefs futuros a Kimi

- Los materiales de Kimi apuntan a GitHub/disco para los parches. **Kimi tampoco le
  pide nada a Elán.**
- Lección vigente para todos: antes de concluir que algo está perdido o de pedirle a
  Elán que lo re-envíe, se verifica por contenido/hash y por nombres parecidos, no
  solo por el nombre exacto.
- Precisión de Elán (12:01): el problema no es solo pedirle algo que ya tiene — es que
  el pedido lo pone a ÉL como el cuello de botella, como si no hubiera pasado las cosas
  y por eso no se trabaja, cuando él ya las pasó. Si aun así algo no se localiza, el
  pedido dice claro "no logramos localizar lo que ya nos pasaste" — el fallo es
  nuestro, jamás enmarcado como que él no lo pasó. Vale también para decisiones: si
  algo "no está decidido", verificar en el tablero y en sus mensajes antes de volver a
  preguntarle como si no hubiera decidido.
