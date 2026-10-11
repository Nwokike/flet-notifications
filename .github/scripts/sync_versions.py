"""Sync the Flutter package version with the Python project version.

Usage (in CI, before building)::

    uv run python .github/scripts/sync_versions.py

Reads the version from ``pyproject.toml`` and stamps it into every
``src/flutter/*/pubspec.yaml``. Prevents the Python/Dart version drift
that bit flet-geolocator (0.25.2 Flutter vs 0.2.0 Python).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', pyproject, re.M)
    if not match:
        print("error: no version in pyproject.toml", file=sys.stderr)
        return 1
    version = match.group(1)

    changed: list[str] = []
    for pubspec in sorted(root.glob("src/flutter/*/pubspec.yaml")):
        text = pubspec.read_text(encoding="utf-8")
        new_text, count = re.subn(
            r'^version: .*$',
            f"version: {version}",
            text,
            count=1,
            flags=re.M,
        )
        if new_text != text:
            pubspec.write_text(new_text, encoding="utf-8")
            changed.append(str(pubspec.relative_to(root)))
    if changed:
        print(f"synced version {version} -> {', '.join(changed)}")
    else:
        print(f"versions already at {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
