#!/usr/bin/env python3
"""Repository-level integrity checks for Global Pulse.

This complements syntax checks by catching stale browser assets, duplicate HTML
IDs/scripts, broken local references, and malformed JSON artifacts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"


def main() -> None:
    html = INDEX.read_text(encoding="utf-8")

    # Every locally referenced script/style/image/manifest must exist.
    refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html, flags=re.I)
    missing: list[str] = []
    for ref in refs:
        if ref.startswith(("http://", "https://", "//", "data:", "#")):
            continue
        local = ref.split("?", 1)[0].split("#", 1)[0]
        if not local:
            continue
        if not (ROOT / local).exists():
            missing.append(local)
    if missing:
        raise SystemExit("Missing local browser assets: " + ", ".join(sorted(set(missing))))

    ids = re.findall(r'\bid=["\']([^"\']+)["\']', html, flags=re.I)
    duplicates = sorted({x for x in ids if ids.count(x) > 1})
    if duplicates:
        raise SystemExit("Duplicate HTML ids: " + ", ".join(duplicates))

    scripts = re.findall(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\']', html, flags=re.I)
    normalized = [x.split("?", 1)[0] for x in scripts]
    duplicate_scripts = sorted({x for x in normalized if normalized.count(x) > 1})
    if duplicate_scripts:
        raise SystemExit("Duplicate script inclusions: " + ", ".join(duplicate_scripts))

    json_paths = [
        Path("site.webmanifest"),
        *sorted((ROOT / "data").glob("*.json")),
    ]
    for path in json_paths:
        json.loads(path.read_text(encoding="utf-8"))

    # These are intentionally retired renderers. Keeping them around invites
    # future installers to accidentally revive an older implementation.
    retired = [
        "global_pulse_graph_stable.js",
        "global_pulse_graph_v3.js",
        "global_pulse_graph_pro.js",
        "intelligence_web_v1.js",
    ]
    leftovers = [x for x in retired if (ROOT / x).exists()]
    if leftovers:
        raise SystemExit("Retired renderer files remain: " + ", ".join(leftovers))

    print("REPOSITORY INTEGRITY PASSED")
    print(f"Local browser references checked: {len([r for r in refs if not r.startswith(('http://','https://','//','data:','#'))])}")
    print(f"JSON artifacts checked: {len(json_paths)}")
    print("No duplicate HTML ids or browser script inclusions detected.")


if __name__ == "__main__":
    main()
