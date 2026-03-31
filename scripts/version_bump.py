#!/usr/bin/env -S uv run
"""
Bumps the version in pyproject.toml. Usage: version_bump.py patch|minor|major
"""

import sys
import tomllib
from pathlib import Path

part = sys.argv[1] if len(sys.argv) == 2 else None
path = Path(__file__).parent.parent / "pyproject.toml"

with open(path, "rb") as f:
    data = tomllib.load(f)

old = data["project"]["version"]
major, minor, patch = (int(x) for x in old.split("."))

match part:
    case "major":
        major, minor, patch = major + 1, 0, 0
    case "minor":
        major, minor, patch = major, minor + 1, 0
    case "patch":
        major, minor, patch = major, minor, patch + 1
    case _:
        print("Usage: version_bump.py patch|minor|major", file=sys.stderr)
        sys.exit(1)

new = f"{major}.{minor}.{patch}"
path.write_text(path.read_text().replace(f'version = "{old}"', f'version = "{new}"', 1))
print(f"Bumped {old} -> {new}")
