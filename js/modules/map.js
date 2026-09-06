/** Interactive World Map — complete live snapshot layers with one readable detail panel. */
import { getState } from '../core/state.js';
import { CONFIG } from '../core/config.js';
import { escapeHtml } from '../core/utils.js';
let map=null,layerGroups={},activeFilter=localStorage.getItem('gp.mapFilter')||'all',selectedMarker=null;

export function initMap(){
  const container=document.getElementById('mapContainer'); if(!container||map||typeof L==='undefined')return;
  map=L.map(container,{center:CONFIG.mapDefaultCenter,zoom:CONFIG.mapDefaultZoom,zoomControl:true,attributionControl:true,closePopupOnClick:true});
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}).addTo(map);
  layerGroups={conflicts:L.layerGroup().addTo(map),hazards:L.layerGroup().addTo(map),strategic:L.layerGroup().addTo(map),cartel:L.layerGroup().addTo(map)};
  document.querySelectorAll('[data-layer]').forEach(btn=>btn.addEventListener('click',()=>{const key=btn.dataset.layer;if(!layerGroups[key])return;const on=map.hasLayer(layerGroups[key]);on?map.removeLayer(layerGroups[key]):map.addLayer(layerGroups[key]);btn.classList.toggle('primary',!on);}));
  const toggle=document.getElementById('mapFilterToggle'),panel=document.getElementById('mapFilterPanel');
  toggle?.addEventListener('click',()=>{const open=panel.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));panel.setAttribute('aria-hidden',String(!open));setTimeout(()=>map.invalidateSize(),0);});
  document.querySelectorAll('[data-map-filter]').forEach(btn=>btn.addEventListener('click',()=>{activeFilter=btn.dataset.mapFilter||'all';localStorage.setItem('gp.mapFilter',activeFilter);document.querySelectorAll('[data-map-filter]').forEach(b=>b.classList.toggle('primary',b===btn));renderMap();}));
  const saved=document.querySelector(`[data-map-filter="${CSS.escape(activeFilter)}"]`); saved?.classList.add('primary');
  map.on('click',()=>closeDetail());
  setTimeout(()=>map.invalidateSize(),100);
}
function groupFor(p){const raw=String(p.type||p.layer||p.eventType||p.category||'conflicts').toLowerCase();if(raw.includes('hazard')||raw.includes('quake')||raw.includes('disaster')||raw.includes('fire')||raw.includes('storm')||raw.includes('flood'))return'hazards';if(raw.includes('strategic')||raw.includes('base')||raw.includes('infra')||raw.includes('chokepoint'))return'strategic';if(raw.includes('cartel')||raw.includes('crime')||raw.includes('enforcer')||raw.includes('organized'))return'cartel';return'conflicts';}
function matchesFilter(group){return activeFilter==='all'||activeFilter===group||activeFilter==='conflict'&&group==='conflicts';}
export function renderMap(){
  if(!map)initMap(); if(!map)return;
  const {snapshot}=getState(); if(!snapshot)return;
  Object.values(layerGroups).forEach(g=>g.clearLayers());
  const all=[...(Array.isArray(snapshot.markers)?snapshot.markers:[]),...(Array.isArray(snapshot.mapPoints)?snapshot.mapPoints:[]),...(Array.isArray(snapshot.hazards)?snapshot.hazards:[]),...(Array.isArray(snapshot.strategic)?snapshot.strategic:[]),...((snapshot.counterCartelLayer&&Array.isArray(snapshot.counterCartelLayer.points))?snapshot.counterCartelLayer.points:[])];
  const seen=new Set();
  const points=all.filter(p=>{const lat=p?.lat??p?.latitude,lon=p?.lng??p?.lon??p?.longitude;if(lat==null||lon==null)return false;const k=String(p.id||p.eventId||p.url||p.title||p.name||`${lat},${lon}`);if(seen.has(k))return false;seen.add(k);return true;}).slice(0,1200);
  points.forEach(p=>{const lat=Number(p.lat??p.latitude),lon=Number(p.lng??p.lon??p.longitude);if(!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180)return;const groupKey=groupFor(p);if(!matchesFilter(groupKey))return;const group=layerGroups[groupKey]||layerGroups.conflicts;const color=groupKey==='hazards'?'#ffc857':groupKey==='strategic'?'#62a0ff':groupKey==='cartel'?'#fb923c':'#ff6678';const marker=L.circleMarker([lat,lon],{radius:Math.max(4,Math.min(10,Number(p.importance||p.score||0.5)*8)),color,fillColor:color,fillOpacity:0.7,weight:1});marker.on('click',e=>{if(e.originalEvent)e.originalEvent.stopPropagation();showSidePanel(p);});group.addLayer(marker);});
  setTimeout(()=>map.invalidateSize(),0);
}
function closeDetail(){const panel=document.getElementById('mapSidePanel');if(panel){panel.style.display='none';panel.innerHTML='';}selectedMarker=null;}
function showSidePanel(p){closeDetail();selectedMarker=p;const panel=document.getElementById('mapSidePanel');if(!panel)return;const title=p.title||p.name||p.location||'Event';const detail=p.detail||p.summary||p.description||p.reason||'No additional detail in snapshot.';const url=p.url||p.sourceUrl||null;panel.style.display='block';panel.innerHTML=`<div class="gp-card-title">${escapeHtml(title)}</div><div style="font-size:12px;color:var(--muted);margin:4px 0 8px">${escapeHtml(p.type||p.layer||p.eventType||p.category||'')}</div><div style="font-size:13px;color:var(--text-secondary)">${escapeHtml(String(detail).slice(0,600))}</div>${url?`<div style="margin-top:8px"><a href="${escapeHtml(url)}" target="_blank" rel="noopener">Open source ↗</a></div>`:''}<button id="mapDetailClose" class="gp-btn" style="margin-top:10px" type="button">Close</button>`;panel.querySelector('#mapDetailClose')?.addEventListener('click',closeDetail);}
