# Anexo — Correcciones a los briefs Kimi DQI (por Elán, 2026-11-20)

**Fecha:** 2026-11-20 ~10:40 CST
**Origen:** Elán leyó `BRIEFS_KIMI_DQI_2026-11-20.md` (131 l. / md5 `a0fe453f…`) y encontró errores de premisa. Este anexo se pega en los briefs ANTES de pasárselos a Kimi.
**Método del Brujo:** verifiqué las líneas citadas del brief en disco; recomputé por mi cuenta los números que se pueden reproducir (aritmética y break-even); verifiqué en código lo que se puede verificar; los números medidos por Elán en su build se citan como medidos por Elán, no como míos, y digo cuáles no pude reproducir.
**⚠️ EL PATCH NO ESTÁ EN DISCO:** busqué `p15_main64d4cec.patch` en todo `~/workspace` (y en `/home/hatch`) — NO existe. Los únicos `*p15*` son archivos no relacionados. Elán dice que ya lo envió, pero no lo tengo. **Elán debe re-enviarlo.** Sin el patch, Kimi no puede partir de la base corregida. No inventé el patch ni sus contenidos.

---

## Corrección 1 — La base está desactualizada; "75 T es el piso" es falso (corrige §0 y Tarea 1)

**Brief que corrige:** §0 (base QF: Q=1,857, T=710,312) y Tarea 1 (que parte de 710,312 y asume la inversión por torre en 75 T).

**Lo que cambia (medido por Elán en su build, Gold PASS, seed fija, 102,400 tiros, 5 errores de valor, 0 de fase, R=1.2131):** el plan de 15 AND para GF(64) baja la inversión por torre a **66 T** (no 75 T). **Base corregida (QF + 15 AND): Q=1,857, T=670,307, factor DQI ≈ 8.7154, geomean ≈ 4.9876** (contra 4.89215). Desglose medido en su build: BM 248,312, omega 57,540, barrido 4,095 × 89 = 364,455 (66 inversión + 11 escalera + 12 fase).

**Verificado por el Brujo (recomputado, no re-medido):**
- Barrido: 4,095 × 89 = 364,455 ✓ (66 + 11 + 12 = 89).
- Total: 248,312 + 57,540 + 364,455 = 670,307 ✓.
- Factor: 8.22455 × (710,312/670,307) = 8.7154 ✓.
- Geomean: 4.89215 × (8.7154/8.22455)^(1/3) = 4.9876 ✓.
- **No pude reproducir:** el build de Elán mismo (no tengo el patch ni su .kmb); el Gold PASS con 5/0 y R=1.2131 es su medición, no la mía. El desglose (248,312 / 57,540 / 364,455) es su medición, no la mía.

**Efecto en los briefs: Kimi debe partir del patch `p15_main64d4cec.patch` y no de 710,312.** Si no, sus ahorros salen sobreestimados (todo ahorro que proponga se mediría contra una base que ya no existe).

---

## Corrección 2 — La Tarea 3 (eliminar tau, Q→1,425, ×1.698) tiene la premisa mal (corrige Tarea 3, l.102)

**Brief que corrige:** Tarea 3, l.102 — "El registro tau (~432 qubits, ~23% de Q) es 'frío' durante el barrido y solo lo necesita `bm.reverse()`… Q bajaría de 1,857 a ~1,425, y el factor DQI subiría por (1,857/1,425)² = 1.698×".

**Por qué falla (Elán):** tau es estado del propio BM, porque `σ ← σ + α·x·τ` lo usa en las 70 rondas. El pico global de 1,857 ocurre dentro del BM, con tau vivo (el pico del barrido es 1,837 en su medición). Soltar tau solo durante el barrido no baja el máximo. Qué haría falta: un BM sin tau. Recomputarlo después tampoco cabe, porque ya probaron que τ∝Psi es falso y tau no sale de σ y S.

**Verificado por el Brujo (en código):** `forward_round` (`dqi_bm_stage_v1.py` l.248) llama a `bm_update` (l.263–265), que hace `self._mul(alpha, self.tau[i], self.sigma[i])` — tau se lee en CADA una de las 70 rondas, no solo en `bm.reverse()`. `bm_swap` (l.260–262) también usa tau en cada ronda. La premisa "frío durante el barrido" es falsa: tau está vivo durante todo el BM. El pico global de 1,857 dentro del BM es consistente con A-TE-3 (el pico es intra-etapa, casi seguro en la última ronda de `bm_forward`). **No pude reproducir:** el pico del barrido de 1,837 (medición de Elán, no tengo su build). **Precisión D-KB-1 (Datos, aplicada):** las citas de línea son de la copia QF (`tau35-prune/src/dqi_bm_stage_v1.py`); en la copia del repo (`~/workspace/qcc-dqi/src/dqi_bm_stage_v1.py`) `forward_round` está en l.157 y `bm_update` en l.172–174 (verificado por el Brujo: l.157 `def forward_round`, l.172 `with b.mark('bm_update')`, l.173 `for i in range(self.bu(r) + 1)`, l.174 `self._mul(alpha, self.tau[i], self.sigma[i])`). La lógica es idéntica en ambas copias. **Corrección A-V2-3 (Auditor, aplicada):** la cita original decía l.170–173 y l.173 para el `_mul` — corrida por una línea; el bloque es l.172–174 y el `_mul` es l.174 (verificado con grep -n; el archivo no cambia desde el 9 nov, no es deriva).

**Lo que debe pedir la tarea:** **"demuestra si existe un BM sin tau"**, no asumir 1.698×. El 1.698× presupone que tau se puede soltar sin costo y que el pico bajaría — ambas premisas son falsas. (El ×1.698 aritmético es correcto como cálculo — (1,857/1,425)² = 1.698 — pero el 1,425 no es alcanzable soltando tau solo durante el barrido.)

---

## Corrección 3 — El presupuesto de la Tarea 1 se encoge con la base nueva (corrige Tarea 1, l.52)

**Brief que corrige:** Tarea 1, l.52 — "T_E < 66,063 T Y ΔQ_E < 180 qubits (con T_E=0). A T_E=16,331 → ΔQ máx 131; a 30,000 → 93; a 50,000 → 40; a 66,063 → 0."

**Tabla corregida (Elán, con la base de 670,307):**

| T_E | ΔQ máx (base 670,307) | ΔQ máx (base 710,312, para comparar) |
|---|---|---|
| 0 | **119** | 180 |
| 16,331 | **71** | 131 |
| 30,000 | **33** | 93 |
| 50,000 | **−19** | 40 |
| T_E máx con ΔQ=0 | **42,679** | 65,951 |

**Verificado por el Brujo (recomputado por mi cuenta con la regla de break-even):** reproduje la tabla completa con la base nueva (Parte B sobre base nueva: T = 248,312 + 57,540 + 94,185 = 400,037, Q = 2,285; costo base nueva = 1,857² × 670,307; break-even (2,285+ΔQ)² × (400,037+T_E) = 1,857² × 670,307): T_E=0 → 118.8 (≈119); 16,331 → 71.2 (≈71); 30,000 → 33.4 (≈33); 50,000 → −18.7 (≈−19); T_E máx con ΔQ=0 → 42,679. **Todos coinciden con Elán.** Además reproduje su tabla QF exacta con el mismo método (T_E=0 → 179.8 ≈ 180; 16,331 → 131.4 ≈ 131; 30,000 → 92.9 ≈ 93; 50,000 → 39.9 ≈ 40; T_E máx con ΔQ=0 → 65,951) — el método está validado. Nota: el brief dice "66,063" como T_E máx; el exacto es **65,951** (Elán lo reprodujo; el 66,063 era el valor redondeado del análisis original).
- **Supuesto explícito de mi recomputación:** la Parte B sobre la base nueva tiene T = 400,037 (BM 248,312 + omega 57,540 + barrido por traza 94,185, que no usa la inversión por torre y no cambia con el patch) y Q = 2,285 (Psi 420 Q). Que reproduzca los 5 números de Elán exactamente valida el supuesto. **Precisión D-KB-2 (Datos, aplicada):** el supuesto está confirmado por una segunda vía independiente — el conteo estructural de inversiones (verificado por el Brujo): BM 250,832 − 248,312 = 2,520 = 280×9; omega 58,170 − 57,540 = 630 = 70×9; barrido 401,310 − 364,455 = 36,855 = 4,095×9; total 2,520 + 630 + 36,855 = 40,005 = 710,312 − 670,307 = 4,445×9 (280 + 70 + 4,095). Cada inversión ahorra exactamente 9 T (75 − 66), y el conteo de inversiones (BM 280, omega 70, barrido 4,095, una por posición) reproduce la baja total. Las cifras de BM y omega de la base nueva quedan confirmadas estructuralmente, no solo por reproducir los 5 números de Elán.

**Consecuencia:** el EEA de peor caso (T_E ≥ 66,063 y ~1,384 qubits) ya no cabía, y ahora cabe menos. La Parte B sigue ganando solo si Psi sale casi gratis en Q (ΔQ_E < 119 con T_E=0, y menos si T_E > 0; a T_E=50,000 ya no hay margen de Q: −19).

---

## Corrección 4 — "Un qubit vale ~20× un Toffoli" está mal (corrige §0, l.12)

**Brief que corrige:** §0, l.12 — "Q está al cuadrado — un qubit vale ~20× un Toffoli".

**Lo correcto (Elán):** un qubit pesa **2·T/Q ≈ 765 Toffoli con la base QF y ≈ 722 con la nueva**. Es ×36 más de lo que dice el brief.

**Verificado por el Brujo (recomputado):**
- QF: 2 × 710,312 / 1,857 = 765.01 ≈ 765 ✓.
- Nueva: 2 × 670,307 / 1,857 = 721.92 ≈ 722 ✓.
- 765/20 = 38.25; 722/20 = 36.1 — el "×36" de Elán corresponde a la base nueva (722/20 = 36.1) ✓.
- **La regla de break-even que sí da el brief es correcta:** T_nuevo/T_viejo < (Q_viejo/Q_nuevo)². Verificado: el score es R·Q²·T, así que score_nuevo < score_viejo ⟺ (Q_nuevo/Q_viejo)² × (T_nuevo/T_viejo) < 1 ⟺ T_nuevo/T_viejo < (Q_viejo/Q_nuevo)². ✓

**Efecto:** si Kimi usa el "20×" para decidir, sacrifica qubits de forma errónea (un qubit cuesta ~36× más de lo que el brief le dice). Debe usar 722 Toffoli/qubit (base nueva) o la regla de break-even, no el 20×.

---

## Confirmaciones — lo que coincide con las pruebas de Elán (para el anexo)

1. **Filtro por f=1 bloqueado por la API — coincide.** El Brujo lo verificó por su cuenta (Workstream 3: `push_condition` exige `km.b`, `bit_store` prohíbe control por qubit, HMR mide en base X y da 50/50). Elán llegó a un cierre equivalente por otra ruta: condicionar cada posición por `E[p]` da 670,218 contra 670,307, o sea ruido, porque `mbuc` es aleatorio. **No pude reproducir** el 670,218 (medición de Elán, no tengo su build); lo cito como suyo.
2. **GF(2¹²) en 42 ANDs y Montgomery peor — coinciden.** Verificado por el Brujo: el barrido de la etapa C midió 435,456 casos, TODOS exactamente 42 ANDs (no existe <42); Montgomery es 2.16–2.52× peor que la inversión por posición (773,841 T a 63 T/mul / 663,303 T a 54 T/mul) y 49,128 Q extra. ✓
3. **Hoisting de delta en omega — coincide con la corrección de base.** Con 66 T el ahorro es ≈ 34×66×2 = **4,488 T**, no los 5,100 del brief (que usa 75 T). Verificado por el Brujo (recomputado): 34×66×2 = 4,488 ✓; 34×75×2 = 5,100 ✓. (La construcción del hoisting verificada por el Brujo — Q=1,857, T=705,212 — usa el ValueInv de 75 T; sobre la base nueva el ahorro sería 4,488 T, es decir T ≈ 665,819 — **proyección, no medición**.)

---

## Agregados a la Tarea 2 (BM) — preguntas nuevas para Kimi

**A. Ventana de coeficientes no nulos de σ y tau por ronda.** `bm_update` son 117,432 T = 2,796 multiplicaciones de 42 T (1,398 por dirección) — verificado por el Brujo (conté el loop yo mismo: 1,398 muls/dir, 2,796 total; 117,432/2,796 = 42.0 exacto). Preguntar explícitamente: **¿cuál es la ventana de coeficientes no nulos de σ y tau por ronda?** La cota `bu(r)` es de peor caso (bu(r) = min(35, r//2+2) — crece con r hasta 35). Si en la práctica solo una ventana angosta de σ y tau es no nula por ronda, las multiplicaciones reales son menos que 2,796 y hay un ahorro medible. Que Kimi mida la ventana por ronda (no la asuma).

**B. Cuánto error de decodificación tolera el score.** Pasar de 5 errores a 0 solo mueve R de 1.2131 a ≈1.191, o sea **~1.8% del DQI**. Verificado por el Brujo (lente Murphy, con las funciones del propio verificador: k=0 → R = 1.191260; 1.2131/1.19126 = 1.0183 → +1.83%). Eso acota lo que vale recortar casos raros: **ninguna optimización que solo reduzca los errores de decodificación puede ganar más de ~1.8% del DQI.** Si Kimi propone recortar casos raros (p. ej. pesos altos), que demuestre que el ahorro en T o Q supera ese techo — si no, no vale la pena.

---

## Resumen para pegar en los briefs

| # | Corrección | Brief que corrige | Base nueva |
|---|---|---|---|
| 1 | Base QF + 15 AND: T=670,307 (no 710,312); inversión por torre 66 T (no 75 T); factor 8.7154, geomean 4.9876 | §0, Tarea 1 | Kimi parte de `p15_main64d4cec.patch` (**Elán debe re-enviarlo — no está en disco**) |
| 2 | Tau NO es frío: se lee en las 70 rondas del BM; el pico 1,857 está dentro del BM. La tarea debe pedir "demuestra si existe un BM sin tau", no asumir 1.698× | Tarea 3, l.102 | — |
| 3 | Presupuesto Tarea 1 con base nueva: ΔQ máx 119 / 71 / 33 / −19 (T_E 0 / 16,331 / 30,000 / 50,000); T_E máx con ΔQ=0 → 42,679 | Tarea 1, l.52 | Parte B solo gana si Psi sale casi gratis en Q |
| 4 | Un qubit vale 2·T/Q ≈ 722 Toffoli (base nueva), no ~20×. Usar 722 o la regla T_nuevo/T_viejo < (Q_viejo/Q_nuevo)² | §0, l.12 | — |
| A | Tarea 2: preguntar por la ventana de coeficientes no nulos de σ y tau por ronda (bu(r) es peor caso) | Tarea 2 (agregado) | bm_update = 2,796 muls × 42 T |
| B | Tarea 2: el techo por recortar errores es ~1.8% del DQI (R 1.2131 → 1.191) | Tarea 2 (agregado) | — |

**Números citados como medidos por Elán (no re-medidos por el Brujo):** 670,307, 8.7154, 4.9876, 248,312, 57,540, 364,455, 66 T, 1,837 (pico del barrido), 42,679 (recomputado y verificado por el Brujo — ver Corrección 3), 670,218 (condicionar por E[p]), 1.8% (recomputado y verificado por el Brujo — ver Agregado B). **Números recomputados/verificados por el Brujo:** 364,455; 670,307; 8.7154; 4.9876; la tabla de la Corrección 3 completa (119/71/33/−19/42,679) y la tabla QF (180/131/93/40/65,951); 765 y 722; 4,488; 2,796 muls; el uso de tau en las 70 rondas (en código). **No pude reproducir:** el build de Elán (sin patch), su Gold PASS (5/0, R=1.2131), el pico del barrido de 1,837, el 670,218. Nada a Kaggle, nada a main, nada al repo. Cadena: Brujo → Datos supervisa → Auditor revisa → Elán decide (y es él quien le pasa los briefs corregidos a Kimi).
