from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Repair the Update 1 script typo if it is present in the generated dashboard.
s = s.replace("if(e.target===back)close());", "if(e.target===back)close()});")

css = r'''
<style id="gp-map-pro-css">
/* Global Pulse Update 2 — professional intelligence map */
.gp-map-tools{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 12px}.gp-map-tool{border:1px solid #29445f;background:#081522;color:#b9cbe0;border-radius:8px;padding:7px 10px;font:600 10px/1 system-ui;cursor:pointer}.gp-map-tool.active{border-color:#6b9bd0;background:#10243a;color:#eef6ff}.gp-map-legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px;padding:9px 10px;border:1px solid #1d3349;border-radius:9px;background:#07111b;color:#8196aa;font-size:10px}.gp-map-legend span{display:inline-flex;align-items:center;gap:5px}.gp-dot{width:8px;height:8px;border-radius:50%;display:inline-block}.gp-dot.conflict{background:#ef6262}.gp-dot.osint{background:#e0ad54}.gp-dot.diplomatic{background:#67a0df}.gp-dot.economic{background:#8d76c9}.gp-dot.humanitarian{background:#69b98b}.gp-map-status{font-size:10px;color:#70879c;margin-left:auto}.gp-event-popup{min-width:210px}.gp-event-popup h4{margin:0 0 5px;font-size:13px}.gp-event-popup p{margin:5px 0;color:#6d8092;font-size:10px;line-height:1.45}.gp-event-type{display:inline-block;margin-bottom:6px;padding:3px 6px;border:1px solid #36506a;border-radius:5px;color:#8fb5de;font-size:9px;text-transform:uppercase;letter-spacing:.06em}.gp-event-source{display:inline-block;margin-top:6px;color:#72a7e5;font-size:10px}.gp-cluster{background:#0b1724;border:2px solid #e0ad54;color:#f4d58e;border-radius:50%;display:flex;align-items:center;justify-content:center;font:700 11px system-ui;box-shadow:0 0 0 3px rgba(224,173,84,.12)}
@media(max-width:720px){.gp-map-tools{overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px}.gp-map-tool{white-space:nowrap}.gp-map-status{width:100%;margin-left:0}}
</style>
'''
if 'gp-map-pro-css' not in s:
    s=s.replace('</head>',css+'\n</head>',1)

js = r'''
<script id="gp-map-pro-js">
/* Update 2: professional conflict / OSINT map layer */
(function(){
  const theaterCoords={
    ukraine:[49,31.2,5.2],gaza:[31.4,34.4,5.2],"israel-iran":[32,44,5.2],hormuz:[26.3,53.4,5.2],yemen:[15.4,44.2,5.5],syria:[35,38.9,5.2],iraq:[33.2,43.8,5.2],sudan:[15.5,30.2,5.2],"south-sudan":[6.8,31.3,5.2],drc:[-1.5,29.2,5.2],somalia:[5.8,46.2,5.2],ethiopia:[9.1,40.5,5.2],nigeria:[9,8.7,5.2],"sahel-mali":[17,-3,5.2],"sahel-burkina":[12.4,-1.6,5.2],"sahel-niger":[17.6,8.1,5.2],cameroon:[5.9,10.2,5.2],chad:[15.3,18.7,5.2],libya:[27,17,5.2],mozambique:[-12.3,40.5,5.2],myanmar:[21,96,5.2],afghanistan:[33.9,67.7,5.2],pakistan:[30.4,69.3,5.2],taiwan:[24,120.7,5.2],korea:[38.5,127.9,5.2],"south-china-sea":[12,114,5.2],haiti:[18.97,-72.3,5.2],mexico:[23.6,-102.5,5.2],ecuador:[-1.8,-78.2,5.2],colombia:[4.6,-74.1,5.2]
  };
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const typeOf=m=>{const t=String(m?.eventType||m?.type||'conflict').toLowerCase();if(/osint|social|source map/.test(t))return'osint';if(/diplomat|talk|ceasefire|negoti/.test(t))return'diplomatic';if(/economic|market|sanction|trade|oil/.test(t))return'economic';if(/humanitarian|aid|displacement|refugee/.test(t))return'humanitarian';return'conflict'};
  function markerData(){return Array.isArray(window.DATA?.markers)?window.DATA.markers:[]}
  function ensureTools(){const mapRoot=document.getElementById('map');if(!mapRoot||document.getElementById('gpMapTools'))return;const host=mapRoot.parentElement;const wrap=document.createElement('div');wrap.id='gpMapTools';wrap.className='gp-map-tools';wrap.innerHTML='<button class="gp-map-tool active" data-mapfilter="all">ALL</button><button class="gp-map-tool" data-mapfilter="conflict">CONFLICT</button><button class="gp-map-tool" data-mapfilter="osint">OSINT</button><button class="gp-map-tool" data-mapfilter="diplomatic">DIPLOMATIC</button><button class="gp-map-tool" data-mapfilter="economic">ECONOMIC</button><button class="gp-map-tool" data-mapfilter="humanitarian">HUMANITARIAN</button><span class="gp-map-status" id="gpMapStatus"></span>';mapRoot.parentElement.insertBefore(wrap,mapRoot);const leg=document.createElement('div');leg.id='gpMapLegend';leg.className='gp-map-legend';leg.innerHTML='<span><i class="gp-dot conflict"></i> Conflict</span><span><i class="gp-dot osint"></i> OSINT / Report</span><span><i class="gp-dot diplomatic"></i> Diplomatic</span><span><i class="gp-dot economic"></i> Economic</span><span><i class="gp-dot humanitarian"></i> Humanitarian</span>';wrap.insertAdjacentElement('afterend',leg);wrap.querySelectorAll('[data-mapfilter]').forEach(b=>b.onclick=()=>{window.gpMapFilter=b.dataset.mapfilter;wrap.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));if(typeof window.renderMap==='function')window.renderMap()})}
  function patchRender(){if(typeof window.renderMap!=='function'||window.renderMap.__gp2)return false;const original=window.renderMap;function enhanced(){ensureTools();const result=original.apply(this,arguments);setTimeout(()=>decorate(),0);return result}enhanced.__gp2=true;window.renderMap=enhanced;return true}
  function decorate(){const status=document.getElementById('gpMapStatus');if(status){const data=markerData();const f=window.gpMapFilter||'all';const n=data.filter(m=>f==='all'||typeOf(m)===f).length;status.textContent=n+' map signal'+(n===1?'':'s')}
    const data=markerData(),f=window.gpMapFilter||'all';document.querySelectorAll('.leaflet-marker-icon').forEach(el=>{const t=String(el.title||'').toLowerCase();el.style.opacity=f==='all'||t.includes(f)?'1':'.18'})
  }
  function installFilterAwareRender(){
    if(window.__gp2FilterInstalled)return true;
    const original=window.renderMap;
    if(typeof original!=='function')return false;
    function wrapped(){
      const old=window.DATA?.markers;
      const data=markerData();const f=window.gpMapFilter||'all';
      if(window.DATA&&f!=='all')window.DATA.markers=data.filter(m=>typeOf(m)===f);
      const out=original.apply(this,arguments);
      if(window.DATA&&old)window.DATA.markers=old;
      setTimeout(decorate,20);return out;
    }
    wrapped.__gp2=true;window.renderMap=wrapped;window.__gp2FilterInstalled=true;return true;
  }
  function addEventPopups(){
    if(!window.map||!window.L)return;
    if(window.__gp2Popups)return;
    const data=markerData();
    data.forEach(m=>{if(!Number.isFinite(+m.lat)||!Number.isFinite(+m.lng))return;const title=esc(m.title||m.name||'Map signal');const typ=typeOf(m);const detail=esc(m.detail||m.description||'');const url=m.url||m.sourceUrl||'';const html='<div class="gp-event-popup"><span class="gp-event-type">'+typ+'</span><h4>'+title+'</h4>'+ (detail?'<p>'+detail+'</p>':'') + (url?'<a class="gp-event-source" href="'+esc(url)+'" target="_blank" rel="noopener">Open source ↗</a>':'')+'</div>';L.circleMarker([+m.lat,+m.lng],{radius:4,weight:1,fillOpacity:.75,opacity:.9,className:'gp-event-'+typ}).bindPopup(html).addTo(window.map)})
    window.__gp2Popups=true;
  }
  function boot(){ensureTools();installFilterAwareRender();if(typeof window.renderMap==='function')window.renderMap();setTimeout(()=>{decorate();addEventPopups()},250)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,300));else setTimeout(boot,300);
})();
</script>
'''
if 'gp-map-pro-js' not in s:
    s=s.replace('</body>',js+'\n</body>',1)

p.write_text(s,encoding='utf-8')
print('Update 2 map patch prepared')
