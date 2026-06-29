---
name: compat-matrix
description: >-
  Cross-OS / cross-Minecraft-version build-and-render compatibility harness for
  The-Minecraft-Overviewer. Builds the c_overviewer C extension against each
  environment's numpy and Pillow, then renders a set of test worlds against
  their matching-version Minecraft client jars and reports a pass/fail matrix.
when_to_use: >-
  Use before merging changes that touch the C extension, setup.py, dependency
  pins, or version-specific texture/world handling. Run it to confirm Overviewer
  still builds and renders on Ubuntu 22.04 / 24.04 / 26.04 (numpy/Pillow from
  apt) and Windows 11 with Python >= 3.12 (numpy/Pillow from pip), across the
  supported Minecraft world formats.
entrypoints:
  - run_matrix.py   # host orchestrator (Windows): drives all OS legs
  - render_test.py  # in-environment worker: build + render + result.json
inputs:
  worlds:   "Derek-Single (MC 1.21.11), Tester (MC 26.1), GiveEr26_2 (MC 26.2)"
  textures: "matching-version Minecraft client jars from .minecraft/versions"
outputs:
  - "per-leg renders + result.json under the --work dir"
  - "a printed PASS/FAIL matrix; process exit code 0 iff every leg passed"
requires:
  - docker            # for the Ubuntu legs
  - "a C toolchain"   # gcc in the containers; MSVC for the Windows leg
  - "installed MC client jars for 1.21.11, 26.1, 26.2"
  - "the three test worlds present in the saves dir"
network: "yes — fetches matching Pillow sdist C headers from PyPI at build time"
safety: "read-only on real saves; worlds are copied to a scratch dir before rendering"
---

# Overviewer compatibility matrix

This folder verifies that Overviewer **builds and renders** across the operating
systems and Minecraft versions we support, using each platform's *own* numpy and
Pillow (apt-provided on Ubuntu, pip on Windows). It exists because several
incompatibilities only appear on specific combinations — e.g. numpy 2.x build
flags on gcc, the Pillow 12 C-API change, and Minecraft 26.2 texture relocations.

## High-level quickstart

Run the whole matrix from the **repo root on the Windows host** (needs Docker
Desktop running and the Minecraft client jars installed):

```bash
python test/compat/run_matrix.py
```

That stages the test worlds to a scratch dir, then runs four legs — Windows
native plus Ubuntu 22.04 / 24.04 / 26.04 containers — building the C extension
and rendering all three worlds in each. It prints a matrix like:

```
scenario           python   numpy      result   per-world
Windows-native     3.14.5   2.5.0      PASS     Derek-Single=ok Tester=ok GiveEr26_2=ok
Ubuntu 22.04       3.10.12  1.21.5     PASS     Derek-Single=ok Tester=ok GiveEr26_2=ok
Ubuntu 24.04       3.12.3   1.26.4     PASS     Derek-Single=ok Tester=ok GiveEr26_2=ok
Ubuntu 26.04       3.14.4   2.3.5      PASS     Derek-Single=ok Tester=ok GiveEr26_2=ok
```

Exit code is `0` only if every leg passed. Common subsets:

```bash
# Just the Ubuntu legs (skip the Windows native build):
python test/compat/run_matrix.py --skip-windows

# A single Ubuntu version:
python test/compat/run_matrix.py --skip-windows --ubuntu 26.04

# Point at non-default saves / versions / scratch locations:
python test/compat/run_matrix.py \
    --saves    "D:/mc/saves" \
    --versions "D:/mc/versions" \
    --work     "D:/tmp/ovmatrix"
```

Renders and a machine-readable `result.json` for each leg land under
`--work/out/<leg>/` (default `--work` is `…/Temp/ov_compat_matrix`). Open any
`…/out/<leg>/<world>/index.html` to eyeball a render.

## Prerequisites

- **Docker** running (Ubuntu legs). Base images `ubuntu:22.04/24.04/26.04` are pulled on demand.
- **Minecraft client jars** for each world's version under the versions dir, i.e.
  `versions/1.21.11/1.21.11.jar`, `versions/26.1/26.1.jar`, `versions/26.2/26.2.jar`.
  These supply version-accurate textures (server jars contain no textures).
- **The three test worlds** in the saves dir: `Derek-Single`, `Tester`, `GiveEr26_2`.
- **A C compiler** — gcc is installed inside the containers; the Windows leg needs the
  MSVC build tools already present on the host.
- **Network access** — each leg downloads the matching Pillow source distribution to get
  `Imaging.h` (neither pip wheels nor apt ship Pillow's C headers).

---

## Deeper dive

### Files

| File | Role |
|------|------|
| `run_matrix.py` | Host orchestrator. Stages worlds, runs the Windows-native leg in a fresh venv and each Ubuntu leg in a container, collects `result.json`, prints the matrix. |
| `render_test.py` | The per-environment worker. Runs *inside* a leg: prints env + numpy/Pillow provenance, ensures Pillow headers, builds `c_overviewer`, renders each world, writes `result.json`. OS-agnostic (stdlib + project deps only). |
| `Dockerfile.ubuntu` | Parametrized image (`--build-arg BASE=ubuntu:<ver>`). Installs OS-provided deps via apt (`python3-numpy python3-pil python3-networkx python3-requests`, build tooling). |
| `entrypoint.sh` | Container entry: copies the read-only repo to a writable `/work`, then invokes `render_test.py` against the mounted worlds/versions/output. |

### What each leg does

1. **Report the environment** — OS, Python, and numpy/Pillow version **and file path**, so
   you can confirm *which* numpy/Pillow was used (apt vs pip, 1.x vs 2.x).
2. **Ensure Pillow C headers** — read `PIL.__version__`, download that exact Pillow sdist,
   extract `src/libImaging/*.h`, and expose them via `PIL_INCLUDE_DIR`.
3. **Build** `c_overviewer` with `setup.py build_ext --inplace` against the leg's numpy.
4. **Render** each world to its own output dir with the matching client jar as `texturepath`.
5. **Judge** — a world passes if Overviewer exits 0 and every requested dimension produced
   `> 0` PNG tiles. The leg passes if all worlds pass.

### World / version / texture map (defined in `render_test.py`)

| World | MC version | Dimensions rendered | Layout exercised |
|-------|-----------|---------------------|------------------|
| `Derek-Single` | 1.21.11 | overworld | legacy (`region/`, `DIM*`) |
| `Tester` | 26.1 | overworld, nether, end | new `dimensions/minecraft/*` |
| `GiveEr26_2` | 26.2 | overworld, nether, end | new layout + 26.2 texture relocations |

To add a world, extend the `WORLDS` dict in `render_test.py` (and have a matching
`versions/<ver>/<ver>.jar` and a copy of the world available).

### Why containers, and the dev-box fallback trap

The Ubuntu legs run in **isolated containers that mount only the matching client jar**.
This is deliberate: on a developer machine with many Minecraft versions installed,
Overviewer silently **falls back to older jars** for any texture missing from the target
version's jar. That masks version-specific texture breakage (e.g. the Minecraft 26.2
bed/sign/pillar relocations) — a render can "pass" on the dev box yet fail for a real user
who only has 26.2. The container is the honest test; always trust it over a local run.

### Dependency policy (per OS)

- **Ubuntu**: use what the OS provides — numpy, Pillow, networkx, requests all come from
  `apt`. Nothing runtime is `pip`-installed. (`SETUPTOOLS_USE_DISTUTILS=local` is set so
  `setup.py` still imports `distutils` on Python ≥ 3.12, which removed it from stdlib.)
- **Windows**: everything from `pip` in a throwaway venv created by the orchestrator
  (relaxed `numpy>=1.21,<3`, `pillow>=10,<13`, plus networkx/requests — not the
  Windows-packaging extras).

### Interpreting results

- `result.json` (per leg) contains the full env block and per-world tile counts — diff it
  across runs to see what changed.
- A leg with `result == null` in the matrix means the container build/run itself failed
  (e.g. a compile error) — read that leg's stdout, not its (absent) `result.json`.
- A world that builds but renders **0 tiles** is almost always a missing/renamed texture
  for that Minecraft version — run that one world with `--verbose` against the matching
  jar to see the exact `Could not find the textures …` path.

### Running a single leg by hand (debugging)

In-place worker (uses the current interpreter's numpy/Pillow):

```bash
python test/compat/render_test.py \
    --worlds  "<staged worlds dir>" \
    --versions "<versions dir>" \
    --output  "<output dir>"
```

One Ubuntu image + container directly:

```bash
docker build --build-arg BASE=ubuntu:26.04 -t ov-compat-2604 -f test/compat/Dockerfile.ubuntu test/compat
docker run --rm \
    -v "<repo>:/repo:ro" \
    -v "<staged worlds>:/worlds:ro" \
    -v "<versions>:/mc-versions:ro" \
    -v "<output>:/output" \
    ov-compat-2604
```

> Note: this harness is a developer/CI utility, kept separate from the unit test suite
> (`test/test_*.py`). It shells out to Docker and a platform compiler and is not collected
> by `pytest`.
