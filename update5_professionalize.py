from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Remove previous Update 5 injection so reruns stay idempotent.
s=re.sub(r'\n<style id="gp-final-css">.*?</style>\n', '\n', s, flags=re.S)
s=re.sub(r'\n<script id="gp-final-js">.*?</script>\n', '\n', s, flags=re.S)
s=re.sub(r'\n<div class="gp-finalbar" id="gpFinalBar">.*?</div>\n', '\n', s, flags=re.S)

css='''
<style id="gp-final-css">
/* Global Pulse Update 5 — final command-center polish */
.gp-finalbar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 12px;margin:12px 0;border:1px solid var(--line);border-radius:11px;background:#08131e}.gp-finalbar .fresh{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--muted)}.gp-finalbar .dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 4px rgba(72,223,131,.1)}.gp-finalbar button{min-height:32px;padding:6px 10px}.gp-method{font-size:10px;color:var(--muted);line-height:1.55}.gp-method b{color:var(--text)}.leaflet-container{font:12px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.leaflet-control-attribution{font-size:8px}.panel{contain:layout paint}.story,.item,.ccard,.evidence-card{content-visibility:auto;contain-intrinsic-size:120px}.open,.map-source,button,.filter{touch-action:manipulation}@media(max-width:720px){.gp-finalbar{align-items:flex-start}.gp-finalbar button{flex-shrink:0}.gp-method{font-size:9px}}
</style>
'''
if '</head>' not in s: raise SystemExit('index.html missing </head>')
s=s.replace('</head>',css+'</head>',1)

bar='''
<div class="gp-finalbar" id="gpFinalBar"><div><div class="fresh"><span class="dot"></span><span id="gpFreshText">DATA PIPELINE ACTIVE</span></div><div class="gp-method"><b>Methodology:</b> public-source aggregation · recency-weighted theater signals · provenance shown separately from severity.</div></div><button class="filter" id="gpTopRefresh" type="button">Refresh view</button></div>
'''
if 'id="gpFinalBar"' not in s:
    if '</header>' not in s: raise SystemExit('index.html missing </header>')
    s=s.replace('</header>','</header>'+bar,1)

js='''
<script id="gp-final-js">
(function(){
  const byId=id=>document.getElementById(id);
  function setFresh(){
    const t=window.DATA&&window.DATA.updatedAt;
    const el=byId('gpFreshText');
    if(!el)return;
    if(!t){el.textContent='DATA STATUS · AWAITING REFRESH';return}
    const d=new Date(t), age=(Date.now()-d.getTime())/60000;
    el.textContent=age<60?`DATA FRESH · ${Math.max(0,Math.round(age))}m ago`:`DATA UPDATED · ${d.toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}`;
  }
  function wire(){
    const b=byId('gpTopRefresh');
    if(b)b.onclick=()=>location.reload();
    setFresh();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire);else wire();
})();
</script>
'''
if '</body>' not in s: raise SystemExit('index.html missing </body>')
s=s.replace('</body>',js+'</body>',1)

s=s.replace('.grid{display:grid;', '.grid{align-items:start;display:grid;',1)
s=s.replace('.panel{background:', '.panel{align-self:start;background:',1)

p.write_text(s,encoding='utf-8')
print('Update 5 applied')
