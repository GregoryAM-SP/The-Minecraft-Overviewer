"""Extract default properties from Minecraft's blocks report.

See docs/running.rst (Minecraft 26.3+ saves) for when to regenerate this file.
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="reports/blocks.json from Minecraft --reports")
    parser.add_argument("output", type=Path, help="overviewer_core/blockstate_defaults.py")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    lines = [
        "# Generated from a Minecraft Java Edition blocks report.",
        "# Regenerate with contrib/generateBlockstateDefaults.py; do not edit by hand.",
        "",
        "DEFAULT_BLOCK_PROPERTIES = {",
    ]
    for name, block in sorted(report.items()):
        defaults = [state for state in block["states"] if state.get("default")]
        if len(defaults) != 1:
            raise ValueError("Expected one default state for %s" % name)
        properties = defaults[0].get("properties", {})
        if properties:
            lines.append("    %r: %r," % (name, dict(sorted(properties.items()))))
    lines.append("}")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
