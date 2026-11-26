# Revisión a fondo — Frente Quantum (Brujo) — 2026-11-24

**Orden:** Elán, 2026-11-24 ~11:59 (principal, por voz) — todos revisen sus proyectos a
fondo; el tablero y el principal están desactualizados y se está retrabajando lo ya
hecho/decidido. **Método:** verificado en disco (md5) y en vivo (Kaggle/GitHub) donde se
indica; lo no re-verificado hoy se marca como "del registro".

## A. VIGENTE (verificado hoy o con cadena completa)

1. **Selección final Quantum: v7 (58647127, 5.00918) + v6 (58633092, 5.00379).** Verificado
   en vivo por el Brujo 2026-11-24 11:52 (conector Kaggle, grupo Selected). La v4.1 está
   FUERA. Producción vigente = v7, 5.00918, mejor marca.
2. **Gold (motor nuevo), segunda corrida: M11 FAIL, cadena COMPLETA.** Reporte
   `gold-verif/REPORTE_GOLD_DECODIFICADOR_COMPLETO_2026-11-23.md` (md5 `c295511a…`),
   Datos `07dd1cef…`, Brujo `d768f326…` + adenda `9fcd2b6f…`, Auditor `54851ee5…` —
   todos CONCURRO (PASA). Circuito completo Q=15,432, T=149,796; verificador oficial
   102,400/102,400 errores de valor, 0 de fase. Causa: M6/M9 placeholders (Euclides
   no-op, scan de 1 escalera). M12 no ejecutado. **Pendiente de Elán: rediseño de Q +
   M6/M9 reales (tercera corrida).**
3. **H8: conjunto de fallo NO ACOTABLE, Fase 2b.** Re-do NO PASA (en firme); corrección
   mínima PASA, cadena completa (Brujo `381f8910…` + adenda `331c2795…`). El Gold lo
   decide Elán (ver A.2).
4. **Opción (b): parte 1 en disco, derivación completa para hoy 15:00.**
   `NOTA_TRABAJO_OPCION_B_CARRY_2026-11-23.md` (`31ae87d4…`) y
   `DERIVACION_CARRY_PARTE1_CODIGO_2026-11-24.md` (`d5ad1cbe…`): semántica exacta del
   código, equivalencia del marker, reducción a las condiciones (A) y (B). Falta probar
   (A)/(B) desde el oráculo.
5. **Kimi briefs + parches: mapeados y en GitHub (hoy ~12:05).** Rama
   `local/kimi-briefs-v2-2026-11-24` desde main `457cc742`, commit `20a96806…`, 8
   archivos en `docs/kimi-briefs/` (briefs v1+v2, anexo, mapa, verificación Brujo v2,
   revisión Auditor v2, parches QF+P15 con nombres canónicos). Verificado por read-back
   (blob SHA `cb279afd…` idéntico). Nada a main.
6. **GitHub main: `457cc742`** (PR #36, B7). Verificado en vivo hoy (list_commits).
7. **GitHub tag: pendiente de confirmación de Elán** (propuesto `v5-4.90803`).
8. **CASMI v4 con fusión V1 (k=15): GO de Elán 11:57–11:58, despachado al Sabueso.**
   No es mi frente; se anota porque es la decisión del día.

## B. REZAGADO (lo que el tablero / mis listas decían y ya no es así)

1. **TABLERO, sección Quantum:** dice score 3.33544, selección final ref 58289295,
   notebook v2 público, main `e4d4180`/`cc798147`, "ZIP→main". Todo de nov 12–13.
   **Nada de eso es vigente** (ver A.1, A.6; notebook ver §G).
2. **Mi propia lista (hasta hoy 11:52):** selección final "v6 + v4.1 hasta que Elán la
   marque". Rezagada; corregida en vivo 11:52 y en MEMORY.md. No vuelve a listarse
   como pendiente.
3. **Briefs Kimi v2 (l.6, l.157):** "EL PATCH NO ESTÁ EN DISCO — Elán debe
   re-enviarlo". SUPERADO por §A.5. Elán no re-envía nada.
4. **Auditoría de tareas pendientes del 12 nov (0/8):** su foto ya no describe el
   frente; el estado actualizado es §E.

## C. YA DECIDIDO / HECHO Y SE ESTABA RETRABAJANDO (el retrabajo que Elán señaló)

1. **Selección final:** Elán ya la había marcado (v7+v6). Yo la seguía listando como
   pendiente y el Coordinador la relayó así a las 11:34. **Detenido hoy 11:52.**
2. **Parche P15 (+ QF):** Elán lo pasó el 20 nov (4 días). Se lo seguimos pidiendo
   porque los briefs buscaban el nombre exacto. **REGLA (Elán, hoy ~12:00, registrada
   en MEMORY.md): el P15 y el QF NO se le vuelven a pedir a Elán** — quien los necesite
   los toma de GitHub (`docs/kimi-briefs/patches/`) o del disco. Lección: antes de
   concluir que algo está perdido o pedir re-envío, verificar por contenido/hash y por
   nombres parecidos, no solo por el nombre exacto.
3. **Fusión V1 de CASMI:** medida y recomendada, nunca construida (la v3 se hizo con
   V0). Otro frente; Elán ya dio el GO a la v4 (ver A.8).
4. **Gold "completado" con placeholders vacíos:** la primera corrida Gold se reportó
   con M7/M8/M9 en stub (mismo sha `4a5f45be…`); la segunda corrida los hizo reales
   en tamaño pero M6/M9 siguen siendo placeholders funcionales (Euclides no-op, scan
   de 1 escalera). No se vuelve a reportar un Gold como "completo" sin M11 PASS.

## D. FALTANTE EN EL TABLERO (lo que el Coordinador debe actualizar)

Todo §A: scores v6/v7, selección v7+v6, Gold segunda corrida (M11 FAIL, cadena
completa, decisión pendiente), H8 (NO ACOTABLE, corrección PASA), opción (b) (parte 1
hecha, cierre 15:00 hoy), Kimi (mapeo + rama `local/kimi-briefs-v2-2026-11-24`,
commit `20a96806…`), main `457cc742`, notebook v7 (§G), tag pendiente, regla P15
(§C.2). El tablero no tiene nada del 20–24 nov en Quantum.

## E. Auditoría del 12 nov (8 ítems) — estado actualizado

1. **Marcar selección final — HECHA.** Elán la marcó; verificado en vivo (A.1).
2. **Postura C14/B7 del planner — DECIDIDA POR DIRECCIÓN.** Elán (20–21 nov):
   replicar/adaptar a nuestra arquitectura, no copiar literal; ruta defendible =
   reconstruir con generador propio + cita + declaración (precedente V34, nov 8).
   La adopción literal del planner queda cerrada.
3. **Posible v3 del notebook — SUPERADA.** El notebook v7 está construido (ver §G);
   el concepto "v3" es obsoleto (scores ya en 5.00918).
4. **Actualizar final_submission.zip — HECHA/SUPERADA.** ZIP v7 subido a Kaggle
   (ref 58647127, 5.00918). Los zips viejos (2c3018f8/ce1d12a6) son históricos.
5. **Binarios grandes — PARCIAL.** ZIP v7 en Kaggle; .kmb en Drive (respaldos
   verificados). GitHub Release sigue sin crearse (0 releases al 12 nov; **no
   verificado hoy**).
6. **Relativizar .py + vender kickmix — PENDIENTE, sin avance registrado.** Clones en
   `github/relativizar/` bajo restricción de solo lectura; sin ejecutor asignado.
7. **Prueba de Kiwi — HECHA.** Kimi respondió; respuesta verificada 20 nov (T1 NO
   CABE, T2 NO ESTABLECIDO, T3 tau[35] REFUTADO).
8. **Descarga de Lera — PENDIENTE DE DECISIÓN, posiblemente superada.** La frontera
   dfthcsos (8,143,60) ya se midió localmente desde el notebook público. **Preguntar
   a Elán si sigue vigente o queda cerrada por la medición local.**

## F. Pendientes pequeños (del registro, no re-verificados hoy)

O7 + adenda D-O7-7; corrección de alcance combined-build línea 12 + fórmula A-QF-1;
figura 9.6453 vs 9.6452 (decisión Datos/Elán); micro-opt invsqrt fila 1 (espera
Datos, necesita Gold); escala diádica (espera Datos); medir las tres formas de ángulos
en DQI (GO pendiente); spiral agent como constructor (cambio de rol); Tests A/C;
Kimi Tarea 2 (NO ESTABLECIDA). Ninguno bloquea lo vigente.

## G. Notebook v7 — ESTADO AMBIGUO, VERIFICACIÓN EN VIVO PENDIENTE

- `save_notebook_v7.log` (20 nov 10:43): guardado devolvió **versión 7** (kernel
  144639626). No hay `build_notebook_v7.py` (solo hasta v6); la v7 es la v6 + la
  corrección D-NB6-1.
- `get_notebook_info_v7.log` (misma hora 10:43): `current_version_number: 7`, pero el
  blob muestra contenido **v5** (4.90803, ref 58594222, main `a13598a9`).
- **No se puede afirmar** "publicado con la corrección" ni "no publicado" con estos
  logs. **Falta una consulta en vivo nueva** que diga qué contiene hoy la pública.
  No se republica nada sin esa verificación y sin GO de Elán.

## H. Regla nueva (de hoy)

**El P15 y el QF no se le vuelven a pedir a Elán.** GitHub: `docs/kimi-briefs/patches/`
(rama `local/kimi-briefs-v2-2026-11-24`); disco: `~/workspace/user/files/`.
