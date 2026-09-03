#!/usr/bin/env python3
"""Install the resilient FastAPI/live-snapshot reporting UI into Global Pulse."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"

CSS = r'''<style id="gp-live-reporting-css">
.gp-reporting-feed{display:grid;gap:10px}.gp-reporting-card{position:relative;padding:13px;background:var(--panel2);border:1px solid var(--line);border-radius:12px;transition:border-color .16s ease,transform .16s ease,background .16s ease}.gp-reporting-card:hover{border-color:#315274;background:#09131e;transform:translateY(-1px)}.gp-reporting-source{display:inline-flex;align-items:center;gap:5px;margin-bottom:7px;padding:4px 7px;border:1px solid rgba(98,160,255,.3);border-radius:6px;background:rgba(98,160,255,.08);color:var(--blue);font-size:9px;font-weight:850;letter-spacing:.07em;text-transform:uppercase}.gp-reporting-title{display:block;margin:2px 0 6px;color:var(--text);font-size:15px;font-weight:850;line-height:1.35}.gp-reporting-title:hover{color:var(--blue)}.gp-reporting-time{display:block;margin-bottom:8px;color:var(--muted);font-size:10px}.gp-reporting-summary{margin:0;color:var(--muted);font-size:11px;line-height:1.55}.gp-reporting-source-name{margin-top:8px;color:var(--muted);font-size:9px}.gp-reporting-action{display:inline-block;margin-top:10px;padding:7px 10px;border:1px solid rgba(98,160,255,.35);border-radius:7px;background:rgba(98,160,255,.08);color:var(--blue);font-size:10px;font-weight:800}.gp-reporting-action:hover{background:rgba(98,160,255,.15)}.gp-reporting-alert{padding:13px;border:1px solid rgba(255,102,120,.35);border-left:3px solid var(--red);border-radius:11px;background:rgba(255,102,120,.07)}.gp-reporting-alert strong{display:block;margin-bottom:3px;color:var(--red);font-size:11px;letter-spacing:.05em;text-transform:uppercase}.gp-reporting-alert span{color:var(--muted);font-size:10px}.gp-reporting-empty{padding:18px;border:1px dashed var(--line);border-radius:10px;color:var(--muted);text-align:center;font-size:11px}.gp-reporting-count{color:var(--muted);font-size:10px;white-space:nowrap}.gp-reporting-fallback .gp-reporting-card{border-color:rgba(255,200,87,.22)}@media(max-width:720px){.gp-reporting-card{padding:12px}.gp-reporting-title{font-size:14px}.gp-reporting-summary{font-size:11px}}
</style>'''

REPORTING_HTML = r'''<section id="reporting" class="panel wide" aria-labelledby="latest-reporting-title">
  <div class="section-head">
    <div>
      <h2 id="latest-reporting-title">Latest Reporting</h2>
      <div class="muted">Near-live reporting aggregated from the Global Pulse news pipeline.</div>
    </div>
    <span id="pulse-reporting-count" class="gp-reporting-count" aria-live="polite">—</span>
  </div>
  <div id="pulse-reporting-feed" class="gp-reporting-feed" aria-live="polite" aria-busy="false"></div>
</section>'''


def patch_index():
    html = INDEX.read_text(encoding="utf-8")

    # Remove older copies of this integration if the workflow is rerun.
    html = re.sub(r'<style id="gp-live-reporting-css">.*?</style>', '', html, flags=re.S)
    html = re.sub(r'<script id="gp-live-reporting-config">.*?</script>', '', html, flags=re.S)
    html = re.sub(r'<script src="global_pulse_reporting\.js" defer></script>', '', html)

    # Replace an existing Latest Reporting panel if one is present. The generated
    # page has changed over time, so use several conservative patterns.
    pattern = r'<section[^>]*id=["\']reporting["\'][\s\S]*?</section>'
    html, count = re.subn(pattern, REPORTING_HTML, html, count=1, flags=re.I)
    if count == 0:
        # If the old page does not expose an id, replace the first heading whose
        # visible text is Latest Reporting through its containing section.
        pattern2 = r'<section[^>]*>[\s\S]*?<h2[^>]*>\s*Latest Reporting\s*</h2>[\s\S]*?</section>'
        html, count = re.subn(pattern2, REPORTING_HTML, html, count=1, flags=re.I)
    if count == 0:
        # Last-resort placement: append before the existing closing main/wrap.
        marker = '</main>' if '</main>' in html else '</div>\n</body>'
        html = html.replace(marker, REPORTING_HTML + '\n' + marker, 1)

    config = '<script id="gp-live-reporting-config">window.GLOBAL_PULSE_API="http://127.0.0.1:8000/";</script>'
    html = html.replace('</head>', CSS + '\n' + config + '\n</head>', 1)
    html = html.replace('</body>', '<script src="global_pulse_reporting.js" defer></script>\n</body>', 1)

    INDEX.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    patch_index()
    print("Update 9 applied: resilient live FastAPI reporting integration installed.")
