#!/usr/bin/env python3
"""Validate the canonical standalone Intelligence Web entry point without rewriting it."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent; PAGE=ROOT/'intelligence-web.html'; JS=ROOT/'intelligence_web_v2.js'
if not PAGE.exists(): raise SystemExit('intelligence-web.html is missing')
if not JS.exists(): raise SystemExit('intelligence_web_v2.js is missing')
page=PAGE.read_text(encoding='utf-8'); js=JS.read_text(encoding='utf-8')
required_page=('ForceGraph3D','3d-force-graph@1.80.0','data/snapshot.json','unpkg.com/3d-force-graph@1.80.0','intelligence_web_v2.js?v=')
required_js=('enableNodeDrag(true)','WHY THIS NODE IS CONNECTED','SOURCES FOR THIS NODE','OPEN ORIGINAL SOURCE','makeEmergencyData')
for marker in required_page:
    if marker not in page: raise SystemExit(f'Intelligence Web page missing required marker: {marker}')
for marker in required_js:
    if marker not in js: raise SystemExit(f'Intelligence Web renderer missing required marker: {marker}')
print('Verified canonical Intelligence Web renderer; page is not rewritten by refresh jobs')
