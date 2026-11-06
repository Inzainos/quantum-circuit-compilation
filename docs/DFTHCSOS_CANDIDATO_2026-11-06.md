# Integración 2026-11-06: invsqrt + DQI BM + dfthcsos refit

Rama `local/integracion-v1`, basada en
`feat/dqi-bm-invsqrt-q139` (commit 4ee3d4e) + el candidato dfthcsos de
Mole. El ZIP final es `submission/final_submission.zip` (59,609,468 bytes,
SHA-256 `ce1d12a6fdec6c4522325c334e1ae029a2a5b736eb5422e9723d959961afb35a`),
reconstruido con `submission/rebuild_valid_zip.py
--dfthcsos-zip` a partir de los scripts del repo. Es el artefacto que
nombra la regla 3 de AGENTS.md; el `submission/submission.zip` inválido
de la PR #17 se deja como está (no se toca en esta rama).

## Componentes y verificación

| Benchmark | Origen | Score verificado | Verificación |
|---|---|---|---|
| invsqrt | `src/invsqrt_logshift2.py --deg 2 --j 8 --wc 28 --dd 13 --sesgo 1` | **390,005.06** (Q=139, T=2,561, peor error 0.792) | Verificador oficial, dominio completo, 1 tiro/x: **PASS**. Circuito SHA-256 `7e842bbf…3faf79`. |
| dqi | `src/dqi_decoder_v1.py` (decodificador Berlekamp–Massey completo) | **≈3.83e12 estimado** (784,172 Toffoli, Q=2,016, R≈1.20) | Muestreo con las funciones del verificador oficial: 102,400 tiros, 0 fallos (el otro agente reportó 2). **El `verify_submission_dqi.py` completo NO corre en esta caja** (`reaction_depth()` → `std::bad_alloc`, igual que con v10): la cifra dqi es una estimación medida, no un PASS del verificador. Circuito SHA-256 `b555beda…a698`. |
| dfthcsos | Candidato `lbfgs_ep100_rho1e-4` (Mole) | **3,336,160,975** (−0.58% vs baseline 3,355,599,588; λ_eff 49.016) | Verificador oficial contra datos oficiales de FeMoCo: **PASS**. Submission SHA-256 `aa57a7d8…052bdf`. |

Media geométrica combinada (aritmética, no corrida del evaluador de
Kaggle): invsqrt 5.309x × dqi ~6.32x × dfthcsos 1.0058x → **≈3.23x**
(hasta ~3.4x si el R de dqi es 1.0 en vez de 1.20). Frente a la
frontera pública ~24.94 sigue habiendo distancia, pero duplica el
1.6130x de la entrega del 4 de noviembre.

## El candidato dfthcsos (lo que aporta Mole)

- Factorización (65, 60, 60) reentrenada con el entrenador del
  Starter Kit de Kaggle (`train_df_thc_qaggle.py`, JAX + Optax),
  optimizador LBFGS, 100 épocas, rho=1e-4, eps=0.017, partiendo de la
  factorización base 65_60_60. Lambda quedó casi congelada (308.448 →
  308.361, −0.03%): λ_eff se mueve con el gap SOS, no con Λ, así que
  esta línea tiene techo ~−0.6%.
- Codificación a 12 bits (`build_circuits.py` del Starter Kit);
  la factorización continua sola habría fallado el gap (3.9125 < piso
  3.914898) y el paso de codificación lo subió a 3.92049.
- Márgenes delgados, hay que saberlo: error_2 19.37/20 mHa,
  E_gap 3.92049 (margen 5.6 mHa sobre el piso 3.914898).
- Archivos: `dfthcsos/angle_k_0…9.kmx` + `dfthcsos/submission.npz`
  (SHA-256 `d89772be…b7fa4d`). La factorización continua y los logs
  del entrenamiento están en el scratch de Mole
  (`dfthcsos-refit/candidates/lbfgs_ep100_rho1e-4/`), no versionados
  aquí: el repo solo versiona el ZIP final, según su convención.

## Cómo se reconstruyó

```bash
python3 submission/rebuild_valid_zip.py salida/submission.zip \
    --dfthcsos-zip <zip con dfthcsos/ del candidato>
```

Regenera invsqrt.kmb y dqi.kmb desde el código del repo y copia
`dfthcsos/` del ZIP dado. Nota de entorno: el script usa
`tempfile.TemporaryDirectory()`; en cajas donde `/tmp` es un tmpfs
de 512 MB hay que poner `TMPDIR` en disco (el .kmb de dqi pesa
631 MB y no cabe en `/tmp`).
