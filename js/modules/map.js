/** Global Situation Map — layered, My Maps-style intelligence renderer. */
import { getState } from '../core/state.js';
import { CONFIG } from '../core/config.js';
import { escapeHtml } from '../core/utils.js';

let map=null;
let layerGroups={};
let activeLayers=JSON.parse(localStorage.getItem('gp.mapLayers')||'{"conflicts":true,"hazards":true,"strategic":true,"cartel":true,"osint":true}');
let activeFilter='all';
let selectedMarker=null;
let fallbackSnapshot=null;
let fallbackLinks=null;
let directLoadStarted=false;
let searchQuery='';
let controlsBuilt=false;

const LAYERS={
  conflicts:{label:'Conflicts & Military',color:'#ff4d67',icon:'⚔️'},
  hazards:{label:'Hazards & Disasters',color:'#ffc857',icon:'⚠️'},
  strategic:{label:'Strategic Sites',color:'#62a0ff',icon:'🎯'},
  cartel:{label:'Cartel / Organized Crime',color:'#fb923c',icon:'🕶️'},
  osint:{label:'OSINT / Reporting',color:'#aa8df7',icon:'🛰️'}
};

export function initMap(){
  const container=document.getElementById('mapContainer');
  if(!container||map||typeof L==='undefined')return;
  map=L.map(container,{center:CONFIG.mapDefaultCenter,zoom:CONFIG.mapDefaultZoom,zoomControl:true,attributionControl:true,closePopupOnClick:true,worldCopyJump:true,preferCanvas:true});
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OpenStreetMap contributors',maxZoom:19}).addTo(map);
  layerGroups={};
  Object.keys(LAYERS).forEach(k=>{layerGroups[k]=L.layerGroup().addTo(map)});
  buildMapControls();
  const toggle=document.getElementById('mapFilterToggle'),panel=document.getElementById('mapFilterPanel');
  toggle?.addEventListener('click',()=>{const open=panel.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));panel.setAttribute('aria-hidden',String(!open));setTimeout(()=>map.invalidateSize(),50)});
  document.querySelectorAll('[data-map-filter]').forEach(btn=>btn.addEventListener('click',()=>{activeFilter=btn.dataset.mapFilter||'all';localStorage.setItem('gp.mapFilter',activeFilter);document.querySelectorAll('[data-map-filter]').forEach(b=>b.classList.toggle('primary',b===btn));renderMap()}));
  document.querySelector(`[data-map-filter="${CSS.escape(activeFilter)}"]`)?.classList.add('primary');
  map.on('click',()=>closeDetail());
  setTimeout(()=>map.invalidateSize(),100);
}

function buildMapControls(){
  if(controlsBuilt)return;
  controlsBuilt=true;
  const body=document.getElementById('mapContainer')?.parentElement;
  if(!body)return;
  const existing=document.getElementById('gpMapMyMapsControls');
  if(existing)existing.remove();
  const wrap=document.createElement('div');
  wrap.id='gpMapMyMapsControls';
  wrap.className='gp-map-mymaps-controls';
  wrap.innerHTML=`
    <div class="gp-map-toolbar">
      <button type="button" class="gp-map-tool" id="gpMapLayersToggle" aria-expanded="false">☰ Layers</button>
      <button type="button" class="gp-map-tool" id="gpMapFit">◎ Fit all</button>
      <button type="button" class="gp-map-tool" id="gpMapReset">↺ Reset</button>
      <input id="gpMapSearch" class="gp-map-search" type="search" placeholder="Search places, events, countries…" autocomplete="off" />
      <span id="gpMapCount" class="gp-map-count">Loading signals…</span>
    </div>
    <div id="gpMapLayersPanel" class="gp-map-layers-panel" aria-hidden="true">
      <div class="gp-map-panel-title">MAP LAYERS</div>
      <div class="gp-map-panel-subtitle">Turn intelligence layers on or off</div>
      <div id="gpMapLayerRows"></div>
    </div>`;
  body.insertBefore(wrap,document.getElementById('mapContainer'));
  const rows=document.getElementById('gpMapLayerRows');
  Object.entries(LAYERS).forEach(([key,meta])=>{
    const row=document.createElement('label');row.className='gp-map-layer-row';
    row.innerHTML=`<input type="checkbox" data-gp-layer="${key}" ${activeLayers[key]!==false?'checked':''}><span class="gp-map-layer-dot" style="background:${meta.color}"></span><span class="gp-map-layer-icon">${meta.icon}</span><span class="gp-map-layer-name">${meta.label}</span><span class="gp-map-layer-count" id="gpMapLayerCount-${key}">0</span>`;
    rows.appendChild(row);
    row.querySelector('input').addEventListener('change',e=>{activeLayers[key]=e.target.checked;localStorage.setItem('gp.mapLayers',JSON.stringify(activeLayers));syncGroups();renderMap()});
  });
  document.getElementById('gpMapLayersToggle')?.addEventListener('click',()=>{
    const panel=document.getElementById('gpMapLayersPanel');
    const open=panel.classList.toggle('open');
    panel.setAttribute('aria-hidden',String(!open));
    document.getElementById('gpMapLayersToggle').setAttribute('aria-expanded',String(open));
  });
  document.getElementById('gpMapFit')?.addEventListener('click',fitAll);
  document.getElementById('gpMapReset')?.addEventListener('click',()=>{searchQuery='';activeFilter='all';activeLayers=Object.fromEntries(Object.keys(LAYERS).map(k=>[k,true]));localStorage.removeItem('gp.mapLayers');localStorage.removeItem('gp.mapFilter');const s=document.getElementById('gpMapSearch');if(s)s.value='';document.querySelectorAll('[data-gp-layer]').forEach(x=>x.checked=true);renderMap();fitAll()});
  document.getElementById('gpMapSearch')?.addEventListener('input',e=>{searchQuery=e.target.value.trim().toLowerCase();renderMap()});
}

function syncGroups(){Object.entries(layerGroups).forEach(([k,g])=>{if(activeLayers[k]){if(!map.hasLayer(g))g.addTo(map)}else if(map.hasLayer(g))map.removeLayer(g)})}
function num(v){const n=Number(v);return Number.isFinite(n)?n:null}
function coords(p){
  if(!p||typeof p!=='object')return null;
  let lat=num(p.lat??p.latitude??p.lat_deg??p.coordinates?.lat??p.location?.lat??p.location?.latitude);
  let lon=num(p.lng??p.lon??p.longitude??p.long??p.coordinates?.lon??p.coordinates?.lng??p.location?.lon??p.location?.lng??p.location?.longitude);
  if((lat==null||lon==null)&&Array.isArray(p.coordinates)&&p.coordinates.length>=2){lon=num(p.coordinates[0]);lat=num(p.coordinates[1])}
  if((lat==null||lon==null)&&Array.isArray(p.geometry?.coordinates)&&p.geometry.coordinates.length>=2){lon=num(p.geometry.coordinates[0]);lat=num(p.geometry.coordinates[1])}
  return lat!=null&&lon!=null&&Math.abs(lat)<=90&&Math.abs(lon)<=180?[lat,lon]:null;
}
function classify(p,source=''){
  const raw=[p?.layer,p?.type,p?.eventType,p?.category,p?.signal,p?.sourceType,p?.group,p?.kind,source,p?.title,p?.name].filter(Boolean).join(' ').toLowerCase();
  if(/cartel|organized.?crime|crime|gang|narco|enforcer/.test(raw))return'cartel';
  if(/hazard|gdacs|earthquake|quake|disaster|wildfire|fire|storm|flood|cyclone|hurricane|landslide|drought|environment/.test(raw))return'hazards';
  if(/strategic|chokepoint|military.?base|infrastructure|infra|flashpoint|regional node/.test(raw))return'strategic';
  if(/osint|regional|social|reporting|source|news|article/.test(raw))return'osint';
  return'conflicts';
}
function flatten(value,source='',out=[],seen=new WeakSet(),depth=0){
  if(depth>10||value==null||typeof value!=='object'||seen.has(value))return out;
  seen.add(value);
  if(Array.isArray(value)){value.forEach(v=>flatten(v,source,out,seen,depth+1));return out}
  const c=coords(value);if(c)out.push({...value,__lat:c[0],__lon:c[1],__source:source});
  for(const [k,v] of Object.entries(value)){if(v&&typeof v==='object')flatten(v,source||k,out,seen,depth+1)}
  return out;
}
function collectSnapshot(snapshot){
  if(!snapshot)return [];
  const preferred=[
    ...(Array.isArray(snapshot.markers)?snapshot.markers:[]),
    ...(Array.isArray(snapshot.osintMaps?.regionalPoints)?snapshot.osintMaps.regionalPoints:[]),
    ...(Array.isArray(snapshot.osintMaps?.markers)?snapshot.osintMaps.markers:[]),
    ...(Array.isArray(snapshot.conflictDataset?.markers)?snapshot.conflictDataset.markers:[]),
    ...(Array.isArray(snapshot.mapPoints)?snapshot.mapPoints:[]),
    ...(Array.isArray(snapshot.map_points)?snapshot.map_points:[]),
    ...(Array.isArray(snapshot.points)?snapshot.points:[])
  ];
  const direct=flatten(preferred,'snapshot');
  return direct.length?direct:flatten(snapshot,'snapshot');
}
function collectMapData(data){return data?flatten(data,'live-map-data'):[]}
function dedupe(points){
  const seen=new Set();
  return points.filter(p=>{const key=String(p.id||p.eventId||p.mapId||p.datasetEventId||p.sourceUrl||p.url||`${p.__lat.toFixed(5)},${p.__lon.toFixed(5)},${p.title||p.name||''}`);if(seen.has(key))return false;seen.add(key);return true});
}
function matchesFilter(group){return activeFilter==='all'||activeFilter===group||(activeFilter==='conflict'&&group==='conflicts')}
function visiblePoints(){
  const state=getState();
  const points=dedupe([...collectSnapshot(state.snapshot),...collectMapData(state.mapData),...collectSnapshot(fallbackSnapshot),...collectMapData(fallbackLinks)]);
  return points.filter(p=>{if(!coords(p))return false;const group=classify(p,p.__source);if(!activeLayers[group])return false;if(!matchesFilter(group))return false;if(!searchQuery)return true;const hay=[p.title,p.name,p.location,p.country,p.region,p.city,p.detail,p.summary,p.description,p.source,p.type,p.layer,p.eventType,p.category].map(x=>String(x??'').toLowerCase()).join(' ');return hay.includes(searchQuery)}).slice(0,4000);
}
async function directMapLoad(){
  if(directLoadStarted)return;
  directLoadStarted=true;
  const bust=`?map=${Date.now()}`;
  try{
    const [snapRes,linksRes]=await Promise.all([fetch(`${CONFIG.endpoints.snapshot}${bust}`,{cache:'no-store'}),fetch(`${CONFIG.endpoints.mapLinks}${bust}`,{cache:'no-store'})]);
    fallbackSnapshot=snapRes.ok?await snapRes.json():null;
    fallbackLinks=linksRes.ok?await linksRes.json():null;
  }catch(err){console.warn('Direct map data load failed',err)}
  renderMap();
}
export function renderMap(){
  if(!map)initMap();
  if(!map)return;
  Object.values(layerGroups).forEach(g=>g.clearLayers());
  syncGroups();
  const points=visiblePoints();
  const counts={conflicts:0,hazards:0,strategic:0,cartel:0,osint:0};
  points.forEach(p=>{
    const groupKey=classify(p,p.__source),group=layerGroups[groupKey];if(!group)return;counts[groupKey]++;
    const meta=LAYERS[groupKey],importance=Math.max(.8,Math.min(2,Number(p.importance??p.score??p.severityScore??1)||1));
    const marker=L.circleMarker([p.__lat,p.__lon],{radius:Math.max(6,Math.min(11,importance*6)),color:'#ffffff',fillColor:meta.color,fillOpacity:.95,weight:2,opacity:1});
    marker.bindTooltip(String(p.title||p.name||p.location||p.event||meta.label).slice(0,120),{direction:'top',opacity:.95,sticky:false});
    marker.on('click',e=>{if(e.originalEvent)e.originalEvent.stopPropagation();showSidePanel(p)});
    group.addLayer(marker);
  });
  updateCount(points.length,counts);
  Object.keys(LAYERS).forEach(k=>{const el=document.getElementById(`gpMapLayerCount-${k}`);if(el)el.textContent=counts[k].toLocaleString()});
  if(!points.length||points.length<10)directMapLoad();
  setTimeout(()=>map.invalidateSize(),50);
}
function updateCount(total,counts){const el=document.getElementById('gpMapCount');if(el)el.textContent=`${total.toLocaleString()} signals · ${Object.values(counts).reduce((a,b)=>a+b,0).toLocaleString()} visible`}
function fitAll(){
  if(!map)return;
  const points=visiblePoints();
  if(points.length){map.fitBounds(L.latLngBounds(points.map(p=>[p.__lat,p.__lon])).pad(.08),{maxZoom:5,animate:true})}
  else map.setView(CONFIG.mapDefaultCenter,CONFIG.mapDefaultZoom,{animate:true});
}
function closeDetail(){const panel=document.getElementById('mapSidePanel');if(panel){panel.style.display='none';panel.innerHTML=''}selectedMarker=null}
function showSidePanel(p){
  closeDetail();selectedMarker=p;const panel=document.getElementById('mapSidePanel');if(!panel)return;
  const title=p.title||p.name||p.location||p.event||'Map signal';
  const detail=p.detail||p.summary||p.description||p.reason||p.recent||'No additional detail in source data.';
  const url=p.url||p.sourceUrl||p.source_url||null;
  const type=p.type||p.layer||p.eventType||p.category||p.__source||'';
  const group=classify(p,p.__source),meta=LAYERS[group];
  panel.style.display='block';
  panel.innerHTML=`<div class="gp-map-detail-head"><span class="gp-map-detail-icon">${meta.icon}</span><div><div class="gp-card-title">${escapeHtml(title)}</div><div class="gp-map-detail-type" style="color:${meta.color}">${escapeHtml(meta.label)}</div></div><button id="mapDetailClose" class="gp-btn" type="button" aria-label="Close">×</button></div><div class="gp-map-detail-coords">${p.__lat.toFixed(4)}, ${p.__lon.toFixed(4)}</div><div class="gp-map-detail-text">${escapeHtml(String(detail).slice(0,1200))}</div>${p.source?`<div class="gp-map-detail-source">Source: ${escapeHtml(p.source)}</div>`:''}${/^https?:\/\//i.test(String(url||''))?`<div style="margin-top:10px"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a></div>`:''}`;
  panel.querySelector('#mapDetailClose')?.addEventListener('click',closeDetail);
}
