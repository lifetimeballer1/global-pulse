#!/usr/bin/env python3
"""Add keyless map basemap switching and safe source-photo support.

Google Maps photos are not scraped or cached. When a marker has a legitimate
image URL supplied by an upstream feed, it is shown with a source link. Every
marker also gets a no-key Google Maps link built from its coordinates so users
can open the place/event in Google Maps and inspect available imagery there.
"""
from pathlib import Path
import re

INDEX = Path(__file__).resolve().parent / "index.html"

CSS = r'''<style id="gp-map-media-css">
.gp-map-media{display:block;width:100%;max-height:170px;object-fit:cover;border-radius:8px;margin:7px 0 8px;border:1px solid #1b2b3d;background:#07101a}.gp-map-media-credit{font-size:9px;color:#91a4b8;margin-top:-4px;margin-bottom:6px}.gp-map-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.gp-map-action{display:inline-block;padding:6px 8px;border:1px solid #1b2b3d;border-radius:7px;background:#09121c;color:#62a0ff;font-size:10px;font-weight:800}.gp-map-action:hover{background:#102033}.gp-map-photo-note{font-size:9px;color:#91a4b8;margin-top:6px;line-height:1.35}
</style>'''

JS = r'''<script id="gp-map-media-js">
(function(){
  "use strict";
  let installed=false;
  const esc=v=>String(v??"").replace(/[&<>\"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;","'":"&#39;"}[m]));
  const validUrl=v=>{try{const u=new URL(String(v||""));return /^https?:$/.test(u.protocol)}catch(_){return false}};
  const markerFor=(lat,lng)=>{
    const ms=Array.isArray(window.DATA?.markers)?window.DATA.markers:[];
    let best=null,dist=Infinity;
    for(const m of ms){const a=Number(m?.lat??m?.latitude),b=Number(m?.lng??m?.lon??m?.longitude);if(!Number.isFinite(a)||!Number.isFinite(b))continue;const d=Math.abs(a-lat)+Math.abs(b-lng);if(d<dist){dist=d;best=m}}
    return best && dist<0.0001 ? best : null;
  };
  const photoOf=m=>{
    for(const k of ["imageUrl","image_url","image","thumbnailUrl","thumbnail","photoUrl","photo_url","mediaUrl","media_url"]){const v=m?.[k];if(validUrl(v))return String(v)}
    if(Array.isArray(m?.images))for(const v of m.images)if(validUrl(v))return String(v);
    return "";
  };
  const mapsUrl=(m,lat,lng)=>{for(const k of ["googleMapsUrl","google_maps_url","mapsUrl","maps_url"]){if(validUrl(m?.[k]))return String(m[k])}return "https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(lat+","+lng)};
  function addBaseSwitch(map){
    if(!window.L||map.__gpBaseSwitch)return;
    let dark=null; map.eachLayer(x=>{if(!dark&&x instanceof L.TileLayer)dark=x});
    if(!dark)return;
    const street=L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"&copy; OpenStreetMap contributors"});
    L.control.layers({"Dark intelligence":dark,"OpenStreetMap":street},null,{collapsed:true,position:"topright"}).addTo(map);
    map.__gpBaseSwitch=true;
  }
  function install(){
    if(installed||!window.gpGlobalMap||!window.DATA)return false;
    installed=true;
    const map=window.gpGlobalMap;
    addBaseSwitch(map);
    map.on("popupopen",e=>{
      const src=e.popup&&e.popup._source;if(!src)return;
      const ll=src.getLatLng(),m=markerFor(ll.lat,ll.lng);if(!m)return;
      const el=e.popup.getElement();if(!el)return;
      const content=el.querySelector(".leaflet-popup-content");if(!content||content.querySelector(".gp-map-actions"))return;
      const photo=photoOf(m),mu=mapsUrl(m,ll.lat,ll.lng),source=String(m.sourceUrl||m.url||"");
      const box=document.createElement("div");
      let html="";
      if(photo)html+='<a href="'+esc(photo)+'" target="_blank" rel="noopener noreferrer"><img class="gp-map-media" src="'+esc(photo)+'" loading="lazy" referrerpolicy="no-referrer" alt="Source image"></a><div class="gp-map-media-credit">Image supplied by the event/source feed.</div>';
      html+='<div class="gp-map-actions"><a class="gp-map-action" href="'+esc(mu)+'" target="_blank" rel="noopener noreferrer">Open in Google Maps ↗</a>';
      if(source&&validUrl(source))html+='<a class="gp-map-action" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">Open source ↗</a>';
      html+='</div>';
      if(!photo)html+='<div class="gp-map-photo-note">No source image was supplied for this signal. Google Maps may have place imagery available after opening the location.</div>';
      content.insertAdjacentHTML("beforeend",html);
    });
    return true;
  }
  let tries=0;const timer=setInterval(()=>{if(install()||++tries>120)clearInterval(timer)},250);
})();
</script>'''


def main():
    s=INDEX.read_text(encoding="utf-8")
    s=re.sub(r'\n<style id="gp-map-media-css">.*?</style>\n?', '\n', s, flags=re.S)
    s=re.sub(r'\n<script id="gp-map-media-js">.*?</script>\n?', '\n', s, flags=re.S)
    s=s.replace('</head>',CSS+'\n</head>',1)
    s=s.replace('</body>',JS+'\n</body>',1)
    INDEX.write_text(s,encoding='utf-8')
    print('Installed keyless basemap switcher + source-photo/Google-Maps popup actions')

if __name__=='__main__': main()
