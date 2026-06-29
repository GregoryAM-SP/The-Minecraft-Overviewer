#!/usr/bin/env python3
"""In-environment compatibility worker for the numpy / MC-version render matrix.

Runs *inside* one environment (Windows native, or an Ubuntu container) and:

  1. prints the OS, Python, and numpy/Pillow version + provenance (so we can
     prove which numpy was used -- apt vs pip, 1.x vs 2.x);
  2. ensures Pillow's C headers are available (neither pip nor apt ship
     ``Imaging.h``) by fetching the matching Pillow sdist headers if needed and
     exposing them via ``PIL_INCLUDE_DIR``;
  3. builds the ``c_overviewer`` C extension against this environment's numpy;
  4. renders each test world against its *matching-version* Minecraft client
     jar and checks the render produced tiles;
  5. writes a JSON result summary.

It is intentionally dependency-light (stdlib + the project's own deps) so the
same file works unmodified on every target OS.
"""

import argparse
import glob
import io
import json
import os
import platform
import subprocess
import sys
import tarfile
import urllib.request

# world name -> (version dir / jar basename, [dimensions])
# Matching-version client jars supply version-accurate textures.
WORLDS = {
    "Derek-Single": ("1.21.11", ["overworld"]),                  # legacy layout
    "Tester":       ("26.1",    ["overworld", "nether", "end"]),  # 26.1 new layout
    "GiveEr26_2":   ("26.2",    ["overworld", "nether", "end"]),  # 26.2 new layout
}


def log(msg):
    print(msg, flush=True)


def numpy_provenance():
    import numpy
    return {"version": numpy.__version__, "path": os.path.dirname(numpy.__file__)}


def pillow_provenance():
    import PIL
    return {"version": PIL.__version__, "path": os.path.dirname(PIL.__file__)}


def find_imaging_header():
    """Return a directory containing Imaging.h if one is already discoverable."""
    candidates = []
    env = os.environ.get("PIL_INCLUDE_DIR")
    if env:
        candidates.extend(env.split(os.pathsep))
    import PIL
    pil_dir = os.path.dirname(PIL.__file__)
    candidates.append(pil_dir)
    candidates.append(os.path.join(pil_dir, "include"))
    candidates.append(os.path.join(sys.prefix, "include"))
    for c in candidates:
        if c and os.path.exists(os.path.join(c, "Imaging.h")):
            return c
    return None


def ensure_pillow_headers(workdir):
    """Make sure Imaging.h is reachable; fetch the matching sdist if not.

    Modern Pillow wheels (and Debian/Ubuntu's python3-pil) do not ship the C
    headers that Overviewer's extension #includes, so download the source
    distribution that matches the *installed* Pillow version and expose its
    libImaging headers via PIL_INCLUDE_DIR.
    """
    found = find_imaging_header()
    if found:
        os.environ["PIL_INCLUDE_DIR"] = found
        log("Pillow headers already present at: %s" % found)
        return found

    import PIL
    version = PIL.__version__
    log("Pillow headers missing; fetching matching sdist for Pillow %s ..." % version)
    meta_url = "https://pypi.org/pypi/pillow/%s/json" % version
    with urllib.request.urlopen(meta_url) as r:
        meta = json.load(r)
    sdist = next(u for u in meta["urls"] if u["packagetype"] == "sdist")
    dest = os.path.join(workdir, "pil-headers")
    os.makedirs(dest, exist_ok=True)
    with urllib.request.urlopen(sdist["url"]) as r:
        data = r.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        for m in tf.getmembers():
            base = os.path.basename(m.name)
            if base.endswith(".h") and "/libImaging/" in m.name.replace("\\", "/"):
                m.name = base
                tf.extract(m, dest)
    if not os.path.exists(os.path.join(dest, "Imaging.h")):
        raise RuntimeError("could not obtain Imaging.h from Pillow %s sdist" % version)
    os.environ["PIL_INCLUDE_DIR"] = dest
    log("Pillow headers extracted to: %s" % dest)
    return dest


def build_extension(repo):
    log(">>> Building c_overviewer against numpy %s ..." % numpy_provenance()["version"])
    subprocess.run([sys.executable, "setup.py", "build_ext", "--inplace"],
                   cwd=repo, check=True)


def render_world(repo, name, versions_dir, worlds_dir, out_root):
    version, dims = WORLDS[name]
    jar = os.path.join(versions_dir, version, "%s.jar" % version)
    world_path = os.path.join(worlds_dir, name)
    out_dir = os.path.join(out_root, name)
    conf = os.path.join(out_root, "%s.conf" % name)
    os.makedirs(out_dir, exist_ok=True)

    lines = [
        "worlds[%r] = r%r" % (name, world_path),
        "outputdir = r%r" % out_dir,
        "texturepath = r%r" % jar,
        'rendermode = "normal"',
    ]
    for d in dims:
        lines.append("renders[%r] = {'world': %r, 'title': %r, 'dimension': %r}"
                     % (d, name, d, d))
    with open(conf, "w") as f:
        f.write("\n".join(lines) + "\n")

    log("\n#### Rendering %s (mc %s, dims: %s)" % (name, version, ", ".join(dims)))
    proc = subprocess.run([sys.executable, "overviewer.py", "--config=%s" % conf],
                          cwd=repo)
    tiles = {d: len(glob.glob(os.path.join(out_dir, d, "**", "*.png"), recursive=True))
             for d in dims}
    ok = proc.returncode == 0 and all(t > 0 for t in tiles.values())
    log("   exit=%d tiles=%s -> %s" % (proc.returncode, tiles, "PASS" if ok else "FAIL"))
    return {"world": name, "mc_version": version, "exit_code": proc.returncode,
            "tiles": tiles, "passed": ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--worlds", required=True, help="dir containing the test worlds")
    ap.add_argument("--versions", required=True, help="dir containing <ver>/<ver>.jar")
    ap.add_argument("--output", required=True, help="dir to write renders into")
    ap.add_argument("--result-json", default=None, help="optional path for JSON result")
    args = ap.parse_args()

    os.makedirs(args.output, exist_ok=True)
    env = {
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "numpy": numpy_provenance(),
        "pillow": pillow_provenance(),
    }
    log("=" * 64)
    log("OS      : %s" % env["os"])
    log("Python  : %s (%s)" % (env["python"], sys.executable))
    log("numpy   : %(version)s  [%(path)s]" % env["numpy"])
    log("Pillow  : %(version)s  [%(path)s]" % env["pillow"])
    log("=" * 64)

    ensure_pillow_headers(args.output)
    build_extension(args.repo)

    results = [render_world(args.repo, name, args.versions, args.worlds, args.output)
               for name in WORLDS]
    summary = {"env": env, "results": results,
               "passed": all(r["passed"] for r in results)}

    out_json = args.result_json or os.path.join(args.output, "result.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    log("\n==== %s ====" % ("ALL WORLDS PASSED" if summary["passed"] else "FAILURES PRESENT"))
    log("result json: %s" % out_json)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
