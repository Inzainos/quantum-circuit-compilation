# Build the draft public Kaggle notebook (.ipynb) for the QCC submission.
# Run: /home/hatch/workspace/py313/python/bin/python3.13 build_notebook.py
# Output: qcc_submission_logshift2_fused_dqi_lbfgs.ipynb  (same dir)
# Rule 0: every number below is copied from a measured log/report cited in
# NOTEBOOK_REPORTE.md. Nothing here is invented; unmeasured things are
# labelled as such inside the notebook.
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3.13 (py313)", "language": "python", "name": "py313"},
    "language_info": {"name": "python", "version": "3.13"},
    "title": "Verifiable Quantum Circuit Compilation — logshift2 + DQI without t (Q=1,864) + lbfgs chemistry",
}

def md(src):
    return nbf.v4.new_markdown_cell(src.strip())

def code(src):
    return nbf.v4.new_code_cell(src.strip())

cells = []

cells.append(md(r"""
# Verifiable Quantum Circuit Compilation — measured submission

## logshift2 invsqrt + DQI without t (Q = 1,864) + lbfgs chemistry

**Author:** Elán Zainos Corona (Fractal Core)
**Competition:** Google Quantum AI — Verifiable Quantum Circuit Compilation (Kaggle)
**Milestone:** 20 November 2026 ($10k prize requires a public notebook)
**Final deadline:** 20 January 2027

**Submission (adopted 2026-11-12, decision of the author):**

| Task | Circuit | Measured numbers |
|---|---|---|
| invsqrt | logshift2 | Q = 139, C = 2,805.79, score **390,005.06** — PASS official verifier, full domain |
| DQI | fused + E1d, t eliminated | Q = **1,864**, T = 786,272, DQI geomean **3.4099×** (calculated) — PASS sim n=6 + PASS official verifier Gold (Kali, 102,400 shots, 2 value errors, 0 phase) |
| dfthcsos | lbfgs (65,60,60) | score **3,336,160,975**, error₂ 19.371 mHa, error₁ 3.340 mHa — PASS official verifier (254,464 shots) |
| **Total** | | **geomean ≈ 3.410× (calculated — see the honesty box below)** |

**Kaggle-measured score of this submission: 3.41660** (ref 58286822, 2026-11-12). Previous best: **3.33544** (ref 58277509, 2026-11-12). The geomean of *this* submission was calculated as 3.40990× from the documented references before upload; the authoritative score is the Kaggle-measured one above.

> **Honesty box — read before citing any number in this notebook.**
> - Every number in this notebook comes from a measurement log cited in the accompanying report (`NOTEBOOK_REPORTE.md`). Numbers that are *calculated* from measured inputs are labelled **calculated**; numbers measured on the Kaggle platform are labelled **Kaggle-measured**.
> - The full submission ZIP itself has **not** been run through the complete official verifier as one piece; it **has** been scored by Kaggle (ref 58286822, 3.41660). Each piece **has** passed its own official verifier separately (invsqrt: full domain; DQI without t: simulator n=6 + official verifier Gold on a 16-CPU machine, 102,400 shots, 2 value errors, 0 phase; dfthcsos lbfgs: official verifier, 254,464 shots). The ZIP-level check done here is integrity + identity by sha256 of every member against the verified pieces.
> - The Kaggle **final selection is 0 of 2** — only the author can mark it in his account. Nothing in this notebook submits anything.
> - This notebook is **published** (version 3, updated 2026-11-12 with the DQI without t). It was first published as version 2 on 2026-11-12.
"""))

cells.append(md(r"""
## 0. The competition and the score

The competition asks for **verifiable** quantum circuits for three benchmarks, built with the **kickmix** gate set (Qualtran / Google). A submission is a ZIP with `invsqrt.kmb`, `dqi.kmb`, and `dfthcsos/` (angle circuits + `submission.npz`). The score is the **geometric mean of the improvement ratios** over the three tasks against the competition references:

$$\text{score} = \left( r_{\text{invsqrt}} \times r_{\text{DQI}} \times r_{\text{dfthcsos}} \right)^{1/3}$$

- **invsqrt** (fusion energy): cost = $Q \times C$, where $C$ = Toffolis + T/4. Lower is better.
- **DQI** (combinatorial optimization, Reed–Solomon syndrome decoder): cost = $R \cdot Q^2 \cdot T$. $Q$ is squared, so one qubit saved is worth more than one Toffoli saved.
- **dfthcsos** (quantum chemistry, FeMoCo): cost = $\lambda_{\text{eff}} \times T \times Q$ of the block encoding.

**The official verifier is the truth.** With measurement-based uncomputation (HMR), a classical simulator can give false positives — we learned that the hard way (a simulator-PASS circuit failed the official verifier on x=1 with a 0.5-turn phase error, 180°). Nothing in this notebook is claimed as verified unless the official verifier passed it.

Verifier facts (read from the verifier code, measured):
- Tolerance **TOL = 2⁻²⁴ ≈ 5.960e-08 turns, relative per x**: tol(x) = 2⁻²⁴ · θ(x).
- It requires **all ancillas back to |0⟩ AND the input register x restored**, for every input.
- The invsqrt circuit must have **exactly one register named `x`** (22 qubits).
- **Depth does not enter the score** (it is reported only).

### Rules that shape this submission (verified on the official competition page)

- **C14 — own original work (all submissions)** and **B7 — winners deliver the generator code.** This submission is our own original work, and this notebook presents the generator code (or its exact location in the repository) for every piece.
- **C6a/C5d — private code-sharing between teams is PROHIBITED. C6b/B6 — using public OSI-licensed code IS allowed**, with attribution. The public V34 circuit (see §1.3) is Apache 2.0; we studied it, rebuilt *in its style* with our own builder, and declare the derivation — we never put the literal V34 circuit in the ZIP.
- The competition's box (fixed gate set, fixed metric, fixed verifier) is real. The freedom is in the **algorithm, the representation, and the metric's blind spots** (rotations / CX / HMR are uncounted) — not in new gates.
"""))

cells.append(code(r"""
# 0. The geomean, recomputed from the documented references.
# References (documented): invsqrt ref 2,070,563 (NR baseline Q x C);
# DQI ratio 6.77x at Q=1,949; dfthcsos sample ratio 1.00583x.
# All three ratios below are CALCULATED from measured inputs, not Kaggle-measured.
import math

invsqrt_ratio = 2_070_563 / 390_005.06            # logshift2 score 390,005.06
dqi_ratio     = 6.77 * (1949/1864)**2 * (784172/786272)   # fused+E1d, t eliminated Q=1,864 T=786,272
dfthcsos_ratio = 1.00583 * (3_355_599_588 / 3_336_160_975)  # lbfgs -0.58% vs sample

product = invsqrt_ratio * dqi_ratio * dfthcsos_ratio
geomean = product ** (1/3)

print(f"invsqrt ratio  = {invsqrt_ratio:.5f}")
print(f"DQI ratio      = {dqi_ratio:.5f}")
print(f"dfthcsos ratio = {dfthcsos_ratio:.5f}")
print(f"product        = {product:.5f}")
print(f"geomean        = {geomean:.5f}x   <-- CALCULATED, not Kaggle-measured")

# For reference: the previous composition (logshift2 + DQI fused+E1d Q=1,934 + lbfgs)
prev = (2_070_563/390_005.06) * 6.86807 * 1.01169
print(f"previous composition geomean = {prev**(1/3):.5f}x")
print(f"improvement over previous    = +{geomean - prev**(1/3):.4f}x")
"""))

cells.append(md(r"""
## 1. invsqrt — logshift2 (Q = 139, score 390,005.06)

### 1.1 What it is

**logshift2** computes the phase $2/\sqrt{x}$ by a *log-shift* pipeline: normalise $x$ (barrel shift by the scale $s_b$), look up polynomial coefficients per segment, evaluate a degree-2 Horner polynomial in the normalised mantissa, and apply the phase by direct polynomial phasing (one rotation per monomial). The scale lives **in the value** (shift $V$ by $s_b$; the phase comes from the bits of the shifted value), not in the angles — the angles are fixed at compile time in kickmix, so there is no "rotate by a register value" primitive.

Generator (repository, branch `fix/zip-final-2026-11-07`, HEAD `a40a82f`):

```
src/invsqrt_logshift2.py --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1 --out invsqrt.kmb
```

Parameters: `PipelineLog2`, deg = 2, j = 8, wc = 28, dd = 13, sesgo = 1 (PR #19).

**Measured profile** (Claude, 2026-11-08): widths x 22, `coef` 58 (c0 = 28, c1 = 19, c2 = 11), `y1` 38, `sb` 4, `sel` 1; peak Q = 139. Toffoli split: Horner 1,484 (58%), coefficient lookup 551 (510 load + 41 unload), denormalisation 260, normalisation 224, half-turn 42. The Horner is at its precision floor (deg = 2, j = 8, dd = 13 — the error comes from dd quantisation, not from the degree).

**Lineage (measured):** NR baseline 2,070,562 → dbhexa (Honeycomb Grid) Q = 254, T = 7,405, score 1,935,003 → halfsplit 570,323 → logshift v1 526,689 → logshift2 497,462 → PR #19 **390,005**.

### 1.2 Verification — PASS, full domain

- **Official verifier, full domain: 200,540,928 shots. PASS.** Worst error 0.7919559187816102 of tolerance, at x = 2,764,799.
- Circuit sha256: `7e842bbfba8fb40d32c05b3b195073cf368981a92de77197ed22bd3a3f3faf79`.
- C = 2,805.79 is the 2-decimal rounding of the exact C = 390,005.06 / 139 = 2,805.7918 (the score 390,005.06 is authoritative).
"""))

cells.append(code(r"""
# 1. invsqrt — score and ratio, recomputed from the measured numbers.
# Documented score (official verifier): 390,005.06. C = 2,805.79 is the
# 2-decimal rounding of the exact C (score / Q = 2,805.7918...), so the
# score is taken as authoritative here, not recomputed from the rounded C
# (139 x 2,805.79 = 390,004.81 would differ by 0.25 from rounding alone).
Q = 139
score = 390_005.06
C_exact = score / Q
ratio = 2_070_563 / score
print(f"invsqrt score Q x C = {Q} x {C_exact:.4f} = {score:,.2f}  (C = 2,805.79 rounded to 2 decimals)")
print(f"invsqrt ratio vs NR baseline (2,070,563) = {ratio:.5f}")
print("Verification: PASS official verifier, full domain (200,540,928 shots),")
print("worst error 0.7920 of tolerance at x=2,764,799.")
"""))

cells.append(md(r"""
### 1.3 The V34 reference — and what we took from it (declared)

The public frontier reference is **V34** (SomeJoint / Agniv Banerjee): **score 97,870** (Q = 62, C = 1,578.56, 41 generic rotations, PASS official verifier, worst error 0.9993 of tolerance; full-domain re-check 97,921.58, C = 1,579.38). The circuit is yoyobar's 62-qubit circuit plus Ehan Mallick's two AND merges, distributed by Alex Chilton. Notebook *"Quantum Circuits | 24.65 Local GM: Chem Refit"*, v36, score 24.65393, 2026-11-04, **Apache 2.0**; dataset *"QCC ladder parts"* (v10), also Apache 2.0.

**Derivation declaration (decision of the author, 2026-11-08):** we studied V34 and **rebuilt in its style with our own builder, declaring the derivation** — the literal V34 circuit (or a literal builder translation of it) is **never** in the ZIP, per rule C14 (own original work). A literal translation is also infeasible in practice (~3.3×10¹⁴ ANF terms in the b21921 accumulation). Apache 2.0 obligations honoured: licence copy included, authorship notices kept, modified files marked, source cited in the README.

What V34 taught us (measured, by dissection of the .kmx):
- Its scale is literally a **bit shift**: the normalised mantissa is identical for the same M regardless of L (12/12 exact); the CSWAP controls of the rotation blocks are pure functions of L. Normalisation costs 71 Toffoli — no division, no lookup.
- It accumulates **phase in 2 qubits** (rotations), not a value in wide registers; it cleans with HMR (free) instead of reversible uncomputation; it processes 51 clusters sequentially, reusing the same ~48 qubits.
- It already shares ANDs (1,183 CCX compute only 532 distinct ANDs, 2.22 CCX/AND) — a "global AND cache" is not a new lever. ABC and mockturtle do not improve its phase network (locally optimal).
- q50 cannot be removed: V34 without the 21 `Z_POW q50` FAILS the verifier on x = 1 (phase error −3.052e-05 vs tol 5.960e-08).

**The honest state of invsqrt:** logshift2 is the best *measured* circuit we have (390,005). The closest measured route toward V34 was **u24+M2a pruned: 107,683** (Q = 63, C = 1,709.25 — 10% above V34). It is blocked by the **scale**: the angles are fixed at compile time, the segment-dependent function g(M_k) is smooth and dense (its ANF is complete: 4,194,303 monomials), and both escapes pay more than the Horner they replace. The open items are the scale (u24) and the **root cause of the Prototype A ANGLE_OFF failure** in the official verifier (simulator PASSED at 0.6557 tol; the verifier FAILED — hypotheses: units convention half-turns vs turns, or an HMR/classical-bit interaction; not proven).
"""))

cells.append(md(r"""
## 2. DQI — fused + E1d, t eliminated (Q = 1,864, T = 786,272)

### 2.1 What it is

The DQI task is a reversible **Reed–Solomon syndrome decoder** (Berlekamp–Massey, n = 70, m = 4,095, degree 12, r = 2,016). The decoder runs `bm_forward` (69 rounds), an omega stage, a scan (4,095 positions, 98.0 T/position — 51.2% of all T), and `bm_reverse`. The author's order for this task: **Q first (it is squared in the cost), then T, then R.**

The peak lives in the scan: 1,794 live qubits (S 840 + σ 432 + τ 432 + d 8 + H 12 + p flags 70) + 70 scan transients = 1,864. Three measured improvements, stacked:

**F1b — fusion of multiply and inverse in the alpha block** (2026-11-11).
The alpha block computes P = X·D, Pinv = inv(P), and α = mux(P, Pinv). The inversion is not in-place (ValueInv3 needs a destination register in |0⟩), so the fusion computes **inv(P) directly into α** (the destination already exists and is in |0⟩) and selects by **CSWAP** between P and α — Pinv is never materialised. Cost of selection: 12 CSWAP = 12 Toffoli + 24 CX (vs 12 CCX + 36 CX of the original mux — same Toffoli, fewer CX). **Saving: the Pinv register, 12 qubits.** The block adds +30 live qubits instead of +42. **Q 1,949 → 1,937 (−12), T identical 784,172 (ΔT = 0).**

**T-elimination — drop the t flag, reconstruct it from d** (2026-11-12, Front A inspection + experimental branch).
The BM stage kept two 1-bit flags per round, p and t, alive across the whole forward (70 + 70 persistent qubits). Front A measured that t is reconstructible from d: d is exactly d_r = (r+1) − 2L_r (verified 3,200/3,200 trials, 0 violations), and the rule t = (¬p) ∧ (d_post ≤ 0) held in 238,000/238,000 simulated rounds. The only logically possible falsifying branch (D = 0, d < 0) never appeared. The literal prescription (keep nz alive, uncompute t at 0 T) turned out not implementable — del_and cleans the target, not a control, and t = nz ⊕ p means CX alone can free only one of the two — so the branch implemented the symmetric Option B: _flags computes only p; _dclear reconstructs w = (¬p) ∧ (d_post ≤ 0) (9 T, 11 transient ancillas) after freeing the tower inversion, uses w as the cswap control, and frees it immediately — in both directions. Cost: 9 T × 140 calls = +1,260 T (the forward pays 9 T/round too, not 0 T as first projected — a +630 T honest deviation). **Q 1,934 → 1,864 (−70), T 785,012 → 786,272 (+1,260).**

**E1d — free N′ before the products** (2026-11-12, the inverter redesign).
The tower inverter ValueInv3 (GF(2¹²) = GF((2⁶)²)) keeps 18 scaffolds alive at once (N 6 + rc 6 + N′ 3 + r 3). E1d frees N′ (3 qubits) after computing r, before the products in rc (0 T, `mulN_del` with N), and recomputes it in the undo (+6 T per inversion). Scaffolds after forward: 18 → 15; T per inversion 75 → 81. Applied to the 140 alpha-block inversions only: **ΔT = +840, Q 1,937 → 1,934 (−3).**

The full ladder, measured on complete DQI builds:

| Variant | Q | T | Geomean (DQI part) | Verdict |
|---|---|---|---|---|
| Baseline | 1,949 | 784,172 | 3.31× | reference |
| Fused (F1b) | 1,937 | 784,172 | 3.3237× | gain |
| Fused + E1d | 1,934 | 785,012 | 3.3259× | superseded |
| E1 (recompute N) | 1,934 | 786,692 | 3.3236× | wash |
| E2 (recompute N, N′, r) | 1,934 | 787,952 | 3.3218× | worse |
| **Fused + E1d, t eliminated** | **1,864** | **786,272** | **3.4099×** | **adopted** |

**Why 1,934 was a floor — and how t broke it (measured):** all three recompute variants hit the same Q = 1,934 because the **scan peak** fixed it (70 over base → 1,934). The 70 were not scan transients but the 70 persistent **t flags** — once t is reconstructed from d instead of stored, the live qubits drop 1,864 → 1,794 and the peak drops to **1,864**, now fixed by the scan itself (1,794 live + 70 scan transients). Lowering it further would require redesigning the scan's tower too, but the scan has 4,095 inversions — E1d there would cost +6 × 4,095 = +24,570 T (geomean ~3.30×, worse). The T of the scan kills any Q gain by that route. The scan sub-front is closed (Front A): its ~70 transients are ~45 irreducible, and the only ways down cost more T than the Q they save.

**A measured lesson:** the standalone Q of the tower (57 in all four variants) does **not** predict the Q of the full circuit — the full build had to be measured. The real peak is fixed by the live qubits *after* the tower forward (where the scaffolds are already freed), not by the transient peak during the products/undo, because the qubit pool reuses free qubits.
"""))

cells.append(code(r"""
# 2. DQI — ratio and geomean chain, recomputed from the measured Q/T.
# Cost = R * Q^2 * T, so the ratio vs the Q=1,949 baseline scales as (Q0/Q)^2 * (T0/T).
# The 6.77x reference ratio is the documented DQI ratio at Q=1,949.
base_ratio = 6.77
for label, Q, T in [("baseline", 1949, 784172),
                    ("fused F1b", 1937, 784172),
                    ("fused + E1d", 1934, 785012),
                    ("fused + E1d, t elim. (adopted)", 1864, 786272)]:
    ratio = base_ratio * (1949/Q)**2 * (784172/T)
    print(f"{label:24s} Q={Q}  T={T}  DQI ratio = {ratio:.5f}")

# Geomean chain (DQI is 1 of 3 tasks, so a DQI factor f moves the geomean by f**(1/3)).
print()
print("geomean 3.31x -> 3.3237x (fusion, -12 Q, dT=0) -> 3.3259x (E1d, -3 Q, +840 T)")
print("       -> 3.4099x (t eliminated, -70 Q, +1,260 T)")
print("t elimination is +0.0840x of geomean; E1 is a wash (3.3236x), E2 is worse (3.3218x).")
"""))

cells.append(md(r"""
### 2.2 Verification — PASS (gold standard, 102,400 shots)

- **Simulator, n = 6, Tests A–C (exact):** forward identical (S/σ/τ/d/H), round trip restores the initial state, baseline round trip == sin-t round trip on the persistent registers. **All pass, 6 seeds.** (Forward at n = 6: Q 318 → 312 (−6, the six eliminated t flags), T 4,338 → 4,392 (+54 = 6 rounds × 9 T); round trip T 7,752 → 7,860 (+108 = 6 × 18) — exactly the symmetric Option B cost.)
- **Official verifier, Gold, Kali (16 CPUs, 7 GB RAM), 102,400 shots: PASS** for the DQI without t (Q = 1,864, T = 786,272). **2 value errors, 0 phase errors, eps_plus 0.000949, R = 1.2014** — identical digit by digit to the Gold of the fused+E1d circuit (Q = 1,934, also PASS at 102,400 shots, 2 value errors, 0 phase, eps_plus 0.000949, R = 1.2014). The theoretical reserve (the D = 0, d < 0 branch, where the t reconstruction could fail) produced **no additional error** in 102,400 shots. DQI score: 3,527,544,869,511 → 3,282,070,743,071 (−6.96%); DQI ratio 6.86807 → 7.38175.
- **Earlier evidence (2,560 shots):** PASS for both the fused circuit (Q = 1,937) and the fused+E1d circuit (Q = 1,934), 0 value errors, 0 phase errors, eps_plus 0.0341 < 1/16. With 2,560 shots and 0 errors the verifier computed R = 4.94 — that R was **inflated by the sample size**; the Gold run at 102,400 shots gives the real R = 1.2014. Internal consistency checks exact at 2,560 shots: CCX Δ = +2,150,400 = 840 Toffoli × 2,560 shots; num_bits Δ = +420 = 140 alpha inversions × 3 bits. At 102,400 shots the per-shot deltas are exact: CCX +1,260.00, R +1,260.00, HMR +1,260.00 (9 T × 140 _t_recon calls) — no hidden change in the circuit.
- The full DQI verifier does not run on an 8 GB box (bad_alloc); DQI validation there is by sampling and small-scale simulation.

### 2.3 Alternatives that were measured and closed (not hand-waved)

| Route | Measured result | Verdict |
|---|---|---|
| Itoh–Tsujii, binary (11 muls) | ~1,386 T/inv, 168 scaffolds | NO-GO (T and scaffolds) |
| Itoh–Tsujii, optimal addition chain (~5 muls) | ~315 T/inv (lower bound, not built) | NO-GO (315 >> 75 T of the tower) |
| Builtin `init_gf2_inverse_with_scaffold` | 48 scaffolds, 315 T | NO-GO |
| Cubic tower GF(2⁴)³ | ≥ 20 scaffolds (structural: 12 + 4 + 4); norm ANF 442 cubic monomials, ≥ 884 ANDs for the norm alone | NO-GO |
| 12-bit lookup inversion | 4,094 T exact (2¹² − 2) | NO-GO |
| BM in-place / q-d rhombus | q-d fails 21.8% / 21.0% with the real verifier weights | Dead route |
| 2×2 block rhombus (classical result) | ε = 0.0000 in 2000/2000 — but the kickmix circuit measures Q = 2,683, geomean 2.19–2.72× | Classical result, NOT a winning circuit |

The public frontier for DQI (BM+Forney, Q ≈ 889, ~54.73×) is a different decoder, not an optimisation of this one — it is a reference, not the opponent. The opponent is our own previous best.
"""))

cells.append(md(r"""
## 3. dfthcsos — lbfgs (65,60,60) (score 3,336,160,975)

### 3.1 What it is

The chemistry task is the block encoding of the **FeMoCo** Hamiltonian (FeMoCo76o113e) by a **DFTHC factorisation** (double-factorised tensor hypercontraction): a factorisation $(U, W, H_2, H_1)$ of rank (65,60,60), encoded with **brot = 12** bits per rotation and batch size 8, emitted as 10 ANGLE circuits (`angle_k_0..9`, 119 qubits each, max_magic 3,974) with a log-depth Givens tree.

The adopted factorisation was trained by **LBFGS**: (65,60,60), rho = 1e-4, epsilon = 0.017, **100 epochs, wall 2,562.1 s**, saved as `lbfgs_rho1e-4_eps17_65_60_60_ep100.npz`. The candidate was built with the starter-kit pipeline: `check_factorization.py` (continuous check) → `encode.py` (brot = 12) → `build_circuits.py` (brot = 12, batch = 8) → official verifier.

| Quantity | Measured |
|---|---|
| Score | **3,336,160,975** (−0.58% vs the sample's 3,355,599,588) |
| λ_eff | 49.0158 (sample: 49.301) |
| error₁ / error₂ | **3.340 mHa / 19.371 mHa** (continuous error₂ 16.9850 mHa) |
| T / Q | 93,237 / 730 (angles 79,480 T = 85.2% + heuristic 13,757 T) |
| Angles | 3,976 vectors, 75 angles, 10 circuits |
| Verification | **PASS official verifier, 254,464 shots** |

### 3.2 Why this factorisation — and what did not work

The delivery used to carry the **sample** factorisation (score 3,355,599,588, ratio 1.00583×). The author first ordered training the small form (8,143,60) instead of inserting this lbfgs candidate ("do NOT insert the −0.58% candidate", 2026-11-09). That path was then **measured and closed**:

- **Staged ladder floors** (re-verified exact): rank 65 → 29.63, rank 32 → 223.05, rank 16 → 613.80, rank 8 → **857.26 mHa**. Rank 8 has no continuous capacity.
- **Refit to brot = 8: NO PASS.** Naive 12 → 8: error₂ 159.193, error₁ 52.618 mHa. AdaRound worse (242.327 / 53.823). (Correction, rule 0: an earlier error₁ = 571.424 mHa was staleness of obsolete one-body rows, not quantisation; the correct value is ≈ 52.6 mHa.)
- **Factorisation from scratch with brot = 8 in the loop: NO PASS.** Best new factor: error₂ at 8 bits **1,736.759 mHa** (87× over). The quantisation penalty is negligible (+15.5 mHa) — the blockage is capacity, not quantisation.
- **Mixed brot** (1b10 + 2b12) passes the errors but the planner rejects 15/15 batches at brot = 12 — the **128-qubit layout** is the binding constraint (high_cache budget ≤ 56 at brot = 12; our factors need 247/batch).
- **Design criterion, measured** (from B143, the only table the compiler accepts): per batch, **products ≤ ~225 AND high_cache ≤ ~69**. All five of our factors have high_cache 247/batch (3.6×). high_cache does not move with training or quantisation — it is structural to the table.

So the author reversed the earlier decision and adopted the lbfgs candidate (decision 2026-11-12, "Sí, adopten todo (fusión + E1d + lbfgs)"). It is the only dfthcsos improvement that exists and is verified. The frontier (8,143,60) + full-XOR (T = 16,366, Q = 430, ~9.78×) still needs a factor trained at brot = 8 with a sparse table — no such factor exists, and no method to produce one is known.
"""))

cells.append(code(r"""
# 3. dfthcsos — ratio, recomputed from the measured scores.
sample_score = 3_355_599_588
lbfgs_score  = 3_336_160_975
ratio = 1.00583 * (sample_score / lbfgs_score)
print(f"lbfgs score  = {lbfgs_score:,}  (sample: {sample_score:,}, -0.58%)")
print(f"dfthcsos ratio = 1.00583 x ({sample_score}/{lbfgs_score}) = {ratio:.5f}")
print("error_1 = 3.340 mHa, error_2 = 19.371 mHa, lambda_eff = 49.0158")
print("Verification: PASS official verifier, 254,464 shots.")
"""))

cells.append(md(r"""
## 4. The submission ZIP — what is in it, and how it was verified

Build script: `submission/build_submission.py` (repository, branch `fix/zip-final-2026-11-07`, HEAD `a40a82f`). It packs `invsqrt.kmb`, `dqi.kmb`, `dfthcsos/angle_k_0…9` (numbered from 0, no gaps) and `dfthcsos/submission.npz` (keys U, W, H2_I, H1_I, Hsym_lower, tree_edges).

**Adopted ZIP** (`valid_submission_fb4e95b.zip`):

| Member | Size | sha256 | Verified piece |
|---|---|---|---|
| `invsqrt.kmb` | 437,575 B | `7e842bbf…faf79` | logshift2, Q = 139, score 390,005.06, PASS official full domain |
| `dqi.kmb` | 624,960,230 B | `8dd3e6a3…6bf` | fused+E1d, t eliminated, Q = 1,864, T = 786,272, PASS sim n=6 + PASS official Gold (Kali, 102,400 shots) |
| `dfthcsos/angle_k_0..9.kmx` | ~2.2–2.6 MB each | `adf19022…`, `6104ef8f…`, … | lbfgs (65,60,60), 119 qubits each |
| `dfthcsos/submission.npz` | 4,537,436 B | `d89772be…7fa4d` | lbfgs, score 3,336,160,975, error₂ 19.371 mHa |

- ZIP sha256: `ba222d1c130acec71406b1b5473e78140ce87f4af8041db5907dc4ff8b9e0703`; 66,288,156 B (63.2 MB); **13 files; `testzip` = None (intact)**.
- **All 13 members match by sha256 with the verified pieces** (`TODOS LOS MIEMBROS COINCIDEN: True`).
- The previous adopted ZIP is backed up (sha `171d5a81…`, 66,225,789 B, fused+E1d DQI Q = 1,934). `final_submission.zip` and `integracion/submission.zip` were left intact on purpose — whether they are updated with the sin-t DQI is the author's decision.

The cell below re-checks the ZIP integrity and the member hashes **if the ZIP is attached as a dataset** (in Kaggle: `/kaggle/input/...`; locally: the path in the report). If it is not attached, it prints the expected hashes so the check can be run by hand.
"""))

cells.append(code(r"""
# 4. ZIP integrity + member identity (runs if the submission ZIP is attached).
import hashlib, zipfile, os

EXPECTED_ZIP_SHA = "ba222d1c130acec71406b1b5473e78140ce87f4af8041db5907dc4ff8b9e0703"
EXPECTED = {
    "invsqrt.kmb": "7e842bbfba8fb40d32c05b3b195073cf368981a92de77197ed22bd3a3f3faf79",
    "dqi.kmb": "8dd3e6a30aa0f87f71249aa5ec2b465e1e9817172aee1fb3120ccdc2bb3aa6bf",
    "dfthcsos/submission.npz": "d89772be6b4b8484",
}
CANDIDATES = [
    "/kaggle/input/qcc-submission/valid_submission_fb4e95b.zip",
    "/home/hatch/workspace/qcc-data/valid_submission_fb4e95b.zip",
]

path = next((p for p in CANDIDATES if os.path.exists(p)), None)
if path is None:
    print("Submission ZIP not attached in this environment.")
    print("Expected ZIP sha256:", EXPECTED_ZIP_SHA)
    print("Attach valid_submission_fb4e95b.zip as a dataset and re-run this cell.")
else:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    print("ZIP:", path)
    print("sha256 match:", h.hexdigest() == EXPECTED_ZIP_SHA, "|", h.hexdigest()[:16], "...")
    with zipfile.ZipFile(path) as z:
        print("testzip (None = intact):", z.testzip())
        print("members:", len(z.namelist()))
        for name, prefix in EXPECTED.items():
            data = z.read(name)
            print(f"  {name:28s} sha match: {hashlib.sha256(data).hexdigest().startswith(prefix)}")
    print("All members match the verified pieces: see the adoption report for the full 13-member check.")
"""))

cells.append(md(r"""
## 5. Verification status and caveats — the whole picture

| Piece | Official verifier | Simulator / other | Status |
|---|---|---|---|
| invsqrt logshift2 | **PASS, full domain** (200,540,928 shots) | — | Verified |
| DQI fused | **PASS** (Kali, 2,560 shots, 0 err) | sim n=6, Tests A–C PASS | Verified |
| DQI fused+E1d | **PASS Gold** (Kali, 102,400 shots, 2 value, 0 phase) | sim n=6, Tests A–C PASS; primitive 4096/4096 | Verified |
| DQI fused+E1d, t eliminated | **PASS Gold** (Kali, 102,400 shots, 2 value, 0 phase) | sim n=6, Tests A–C PASS, 6 seeds | Verified |
| dfthcsos lbfgs | **PASS** (254,464 shots) | continuous error₂ 16.9850 mHa | Verified |
| **Full ZIP** | **Not run** (~45 min on Kaggle) | integrity + sha256 identity of all 13 members | **Not fully verified** |

**What the geomean is and is not.** 3.40990× is **calculated** from the documented references (invsqrt ref 2,070,563; DQI ratio 6.77× at Q = 1,949; dfthcsos sample ratio 1.00583×). The Kaggle-measured geomean of this submission is **3.41660** (ref 58286822, 2026-11-12) — the authoritative score. Previous best: 3.33544 (ref 58277509, 2026-11-12). The calculated and measured values differ by the exact Kaggle references vs the documented rounded ones (6.77× and 1.00583×, 3 figures).

**Open items (not hidden):**
- Kaggle final selection: **0 of 2** — only the author can mark it (manual, ~5 min). The submission to mark is ref 58286822 (3.41660).
- Whether `final_submission.zip` and `integracion/submission.zip` are updated with the sin-t DQI — the author's decision.
- Next measured lever (not yet verified as a circuit change): `build_omega_tmp` uses the 63-Toffoli constructor in 630 gf_mul calls per direction; Karatsuba (54 Toffoli) would save 11,340 T (~1.44% of T) at the same Q. Arithmetic on measured per-call costs — it needs its own build and official verification.
- The (8,143,60) + full-XOR chemistry frontier (~9.78×) needs a sparse factor (high_cache ≤ 69/batch, products ≤ 225/batch); no such factor exists.
- Prototype A ANGLE_OFF root cause — open (hypotheses: units convention half-turns vs turns, or HMR/classical-bit interaction).
- The LOD one-hot normalisation (72 Toffoli, 18.2× cheaper than the old 1,312) is an orphaned asset — the phase network it was meant to pair with turned out dense.
"""))

cells.append(md(r"""
## 6. Attributions, licence, and what this submission is not

- **V34 derivation (Apache 2.0):** the public V34 circuit is by **Agniv Banerjee (SomeJoint)** — yoyobar's 62-qubit circuit plus **Ehan Mallick's** two AND merges, distributed by **Alex Chilton**. Notebook *"Quantum Circuits | 24.65 Local GM: Chem Refit"*, v36, 2026-11-04; dataset *"QCC ladder parts"* (v10). Both Apache 2.0. We studied V34, rebuilt in its style with our own builder, and declare the derivation. The literal V34 circuit is not in the ZIP. Apache 2.0 obligations: licence copy included, authorship notices kept, modified files marked, source cited.
- **Competition rules:** C14 (own original work), B7 (winners deliver the generator code), C6a/C5d (no private code-sharing between teams), C6b/B6 (public OSI-licensed code allowed, with attribution) — verified on the official competition page.
- **Principle of this work:** looking at others' work (SomeJoint, clduab11, Chilton, Lera) as reference is allowed; depending on it (a literal delivery, a downloaded factor as-is) is not. Everything in the ZIP was built and verified by us, with derivations declared where they apply.
- **The planner posture is OPEN and is not part of this submission.** A full-XOR planner (Apache 2.0, clduab11's repository, commit `b92db3a`) was downloaded for measurement/testing only; whether it is used as-is with attribution (like a library) or reimplemented from the method is undecided. Nothing from it is in the delivery, and this notebook does not present it as part of the submission.
- **References:** Khattar et al., *Google Quantum AI — Verifiable Quantum Circuit Compilation* (Kaggle, 2026; arXiv:2610.23832); Babbush et al., kickmix circuits (arXiv:2603.28846).
"""))

cells.append(md(r"""
## 7. Reproducibility — generator code and exact commands

Repository: `quantum-circuit-compilation` clone, branch `fix/zip-final-2026-11-07`, HEAD `a40a82f` (read-only for this work). DQI verifier worktree `quantum-sandbox` @ `4ac3d45`.

**invsqrt (logshift2):**
```
src/invsqrt_logshift2.py --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1 --out invsqrt.kmb
# PipelineLog2, deg=2, j=8, wc=28, dd=13, sesgo=1 (PR #19)
```

**DQI (fused + E1d, t eliminated):**
```
# Baseline decoder: src/dqi_decoder_v1.py :: build_decoder(n=70, LS=36, LO=35, m=4095)
# Fusion (F1b): dqi-perfil/fusion_mul_inv/bm_fused.py (BMStageFused, _alpha_sel_fused)
# E1d tower:    dqi-perfil/redisenio_inversor/tower_inv3_e1d.py (free N' before products)
# t elimination: src/dqi_bm_stage_v1.py (_t_recon, _dclear without t), src/bm_fused.py,
#   src/bm_fused_e1d.py — updated in the repo (commit c0fb9a57, branch fix/zip-final-2026-11-07)
# Full build:   dqi-perfil/rama_t_eliminada/construir_dqi_sin_t.py  -> dqi_sin_t.kmb
#   TOTAL SIN-T Q=1864 T=786272 (104 s); sha256 8dd3e6a3...6bf
#   (previous build: dqi-perfil/verificacion_e1d/construir_dqi_e1d.py -> dqi_fusionado_e1d.kmb,
#    TOTAL E1d-alpha Q=1934 T=785012, sha256 16e06d61...3664)
# Verify (sim n=6):  dqi-perfil/rama_t_eliminada/verificar_sin_t.py  (Tests A-C, all PASS, 6 seeds)
# Verify (official Gold): Kali, verifiers/dqi/verify_submission_dqi.py --num-shots 102400 --batch-size 256
#   PASS, 2 value errors, 0 phase errors, eps_plus 0.000949, R 1.2014 (5 min 28 s)
```

**dfthcsos (lbfgs):**
```
# Train: LBFGS (65,60,60), rho=1e-4, eps=0.017, 100 epochs (wall 2,562.1 s)
#        -> lbfgs_rho1e-4_eps17_65_60_60_ep100.npz
# Build candidate: dfthcsos-refit/build_candidate.sh <factorization.npz> lbfgs_ep100_rho1e-4 12 8
#   1) check_factorization.py  2) encode.py --brots 12  3) build_circuits.py --brot 12 --batch-size 8
#   4) official verifier on the candidate dir -> PASS, 254,464 shots
```

**ZIP:**
```
# submission/build_submission.py  -> valid_submission_fb4e95b.zip
# sha256 ba222d1c130acec71406b1b5473e78140ce87f4af8041db5907dc4ff8b9e0703 (66,288,156 B, 13 files)
```

**Environments:** this work ran on a local box (Python 3.13, 7.7 GB RAM; the full DQI verifier does not run there — bad_alloc) and on a Kali sandbox over Tailscale (16 CPUs, 7 GB RAM; the official DQI verifier used 6.6 GB RSS at 1 worker — do not raise `--max-workers` without measuring). Python output to log files is block-buffered: use `python -u`.

**What a reader can reproduce from this notebook alone:** the score arithmetic (§0–§3 code cells) and the ZIP integrity/identity check (§4, with the ZIP attached as a dataset). Rebuilding the circuits needs the repository + kickmix + the official verifier (Kali); the exact commands are above.
"""))

cells.append(md(r"""
## 8. Open items and future work

1. **Omega multiplier (Karatsuba in build_omega_tmp):** the 63-Toffoli constructor in 630 gf_mul calls per direction would save 11,340 T (~1.44%) with Karatsuba (54 Toffoli) at the same Q — needs its own build + official verification in a clean branch, after this submission is secured on Kaggle.
2. **Chemistry frontier:** (8,143,60) + full-XOR would give ~9.78×, but it needs a factor with a sparse angle table (per batch: products ≤ ~225 AND high_cache ≤ ~69). Every factor we trained has high_cache 247/batch. A future factor must pass that criterion *before* training investment.
3. **invsqrt scale (u24):** the only path to a large jump (390,005 → ~107,683 measured as the closest route) is blocked by the segment-dependent scale; the blockage is determined (fixed angles at compile time, dense g(M_k), escapes pay more than the Horner).
4. **Prototype A ANGLE_OFF root cause** — open; the simulator passed and the official verifier failed, and the cause is not proven.
5. **Kaggle final selection (0 of 2)** — the author's decision only (manual, in his account; mark ref 58286822).

---

*Updated 2026-11-12 (version 3): DQI without t adopted (Q = 1,864, T = 786,272, Gold PASS 102,400 shots); ZIP uploaded to Kaggle (ref 58286822, measured geomean 3.41660). Numbers are measured or calculated from measured inputs; the sources are the work logs cited in the accompanying report.*
"""))

nb.cells = cells
out = "/home/hatch/workspace/qcc-data/notebook/qcc_submission_logshift2_fused_dqi_lbfgs.ipynb"
with open(out, "w") as f:
    nbf.write(nb, f)
print("wrote", out, "cells:", len(cells))
