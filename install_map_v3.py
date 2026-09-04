#!/usr/bin/env python3
"""Keep the canonical 2D map installer isolated and clean generated HTML.

The 3D experiment is intentionally disabled for now. This script does not
replace or rebuild the canonical Leaflet map; it removes stale 3D blocks and
runs the idempotent generated-index cleanup as the final browser assembly step.
"""
from pathlib import Path

INDEX = Path(__file__).resolve().parent / "index.html"
START = "<!-- GP-MAP-3D-START -->"
END = "<!-- GP-MAP-3D-END -->"

html = INDEX.read_text(encoding="utf-8")
removed = 0
while START in html:
    a, rest = html.split(START, 1)
    if END in rest:
        _, b = rest.split(END, 1)
        html = a + b
        removed += 1
    else:
        html = a
        removed += 1
INDEX.write_text(html, encoding="utf-8")

# Keep the generated entry point idempotent after all UI installers have run.
from clean_index import main as clean_index
clean_index()

print(f"Canonical 2D map preserved; removed {removed} deprecated 3D globe block(s).")
