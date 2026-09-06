/** Global Situation Map — canonical renderer for all live geographic intelligence. */
import { getState } from '../core/state.js';
import { CONFIG } from '../core/config.js';
import { escapeHtml } from '../core/utils.js';
let map=null,layerGroups={},activeFilter=localStorage.getItem('gp.mapFilter')||'all',selectedMarker=null,lastPoints=[];

export function initMap(){
 const container=document.getElementById('mapContainer');
 if(!container||map||typeof L==='undefined')return;
 map=L.map(container,{center:CONFIG.mapDefaultCenter,zoom:CONFIG.mapDefaultZoom,zoomControl:true,attributionControl:true,closePopupOnClick:true,worldCopyJump:true,preferCanvas:true});
 L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}).addTo(map);
 layerGroups={conflicts:L.layerGroup().addTo(map),hazards:L.layerGroup().addTo(map),strategic:L.layerGroup().addTo(map),cartel:L.layerGroup().addTo(map),osint:L.layerGroup().addTo(map)};
 document.querySelectorAll('[data-layer]').forEach(btn=>btn.addEventListener('click',()=>{const key=btn.dataset.layer;const group=layerGroups[key];if(!group)return;const on=map.hasLayer(group);on?map.removeLayer(group):map.addLayer(group);btn.classList.toggle('primary',!on)}));
 const toggle=document.getElementById('mapFilterToggle'),panel=document.getElementById('mapFilterPanel');
 toggle?.addEventListener('click',()=>{const open=panel.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));panel.setAttribute('aria-hidden',String(!open));setTimeout(()=>map.invalidateSize(),50)});
 document.querySelectorAll('[data-map-filter]').forEach(btn=>btn.addEventListener('click',()=>{activeFilter=btn.dataset.mapFilter||'all';localStorage.setItem('gp.mapFilter',activeFilter);document.querySelectorAll('[data-map-filter]').forEach(b=>b.classList.toggle('primary',b===btn));renderMap()}));
 document.querySelector(`[data-map-filter="${CSS.escape(activeFilter)}"]`)?.classList.add('primary');
 map.on('click',()=>closeDetail());
 setTimeout(()=>map.invalidateSize(),100);
}
function num(v){const n=Number(v);return Number.isFinite(n)?n:null}
function coords(p){if(!p||typeof p!=='object')return null;let lat=num(p.lat??p.latitude??p.lat_deg??p.coordinates?.lat??p.location?.lat??p.location?.latitude),lon=num(p.lng??p.lon??p.longitude??p.long??p.coordinates?.lon??p.coordinates?.lng??p.location?.lon??p.location?.lng??p.location?.longitude);if((lat==null||lon==null)&&Array.isArray(p.coordinates)&&p.coordinates.length>=2){lon=num(p.coordinates[0]);lat=num(p.coordinates[1])}if((lat==null||lon==null)&&Array.isArray(p.geometry?.coordinates)&&p.geometry.coordinates.length>=2){lon=num(p.geometry.coordinates[0]);lat=num(p.geometry.coordinates[1])}return lat!=null&&lon!=null&&Math.abs(lat)<=90&&Math.abs(lon)<=180?[lat,lon]:null}
function classify(p,source='') {const raw=[p?.layer,p?.type,p?.eventType,p?.category,p?.signal,p?.sourceType,p?.group,p?.kind,source].filter(Boolean).join(' ').toLowerCase();if(/cartel|organized.?crime|crime|gang|narco|enforcer/.test(raw))return'cartel';if(/hazard|gdacs|earthquake|quake|disaster|wildfire|fire|storm|flood|cyclone|hurricane|landslide|drought/.test(raw))return'hazards';if(/strategic|chokepoint|military.?base|infrastructure|infra|reference/.test(raw))return'strategic';if(/osint|regional|social|reporting|source/.test(raw))return'osint';return'conflicts'}
function flatten(value,source='',out=[],seen=new WeakSet(),depth=0){if(depth>7||value==null)return out;if(typeof value!=='object')return out;if(seen.has(value))return out;seen.add(value);if(Array.isArray(value)){value.forEach(v=>flatten(v,source,out,seen,depth+1));return out}const c=coords(value);if(c)out.push({...value,__lat:c[0],__lon:c[1],__source:source});for(const [k,v] of Object.entries(value)){if(k==='coordinates'||k==='geometry'||k==='location')continue;if(v&&typeof v==='object')flatten(v,source||k,out,seen,depth+1)}return out}
function sourcePoints(data){const out=[];const add=(v,s)=>flatten(v,s,out);
 add(data?.events,'events');add(data?.regional,'regional');add(data?.cartel,'cartel');add(data?.links,'links');return out}
function snapshotPoints(snapshot){const out=[];const keys=['markers','mapPoints','map_points','points','hazards','strategic','events'];keys.forEach(k=>flatten(snapshot?.[k],k,out));if(snapshot?.osintMaps)flatten(snapshot.osintMaps,'osintMaps',out);if(snapshot?.counterCartelLayer)flatten(snapshot.counterCartelLayer,'counterCartelLayer',out);return out}
function dedupe(points){const seen=new Set();return points.filter(p=>{const key=String(p.id||p.eventId||p.mapId||p.url||p.sourceUrl||`${p.__lat.toFixed(5)},${p.__lon.toFixed(5)},${p.title||p.name||''}`);if(seen.has(key))return false;seen.add(key);return true})}
function matchesFilter(group){return activeFilter==='all'||activeFilter===group||(activeFilter==='conflict'&&group==='conflicts')}
function visiblePoints(){const state=getState();const combined=dedupe([...snapshotPoints(state.snapshot),...sourcePoints(state.mapData)]);const points=combined.filter(p=>coords(p)&&matchesFilter(classify(p,p.__source))).slice(0,2500);return points}
export function renderMap(){
 if(!map)initMap();if(!map)return;
 Object.values(layerGroups).forEach(g=>g.clearLayers());
 const points=visiblePoints();lastPoints=points;
 const counts={conflicts:0,hazards:0,strategic:0,cartel:0,osint:0};
 points.forEach(p=>{const groupKey=classify(p,p.__source),group=layerGroups[groupKey]||layerGroups.conflicts;counts[groupKey]++;const color={conflicts:'#ff6678',hazards:'#ffc857',strategic:'#62a0ff',cartel:'#fb923c',osint:'#aa8df7'}[groupKey]||'#62a0ff';const importance=Math.max(0.5,Math.min(1.2,Number(p.importance??p.score??p.severityScore??0.6)));const marker=L.circleMarker([p.__lat,p.__lon],{radius:Math.max(4,Math.min(9,importance*7)),color,fillColor:color,fillOpacity:.78,weight:1});marker.on('click',e=>{if(e.originalEvent)e.originalEvent.stopPropagation();showSidePanel(p)});group.addLayer(marker)});
 updateCount(points.length,counts);
 if(points.length){const bounds=L.latLngBounds(points.map(p=>[p.__lat,p.__lon]));if(!window.__gpMapInitialFit){map.fitBounds(bounds.pad(.06),{maxZoom:5});window.__gpMapInitialFit=true}}
 setTimeout(()=>map.invalidateSize(),50);
}
function updateCount(total,counts){let el=document.getElementById('gpMapCount');if(!el){el=document.createElement('div');el.id='gpMapCount';el.className='gp-map-count';document.getElementById('mapContainer')?.parentElement?.insertBefore(el,document.getElementById('mapContainer'))}el.textContent=`${total.toLocaleString()} signals · ${counts.conflicts} conflict · ${counts.hazards} hazard · ${counts.strategic} strategic · ${counts.cartel} crime`}
function closeDetail(){const panel=document.getElementById('mapSidePanel');if(panel){panel.style.display='none';panel.innerHTML=''}selectedMarker=null}
function showSidePanel(p){closeDetail();selectedMarker=p;const panel=document.getElementById('mapSidePanel');if(!panel)return;const title=p.title||p.name||p.location||p.event||'Map signal';const detail=p.detail||p.summary||p.description||p.reason||p.recent||'No additional detail in snapshot.';const url=p.url||p.sourceUrl||p.source||null;const type=p.type||p.layer||p.eventType||p.category||p.__source||'';panel.style.display='block';panel.innerHTML=`<div class="gp-card-title">${escapeHtml(title)}</div><div style="font-size:12px;color:var(--muted);margin:4px 0 8px">${escapeHtml(type)}</div><div style="font-size:13px;color:var(--text-secondary)">${escapeHtml(String(detail).slice(0,700))}</div>${/^https?:\/\//i.test(String(url||''))?`<div style="margin-top:8px"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a></div>`:''}<button id="mapDetailClose" class="gp-btn" style="margin-top:10px" type="button">Close</button>`;panel.querySelector('#mapDetailClose')?.addEventListener('click',closeDetail)}
