#!/usr/bin/env python3
"""Orchestrate the numpy / MC-version compatibility matrix from the host.

Scenarios:
  * Windows-native (Python >= 3.12, numpy from pip)  -- run with a fresh venv;
  * Ubuntu 22.04 / 24.04 / 26.04 containers (numpy from apt) -- run via Docker.

Each scenario builds the C extension against that environment's numpy and
renders the three test worlds against their matching-version client jars
(see render_test.py). Results are aggregated into a pass/fail matrix.

This is a developer/CI utility, not part of the unit test suite. It shells out
to docker and (for the Windows leg) to the platform Python; run it from the
repo root on the Windows host that has Docker Desktop and the MC client jars.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
WORLDS = ["Derek-Single", "Tester", "GiveEr26_2"]

DEFAULT_SAVES = os.path.expandvars(r"%APPDATA%\.minecraft\saves")
DEFAULT_VERSIONS = os.path.expandvars(r"%APPDATA%\.minecraft\versions")


def run(cmd, **kw):
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, **kw)


def stage_worlds(saves, work):
    """Copy the test worlds to a scratch dir so we never render the live saves."""
    dst = os.path.join(work, "worlds")
    os.makedirs(dst, exist_ok=True)
    for w in WORLDS:
        src = os.path.join(saves, w)
        d = os.path.join(dst, w)
        if not os.path.isdir(src):
            raise SystemExit("world not found: %s" % src)
        if not os.path.isdir(d):
            print("staging world %s ..." % w, flush=True)
            shutil.copytree(src, d)
    return dst


def read_result(out_dir):
    p = os.path.join(out_dir, "result.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None


def run_windows(worlds, versions, work):
    out = os.path.join(work, "out", "windows")
    os.makedirs(out, exist_ok=True)
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


def run_ubuntu(tag, worlds, versions, work):
    image = "ov-compat-%s" % tag.replace(":", "-").replace(".", "")
    out = os.path.join(work, "out", tag.replace(":", "-"))
    os.makedirs(out, exist_ok=True)
    build = run(["docker", "build", "--build-arg", "BASE=ubuntu:%s" % tag,
                 "-t", image, "-f", os.path.join(HERE, "Dockerfile.ubuntu"), HERE])
    if build.returncode != 0:
        return ("Ubuntu %s" % tag, build.returncode, None)
    proc = run(["docker", "run", "--rm",
                "-v", "%s:/repo:ro" % REPO,
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--saves", default=DEFAULT_SAVES)
    ap.add_argument("--versions", default=DEFAULT_VERSIONS)
    ap.add_argument("--work", default=os.path.join(tempfile.gettempdir(), "ov_compat_matrix"))
    ap.add_argument("--ubuntu", nargs="*", default=["22.04", "24.04", "26.04"])
    ap.add_argument("--skip-windows", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.work, exist_ok=True)
    worlds = stage_worlds(args.saves, args.work)

    rows = []
    if not args.skip_windows and sys.platform == "win32":
        rows.append(run_windows(worlds, args.versions, args.work))
    for tag in args.ubuntu:
        rows.append(run_ubuntu(tag, worlds, args.versions, args.work))

    print_matrix(rows)
    return 0 if all(res is not None and res["passed"] for _, _, res in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
