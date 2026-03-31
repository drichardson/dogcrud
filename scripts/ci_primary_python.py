#!/usr/bin/env -S uv run
"""
Prints the highest non-experimental Python version from the CI test matrix.
"""

import sys
from pathlib import Path

import yaml

root = Path(__file__).parent.parent
ci = yaml.safe_load((root / ".github/workflows/ci.yaml").read_text())

matrix = ci["jobs"]["tests"]["strategy"]["matrix"]
versions = [str(v) for v in matrix["python-version"]]

if not versions:
    print("ERROR: no python-version entries in CI matrix", file=sys.stderr)
    sys.exit(1)

print(max(versions, key=lambda v: tuple(int(x) for x in v.split("."))))
