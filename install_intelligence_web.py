#!/usr/bin/env python3
"""Install/verify the standalone 3D Intelligence Web without overwriting its UI.

The HTML page is the source of truth. This prevents scheduled refreshes from
reverting fixes to the interactive 3D graph.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
PAGE = ROOT / "intelligence-web.html"

required = ["3d-force-graph@1.80.0", "enableNodeDrag(true)", "data/snapshot.json", "gpLoad3D"]
if not PAGE.exists():
    raise SystemExit("intelligence-web.html is missing")
page = PAGE.read_text(encoding="utf-8")
missing = [x for x in required if x not in page]
if missing:
    raise SystemExit("3D Intelligence Web missing required features: " + ", ".join(missing))

BUTTON = '<!-- GP-INTELLIGENCE-WEB-START --><div class="gp-intel-web-entry" style="display:flex;justify-content:center;margin:4px 0"><a href="intelligence-web.html" style="display:inline-block;padding:9px 14px;border:1px solid #39ff88;border-radius:9px;background:rgba(57,255,136,.08);color:#39ff88;font-weight:900;letter-spacing:.08em;font-size:11px">◈ INTELLIGENCE WEB — 3D</a></div><!-- GP-INTELLIGENCE-WEB-END -->'

html = INDEX.read_text(encoding="utf-8")
start = "<!-- GP-INTELLIGENCE-WEB-START -->"
end = "<!-- GP-INTELLIGENCE-WEB-END -->"
if start in html and end in html:
    a = html.index(start)
    b = html.index(end, a) + len(end)
    html = html[:a] + BUTTON + html[b:]
elif "</body>" in html:
    html = html.replace("</body>", BUTTON + "</body>", 1)
else:
    raise SystemExit("index.html has no </body>")
INDEX.write_text(html, encoding="utf-8")
print("Verified robust 3D Intelligence Web; page UI was not overwritten.")
