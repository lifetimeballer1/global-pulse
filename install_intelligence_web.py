#!/usr/bin/env python3
"""Keep the canonical standalone Intelligence Web entry point intact.

The page and renderer are versioned files in the repository. Earlier versions of
this installer rewrote the HTML on every refresh, which could undo a UI fix.
The production workflow now validates the committed page instead of replacing it.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "intelligence-web.html"
JS = ROOT / "intelligence_web_v2.js"

if not PAGE.exists():
    raise SystemExit("intelligence-web.html is missing")
if not JS.exists():
    raise SystemExit("intelligence_web_v2.js is missing")

page = PAGE.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")
required_page = ("ForceGraph3D", "3d-force-graph@1.80.0", "data/snapshot.json", "unpkg.com/3d-force-graph@1.80.0")
required_js = ("enableNodeDrag(true)", "HOW THIS NODE CONNECTS", "OPEN SOURCE")
for marker in required_page:
    if marker not in page:
        raise SystemExit(f"Intelligence Web page missing required marker: {marker}")
for marker in required_js:
    if marker not in js:
        raise SystemExit(f"Intelligence Web renderer missing required marker: {marker}")

print("Verified canonical Intelligence Web renderer; no file rewrite performed")
