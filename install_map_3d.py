#!/usr/bin/env python3
"""Install the optional no-key 3D globe without replacing the existing Leaflet map."""
from pathlib import Path

INDEX = Path(__file__).resolve().parent / "index.html"
START = "<!-- GP-MAP-3D-START -->"
END = "<!-- GP-MAP-3D-END -->"
BLOCK = r'''<!-- GP-MAP-3D-START -->
<style id="gp-map-3d-css">
.gp-3d-wrap{display:grid;gap:8px;margin:0 0 10px}.gp-3d-toolbar{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.gp-3d-toolbar button{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px;letter-spacing:.04em;min-height:34px;padding:7px 10px;border:1px solid rgba(70,255,160,.22);background:#03100c;color:#8bb8a4;border-radius:7px}.gp-3d-toolbar button:hover,.gp-3d-toolbar button.active{border-color:#49ff9a;color:#49ff9a;background:rgba(73,255,154,.08);box-shadow:0 0 14px rgba(73,255,154,.08)}#gp-3d-count{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:9px;letter-spacing:.04em;color:#6f9b88;margin-left:auto}.gp-3d-stage{position:relative;height:540px;border:1px solid rgba(73,255,154,.2);border-radius:12px;overflow:hidden;background:#020706;display:none;touch-action:none;box-shadow:inset 0 0 70px rgba(0,0,0,.55),0 0 24px rgba(73,255,154,.04)}.gp-3d-stage.active{display:block}.gp-3d-stage:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(rgba(73,255,154,.025) 50%,transparent 50%);background-size:100% 4px;mix-blend-mode:screen;opacity:.55}.gp-3d-stage canvas{width:100%;height:100%;display:block;cursor:grab}.gp-3d-stage canvas:active{cursor:grabbing}.gp-3d-hud{position:absolute;top:10px;left:12px;right:12px;display:flex;justify-content:space-between;font:9px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em;color:rgba(73,255,154,.65);pointer-events:none;text-shadow:0 0 8px rgba(73,255,154,.5)}.gp-3d-hint{position:absolute;left:10px;bottom:9px;padding:6px 8px;border:1px solid rgba(73,255,154,.15);border-radius:6px;background:rgba(2,10,7,.8);backdrop-filter:blur(7px);font:9px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.03em;color:#5e8a76;pointer-events:none}.gp-3d-detail{padding:10px;border:1px solid rgba(73,255,154,.2);border-radius:8px;background:#03100c;color:#709b86;font:10px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}.gp-3d-detail strong{display:block;color:#d5ffe7;font-size:12px;margin-bottom:4px}.gp-3d-detail a{display:inline-block;margin-top:5px;color:#49ff9a}.gp-3d-wrap+.gp-2d-hidden{display:none!important}@media(max-width:720px){.gp-3d-stage{height:390px}.gp-3d-toolbar{overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px}.gp-3d-toolbar button{white-space:nowrap}.gp-3d-count{min-width:max-content;margin-left:0}}
</style>
<script src="global_pulse_map_3d.js?v=2" defer></script>
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
print("Installed Matrix-style isolated no-key 3D globe UI")
