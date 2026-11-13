# kickmix/ — librería compilada (vendida en el repo)

`kickmix` es la capa baja de construcción y verificación de circuitos de la
competición (Qualtran / Google Quantum AI): primitivas reversibles, GF(2),
`CircuitBuilder`, simulador y verificador. Los módulos de `src/` y los
scripts de `scripts/` la importan como `import kickmix as km`.

## Qué hay aquí

- `kickmix.so` — extensión compilada de CPython, **3,220,392 B**,
  sha256 `c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e`.
  Es el mismo binario usado para generar los números medidos vigentes
  (Adopted v3: DQI Q=1,864, T=774,932; ZIP sha `83b0c756…`).
  **No va dentro de esta rama** (el push por conector no admite binarios):
  se distribuye como asset del Release `adopted-v3`
  (https://github.com/Inzainos/quantum-circuit-compilation/releases/tag/adopted-v3).
  Para correr en clon fresco, baja `kickmix.so` de ahí y colócalo en este
  directorio; los scripts no cambian.
- `LICENSE.txt` — Apache License 2.0 (ya estaba versionada en el repo).
- Este `README.md` — origen, límites y cómo correr.

## Límites verificados (medidos 2026-11-06 y 2026-11-12)

- **Solo CPython 3.13, Linux x86-64.** El `.so` es un build Bazel
  (`bazel-out/k8-fastbuild/bin/kickmix/kickmix.so`, BuildID sha1
  `c801b8dfdea5434e28de9b78a95658176992e31d`). En Python 3.12 falla al
  importar (`undefined symbol: PyObject_ClearManagedDict`, símbolo de la
  API 3.13). En otras plataformas o versiones de Python NO carga.
- **Sin fuente en este repo.** Solo el binario + licencia. La fuente
  C++/Python vive en `quantumlib/Qualtran` (según el análisis del
  2026-11-07/08; no re-verificado en vivo aquí).
- **Procedencia del binario: NO establecida con evidencia local.**
  Las dos copias en la máquina de trabajo (`~/workspace/qcc/kickmix/` y
  `~/workspace/qcc-data/kickmix/`, ambas 2026-11-06, sha256 idéntico) son
  la fuente de esta copia vendida. Verificado: el `.so` NO viene del
  dataset Kaggle "Verifiable Circuit Compilation Starter Kit"
  (sohier/verifiable-circuit-compilation-starter-kit v4: no contiene
  ningún `.so`). De dónde se descargó originalmente el binario es un
  pendiente para Elán (ver `docs/` o el reporte de esta rama).
- **Redistribución:** la licencia presente es Apache 2.0 genérica, sin
  línea de copyright con titular. Apache 2.0 permite redistribuir la
  forma Objeto con copia de la licencia, pero Elán debe confirmar que
  vender este binario en el repo público es aceptable antes de pushear
  esta rama.

## Cómo se usa

Nada que instalar: los `.py` de `src/` y `scripts/` resuelven la raíz del
repo desde `__file__` y añaden `<repo>/kickmix` a `sys.path`. Requisito:
correr con **Python 3.13** (p. ej. `python3.13 scripts/medir_fusion.py`
desde la raíz del repo). Comprobación rápida:

```bash
python3.13 -c "import sys; sys.path.insert(0, 'kickmix'); import kickmix; print(kickmix.__file__)"
```

## Si este binario no te sirve

En otra plataforma o versión de Python hay que reconstruir `kickmix.so`
desde la fuente de Qualtran (build Bazel; pasos no verificados aquí) y
colocarlo en este directorio con el mismo nombre. Los scripts no cambian:
buscan `<repo>/kickmix` en `sys.path`.
