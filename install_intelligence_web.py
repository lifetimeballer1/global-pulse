#!/usr/bin/env python3
"""Validate the Intelligence Web integration without assuming how data loading is wired."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent; PAGE=ROOT/'intelligence-web.html'; JS=ROOT/'intelligence_web_v2.js'
if not PAGE.exists(): raise SystemExit('intelligence-web.html is missing')
if not JS.exists(): raise SystemExit('intelligence_web_v2.js is missing')
page=PAGE.read_text(encoding='utf-8'); js=JS.read_text(encoding='utf-8')
for marker in ('id="graph"','intelligence_web_v2.js'):
    if marker not in page: raise SystemExit(f'Intelligence Web page missing required marker: {marker}')
for marker in ('function close(','function show(','data/intelligence_graph.json','WHY THIS NODE IS CONNECTED','SOURCES FOR THIS NODE','OPEN ORIGINAL SOURCE'):
    if marker not in js: raise SystemExit(f'Intelligence Web renderer missing required marker: {marker}')
print('Verified Intelligence Web page and renderer; data loading may be static or dynamic')
