from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Remove previous Update 5 injection so reruns stay idempotent.
s=re.sub(r'\n<style id="gp-final-css">.*?</style>\n', '\n', s, flags=re.S)
s=re.sub(r'\n<script id="gp-final-js">.*?</script>\n', '\n', s, flags=re.S)

css='''\n<style id="gp-final-css">\n/* Global Pulse Update 5 — final command-center polish */\n.gp-finalbar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 12px;margin:0 0 12px;border:1px solid var(--line);border-radius:11px;background:#08131e}.gp-finalbar .fresh{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--muted)}.gp-finalbar .dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 4px rgba(72,223,131,.1)}.gp-finalbar button{min-height:32px;padding:6px 10px}.gp-method{font-size:10px;color:var(--muted);line-height:1.55}.gp-method b{color:var(--text)}.gp-error{display:none;margin:10px 0;padding:10px;border:1px solid rgba(255,102,120,.35);border-radius:9px;background:rgba(255,102,120,.08);color:#ff9aa7;font-size:11px}.gp-skeleton{opacity:.65}.leaflet-container{font:12px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.leaflet-control-attribution{font-size:8px}.panel{contain:layout paint}.story,.item,.ccard,.evidence-card{content-visibility:auto;contain-intrinsic-size:120px}.open,.map-source,button,.filter{touch-action:manipulation}@media(max-width:720px){.gp-finalbar{align-items:flex-start}.gp-finalbar button{flex-shrink:0}.gp-method{font-size:9px}}\n</style>\n'''
s=s.replace('</head>',css+'</head>',1)

# Put a compact reliability/methodology bar directly below the header.
bar='''\n<div class="gp-finalbar" id="gpFinalBar"><div><div class="fresh"><span class="dot"></span><span id="gpFreshText">DATA PIPELINE ACTIVE</span></div><div class="gp-method"><b>Methodology:</b> public-source aggregation · recency-weighted theater signals · provenance shown separately from severity.</div></div><button class="filter" id="gpTopRefresh" type="button">Refresh view</button></div>\n'''
s=s.replace('<div class="wrap" id="top">','<div class="wrap" id="top">'+bar,1)

js='''\n<script id="gp-final-js">\n(function(){\n  const q=s=>document.querySelector(s);\n  const byId=id=>document.getElementById(id);\n  function setFresh(){\n    const t=window.DATA&&window.DATA.updatedAt;\n    const el=byId('gpFreshText');\n    if(!el)return;\n    if(!t){el.textContent='DATA STATUS · AWAITING REFRESH';return}\n    const d=new Date(t), age=(Date.now()-d.getTime())/60000;\n    el.textContent=age<60?`DATA FRESH · ${Math.max(0,Math.round(age))}m ago`:`DATA UPDATED · ${d.toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}`;\n  }\n  function wire(){\n    const b=byId('gpTopRefresh');\n    if(b)b.onclick=()=>{location.reload()};\n    setFresh();\n    window.addEventListener('error',()=>{const e=byId('gpError');if(e)e.style.display='block'});\n  }\n  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire);else wire();\n})();\n</script>\n'''
s=s.replace('</body>',js+'</body>',1)

# Remove accidental empty grid space caused by uneven panel content.
s=s.replace('.panel{background:', '.panel{align-self:start;background:',1)

p.write_text(s,encoding='utf-8')
print('Update 5 applied')
