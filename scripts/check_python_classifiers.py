#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Checks that the Python version classifiers in pyproject.toml match the
non-experimental versions in the CI test matrix (.github/workflows/ci.yaml).
"""

import re
import sys
import tomllib
from pathlib import Path

root = Path(__file__).parent.parent

with open(root / "pyproject.toml", "rb") as f:
    data = tomllib.load(f)

classifier_versions = {
    c.removeprefix("Programming Language :: Python :: ")
    for c in data["project"]["classifiers"]
    if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", c)
}

ci = (root / ".github/workflows/ci.yaml").read_text()

match = re.search(r'python-version: \[([^\]]+)\]\s*\n\s*resolution:', ci)
if not match:
    print("ERROR: could not find python-version matrix in ci.yaml")
    sys.exit(1)

matrix_versions = set(re.findall(r'"(3\.\d+)"', match.group(1)))

if classifier_versions != matrix_versions:
    print(f"MISMATCH")
    print(f"  classifiers: {sorted(classifier_versions)}")
    print(f"  CI matrix:   {sorted(matrix_versions)}")
    sys.exit(1)

print(f"OK: {sorted(matrix_versions)}")
