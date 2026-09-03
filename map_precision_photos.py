#!/usr/bin/env python3
"""Install map-only precision geolocation and media-aware popups.

Precise lookup is deliberately user-triggered: a marker using an approximate
country-center coordinate can be resolved from its headline/country with
OpenStreetMap Nominatim after the user taps Locate precisely. Results are
cached in the browser. No Google Maps API key is required and Google imagery
is never scraped or cached.
"""
from pathlib import Path

INDEX = Path(__file__).resolve().parent / "index.html"
MARK = "<!-- GP-MAP-PRECISION-PHOTOS -->"

CSS = r'''<style id="gp-map-precision-css">
.gp-precision{margin-top:7px;padding-top:7px;border-top:1px solid #1b2b3d}
.gp-precision-status{font-size:9px;color:#91a4b8;line-height:1.35;margin:5px 0}
.gp-precision-actions{display:flex;gap:6px;flex-wrap:wrap}
.gp-precision-btn{display:inline-block;padding:6px 8px;border:1px solid #1b2b3d;border-radius:7px;background:#09121c;color:#62a0ff;font-size:10px;font-weight:800;cursor:pointer}
.gp-precision-btn:disabled{opacity:.55;cursor:wait}
.gp-source-photo{display:block;width:100%;max-height:190px;object-fit:cover;border-radius:8px;margin:7px 0 5px;border:1px solid #1b2b3d;background:#07101a}
.gp-photo-caption{font-size:9px;color:#91a4b8;margin:0 0 6px;line-height:1.35}
.gp-precision-badge{display:inline-block;margin-top:3px;padding:2px 5px;border-radius:5px;background:rgba(72,223,131,.1);color:#48df83;font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.05em}
</style>
'''

JS = r'''<script id="gp-map-precision-js">
(function(){
  "use strict";
  if(window.__gpPrecisionPhotosInstalled)return;
  window.__gpPrecisionPhotosInstalled=true;
  const cacheKey="globalPulseGeocodeV1";
  let cache={};
  try{cache=JSON.parse(localStorage.getItem(cacheKey)||"{}")}catch(_){cache={}}
  const esc=v=>String(v??"").replace(/[&<>\"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;","'":"&#39;"}[m]||m));
  const urlOk=v=>{try{const u=new URL(String(v||""));return u.protocol==="http:"||u.protocol==="https:"}catch(_){return false}};
  const markerData=(lat,lng)=>{
    const all=Array.isArray(window.DATA?.markers)?window.DATA.markers:[];let best=null,dist=Infinity;
    for(const m of all){const a=Number(m?.lat??m?.latitude),b=Number(m?.lng??m?.lon??m?.longitude);if(!Number.isFinite(a)||!Number.isFinite(b))continue;const d=Math.abs(a-lat)+Math.abs(b-lng);if(d<dist){dist=d;best=m}}
    return best&&dist<0.0001?best:null;
  };
  const photo=(m)=>{
    for(const k of ["imageUrl","image_url","image","thumbnailUrl","thumbnail","photoUrl","photo_url","mediaUrl","media_url"]){if(urlOk(m?.[k]))return String(m[k])}
    if(Array.isArray(m?.images))for(const v of m.images)if(urlOk(v))return String(v);
    return "";
  };
  const googleMaps=(m,lat,lng)=>{
    for(const k of ["googleMapsUrl","google_maps_url","mapsUrl","maps_url"]){if(urlOk(m?.[k]))return String(m[k])}
    return "https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(lat+","+lng);
  };
  function renderMedia(content,m,lat,lng){
    if(!content||content.querySelector(".gp-precision"))return;
    const img=photo(m), source=String(m?.sourceUrl||m?.url||"");
    let html="";
    if(img)html+='<a href="'+esc(img)+'" target="_blank" rel="noopener noreferrer"><img class="gp-source-photo" src="'+esc(img)+'" loading="lazy" referrerpolicy="no-referrer" alt="Source event image"></a><div class="gp-photo-caption">Image supplied by the source/event feed.</div>';
    else html+='<div class="gp-photo-caption">No source image is attached to this signal.</div>';
    html+='<div class="gp-precision"><div class="gp-precision-actions"><button type="button" class="gp-precision-btn" data-gp-locate>LOCATE PRECISELY</button><a class="gp-precision-btn" href="'+esc(googleMaps(m,lat,lng))+'" target="_blank" rel="noopener noreferrer">OPEN IN GOOGLE MAPS ↗</a>';
    if(source&&urlOk(source))html+='<a class="gp-precision-btn" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">OPEN SOURCE ↗</a>';
    html+='</div><div class="gp-precision-status" data-gp-status>Current map position: '+esc(m?.locationPrecision || (m?.type==="reported-area" ? "approximate / reported area" : "mapped signal"))+'.</div></div>';
    content.insertAdjacentHTML("beforeend",html);
    const btn=content.querySelector("[data-gp-locate]"),status=content.querySelector("[data-gp-status]");
    if(!btn||!status)return;
    btn.addEventListener("click",()=>locate(m,lat,lng,btn,status));
  }
  async function locate(m,lat,lng,btn,status){
    const q=[m?.title,m?.country,m?.region].filter(Boolean).join(", ").slice(0,240);if(!q)return;
    const key=q.toLowerCase();btn.disabled=true;btn.textContent="LOCATING…";status.textContent="Looking for a precise place from the event headline…";
    try{
      let hit=cache[key];
      if(!hit){
        const last=Number(localStorage.getItem("gpNominatimLast")||0),wait=Math.max(0,1100-(Date.now()-last));if(wait)await new Promise(r=>setTimeout(r,wait));
        const u="https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&addressdetails=1&q="+encodeURIComponent(q);
        const res=await fetch(u,{headers:{"Accept":"application/json"}});if(!res.ok)throw new Error("geocoder HTTP "+res.status);const arr=await res.json();localStorage.setItem("gpNominatimLast",String(Date.now()));hit=arr&&arr[0];
        if(hit){cache[key]={lat:Number(hit.lat),lng:Number(hit.lon),display:hit.display_name||q};try{localStorage.setItem(cacheKey,JSON.stringify(cache))}catch(_){} }
      }
      if(!hit)throw new Error("No precise place found");
      const a=Number(hit.lat),b=Number(hit.lon),mk=window.gpGlobalMap?markerData(lat,lng):null;
      if(mk){m.lat=a;m.lng=b;m.latitude=a;m.longitude=b;m.locationPrecision="geocoded";m.locationName=hit.display_name||q;}
      if(window.gpGlobalMap){window.gpGlobalMap.setView([a,b],Math.max(window.gpGlobalMap.getZoom(),9),{animate:true});}
      status.innerHTML='<span class="gp-precision-badge">GEOCODED</span> '+esc(hit.display_name||q)+'<br>Coordinates: '+a.toFixed(5)+', '+b.toFixed(5);
      btn.textContent="LOCATION FOUND";
      const gm=contentFor(btn);if(gm){const aTag=gm.querySelector("a.gp-precision-btn");if(aTag)aTag.href=googleMaps(m,a,b)}
    }catch(err){status.textContent="Precise lookup unavailable: "+String(err.message||err)+". The original map position was kept.";btn.textContent="TRY AGAIN"}
    finally{btn.disabled=false}
  }
  function contentFor(el){return el.closest(".leaflet-popup-content")}
  function boot(){
    const map=window.gpGlobalMap;if(!map||map.__gpPrecisionListener)return false;map.__gpPrecisionListener=true;
    map.on("popupopen",e=>{const src=e.popup&&e.popup._source;if(!src)return;const ll=src.getLatLng(),m=markerData(ll.lat,ll.lng);if(!m)return;const el=e.popup.getElement();const content=el&&el.querySelector(".leaflet-popup-content");if(content)renderMedia(content,m,ll.lat,ll.lng)});
    return true;
  }
  let tries=0;const t=setInterval(()=>{if(boot()||++tries>120)clearInterval(t)},100);
})();
</script>
'''

s = INDEX.read_text(encoding="utf-8")
start=s.find(MARK)
if start>=0:
    end=s.find("</body>",start)
    s=s[:start]+MARK+"\n"+CSS+JS+"\n"+s[end:]
else:
    s=s.replace("</head>",CSS+"\n</head>",1)
    s=s.replace("</body>",MARK+"\n"+JS+"\n</body>",1)
INDEX.write_text(s,encoding="utf-8")
print("Installed precise user-triggered geolocation and source-photo-aware map popups")
