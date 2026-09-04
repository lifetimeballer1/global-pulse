#!/usr/bin/env python3
"""Install the optional no-key 3D globe without replacing the existing Leaflet map."""
from pathlib import Path

INDEX = Path(__file__).resolve().parent / "index.html"
START = "<!-- GP-MAP-3D-START -->"
END = "<!-- GP-MAP-3D-END -->"
BLOCK = r'''<!-- GP-MAP-3D-START -->
<style id="gp-map-3d-css">
.gp-3d-wrap{display:grid;gap:8px;margin:0 0 10px}.gp-3d-toolbar{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.gp-3d-toolbar button{font-size:10px;min-height:34px;padding:7px 9px}.gp-3d-toolbar button.active{border-color:var(--cyan);color:var(--cyan);background:rgba(63,197,255,.1)}#gp-3d-count{font-size:10px;color:var(--muted);margin-left:auto}.gp-3d-stage{position:relative;height:540px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#03080d;display:none;touch-action:none;box-shadow:inset 0 0 80px rgba(0,0,0,.25)}.gp-3d-stage.active{display:block}.gp-3d-stage canvas{width:100%;height:100%;display:block;cursor:grab}.gp-3d-stage canvas:active{cursor:grabbing}.gp-3d-hint{position:absolute;left:10px;bottom:9px;padding:6px 8px;border:1px solid rgba(98,160,255,.18);border-radius:7px;background:rgba(5,10,16,.72);backdrop-filter:blur(7px);font-size:9px;color:var(--muted);pointer-events:none}.gp-3d-detail{padding:9px 10px;border:1px solid var(--line);border-radius:9px;background:#08131e;color:var(--muted);font-size:10px;line-height:1.45}.gp-3d-detail strong{display:block;color:var(--text);font-size:12px;margin-bottom:3px}.gp-3d-detail a{display:inline-block;margin-top:4px}.gp-3d-wrap+.gp-2d-hidden{display:none!important}@media(max-width:720px){.gp-3d-stage{height:390px}.gp-3d-toolbar{overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px}.gp-3d-toolbar button{white-space:nowrap}.gp-3d-count{min-width:max-content;margin-left:0}}
</style>
<script src="global_pulse_map_3d.js?v=1" defer></script>
<!-- GP-MAP-3D-END -->'''

html = INDEX.read_text(encoding="utf-8")
if START in html and END in html:
    a, rest = html.split(START, 1)
    _, b = rest.split(END, 1)
    html = a + BLOCK + b
else:
    marker = "</body>"
    if marker not in html:
        raise SystemExit("index.html has no </body>; refusing to install 3D map")
    html = html.replace(marker, BLOCK + "\n" + marker, 1)
INDEX.write_text(html, encoding="utf-8")
print("Installed isolated no-key 3D globe UI")
