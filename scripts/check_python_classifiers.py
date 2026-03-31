#!/usr/bin/env -S uv run
"""
Checks that the Python version classifiers in pyproject.toml match the
non-experimental versions in the CI test matrix (.github/workflows/ci.yaml).
"""

import re
import sys
import tomllib
from pathlib import Path

import yaml

root = Path(__file__).parent.parent

with open(root / "pyproject.toml", "rb") as f:
    data = tomllib.load(f)

classifier_versions = {
    c.removeprefix("Programming Language :: Python :: ")
    for c in data["project"]["classifiers"]
    if re.fullmatch(r"Programming Language :: Python :: \d+\.\d+", c)
}

ci = yaml.safe_load((root / ".github/workflows/ci.yaml").read_text())

matrix = ci["jobs"]["tests"]["strategy"]["matrix"]
matrix_versions = {str(v) for v in matrix["python-version"]}

if classifier_versions != matrix_versions:
    print("MISMATCH")
    print(f"  classifiers: {sorted(classifier_versions)}")
    print(f"  CI matrix:   {sorted(matrix_versions)}")
    sys.exit(1)

print(f"OK: {sorted(matrix_versions)}")
