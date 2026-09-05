#!/usr/bin/env python3
"""Put the Intelligence Web directly on the main Global Pulse page and add a responsive top Commander Center jump bar."""
from pathlib import Path
import re

INDEX = Path('index.html')
if not INDEX.exists():
    raise SystemExit('index.html is missing')

s = INDEX.read_text(encoding='utf-8')

STYLE_ID = 'gp-commander-intel-css'
NAV_ID = 'commanderCenter'
SECTION_ID = 'intelligenceWebSection'

css = '''<style id="gp-commander-intel-css">
#commanderCenter{position:sticky;top:58px;z-index:45;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow:hidden;background:rgba(8,16,25,.96);backdrop-filter:blur(14px);border:1px solid var(--line);border-radius:14px;padding:10px 11px;box-shadow:0 10px 30px rgba(0,0,0,.22)}
#commanderCenter .cc-title{display:flex;align-items:center;justify-content:space-between;gap:10px;min-width:0;margin-bottom:8px}
#commanderCenter .cc-title strong{font-size:11px;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap}
#commanderCenter .cc-title span{font-size:9px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#commanderCenter .cc-nav{display:flex;gap:7px;max-width:100%;min-width:0;overflow-x:auto;overflow-y:hidden;padding:1px 1px 4px;scrollbar-width:thin;-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain}
#commanderCenter .cc-nav a{flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;min-height:34px;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#09121c;color:var(--text);font-size:10px;font-weight:800;white-space:nowrap}
#commanderCenter .cc-nav a:hover,#commanderCenter .cc-nav a:focus{border-color:var(--blue);color:var(--blue);outline:none}
#intelligenceWebSection{scroll-margin-top:112px;min-width:0;max-width:100%;overflow:hidden}
.gp-intel-frame{display:block;width:100%;max-width:100%;min-width:0;height:900px;border:1px solid var(--line);border-radius:12px;background:#03070b;box-sizing:border-box}
.gp-intel-note{font-size:10px;color:var(--muted);margin-top:7px}
@media(max-width:720px){
  body{overflow-x:hidden}
  #commanderCenter{top:51px;width:100%;max-width:100%;padding:8px;border-radius:12px}
  #commanderCenter .cc-title{gap:6px;margin-bottom:7px}
  #commanderCenter .cc-title strong{font-size:10px;letter-spacing:.11em}
  #commanderCenter .cc-title span{display:none}
  #commanderCenter .cc-nav{gap:6px;padding-bottom:3px}
  #commanderCenter .cc-nav a{min-height:36px;padding:8px 11px;font-size:10px}
  .gp-intel-frame{height:820px;border-radius:10px}
}
</style>'''

# Remove/rebuild our own injected pieces so reruns are safe.
s = re.sub(r'\n<style id="'+re.escape(STYLE_ID)+r'">.*?</style>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<section id="'+re.escape(SECTION_ID)+r'"[^>]*>.*?</section>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<div id="'+re.escape(NAV_ID)+r'"[^>]*>.*?</div>\n?', '\n', s, flags=re.S)

# The canonical live reporting module is the single source of truth.
# Remove the older static news section so the page cannot show two
# "Latest Reporting" panels. This is intentionally idempotent because
# refresh runs this installer repeatedly.
s = re.sub(r'\n<section id=["\']newsSection["\'][^>]*>.*?</section>\n?', '\n', s, count=1, flags=re.S | re.I)

if '</head>' not in s or '<main id="main"' not in s:
    raise SystemExit('index.html does not have the expected main document structure')

s = s.replace('</head>', css + '\n</head>', 1)

nav = '''<div id="commanderCenter" aria-label="Commander Center">
  <div class="cc-title"><strong>COMMANDER CENTER</strong><span>Jump to any intelligence layer</span></div>
  <nav class="cc-nav">
    <a href="#top">Overview</a>
    <a href="#mapSection">War Map</a>
    <a href="#intelligenceWebSection">Intelligence Web</a>
    <a href="#conflictSection">Conflicts</a>
    <a href="#reporting">Latest Reporting</a>
    <a href="#analysisCenter">Analysis</a>
    <a href="#evidenceCenter">Evidence</a>
  </nav>
</div>'''
s = s.replace('<main id="main" class="wrap">', '<main id="main" class="wrap">\n' + nav, 1)

section = '''<section id="intelligenceWebSection" class="panel wide" aria-labelledby="intelligence-web-title">
  <div class="section-head"><div><h2 id="intelligence-web-title">Intelligence Web</h2><div class="muted">Evidence-backed relationships between actors, conflicts, political signals, economic pressure and strategic interests.</div></div></div>
  <iframe class="gp-intel-frame" src="intelligence-web.html?v=1" title="Global Pulse Intelligence Web" loading="eager"></iframe>
  <div class="gp-intel-note">The Intelligence Web is embedded directly into the main page. Open a node to inspect its connection basis and source evidence.</div>
</section>'''

anchor = '<section id="mapSection"'
pos = s.find(anchor)
if pos < 0:
    raise SystemExit('Global Situation Map section not found')
s = s[:pos] + section + '\n' + s[pos:]

INDEX.write_text(s, encoding='utf-8')
print('PASS: Commander Center installed; duplicate static Latest Reporting removed')