from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Repair any accidental malformed close-handler left by an earlier UI patch.
s = s.replace("if(e.target===back)close());", "if(e.target===back)close()});")

css = r'''
<style id="gp-map-pro-css">
/* Global Pulse Update 2 — professional intelligence map */
.gp-map-tools{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 12px}.gp-map-tool{border:1px solid #29445f;background:#081522;color:#b9cbe0;border-radius:8px;padding:7px 10px;font:600 10px/1 system-ui;cursor:pointer}.gp-map-tool.active{border-color:#6b9bd0;background:#10243a;color:#eef6ff}.gp-map-legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px;padding:9px 10px;border:1px solid #1d3349;border-radius:9px;background:#07111b;color:#8196aa;font-size:10px}.gp-map-legend span{display:inline-flex;align-items:center;gap:5px}.gp-dot{width:8px;height:8px;border-radius:50%;display:inline-block}.gp-dot.conflict{background:#ef6262}.gp-dot.osint{background:#e0ad54}.gp-dot.diplomatic{background:#67a0df}.gp-dot.economic{background:#8d76c9}.gp-dot.humanitarian{background:#69b98b}.gp-map-status{font-size:10px;color:#70879c;margin-left:auto}.gp-event-popup{min-width:210px}.gp-event-popup h4{margin:0 0 5px;font-size:13px}.gp-event-popup p{margin:5px 0;color:#6d8092;font-size:10px;line-height:1.45}.gp-event-type{display:inline-block;margin-bottom:6px;padding:3px 6px;border:1px solid #36506a;border-radius:5px;color:#8fb5de;font-size:9px;text-transform:uppercase;letter-spacing:.06em}.gp-event-source{display:inline-block;margin-top:6px;color:#72a7e5;font-size:10px}.gp-cluster{background:#0b1724;border:2px solid #e0ad54;color:#f4d58e;border-radius:50%;display:flex;align-items:center;justify-content:center;font:700 11px system-ui;box-shadow:0 0 0 3px rgba(224,173,84,.12)}
/* Prevent CSS grid rows from stretching short panels and creating dead space. */
.grid>.panel{align-self:start}
/* The command-center brief is disabled here until it has a dedicated layout slot. */
#gpBrief{display:none!important}
@media(max-width:720px){.gp-map-tools{overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px}.gp-map-tool{white-space:nowrap}.gp-map-status{width:100%;margin-left:0}}
</style>
'''
if 'gp-map-pro-css' not in s:
    s=s.replace('</head>',css+'\n</head>',1)

js = r'''
<script id="gp-map-pro-js">
/* Update 2: professional conflict / OSINT map layer */
(function(){
  const typeOf=m=>{const t=String(m?.eventType||m?.type||'conflict').toLowerCase();if(/osint|social|source map/.test(t))return'osint';if(/diplomat|talk|ceasefire|negoti/.test(t))return'diplomatic';if(/economic|market|sanction|trade|oil/.test(t))return'economic';if(/humanitarian|aid|displacement|refugee/.test(t))return'humanitarian';return'conflict'};
  function markerData(){return Array.isArray(window.DATA?.markers)?window.DATA.markers:[]}

  /* Keep exactly one map filter control set. Older map filters are removed. */
  function removeLegacyMapControls(){
    document.querySelectorAll('.map-tools,.map-filters,[data-map-controls="legacy"],#mapFilters,#mapFilterBar').forEach(el=>{
      if(el.id!=='gpMapTools' && el.id!=='gpMapLegend') el.remove();
    });
    document.querySelectorAll('#gpMapTools ~ .map-tools,#gpMapLegend ~ .map-tools').forEach(el=>el.remove());
  }

  function ensureTools(){
    const mapRoot=document.getElementById('map');
    if(!mapRoot)return;
    removeLegacyMapControls();
    if(document.getElementById('gpMapTools'))return;
    const host=mapRoot.parentElement;
    if(!host)return;
    const wrap=document.createElement('div');
    wrap.id='gpMapTools';wrap.className='gp-map-tools';
    wrap.innerHTML='<button class="gp-map-tool active" data-mapfilter="all">ALL</button><button class="gp-map-tool" data-mapfilter="conflict">CONFLICT</button><button class="gp-map-tool" data-mapfilter="osint">OSINT</button><button class="gp-map-tool" data-mapfilter="diplomatic">DIPLOMATIC</button><button class="gp-map-tool" data-mapfilter="economic">ECONOMIC</button><button class="gp-map-tool" data-mapfilter="humanitarian">HUMANITARIAN</button><span class="gp-map-status" id="gpMapStatus"></span>';
    host.insertBefore(wrap,mapRoot);
    const leg=document.createElement('div');leg.id='gpMapLegend';leg.className='gp-map-legend';
    leg.innerHTML='<span><i class="gp-dot conflict"></i> Conflict</span><span><i class="gp-dot osint"></i> OSINT / Report</span><span><i class="gp-dot diplomatic"></i> Diplomatic</span><span><i class="gp-dot economic"></i> Economic</span><span><i class="gp-dot humanitarian"></i> Humanitarian</span>';
    wrap.insertAdjacentElement('afterend',leg);
    wrap.querySelectorAll('[data-mapfilter]').forEach(b=>b.onclick=()=>{window.gpMapFilter=b.dataset.mapfilter;wrap.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));renderFilteredMap()});
  }

  function renderFilteredMap(){
    if(typeof window.renderMap!=='function')return;
    const data=markerData(),f=window.gpMapFilter||'all';
    const old=window.DATA?.markers;
    if(window.DATA&&f!=='all')window.DATA.markers=data.filter(m=>typeOf(m)===f);
    try{window.renderMap()}finally{if(window.DATA&&old)window.DATA.markers=old}
    setTimeout(updateStatus,30);
  }

  function updateStatus(){
    const status=document.getElementById('gpMapStatus');
    if(!status)return;
    const data=markerData(),f=window.gpMapFilter||'all';
    const n=data.filter(m=>f==='all'||typeOf(m)===f).length;
    status.textContent=n+' map signal'+(n===1?'':'s');
  }

  function addEventPopups(){
    /* Do not create a second set of map points. The native map renderer owns markers. */
    return;
  }

  function cleanupStrayText(){
    /* Remove accidental standalone Update 2 text nodes if a browser rendered a legacy injection. */
    document.body.childNodes.forEach(n=>{
      if(n.nodeType===Node.TEXT_NODE && /Update 2|professional intelligence map|map patch prepared/i.test(n.nodeValue||'')) n.remove();
    });
  }

  function boot(){
    ensureTools();
    cleanupStrayText();
    updateStatus();
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,250));
  else setTimeout(boot,250);
})();
</script>
'''
if 'gp-map-pro-js' not in s:
    s=s.replace('</body>',js+'\n</body>',1)

p.write_text(s,encoding='utf-8')
print('Update 2 map cleanup applied')
