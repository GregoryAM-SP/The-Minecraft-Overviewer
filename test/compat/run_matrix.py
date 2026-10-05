#!/usr/bin/env python3
"""Orchestrate the numpy / MC-version compatibility matrix from the host.

Scenarios:
  * Windows-native (Python >= 3.12, numpy from pip)  -- run with a fresh venv;
  * Ubuntu 22.04 / 24.04 / 26.04 containers (numpy from apt) -- run via Docker
    or Podman.

Each scenario builds the C extension against that environment's numpy and
renders the selected test worlds against their matching-version client jars
(see render_test.py). Results are aggregated into a pass/fail matrix.

Which worlds exist, which are selected, and where saves / client jars / scratch
output live are all read from a config.json (default: ./config.json). If it is
missing, a short interview creates it; if it exists, the selection is shown for
confirmation before anything runs. See config.example.json for the format.

This is a developer/CI utility, not part of the unit test suite. It shells out
to docker or podman and (for the Windows leg) to the platform Python; run it
from the repo root on a host that has a container engine and the MC client jars.
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MANIFEST_NAME = "manifest.json"  # must match render_test.py
DEFAULT_UBUNTU = ["22.04", "24.04", "26.04"]
ENGINES = ["docker", "podman"]

if sys.platform == "win32":
    MC_HOME = os.path.expandvars(r"%APPDATA%\.minecraft")
elif sys.platform == "darwin":
    MC_HOME = os.path.expanduser("~/Library/Application Support/minecraft")
else:
    MC_HOME = os.path.expanduser("~/.minecraft")


def run(cmd, **kw):
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, **kw)


# --------------------------------------------------------------------------
# config.json
# --------------------------------------------------------------------------

def world_source(cfg, name):
    """Location of a world: its own "path" if given, else <saves_dir>/<name>."""
    return cfg["worlds"][name].get("path") or os.path.join(cfg["saves_dir"], name)


def jar_path(cfg, version):
    return os.path.join(cfg["versions_dir"], version, "%s.jar" % version)


def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    for key in ("saves_dir", "versions_dir", "worlds", "selected"):
        if key not in cfg:
            raise SystemExit("%s: missing required key %r (see config.example.json)"
                             % (path, key))
    unknown = [w for w in cfg["selected"] if w not in cfg["worlds"]]
    if unknown:
        raise SystemExit("%s: selected worlds not listed under \"worlds\": %s"
                         % (path, ", ".join(unknown)))
    for name, w in cfg["worlds"].items():
        if "mc_version" not in w:
            raise SystemExit("%s: world %r has no \"mc_version\"" % (path, name))
        w.setdefault("dimensions", ["overworld"])
    cfg.setdefault("work_dir", os.path.join(tempfile.gettempdir(), "ov_compat_matrix"))
    cfg.setdefault("ubuntu", DEFAULT_UBUNTU)
    cfg.setdefault("windows", True)
    cfg.setdefault("engine", "auto")
    if cfg["engine"] not in ["auto"] + ENGINES:
        raise SystemExit("%s: \"engine\" must be auto, docker or podman" % path)
    return cfg


def save_config(path, cfg):
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print("saved %s" % path)


# --------------------------------------------------------------------------
# Interactive setup / confirmation
# --------------------------------------------------------------------------

def ask(prompt, default=None):
    suffix = " [%s]" % default if default not in (None, "") else ""
    try:
        answer = input("%s%s: " % (prompt, suffix)).strip()
    except EOFError:
        raise SystemExit("\naborted (no input)")
    return answer or (default if default is not None else "")


def ask_yes_no(prompt, default=True):
    answer = ask("%s (%s)" % (prompt, "Y/n" if default else "y/N")).lower()
    return default if not answer else answer.startswith("y")


def ask_dir(prompt, default):
    while True:
        path = os.path.abspath(os.path.expanduser(ask(prompt, default)))
        if os.path.isdir(path):
            return path
        print("  not a directory: %s" % path)


def detect_world_info(world_dir):
    """Best-effort (mc_version, dimensions) for a save, read from level.dat.

    Either value may be None if it cannot be determined; the caller asks.
    """
    version = None
    try:
        # Load nbt.py standalone (stdlib only): importing the overviewer_core
        # package would demand a built c_overviewer extension.
        spec = importlib.util.spec_from_file_location(
            "ov_nbt", os.path.join(REPO, "overviewer_core", "nbt.py"))
        nbt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nbt)
        data = nbt.load(os.path.join(world_dir, "level.dat"))[1]["Data"]
        version = data.get("Version", {}).get("Name")
    except Exception:
        pass

    def has(*parts):
        # Minecraft creates DIM-1/ and DIM1/ (holding just data/) in every
        # world, visited or not, so look for actual region files.
        region = os.path.join(world_dir, *parts, "region")
        try:
            return any(f.endswith(".mca") for f in os.listdir(region))
        except OSError:
            return False
    dims = ["overworld"]
    if has("DIM-1") or has("dimensions", "minecraft", "the_nether"):
        dims.append("nether")
    if has("DIM1") or has("dimensions", "minecraft", "the_end"):
        dims.append("end")
    return version, dims


def list_saves(saves_dir):
    try:
        names = sorted(os.listdir(saves_dir), key=str.lower)
    except OSError:
        return []
    return [n for n in names
            if os.path.isfile(os.path.join(saves_dir, n, "level.dat"))]


def parse_numbers(text, count):
    """Parse "1, 3 4" into zero-based indices, ignoring anything out of range."""
    picked = []
    for tok in text.replace(",", " ").split():
        if tok.isdigit() and 1 <= int(tok) <= count:
            picked.append(int(tok) - 1)
        else:
            print("  ignoring %r" % tok)
    return picked


def describe_world(cfg, name):
    w = cfg["worlds"][name]
    notes = []
    src = world_source(cfg, name)
    if not os.path.isdir(src):
        notes.append("world missing")
    else:
        empty = [d for d in w["dimensions"] if d not in detect_world_info(src)[1]]
        if empty:
            notes.append("no %s data" % "/".join(empty))
    if not os.path.isfile(jar_path(cfg, w["mc_version"])):
        notes.append("jar missing")
    return ("%-24s mc %-9s %-24s%s" % (
        name, w["mc_version"], ", ".join(w["dimensions"]),
        ("  !! " + ", ".join(notes)) if notes else "")).rstrip()


def add_world(cfg, name, source=None):
    src = source or os.path.join(cfg["saves_dir"], name)
    version, available = detect_world_info(src)
    print("\n  %s" % name)
    version = ask("    Minecraft version (client jar to texture with)", version)
    while not version:
        version = ask("    Minecraft version (e.g. 1.21.11)")
    if not os.path.isfile(jar_path(cfg, version)):
        print("    warning: %s not found; install that client version before running"
              % jar_path(cfg, version))
    # Only offer dimensions that have region data: rendering one without any
    # produces no tiles, which the worker counts as a failure.
    if len(available) == 1:
        print("    Dimensions: overworld (the only one with region data)")
        dims = available
    else:
        while True:
            answer = ask("    Dimensions to render (%s)" % "/".join(available),
                         ", ".join(available))
            picked = answer.replace(",", " ").split()
            dims = [d for d in available if d in picked]
            unknown = [d for d in picked if d not in available]
            if unknown:
                print("    not available in this world: %s" % ", ".join(unknown))
            elif dims:
                break
    entry = {"mc_version": version, "dimensions": dims}
    if source:
        entry["path"] = source
    cfg["worlds"][name] = entry


def interview(path):
    print("No %s found -- let's create one.\n" % path)
    print("The matrix renders a few Minecraft worlds, each against the client jar for")
    print("its own Minecraft version, inside every OS environment under test.\n")

    cfg = {}
    cfg["saves_dir"] = ask_dir("Minecraft saves directory",
                               os.path.join(MC_HOME, "saves"))
    cfg["versions_dir"] = ask_dir("Minecraft versions directory (holds <ver>/<ver>.jar)",
                                  os.path.join(MC_HOME, "versions"))
    cfg["work_dir"] = os.path.abspath(os.path.expanduser(ask(
        "Scratch directory for staged worlds and renders",
        os.path.join(tempfile.gettempdir(), "ov_compat_matrix"))))
    cfg["ubuntu"] = ask("Ubuntu versions to test (space separated)",
                        " ".join(DEFAULT_UBUNTU)).split()
    cfg["windows"] = (sys.platform == "win32"
                      and ask_yes_no("Run the Windows-native leg too?"))
    while True:
        cfg["engine"] = ask("Container engine for the Ubuntu legs (auto/docker/podman)",
                            "auto").lower()
        if cfg["engine"] in ["auto"] + ENGINES:
            break
    cfg["worlds"] = {}

    saves = list_saves(cfg["saves_dir"])
    if saves:
        print("\nWorlds found in %s:" % cfg["saves_dir"])
        for i, name in enumerate(saves, 1):
            print("  %2d. %s" % (i, name))
        print("Small worlds covering each Minecraft version / world layout you care")
        print("about make the best test set (renders run once per OS environment).")
        for i in parse_numbers(ask("Worlds to make available for testing (numbers)"),
                               len(saves)):
            add_world(cfg, saves[i])
    while ask_yes_no("\nAdd a world from another location?", default=not cfg["worlds"]):
        src = ask_dir("  World directory (contains level.dat)", None)
        add_world(cfg, ask("  Name for this world", os.path.basename(src)), src)

    if not cfg["worlds"]:
        raise SystemExit("no worlds configured; nothing to test")
    cfg["selected"] = list(cfg["worlds"])
    save_config(path, cfg)
    print("All configured worlds are selected; you can change that next.\n")
    return cfg


def confirm_selection(path, cfg):
    """Show available worlds with the selected ones checked; allow toggling."""
    names = list(cfg["worlds"])
    changed = False
    while True:
        print("\nTest worlds (%s):" % path)
        for i, name in enumerate(names, 1):
            mark = "x" if name in cfg["selected"] else " "
            print("  %2d. [%s] %s" % (i, mark, describe_world(cfg, name)))
        legs = (["Windows-native"] if cfg["windows"] and sys.platform == "win32" else [])
        legs += ["Ubuntu %s (%s)" % (u, cfg["engine"]) for u in cfg["ubuntu"]]
        print("Legs: %s" % (", ".join(legs) or "(none)"))

        answer = ask("Run with the %d selected world(s)? [Y]es / [e]dit / [q]uit"
                     % len(cfg["selected"]), "y").lower()
        if answer.startswith("q"):
            raise SystemExit("aborted")
        if answer.startswith("e"):
            for i in parse_numbers(ask("  Numbers to toggle"), len(names)):
                if names[i] in cfg["selected"]:
                    cfg["selected"].remove(names[i])
                else:
                    cfg["selected"].append(names[i])
            # keep the config's ordering stable
            cfg["selected"] = [n for n in names if n in cfg["selected"]]
            changed = True
            continue
        if not cfg["selected"]:
            print("  select at least one world")
            continue
        if changed:
            save_config(path, cfg)
        return


# --------------------------------------------------------------------------
# Running the legs
# --------------------------------------------------------------------------

def resolve_engine(choice):
    """Pick the container engine CLI: the configured one, or for "auto" the
    first of docker / podman found on PATH."""
    candidates = ENGINES if choice == "auto" else [choice]
    for name in candidates:
        if shutil.which(name):
            return name
    raise SystemExit("no container engine found on PATH (looked for %s); install "
                     "one, or pass --ubuntu with no versions to skip the Ubuntu "
                     "legs" % " / ".join(candidates))


def check_engine(engine):
    """Fail fast if the engine can't reach its daemon / VM.

    Docker Desktop starts its VM itself, but on Windows and macOS Podman's VM
    has to be started explicitly, and otherwise every leg fails separately
    with a connection error.
    """
    proc = subprocess.run([engine, "info"], stdout=subprocess.DEVNULL,
                          stderr=subprocess.PIPE, text=True)
    if proc.returncode == 0:
        return
    err = proc.stderr.strip().splitlines()
    msg = "%s is installed but not reachable:\n  %s" % (
        engine, err[-1] if err else "exit code %d" % proc.returncode)
    if engine == "podman" and sys.platform != "linux":
        msg += "\nStart the Podman machine first:  podman machine start"
    else:
        msg += "\nStart the %s service/daemon and try again." % engine
    raise SystemExit(msg)


def stage_worlds(cfg):
    """Copy the selected worlds to a scratch dir so we never render live saves,
    and write the manifest render_test.py reads."""
    dst = os.path.join(cfg["work_dir"], "worlds")
    os.makedirs(dst, exist_ok=True)
    manifest = []
    for name in cfg["selected"]:
        src = world_source(cfg, name)
        d = os.path.join(dst, name)
        if not os.path.isdir(src):
            raise SystemExit("world not found: %s" % src)
        if not os.path.isdir(d):
            print("staging world %s ..." % name, flush=True)
            shutil.copytree(src, d)
        w = cfg["worlds"][name]
        manifest.append({"name": name, "mc_version": w["mc_version"],
                         "dimensions": w["dimensions"]})
    with open(os.path.join(dst, MANIFEST_NAME), "w") as f:
        json.dump({"worlds": manifest}, f, indent=2)
    return dst


def prepare_output(work, leg):
    out = os.path.join(work, "out", leg)
    os.makedirs(out, exist_ok=True)
    # Drop a previous run's result so a leg that dies early isn't reported
    # with stale (possibly different-world) results.
    stale = os.path.join(out, "result.json")
    if os.path.exists(stale):
        os.remove(stale)
    return out


def read_result(out_dir):
    p = os.path.join(out_dir, "result.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None


def run_windows(worlds, versions, work):
    out = prepare_output(work, "windows")
    venv = os.path.join(work, "venv-win")
    if not os.path.isdir(venv):
        run([sys.executable, "-m", "venv", venv], check=True)
    py = os.path.join(venv, "Scripts", "python.exe")
    run([py, "-m", "pip", "install", "--quiet", "--upgrade",
         "pip", "setuptools", "wheel"], check=True)
    # numpy from pip (relaxed range -> a Python >=3.12 wheel, i.e. numpy 2.x)
    run([py, "-m", "pip", "install", "--quiet",
         "numpy>=1.21,<3", "pillow>=10,<13", "networkx>=3.0", "requests"], check=True)
    proc = run([py, os.path.join("test", "compat", "render_test.py"),
                "--repo", REPO, "--worlds", worlds,
                "--versions", versions, "--output", out], cwd=REPO)
    return ("Windows-native", proc.returncode, read_result(out))


def git_version():
    """The host checkout's tag and commit, for entrypoint.sh (the container has
    no .git, and setup.py rejects the 'unknown' version it falls back to)."""
    info = {}
    for var, cmd in (("OV_VERSION", ["git", "describe", "--tags", "--abbrev=0"]),
                     ("OV_HASH", ["git", "rev-parse", "HEAD"])):
        try:
            out = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        except OSError:  # git not installed
            break
        if out.returncode == 0 and out.stdout.strip():
            info[var] = out.stdout.strip()
    return info


def run_ubuntu(engine, tag, worlds, versions, work):
    image = "ov-compat-%s" % tag.replace(":", "-").replace(".", "")
    out = prepare_output(work, tag.replace(":", "-"))
    build = run([engine, "build",
                 "--build-arg", "BASE=docker.io/library/ubuntu:%s" % tag,
                 "-t", image, "-f", os.path.join(HERE, "Dockerfile.ubuntu"), HERE])
    if build.returncode != 0:
        return ("Ubuntu %s" % tag, build.returncode, None)
    cmd = [engine, "run", "--rm"]
    if engine == "podman":
        # We set no resource limits, so cgroups buy nothing here. Podman
        # machines without systemd (seen on WSL) don't delegate cgroup
        # controllers, and crun then refuses to start any container
        # ("controller `pids` is not available").
        cmd.append("--cgroups=disabled")
    try:
        rel_work = os.path.relpath(os.path.abspath(work), REPO)
    except ValueError:  # different drive on Windows
        rel_work = os.pardir
    if not rel_work.startswith(os.pardir) and rel_work != os.curdir:
        # work_dir lives inside the repo: keep entrypoint.sh from copying the
        # staged worlds and earlier outputs into the container's /work.
        cmd += ["-e", "COMPAT_EXCLUDE=/%s" % rel_work.replace(os.sep, "/")]
    for var, value in git_version().items():
        cmd += ["-e", "%s=%s" % (var, value)]
    # Windows paths are fine for both engines: Podman on Windows translates
    # C:\... to the machine's /mnt/c/... itself.
    proc = run(cmd + ["-v", "%s:/repo:ro" % REPO,
                      "-v", "%s:/worlds:ro" % worlds,
                      "-v", "%s:/mc-versions:ro" % versions,
                      "-v", "%s:/output" % out,
                      image])
    return ("Ubuntu %s" % tag, proc.returncode, read_result(out))


def print_matrix(rows):
    print("\n" + "=" * 72)
    print("COMPATIBILITY MATRIX")
    print("=" * 72)
    hdr = "%-18s %-8s %-10s %-8s %s" % ("scenario", "python", "numpy", "result", "per-world")
    print(hdr)
    print("-" * 72)
    for name, rc, res in rows:
        if res is None:
            print("%-18s %-8s %-10s %-8s (no result; exit=%s)"
                  % (name, "-", "-", "ERROR", rc))
            continue
        env = res["env"]
        per = " ".join("%s=%s" % (r["world"], "ok" if r["passed"] else "FAIL")
                       for r in res["results"])
        print("%-18s %-8s %-10s %-8s %s"
              % (name, env["python"], env["numpy"]["version"],
                 "PASS" if res["passed"] else "FAIL", per))
    print("=" * 72)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", default=os.path.join(os.getcwd(), "config.json"),
                    help="config file (default: ./config.json; created interactively "
                         "if missing)")
    ap.add_argument("--setup", action="store_true",
                    help="re-run the setup interview, overwriting the config")
    ap.add_argument("-y", "--yes", action="store_true",
                    help="don't ask to confirm the selected worlds (non-interactive use)")
    ap.add_argument("--ubuntu", nargs="*", default=None,
                    help="override the config's Ubuntu versions")
    ap.add_argument("--skip-windows", action="store_true")
    ap.add_argument("--engine", choices=["auto"] + ENGINES, default=None,
                    help="override the config's container engine for the Ubuntu legs")
    args = ap.parse_args()

    interactive = sys.stdin.isatty() and not args.yes
    if args.setup or not os.path.exists(args.config):
        if not sys.stdin.isatty():
            raise SystemExit("%s not found and stdin is not interactive; copy "
                             "test/compat/config.example.json there and edit it"
                             % args.config)
        interview(args.config)
    cfg = load_config(args.config)
    if args.ubuntu is not None:
        cfg["ubuntu"] = args.ubuntu
    if args.skip_windows:
        cfg["windows"] = False
    if args.engine:
        cfg["engine"] = args.engine
    if interactive:
        confirm_selection(args.config, cfg)
    if not cfg["selected"]:
        raise SystemExit("%s: no worlds selected" % args.config)

    engine = None
    if cfg["ubuntu"]:
        engine = resolve_engine(cfg["engine"])
        check_engine(engine)

    work = cfg["work_dir"]
    os.makedirs(work, exist_ok=True)
    worlds = stage_worlds(cfg)

    rows = []
    if cfg["windows"] and sys.platform == "win32":
        rows.append(run_windows(worlds, cfg["versions_dir"], work))
    for tag in cfg["ubuntu"]:
        rows.append(run_ubuntu(engine, tag, worlds, cfg["versions_dir"], work))

    print_matrix(rows)
    return 0 if all(res is not None and res["passed"] for _, _, res in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
