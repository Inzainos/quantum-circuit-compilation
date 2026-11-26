# Derivación del carry — Parte 1: semántica exacta del código (EN CURSO)

**Fecha:** 2026-11-24 ~11:45 CST. **Estado: EN CURSO, NO cerrada.** Paso 1 (semántica del
paso de cadena) CERRADO desde el código; paso 2 (identificación cadena↔Euclides) REDUCIDO a
dos condiciones (A) y (B) — su prueba desde el oráculo es lo que falta. ETA del documento
completo: **15:00 CST hoy**. Si (A)/(B) no se prueban, se reporta como HALLAZGO con el
contraejemplo exacto, no como bloqueo abierto.

Fuentes leídas en texto (copias locales de la lectura Fase 1, no del árbol restringido):
- `carry-decoder-lectura-fase1/src_dqi__kit__kv_unfused5__exp__next__carry__flag_carry.py` (101 l.)
- `carry-decoder-lectura-fase1/src_dqi__kit__kv_unfused5__playbook__kit__decoder__final_decoder__decode.py` (442 l.)
- `carry-decoder-lectura-fase1/src_dqi__kit__kv_unfused5__playbook__kit__decoder__exp__decoder__common.py` (`cx` l.52, `combine`)
- `carry-decoder-lectura-fase1/src_dqi__kit__kv_unfused5__playbook__kit__decoder__exp__confluent_extract__model.py` (201 l., oráculo l.136–146)

## 1. La recurrencia implementada (definición, no teorema)

`flag_carry.py`: `carry_forward` (l.22–31) — si `gi==16`, `bank['flag']=pole`; si no, mide el
polo en X (HMR) y guarda el bit en `bank['masks'][gi]`. `carry_pole` (l.34–40) devuelve
`bank['flag']` (con pago CZ si `gi<16`). `carry_next` (l.43–51):

```
b.x(pole)
bank['flag'] = zero_flag(b, list(marker) + [pole])
b.x(pole)
```

`zero_flag` vale 1 si y solo si TODAS sus entradas son 0; con el sándwich X, el polo
contribuye como `[pole==1]`. Es decir, por DEFINICIÓN de la recomputación:

**F_{g−1} = [marker(g−1)==0] ∧ F_g**, con **F_16 = pole_16** (verdadero).

El `marker` (parche de `install`, l.76) es `combine(words[groups[gi−1]['word'] : +2])`: las
dos palabras de 12 bits del registro N del grupo gi−1, leídas durante el retorno del grupo
gi — es decir, en sus valores FORWARD (el grupo gi−1 aún no se ha descomputado en el
retorno, que va de 16 hacia 5). `combine` concatena las palabras (common.py).

La fórmula P(g−1) = P(g) AND cero(N(g−1)) NO es un teorema a probar desde la cadena: ES
la definición de cómo `carry_next` recomputa la bandera. El teorema a probar es que la
bandera recomputada coincide con el polo VERDADERO de cada grupo. El reporte H8 la enmarcó
mal (identidad entre elementos de campo, P_principal ≡ N por definición); el enunciado
correcto es a nivel bit (ver §3).

## 2. Equivalencia del marker (derivada del código)

Sea (N_final, D_final) el par del grupo g−1 al terminar su cadena forward (antes del
cswap), pole_{g−1} = [D_final==0] (`decode.py` l.406: `pole=zero_flag(b,D); b.cswap(pole,N,D)`).

**[marker(g−1)==0] ⟺ pole_{g−1} ∨ [N_final(g−1)==0].**

Cadena de equivalencias, cada paso verificado en el código:

(i) **(N,D) ≠ (0,0) siempre.** Cada paso de cadena es biyectivo (recurrencia §4, q≠0 por
`assert q` en `external_node_chain`) y D₀=1. Luego si D_final==0 entonces N_final≠0, y
tras el cswap el D resultante D₁≠0 en ambos casos.

(ii) **La normalización escala N por un elemento no nulo.** `external_normalize_paired`
(`decode.py` l.352–365): `u = norm(D₁)` (norm_xor_noscratch, l.356) y cada mitad de N se
multiplica por u (l.365: `mul_xor_noscratch(b,half,u,out)` + swap). R = GF(2¹²)[t]/(t²+t+K)
es CAMPO porque trace(2048)=1 (verificado por tres implementaciones en H1); la norma de un
elemento no nulo es no nula. Luego N₂ = u·N₁ con u≠0, así que [N₂==0] ⟺ [N₁==0]. (Las
demás operaciones sobre N son fases HMR, no cambian valores.)

(iii) **Los cx posteriores preservan el cero.** En `external_extraction` forward, tras la
cadena: `cx(b,d,a,c)` con `cx(b,x,z,c)`: `z ^= c·x` (common.py l.52) — es decir a ^= c·d,
d intacto (triangular); `b.cx(d, v[:12])` toca L, no N. Luego [N@carry-point==0] ⟺
[N₂==0]. (Los cx de `external_mul_head` se aplican dos veces y se cancelan.)

(iv) **N₁ = D_final si pole, N_final si no.** Por el cswap: [N₁==0] ⟺ pole_{g−1} ∨
[N_final(g−1)==0].

## 3. Reducción: la corrección del carry equivale a (A) y (B)

Con F_g = pole_g como hipótesis inductiva (base F_16 = pole_16), la corrección
F_{g−1} = pole_{g−1} exige:

**pole_{g−1} = (pole_{g−1} ∨ [N_final(g−1)==0]) ∧ pole_g**  para g = 6..16.

Análisis por casos (P = pole_{g−1}, Q = pole_g, Z = [N_final(g−1)==0]):

- **(A) Q=0 ⟹ P=0.** Si el grupo g no tiene polo, el grupo g−1 tampoco. (Los polos forman
  un sufijo en g: si pole_{g−1}=1 entonces pole_g=1.)
- **(B) Q=1 ∧ Z ⟹ P.** Si el grupo g tiene polo y N_final(g−1)==0, entonces el grupo
  g−1 tiene polo.

(A) y (B) son propiedades de los polos VERDADEROS y de los N finales de la ejecución real
(función del síndrome), no identidades algebraicas. La enumeración H8 (0 fallos en 100,000
muestras del modelo) y el notebook (0 errores en 102,400 tiros) son consistentes con que
(A) y (B) valgan para síndromes válidos; el conjunto de fallo es exactamente donde (A) o
(B) se violan.

## 4. Lo que falta (punto exacto)

Probar (A) y (B) desde el oráculo. El oráculo (`model.py` l.136–146, local) especifica la
división de Hermite: en el nodo i, `de = ev(D,gamma)`; si `de==0` → polo=i; si no,
cabeza (a,b) desde `ev(N,gamma)·inv(de)`, `H = N + [a,b]·D`, `Q = H/(t²+t+κ)` con resto 0;
si H==0 → terminación; `(N,D) ← (D,Q)`. La identificación pendiente: conectar el
D_final(g)==0 / N_final(g)==0 de la cadena (par (N,D) en el anillo R, pasos de Möbius
§4) con el `ev(D,gamma)==0` / terminación del oráculo, y de ahí la estructura de polos
del patrón de errores. Plan: (a) prueba desde el oráculo; (b) verificación empírica de
(A)/(B) instrumentando `extract(bank)` del modelo clásico local sobre instancias
aleatorias (raíces/pesos) — si aparece un contraejemplo, ESE es el hallazgo con el punto
exacto de ruptura.

## 5. Paso de cadena (para el registro)

`external_chain_step` forward no-primero (`decode.py` l.316): D ← D² (transitorio, se
deshace), L ← L + head·D² (con corrección c), L ← q·L, N ← N + head·D, swap(N,D),
N ← q·N. Recurrencia resultante: **N' = q·D, D' = N + head·D** — paso de Euclides /
fracción continua sobre el cociente R = N/D: R' = q/(R + head). Primer paso: inicializa
con D=1 → N' = q, D' = N₀ ⊕ head. D==0 al final ⟺ R₀ iguala el polo del mapa de Möbius
compuesto; N==0 al final ⟺ R₀ iguala su cero (distinto del polo: mapa no degenerado).
