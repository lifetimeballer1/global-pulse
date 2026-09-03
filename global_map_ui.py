#!/usr/bin/env python3
"""Install one deterministic, self-contained Global Pulse map renderer.

The dashboard previously accumulated several competing Leaflet controllers.
This installer removes those injected UI layers and appends exactly one map
renderer that consumes the canonical DATA.markers dataset.
"""
from pathlib import Path
import re

INDEX = Path(__file__).resolve().parent / "index.html"


def install() -> None:
    s = INDEX.read_text(encoding="utf-8")

    # Remove every known experimental/duplicate map and evidence layer.
    patterns = [
        r'\n<style id="gp-own-map-css">.*?</style>\n?',
        r'\n<script id="gp-own-map-js">.*?</script>\n?',
        r'\n<script id="gp-map-pro-js">.*?</script>\n?',
        r'\n<style id="gp-map-pro-css">.*?</style>\n?',
        r'\n<style id="gp-evidence-css">.*?</style>\n?',
        r'\n<script id="gp-evidence-js">.*?</script>\n?',
        r'\n<style id="gp-analysis-css">.*?</style>\n?',
        r'\n<script id="gp-analysis-js">.*?</script>\n?',
        r'\n<section[^>]*id="evidenceCenter"[^>]*>.*?</section>\n?',
        r'\n<section[^>]*id="analysisCenter"[^>]*>.*?</section>\n?',
        r'\n<div[^>]*id="gpMapTools"[^>]*>.*?</div>\n?',
        r'\n<div[^>]*id="gpMapLegend"[^>]*>.*?</div>\n?',
        r'\n<section[^>]*id="gpBrief"[^>]*>.*?</section>\n?',
    ]
    for pattern in patterns:
        s = re.sub(pattern, "\n", s, flags=re.S | re.I)

    # Remove a previous rescue installation before adding the current one.
    s = re.sub(r'\n<style id="gp-map-rescue-css">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="gp-map-rescue-js">.*?</script>\n?', '\n', s, flags=re.S)

    css = r'''
<style id="gp-map-rescue-css">
#map{height:540px;min-height:320px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#07101a}
.gp-mapbar{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin:0 0 9px}.gp-mapbar button{font-size:10px;min-height:34px;padding:7px 9px}.gp-mapbar button.active{border-color:var(--blue);color:var(--blue);background:rgba(98,160,255,.13)}.gp-map-search{flex:1;min-width:170px}.gp-map-count{font-size:10px;color:var(--muted);margin-left:auto}.gp-map-legend{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0;color:var(--muted);font-size:10px}.gp-map-legend i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}.gp-map-legend .c{background:#ff6678}.gp-map-legend .o{background:#ffc857}.gp-map-legend .s{background:#62a0ff}.gp-map-legend .h{background:#48df83}.gp-map-legend .x{background:#aa8df7}
.gp-popup-title{font-weight:850;font-size:13px;margin-bottom:5px}.gp-popup-meta{font-size:10px;color:#91a4b8;margin-bottom:6px}.gp-popup-detail{font-size:11px;line-height:1.4}.gp-popup-link{display:inline-block;margin-top:8px;color:#62a0ff;font-weight:750}
@media(max-width:720px){#map{height:390px}.gp-mapbar{overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px}.gp-mapbar button{white-space:nowrap}.gp-map-search{min-width:150px}.gp-map-count{width:100%;margin-left:0}}
</style>
'''
    s = s.replace("</head>", css + "\n</head>", 1)

    js = r'''
<script id="gp-map-rescue-js">
(function(){
  "use strict";
  const boot=()=>{
    if(!window.L || !window.DATA || !document.getElementById("map")) return false;
    const old=document.getElementById("map");
    const parent=old.parentElement;
    if(!parent) return false;

    // Replace the existing container so an earlier Leaflet instance can never
    // trigger "Map container is already initialized".
    const fresh=document.createElement("div");
    fresh.id="map";
    old.replaceWith(fresh);

    const bar=document.createElement("div");
    bar.className="gp-mapbar";
    bar.innerHTML='<button type="button" class="active" data-f="all">ALL</button><button type="button" data-f="conflict">CONFLICT</button><button type="button" data-f="osint">OSINT</button><button type="button" data-f="organized">ORGANIZED CRIME</button><button type="button" data-f="strategic">STRATEGIC</button><button type="button" data-f="hazard">HAZARDS</button><input class="gp-map-search" id="gpMapSearch" placeholder="Search map signals…" autocomplete="off"><span class="gp-map-count" id="gpMapCount"></span>';
    parent.insertBefore(bar,fresh);

    const legend=document.createElement("div");
    legend.className="gp-map-legend";
    legend.innerHTML='<span><i class="c"></i>Conflict</span><span><i class="o"></i>OSINT</span><span><i class="s"></i>Strategic</span><span><i class="h"></i>Hazard</span><span><i class="x"></i>Organized crime</span>';
    parent.insertBefore(legend,fresh);

    const map=L.map(fresh,{worldCopyJump:true,preferCanvas:true,zoomControl:true,attributionControl:true}).setView([20,0],2);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{maxZoom:19,subdomains:"abcd",attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);

    let layer=(window.L.markerClusterGroup?window.L.markerClusterGroup({showCoverageOnHover:false,removeOutsideVisibleBounds:true}):L.layerGroup()).addTo(map);
    let filter="all";
    let query="";

    const esc=v=>String(v??"").replace(/[&<>\"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;","'":"&#39;"}[m]));
    const kind=m=>{const t=String(m?.eventType||m?.type||m?.layer||"conflict").toLowerCase();if(/organized|crime|cartel|gang/.test(t))return"organized";if(/strategic|chokepoint|flashpoint|node/.test(t))return"strategic";if(/hazard|earthquake|environment|natural/.test(t))return"hazard";if(/osint|source map|social|report/.test(t))return"osint";return"conflict"};
    const latOf=m=>Number(m?.lat??m?.latitude);
    const lngOf=m=>Number(m?.lng??m?.lon??m?.longitude);
    const markerColor=k=>({conflict:"#ff6678",osint:"#ffc857",strategic:"#62a0ff",hazard:"#48df83",organized:"#aa8df7"}[k]||"#62a0ff");

    function render(){
      layer.clearLayers();
      const all=Array.isArray(window.DATA.markers)?window.DATA.markers:[];
      const filtered=all.filter(m=>{
        const la=latOf(m),lo=lngOf(m);if(!Number.isFinite(la)||!Number.isFinite(lo)||Math.abs(la)>90||Math.abs(lo)>180)return false;
        const k=kind(m);if(filter!=="all"&&k!==filter)return false;
        const hay=[m.title,m.detail,m.source,m.region,m.eventType,m.type,m.layer].map(x=>String(x??"").toLowerCase()).join(" ");
        return !query||hay.includes(query);
      });
      filtered.forEach(m=>{
        const k=kind(m), color=markerColor(k), title=esc(m.title||m.name||"Map signal"), detail=esc(m.detail||m.description||"No additional detail available."), source=esc(m.source||"Public source"), event=esc(m.eventType||m.type||k.toUpperCase()), url=String(m.url||m.sourceUrl||"");
        const icon=L.divIcon({className:"",html:'<span style="display:block;width:12px;height:12px;border-radius:50%;background:'+color+';border:2px solid rgba(255,255,255,.75);box-shadow:0 0 0 3px '+color+'33"></span>',iconSize:[12,12],iconAnchor:[6,6]});
        const mk=L.marker([latOf(m),lngOf(m)],{icon});
        mk.bindPopup('<div class="gp-popup-title">'+title+'</div><div class="gp-popup-meta">'+event+' · '+source+'</div><div class="gp-popup-detail">'+detail+'</div>'+(url&&/^https?:\/\//i.test(url)?'<a class="gp-popup-link" href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Open source ↗</a>':""));
        layer.addLayer(mk);
      });
      document.getElementById("gpMapCount").textContent=filtered.length+" signals";
      if(filtered.length){
        const bounds=L.latLngBounds(filtered.map(m=>[latOf(m),lngOf(m)]));
        if(!window.gpMapBooted){map.fitBounds(bounds.pad(0.08),{maxZoom:5});window.gpMapBooted=true;}
      }
      setTimeout(()=>map.invalidateSize(),50);
    }

    bar.querySelectorAll("button[data-f]").forEach(b=>b.addEventListener("click",()=>{filter=b.dataset.f;bar.querySelectorAll("button").forEach(x=>x.classList.toggle("active",x===b));window.gpMapBooted=false;render();}));
    document.getElementById("gpMapSearch").addEventListener("input",e=>{query=e.target.value.trim().toLowerCase();window.gpMapBooted=false;render();});
    window.gpGlobalMap=map;
    window.renderMap=render;
    render();
    return true;
  };
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>{let n=0;const t=setInterval(()=>{if(boot()||++n>80)clearInterval(t);},100);});
  else {let n=0;const t=setInterval(()=>{if(boot()||++n>80)clearInterval(t);},100);}
})();
</script>
'''
    s = s.replace("</body>", js + "\n</body>", 1)
    INDEX.write_text(s, encoding="utf-8")
    print("Installed deterministic Global Pulse map rescue; duplicate map/evidence/analysis layers removed")


if __name__ == "__main__":
    install()
