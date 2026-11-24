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
- Precisión de Elán (12:01), textual: "No, lo que a mí me molesta no es eso, sino que
  siguen pidiéndome cosas que yo ya les había pasado, entonces me hacen ver que el que
  no les ha pasado las cosas soy yo y por eso no están trabajando cuando yo ya les pasé
  las cosas." El problema no es solo pedirle algo que ya tiene — es que el pedido lo
  pone a ÉL como el cuello de botella, como si no hubiera pasado las cosas y por eso no
  se trabaja, cuando él ya las pasó. El P15 es el ejemplo: los briefs concluyeron "NO
  ESTÁ EN DISCO" y le pidieron re-enviarlo, como si no lo hubiera mandado, cuando lo
  mandó hace 4 días. Es un tema de justicia con él: el que no encuentra algo somos
  nosotros, no él el que no lo dio.
- **Regla vigente, para todos los frentes y para lo que se le pida a Kimi a través
  nuestro:**
  1. Antes de pedirle a Elán algo que él pudo haber pasado ya, el frente verifica
     EXHAUSTIVAMENTE: disco, GitHub, TABLERO, contenido/hash y nombres parecidos.
     Pedirle re-enviar es el último recurso, no el primero.
  2. Si aun así no se encuentra, el pedido dice claro: "no logramos localizar lo que ya
     nos pasaste" — el fallo es nuestro, jamás enmarcado como que él no lo pasó.
  3. Esto vale también para decisiones: si algo "no está decidido", se verifica en el
     tablero y en sus mensajes antes de volver a preguntarle como si no hubiera
     decidido.

## Matiz de Elán (12:07) — "no lo tenemos" no es excusa para no trabajar

Cita textual: "Yo solamente veo el ejemplo. Ya les había pasado lo del parche desde
hace cuatro días y apenas me lo están volviendo a pedir, excusándose, y no habían
trabajado excusándose con que yo no se los había pasado. Cuando ese parche ya estaba."

El matiz: el "no me lo pasaste" no solo lo puso a él como el cuello de botella — **fue
la excusa para no haber trabajado**. El parche llevaba 4 días en disco y apenas ahora
se lo vuelven a pedir.

**Regla que se suma a la de las 12:01 y 12:04, tal cual: "no lo tenemos" no es excusa
válida para no trabajar.** Si algo falta, se verifica exhaustivamente EL MISMO DÍA
(disco, GitHub, tablero, hash, nombres parecidos) y si de verdad no aparece, se reporta
ESE MISMO DÍA con la búsqueda exacta que se hizo — no se deja pasar días y luego se le
pide a Elán como si él no lo hubiera dado. El que no encuentra algo somos nosotros; el
que no trabajó por eso, también.
