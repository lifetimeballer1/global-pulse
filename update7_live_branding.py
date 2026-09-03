#!/usr/bin/env python3
"""Global Pulse Update 7: no-key near-live ingestion and J.S. branding."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "update_snapshot.py"
INDEX = ROOT / "index.html"

GDELT_FEEDS = '''    ("GDELT Live — Global", "https://api.gdeltproject.org/api/v2/doc/doc?query=(war%20OR%20conflict%20OR%20military%20OR%20sanctions%20OR%20election%20OR%20crisis)&mode=ArtList&format=rss&maxrecords=250&timespan=15m", "live"),
    ("GDELT Live — Africa", "https://api.gdeltproject.org/api/v2/doc/doc?query=(africa%20OR%20sudan%20OR%20congo%20OR%20sahel%20OR%20nigeria%20OR%20somalia)&mode=ArtList&format=rss&maxrecords=150&timespan=15m", "africa"),
    ("GDELT Live — Americas", "https://api.gdeltproject.org/api/v2/doc/doc?query=(mexico%20OR%20colombia%20OR%20venezuela%20OR%20brazil%20OR%20haiti%20OR%20ecuador%20OR%20peru)&mode=ArtList&format=rss&maxrecords=150&timespan=15m", "americas"),
    ("GDELT Live — Middle East", "https://api.gdeltproject.org/api/v2/doc/doc?query=(gaza%20OR%20iran%20OR%20israel%20OR%20yemen%20OR%20syria%20OR%20iraq)&mode=ArtList&format=rss&maxrecords=150&timespan=15m", "middle-east"),
'''

CSS = '''<style id="gp-brand-live-css">.gp-brand-wrap{display:flex;align-items:baseline;gap:8px;min-width:0}.gp-brand-credit{font-size:9px;font-weight:650;letter-spacing:.08em;color:#70879c;white-space:nowrap}.gp-live-chip{display:inline-flex;align-items:center;gap:6px;margin-left:8px;padding:5px 8px;border:1px solid rgba(72,223,131,.22);border-radius:999px;background:rgba(72,223,131,.06);font-size:9px;color:#91a4b8}.gp-live-chip i{width:6px;height:6px;border-radius:50%;background:#48df83;box-shadow:0 0 0 3px rgba(72,223,131,.08)}.gp-footer-credit{margin:18px 0 8px;text-align:center;color:#566b80;font-size:10px;letter-spacing:.08em}.gp-footer-credit b{color:#91a4b8}@media(max-width:520px){.gp-brand-credit{font-size:8px}.gp-live-chip{display:none}}</style>'''


def patch_snapshot():
    s = SNAP.read_text()
    anchor = 'FEEDS = ['
    if '"GDELT Live — Global"' not in s:
        pos = s.index(anchor) + len(anchor)
        s = s[:pos] + '\n' + GDELT_FEEDS + s[pos:]
    s = re.sub(r'unique\[:120\]', 'unique[:300]', s)
    s = s.replace('GlobalPulse/4.1', 'GlobalPulse/7.0')
    SNAP.write_text(s)


def patch_index():
    s = INDEX.read_text()
    s = re.sub(r'<style id="gp-brand-live-css">.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<div class="gp-footer-credit">.*?</div>', '', s, flags=re.S)
    s = s.replace('<title>Global Pulse — Global Conflict & Intelligence Monitor</title>', '<title>Global Pulse — Global Conflict & Intelligence Monitor · Made by J.S.</title>')
    s = re.sub(r'<div class="brand">.*?</div>', '<div class="gp-brand-wrap"><div class="brand"><b>GLOBAL</b> PULSE</div><span class="gp-brand-credit">Made by J.S.</span></div>', s, count=1, flags=re.S)
    s = s.replace('</header>', '<div class="gp-live-chip"><i></i>NEAR-LIVE OPEN DATA</div></header>', 1)
    s = s.replace('</main>', '<div class="gp-footer-credit">GLOBAL PULSE <b>· Made by J.S.</b> · Public-source intelligence monitor</div></main>', 1)
    s = s.replace('</head>', CSS + '</head>', 1)
    INDEX.write_text(s)


if __name__ == '__main__':
    patch_snapshot()
    patch_index()
    print('Update 7 applied: GDELT near-live feeds, 300-story window, and Made by J.S. branding.')
