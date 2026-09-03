from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
s = s.replace("if(e.target===back)close());", "if(e.target===back)close()});")

css = r'''<style id="gp-map-pro-css">
/* Global Pulse Update 2 — clean professional intelligence map */
.gp-map-tools{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 12px}.gp-map-tool{border:1px solid #29445f;background:#081522;color:#b9cbe0;border-radius:8px;padding:7px 10px;font:600 10px/1 system-ui;cursor:pointer}.gp-map-tool.active{border-color:#6b9bd0;background:#10243a;color:#eef6ff}.gp-map-legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px;padding:9px 10px;border:1px solid #1d3349;border-radius:9px;background:#07111b;color:#8196aa;font-size:10px}.gp-map-legend span{display:inline-flex;align-items:center;gap:5px}.gp-dot{width:8px;height:8px;border-radius:50%;display:inline-block}.gp-dot.conflict{background:#ef6262}.gp-dot.osint{background:#e0ad54}.gp-dot.diplomatic{background:#67a0df}.gp-dot.economic{background:#8d76c9}.gp-dot.humanitarian{background:#69b98b}.gp-map-status{font-size:10px;color:#70879c;margin-left:auto}.grid>.panel{align-self:start}
@media(max-width:720px){.gp-map-tools{overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px}.gp-map-tool{white-space:nowrap}.gp-map-status{width:100%;margin-left:0}}
</style>'''

# Replace the Update 2 CSS on every run so versions cannot stack.
s=re.sub(r'<style id="gp-map-pro-css">.*?</style>',css,s,count=1,flags=re.S)
if 'id="gp-map-pro-css"' not in s:
    s=s.replace('</head>',css+'\n</head>',1)

# Remove every older appended UI script. These were the source of duplicated
# handlers, duplicate map filters, and conflicting map behavior.
legacy_patterns=[
    r'<script>\s*/\* Global Pulse: capture-phase conflict click fix v2 \*/.*?</script>',
    r'<script>\s*/\* Global Pulse: capture-phase conflict click fix v3 \*/.*?</script>',
    r'<script>\s*/\* Global Pulse: capture-phase conflict click \+ intelligence brief/watchlist v4 \*/.*?</script>',
    r'<script>\s*/\* Global Pulse: intelligence brief \+ watchlist \+ reliable conflict focus \*/.*?</script>',
    r'<script id="gp-map-pro-js">.*?</script>'
]
for pattern in legacy_patterns:
    s=re.sub(pattern,'',s,count=1,flags=re.S)

# Remove any duplicate command-center brief left by a previous injected script.
s=re.sub(r'<section[^>]*id="gpBrief"[^>]*>.*?</section>','',s,count=1,flags=re.S)

js = r'''<script id="gp-map-pro-js">
/* Update 2: single clean map controller */
(function(){
  const typeOf=m=>{const t=String(m?.eventType||m?.type||'conflict').toLowerCase();if(/osint|social|source map/.test(t))return'osint';if(/diplomat|talk|ceasefire|negoti/.test(t))return'diplomatic';if(/economic|market|sanction|trade|oil/.test(t))return'economic';if(/humanitarian|aid|displacement|refugee/.test(t))return'humanitarian';return'conflict'};
  const data=()=>Array.isArray(window.DATA?.markers)?window.DATA.markers:[];

  function removeLegacyControls(){
    document.querySelectorAll('.map-tools,.map-filters,#mapFilters,#mapFilterBar,[data-map-controls="legacy"]').forEach(el=>el.remove());
    [...document.querySelectorAll('#gpMapTools')].slice(1).forEach(el=>el.remove());
    [...document.querySelectorAll('#gpMapLegend')].slice(1).forEach(el=>el.remove());
  }

  function ensureTools(){
    const mapEl=document.getElementById('map');if(!mapEl)return;
    removeLegacyControls();
    let tools=document.getElementById('gpMapTools');
    if(!tools){
      tools=document.createElement('div');tools.id='gpMapTools';tools.className='gp-map-tools';
      tools.innerHTML='<button class="gp-map-tool active" data-mapfilter="all">ALL</button><button class="gp-map-tool" data-mapfilter="conflict">CONFLICT</button><button class="gp-map-tool" data-mapfilter="osint">OSINT</button><button class="gp-map-tool" data-mapfilter="diplomatic">DIPLOMATIC</button><button class="gp-map-tool" data-mapfilter="economic">ECONOMIC</button><button class="gp-map-tool" data-mapfilter="humanitarian">HUMANITARIAN</button><span class="gp-map-status" id="gpMapStatus"></span>';
      mapEl.parentElement.insertBefore(tools,mapEl);
    }
    let legend=document.getElementById('gpMapLegend');
    if(!legend){
      legend=document.createElement('div');legend.id='gpMapLegend';legend.className='gp-map-legend';
      legend.innerHTML='<span><i class="gp-dot conflict"></i> Conflict</span><span><i class="gp-dot osint"></i> OSINT / Report</span><span><i class="gp-dot diplomatic"></i> Diplomatic</span><span><i class="gp-dot economic"></i> Economic</span><span><i class="gp-dot humanitarian"></i> Humanitarian</span>';
      tools.insertAdjacentElement('afterend',legend);
    }
    tools.querySelectorAll('[data-mapfilter]').forEach(b=>b.onclick=()=>{window.gpMapFilter=b.dataset.mapfilter;tools.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));renderFiltered()});
  }

  function renderFiltered(){
    if(typeof window.renderMap!=='function')return;
    const all=data(),f=window.gpMapFilter||'all',old=window.DATA?.markers;
    if(window.DATA&&f!=='all')window.DATA.markers=all.filter(m=>typeOf(m)===f);
    try{window.renderMap()}finally{if(window.DATA&&old)window.DATA.markers=old}
    setTimeout(updateStatus,30);
  }

  function updateStatus(){
    const el=document.getElementById('gpMapStatus');if(!el)return;
    const f=window.gpMapFilter||'all',n=data().filter(m=>f==='all'||typeOf(m)===f).length;
    el.textContent=n+' map signal'+(n===1?'':'s');
  }

  function boot(){
    ensureTools();
    updateStatus();
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,250));
  else setTimeout(boot,250);
})();
</script>'''
s=s.replace('</body>',js+'\n</body>',1)

p.write_text(s,encoding='utf-8')
print('Single clean map controller applied')
