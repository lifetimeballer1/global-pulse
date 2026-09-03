#!/usr/bin/env python3
"""Install the self-contained Global Pulse intelligence map UI.

The site already has legacy map code. This installer deliberately replaces the
map DOM node before creating a new Leaflet instance so the page cannot hit
Leaflet's "Map container is already initialized" error. It uses only the
machine-readable Global Pulse marker dataset; it does not scrape a third-party
map or require an API key.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
CSS_ID = "gp-own-map-css"
JS_ID = "gp-own-map-js"

CSS = r'''
/* Global Pulse — self-owned intelligence map */
.gp-own-map-tools{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin:0 0 10px}
.gp-own-map-btn{border:1px solid #263c53;background:#07131f;color:#a9bfd4;border-radius:8px;padding:8px 10px;font:700 10px/1 system-ui;cursor:pointer;white-space:nowrap}
.gp-own-map-btn:hover{border-color:#4d6f92;color:#eef6ff}.gp-own-map-btn.active{border-color:#69a5e6;background:#10263d;color:#fff}
.gp-own-map-search{flex:1;min-width:190px}.gp-own-map-search input{width:100%;min-width:0}
.gp-own-map-meta{display:flex;justify-content:space-between;gap:10px;align-items:center;margin:0 0 9px;padding:8px 10px;border:1px solid #1b2d40;border-radius:9px;background:#06101a;color:#7890a7;font-size:10px}
.gp-own-map-meta b{color:#e9f3ff}.gp-own-map-key{display:flex;flex-wrap:wrap;gap:9px;margin:0 0 9px;color:#71869b;font-size:10px}.gp-own-map-key span{display:inline-flex;align-items:center;gap:5px}.gp-own-map-key i{width:8px;height:8px;border-radius:50%;display:inline-block}
.gp-own-map-key .c{background:#ff6678}.gp-own-map-key .o{background:#ffc857}.gp-own-map-key .s{background:#62a0ff}.gp-own-map-key .h{background:#48df83}.gp-own-map-key .e{background:#aa8df7}
#map.gp-own-map{height:570px!important;background:#07111b}.gp-own-map .leaflet-control-layers{background:#07111b;color:#dce9f7;border:1px solid #20364c}.gp-own-map .leaflet-control-layers label{font-size:11px}.gp-own-map .leaflet-bar a{background:#07111b;color:#dce9f7;border-color:#20364c}
.gp-map-popup{min-width:230px;max-width:310px}.gp-map-popup h4{margin:0 0 7px;font-size:14px;line-height:1.25}.gp-map-popup .gp-p-tag{display:inline-block;margin:0 4px 5px 0;padding:3px 6px;border:1px solid #29445f;border-radius:5px;color:#9eb5ca;font-size:9px;font-weight:850;text-transform:uppercase}.gp-map-popup p{margin:6px 0;color:#91a4b8;font-size:11px;line-height:1.45}.gp-map-popup a{display:inline-block;margin-top:5px;color:#69a5ea;font-size:11px;font-weight:800}.gp-node-pulse{border-radius:50%;box-shadow:0 0 0 5px rgba(98,160,255,.08),0 0 22px rgba(98,160,255,.22)}
.gp-map-error{padding:16px;border:1px solid #5b2b35;background:#1b0d12;color:#ff9aa6;border-radius:10px;font-size:12px}
@media(max-width:720px){#map.gp-own-map{height:430px!important}.gp-own-map-tools{overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px}.gp-own-map-btn{flex:0 0 auto}.gp-own-map-search{min-width:150px;flex:1}.gp-own-map-meta{align-items:flex-start;flex-direction:column;gap:3px}}
'''

JS = r'''
(function(){
  'use strict';
  try {
    const DATA = window.DATA || {};
    let host = document.getElementById('map');
    if(!host || !window.L) return;

    /* The previous dashboard initializes #map first. Replace the DOM node so
       Leaflet receives a completely fresh container instead of throwing. */
    const fresh = host.cloneNode(false);
    fresh.removeAttribute('data-gp-own-map');
    host.replaceWith(fresh);
    host = fresh;
    host.dataset.gpOwnMap='1';
    host.classList.add('gp-own-map');

    const all = Array.isArray(DATA.markers) ? DATA.markers : [];
    const esc = x => String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const classify = m => {
      const s=((m.type||'')+' '+(m.eventType||'')+' '+(m.source||'')).toLowerCase();
      if(/hazard|earthquake|storm|flood|volcano|fire/.test(s)) return 'hazard';
      if(/organized|cartel/.test(s)) return 'organized';
      if(/strategic|reference|chokepoint|flashpoint|node/.test(s)) return 'strategic';
      if(s.includes('diplomatic')) return 'diplomatic';
      if(s.includes('economic')) return 'economic';
      if(s.includes('humanitarian')) return 'humanitarian';
      if(/osint|source map|war news/.test(s)) return 'osint';
      return 'conflict';
    };
    const color = k => ({conflict:'#ff6678',osint:'#ffc857',organized:'#fb923c',strategic:'#62a0ff',hazard:'#aa8df7',diplomatic:'#6fa7e8',economic:'#aa8df7',humanitarian:'#48df83'}[k]||'#62a0ff');
    const valid=all.filter(m=>Number.isFinite(+m.lat)&&Number.isFinite(+m.lng));

    const map=L.map(host,{worldCopyJump:true,zoomControl:true,preferCanvas:true,minZoom:2,maxZoom:12}).setView([20,0],2);
    const dark=L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:20,attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);
    const satellite=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Tiles &copy; Esri'});

    const parent=host.parentElement;
    const controls=document.createElement('div');
    controls.className='gp-own-map-tools';
    controls.innerHTML='<button class="gp-own-map-btn active" data-layer="all">ALL</button><button class="gp-own-map-btn" data-layer="conflict">CONFLICT</button><button class="gp-own-map-btn" data-layer="osint">OSINT</button><button class="gp-own-map-btn" data-layer="organized">ORGANIZED CRIME</button><button class="gp-own-map-btn" data-layer="strategic">STRATEGIC</button><button class="gp-own-map-btn" data-layer="hazard">HAZARDS</button><label class="gp-own-map-search"><input id="gpMapSearch" autocomplete="off" placeholder="Search country, city, event or source…"></label>';
    const meta=document.createElement('div');meta.className='gp-own-map-meta';meta.innerHTML='<span><b id="gpMapShown">0</b> mapped signals</span><span>Last data refresh: <b>'+esc(DATA.updatedAt||'unknown')+'</b></span>';
    const key=document.createElement('div');key.className='gp-own-map-key';key.innerHTML='<span><i class="c"></i>Conflict</span><span><i class="o"></i>OSINT</span><span><i style="background:#fb923c"></i>Organized crime</span><span><i class="s"></i>Strategic</span><span><i class="h"></i>Hazard</span>';
    parent.insertBefore(controls,host);parent.insertBefore(meta,host);parent.insertBefore(key,host);

    const groups={};
    ['conflict','osint','organized','strategic','hazard','diplomatic','economic','humanitarian'].forEach(k=>groups[k]=L.layerGroup().addTo(map));
    const makeMarker=m=>{
      const k=classify(m),c=color(k),size=k==='strategic'?16:10;
      const icon=L.divIcon({className:'',html:'<div class="gp-node-pulse" style="width:'+size+'px;height:'+size+'px;background:'+c+';border:2px solid #07111b"></div>',iconSize:[size,size],iconAnchor:[size/2,size/2]});
      const marker=L.marker([+m.lat,+m.lng],{icon});
      const source=m.source||'Global Pulse',url=m.url||m.sourceUrl||'';
      marker.bindPopup('<div class="gp-map-popup"><h4>'+esc(m.title||m.name||'Signal')+'</h4><span class="gp-p-tag">'+esc(k)+'</span><span class="gp-p-tag">'+esc(source)+'</span>'+(m.confidence?'<span class="gp-p-tag">'+esc(m.confidence)+'</span>':'')+'<p>'+esc(m.detail||'Mapped intelligence signal.')+'</p>'+(m.region?'<p><b>Region:</b> '+esc(m.region)+'</p>':'')+(url?'<a target="_blank" rel="noopener noreferrer" href="'+esc(url)+'">Open source ↗</a>':'')+'</div>',{maxWidth:320});
      return marker;
    };

    const overlays={};Object.keys(groups).forEach(k=>overlays[k.charAt(0).toUpperCase()+k.slice(1)]=groups[k]);
    L.control.layers({'Dark':dark,'Satellite':satellite},overlays,{collapsed:true,position:'topright'}).addTo(map);
    let active='all',query='';
    function redraw(){
      Object.values(groups).forEach(g=>g.clearLayers());
      let count=0;
      for(const m of valid){
        const k=classify(m),text=((m.title||m.name||'')+' '+(m.source||'')+' '+(m.region||'')+' '+(m.detail||'')).toLowerCase();
        if((active==='all'||k===active)&&(!query||text.includes(query))){(groups[k]||groups.conflict).addLayer(makeMarker(m));count++;}
      }
      const el=document.getElementById('gpMapShown');if(el)el.textContent=count.toLocaleString();
    }
    controls.querySelectorAll('.gp-own-map-btn').forEach(b=>b.addEventListener('click',()=>{controls.querySelectorAll('.gp-own-map-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');active=b.dataset.layer;redraw();}));
    const search=document.getElementById('gpMapSearch');if(search)search.addEventListener('input',()=>{query=search.value.trim().toLowerCase();redraw();});
    redraw();
    setTimeout(()=>map.invalidateSize(),250);
    window.addEventListener('resize',()=>map.invalidateSize());
    window.GP_INTELLIGENCE_MAP={map,refresh:redraw,markers:valid};
  } catch(err) {
    const host=document.getElementById('map');
    if(host) host.outerHTML='<div id="map" class="gp-map-error">Intelligence map failed to initialize. The rest of Global Pulse is still available.</div>';
    console.error('Global Pulse map initialization failed:',err);
  }
})();
'''

def install():
    s=INDEX.read_text(encoding='utf-8')
    s=re.sub(r'\n<style id="'+re.escape(CSS_ID)+r'">.*?</style>\n?','\n',s,flags=re.S)
    s=re.sub(r'\n<script id="'+re.escape(JS_ID)+r'">.*?</script>\n?','\n',s,flags=re.S)
    s=s.replace('</head>',f'\n<style id="{CSS_ID}">{CSS}</style>\n</head>',1)
    s=s.replace('</body>',f'\n<script id="{JS_ID}">{JS}</script>\n</body>',1)
    INDEX.write_text(s,encoding='utf-8')
    print('Installed self-owned intelligence map UI')

if __name__=='__main__':install()
