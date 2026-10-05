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
  config:   "./config.json — available worlds, selected worlds, and paths (created interactively on first run; see config.example.json)"
  worlds:   "any saves you choose, each tagged with its Minecraft version and dimensions"
  textures: "matching-version Minecraft client jars from .minecraft/versions"
outputs:
  - "per-leg renders + result.json under work_dir (from config.json)"
  - "a printed PASS/FAIL matrix; process exit code 0 iff every leg passed"
requires:
  - "docker or podman" # for the Ubuntu legs (engine: auto picks whichever is on PATH)
  - "a C toolchain"   # gcc in the containers; MSVC for the Windows leg
  - "installed MC client jars for each selected world's mc_version"
  - "the selected test worlds present at their configured locations"
non_interactive: "pass --yes (or run with non-tty stdin) to skip the selection prompt; config.json must already exist"
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

Run the whole matrix from the **repo root** (needs Docker or Podman running and
the Minecraft client jars installed):

```bash
python test/compat/run_matrix.py
```

**First run:** there is no `config.json` in the current directory yet, so a short
interview creates one. It asks for your saves, versions, and scratch directories,
which Ubuntu versions to test, and whether to run the Windows leg. It then lists
the worlds in your saves directory so you can pick which ones are *available* for
testing. For each world it reads `level.dat` to suggest the Minecraft version and
which dimensions exist; accept or override. Worlds stored elsewhere can be added
by path.

**Every run:** the available worlds are shown with the *selected* ones checked,
along with any missing world or jar, and you confirm before anything runs:

```
Test worlds (config.json):
   1. [x] Legacy-1.21              mc 1.21.11   overworld
   2. [x] NewLayout-26.1           mc 26.1      overworld, nether, end
   3. [ ] Snapshot-26.2            mc 26.2      overworld, nether, end    !! jar missing
Legs: Windows-native, Ubuntu 22.04, Ubuntu 24.04, Ubuntu 26.04
Run with the 2 selected world(s)? [Y]es / [e]dit / [q]uit [y]:
```

`e` lets you toggle worlds by number, and the new selection is saved back to
`config.json`. The script then stages the selected worlds to a scratch dir and
runs each leg (Windows native, plus one container per Ubuntu version). Each leg
builds the C extension and renders every selected world. It prints a matrix like:

```
scenario           python   numpy      result   per-world
Windows-native     3.14.5   2.5.0      PASS     Legacy-1.21=ok NewLayout-26.1=ok
Ubuntu 22.04       3.10.12  1.21.5     PASS     Legacy-1.21=ok NewLayout-26.1=ok
Ubuntu 24.04       3.12.3   1.26.4     PASS     Legacy-1.21=ok NewLayout-26.1=ok
Ubuntu 26.04       3.14.4   2.3.5      PASS     Legacy-1.21=ok NewLayout-26.1=ok
```

Exit code is `0` only if every leg passed. Common options:

```bash
# Non-interactive (agents/CI): use config.json as-is, no confirmation prompt.
python test/compat/run_matrix.py --yes

# Just the Ubuntu legs (skip the Windows native build):
python test/compat/run_matrix.py --skip-windows

# A single Ubuntu version (overrides the config's list for this run):
python test/compat/run_matrix.py --skip-windows --ubuntu 26.04

# Force a container engine (default "auto": docker if on PATH, else podman):
python test/compat/run_matrix.py --engine podman

# Use a different config file, or redo the setup interview:
python test/compat/run_matrix.py --config D:/mc/ovmatrix.json
python test/compat/run_matrix.py --setup
```

Renders and a machine-readable `result.json` for each leg land under
`<work_dir>/out/<leg>/` (default `work_dir` is `…/Temp/ov_compat_matrix`). Open
any `…/out/<leg>/<world>/index.html` to eyeball a render.

### `config.json`

`config.json` holds machine-specific paths and your own worlds, so it is
gitignored. `config.example.json` shows the format:

| Key | Meaning |
|-----|---------|
| `saves_dir` | Where worlds live by default (`<saves_dir>/<world name>`). |
| `versions_dir` | Minecraft versions dir; must contain `<ver>/<ver>.jar` for each world's `mc_version`. |
| `work_dir` | Scratch dir for staged world copies, venv, and renders. Optional. |
| `ubuntu` | Ubuntu versions to run as container legs. Optional, defaults to 22.04 / 24.04 / 26.04. |
| `windows` | Run the Windows-native leg when on Windows. Optional, defaults to `true`. |
| `engine` | Container engine for the Ubuntu legs: `auto`, `docker` or `podman`. Optional, defaults to `auto` (Docker if it's on PATH, otherwise Podman). |
| `worlds` | The **available** worlds, keyed by name: `mc_version`, `dimensions` (`overworld` / `nether` / `end`), and an optional `path` if the world isn't in `saves_dir`. |
| `selected` | The names from `worlds` to test on this run. |

### Choosing test worlds

Use small worlds, because each one is rendered once per leg. Together they should
cover the Minecraft versions and world layouts you care about. A good set is:

- a pre-26.1 world (legacy `region/`, `DIM-1`, `DIM1` layout);
- a 26.1+ world (new `dimensions/minecraft/*` layout) with the nether and end visited;
- a world on the newest supported version, to catch texture relocations.

To create one, start a new world in that Minecraft client version, walk around
long enough to generate some chunks, visit the other dimensions if you want them
rendered, then quit. Add it with `--setup` or by editing `config.json`.

## Prerequisites

- **Docker or Podman** running (Ubuntu legs). Base images
  `docker.io/library/ubuntu:22.04/24.04/26.04` are pulled on demand. The engine is
  checked before anything runs, so a stopped Podman machine fails fast with a hint.
  See [Using Podman](#using-podman).
- **Minecraft client jars** for each selected world's `mc_version` under the versions
  dir, e.g. `versions/1.21.11/1.21.11.jar`. Launch that version once in the official
  launcher to download it. These supply version-accurate textures (server jars
  contain no textures).
- **Test worlds**: see [Choosing test worlds](#choosing-test-worlds).
- **A C compiler** — gcc is installed inside the containers; the Windows leg needs the
  MSVC build tools already present on the host.
- **Network access** — each leg downloads the matching Pillow source distribution to get
  `Imaging.h` (neither pip wheels nor apt ship Pillow's C headers).

### Using Podman

Podman works as a drop-in for Docker here: the same `Dockerfile.ubuntu`, and the
same `build` / `run` flags. Compose isn't used. Select it with `"engine": "podman"`
in `config.json`, or `--engine podman`. With `auto`, it is used whenever `docker`
isn't on PATH.

On Windows and macOS Podman runs containers inside a Linux VM (the "machine"),
which, unlike Docker Desktop, you start yourself:

```bash
podman machine init      # once
podman machine start     # each boot / session
```

**Paths.** On Windows, the orchestrator passes ordinary `C:\...` paths for the
mounts. Podman translates them to the machine's `/mnt/c/...` itself (see
[volume mounting](https://github.com/podman-container-tools/podman/blob/main/docs/tutorials/podman-for-windows.md#volume-mounting)),
so `saves_dir`, `versions_dir` and `work_dir` can stay as Windows paths.

**cgroups.** Podman containers run with `--cgroups=disabled`. The harness sets
no resource limits, and some Podman machines (seen on WSL, where systemd isn't
running inside the machine) don't hand cgroup controllers down to containers.
Without the flag, every container then fails to start with
``crun: controller `pids` is not available``.

**File ownership.** Rootless Podman (the default) maps the container's root
user to you, so renders under `<work_dir>/out/` belong to your user. Under
Docker on Linux they would belong to root.

**Resources for larger worlds.** Overviewer starts one render worker per CPU it
can see, and every worker needs memory. The machine's defaults (often 2 GiB of
RAM, with all of the host's CPUs) are fine for small test worlds. Larger worlds
can run out of memory, which shows up as killed workers or a failed render.
Either give the machine more memory or let it see fewer CPUs, which means fewer
workers:

```bash
podman machine stop
podman machine set --memory 8192 --cpus 4    # MiB; tune to your host
podman machine start
podman machine inspect --format "{{.Resources.Memory}} MiB, {{.Resources.CPUs}} CPUs"
```

When running a world by hand, you can also cap the workers per render with
Overviewer's own switch: `python overviewer.py -p 2 --config=...`. The Docker
Desktop equivalent of the machine settings is *Settings → Resources*.

---

## Deeper dive

### Files

| File | Role |
|------|------|
| `run_matrix.py` | Host orchestrator. Loads or creates `config.json`, confirms the world selection, stages the selected worlds plus a `manifest.json`, runs the Windows-native leg in a fresh venv and each Ubuntu leg in a container, collects `result.json`, prints the matrix. |
| `render_test.py` | The per-environment worker. Runs *inside* a leg: prints env + numpy/Pillow provenance, ensures Pillow headers, builds `c_overviewer`, renders each world listed in the staged `manifest.json`, writes `result.json`. OS-agnostic (stdlib + project deps only). |
| `Dockerfile.ubuntu` | Parametrized image (`--build-arg BASE=docker.io/library/ubuntu:<ver>`), built with Docker or Podman. Installs OS-provided deps via apt (`python3-numpy python3-pil python3-networkx python3-requests`, build tooling). |
| `config.example.json` | Example of the `config.json` format. |
| `entrypoint.sh` | Container entry: copies the read-only repo to a writable `/work`, then invokes `render_test.py` against the mounted worlds/versions/output. |

### What each leg does

1. **Report the environment** — OS, Python, and numpy/Pillow version **and file path**, so
   you can confirm *which* numpy/Pillow was used (apt vs pip, 1.x vs 2.x).
2. **Ensure Pillow C headers** — read `PIL.__version__`, download that exact Pillow sdist,
   extract `src/libImaging/*.h`, and expose them via `PIL_INCLUDE_DIR`.
3. **Build** `c_overviewer` with `setup.py build` (which also generates `primitives.h` and
   `overviewer_version.py`, and builds the extension in place) against the leg's numpy.
4. **Render** each world to its own output dir with the matching client jar as `texturepath`.
5. **Judge** — a world passes if Overviewer exits 0 and every requested dimension produced
   `> 0` PNG tiles. The leg passes if all worlds pass.

### How worlds reach each leg

`run_matrix.py` copies each selected world to `<work_dir>/worlds/<name>`. It skips
worlds that were already staged, so delete the copy to refresh it. It then writes
`<work_dir>/worlds/manifest.json`:

```json
{"worlds": [{"name": "Legacy-1.21", "mc_version": "1.21.11", "dimensions": ["overworld"]}]}
```

That directory is mounted read-only into each container at `/worlds`.
`render_test.py` reads the manifest from there (or from `--manifest`), so it has
no world list of its own.

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
    --worlds  "<staged worlds dir, containing manifest.json>" \
    --versions "<versions dir>" \
    --output  "<output dir>"
```

One Ubuntu image + container directly (`podman` takes the same arguments):

```bash
docker build --build-arg BASE=docker.io/library/ubuntu:26.04 -t ov-compat-2604 -f test/compat/Dockerfile.ubuntu test/compat
docker run --rm \
    -v "<repo>:/repo:ro" \
    -v "<staged worlds>:/worlds:ro" \
    -v "<versions>:/mc-versions:ro" \
    -v "<output>:/output" \
    ov-compat-2604
```

> Note: this harness is a developer/CI utility, kept separate from the unit test suite
> (`test/test_*.py`). It shells out to Docker/Podman and a platform compiler and is not collected
> by `pytest`.
