/** Global Situation Map — Phase 1 canonical marker renderer. */
import { getState } from '../core/state.js';
import { CONFIG } from '../core/config.js';
import { escapeHtml } from '../core/utils.js';

let map=null;
let groups={};
let mapData=null;
let selected=null;
let query='';
let filter='all';
const LAYERS={
  conflicts:{label:'Conflicts & Military',color:'#ff405f',icon:'⚔️'},
  hazards:{label:'Hazards & Disasters',color:'#ffd34d',icon:'⚠️'},
  strategic:{label:'Strategic Sites',color:'#4d9aff',icon:'🎯'},
  cartel:{label:'Cartel / Organized Crime',color:'#ff8a35',icon:'🕶️'},
  osint:{label:'OSINT / Reporting',color:'#b08cff',icon:'🛰️'}
};
let enabled=Object.fromEntries(Object.keys(LAYERS).map(k=>[k,true]));
try{Object.assign(enabled,JSON.parse(localStorage.getItem('gp.mapLayers')||'{}'));filter=localStorage.getItem('gp.mapFilter')||'all'}catch{}

const num=v=>{const n=Number(v);return Number.isFinite(n)?n:null};
function coords(x){
  if(!x||typeof x!=='object')return null;
  let lat=num(x.lat??x.latitude??x.lat_deg??x.coordinates?.lat??x.location?.lat??x.location?.latitude);
  let lon=num(x.lng??x.lon??x.longitude??x.long??x.coordinates?.lon??x.coordinates?.lng??x.location?.lon??x.location?.longitude);
  if((lat==null||lon==null)&&Array.isArray(x.coordinates)&&x.coordinates.length>=2){lon=num(x.coordinates[0]);lat=num(x.coordinates[1])}
  if((lat==null||lon==null)&&Array.isArray(x.geometry?.coordinates)&&x.geometry.coordinates.length>=2){lon=num(x.geometry.coordinates[0]);lat=num(x.geometry.coordinates[1])}
  return lat!=null&&lon!=null&&Math.abs(lat)<=90&&Math.abs(lon)<=180?[lat,lon]:null;
}
function flatten(value,source,out=[],seen=new WeakSet(),depth=0){
  if(value==null||typeof value!=='object'||depth>12||seen.has(value))return out;
  seen.add(value);
  if(Array.isArray(value)){for(const v of value)flatten(v,source,out,seen,depth+1);return out}
  const c=coords(value);if(c)out.push({...value,__lat:c[0],__lon:c[1],__source:source});
  for(const [k,v] of Object.entries(value))if(v&&typeof v==='object')flatten(v,source||k,out,seen,depth+1);
  return out;
}
function classify(p){
  const s=[p.layer,p.type,p.eventType,p.category,p.signal,p.sourceType,p.group,p.kind,p.title,p.name,p.detail,p.description,p.__source].filter(Boolean).join(' ').toLowerCase();
  if(/cartel|organized.?crime|narco|enforcer|gang/.test(s))return'cartel';
  if(/hazard|gdacs|earthquake|wildfire|flood|cyclone|hurricane|storm|landslide|drought|disaster/.test(s))return'hazards';
  if(/strategic|chokepoint|military.?base|infrastructure|flashpoint|strategic site/.test(s))return'strategic';
  if(/osint|regional intelligence|reporting|source|news|article/.test(s))return'osint';
  return'conflicts';
}
function unique(points){
  const seen=new Set();
  return points.filter(p=>{const key=String(p.id??p.eventId??p.mapId??p.sourceUrl??p.url??`${p.__lat.toFixed(4)},${p.__lon.toFixed(4)},${p.title??p.name??''}`);if(seen.has(key))return false;seen.add(key);return true});
}
function collect(){
  const s=getState();
  const sources=[];
  if(s.snapshot)sources.push(['snapshot',s.snapshot]);
  if(s.mapData?.events)sources.push(['events',s.mapData.events]);
  if(s.mapData?.regional)sources.push(['regional',s.mapData.regional]);
  if(s.mapData?.cartel)sources.push(['cartel',s.mapData.cartel]);
  if(s.mapData?.links)sources.push(['links',s.mapData.links]);
  if(mapData?.snapshot)sources.push(['live-snapshot',mapData.snapshot]);
  if(mapData?.events)sources.push(['live-events',mapData.events]);
  if(mapData?.regional)sources.push(['live-regional',mapData.regional]);
  if(mapData?.cartel)sources.push(['live-cartel',mapData.cartel]);
  if(mapData?.links)sources.push(['live-links',mapData.links]);
  if(mapData?.points)sources.push(['live-points',mapData.points]);
  return unique(sources.flatMap(([name,data])=>flatten(data,name))).filter(p=>coords(p));
}
function matches(p){
  const k=classify(p);if(!enabled[k])return false;if(filter!=='all'&&filter!==k&&!(filter==='conflict'&&k==='conflicts'))return false;
  if(!query)return true;
  return [p.title,p.name,p.location,p.country,p.region,p.city,p.detail,p.summary,p.description,p.source,p.type,p.layer,p.eventType].map(v=>String(v??'').toLowerCase()).join(' ').includes(query);
}
function controls(){
  const host=document.getElementById('mapContainer')?.parentElement;if(!host||document.getElementById('gpMapControls'))return;
  const box=document.createElement('div');box.id='gpMapControls';box.className='gp-map-mymaps-controls';
  box.innerHTML=`<div class="gp-map-toolbar"><button class="gp-map-tool" id="gpMapLayers">☰ Layers</button><button class="gp-map-tool" id="gpMapFit">◎ Fit all</button><button class="gp-map-tool" id="gpMapReset">↺ Reset</button><input id="gpMapSearch" class="gp-map-search" type="search" placeholder="Search places, events, countries…"><span id="gpMapCount" class="gp-map-count">0 signals</span></div><div id="gpMapLayerPanel" class="gp-map-layers-panel"><strong>MAP LAYERS</strong><div id="gpMapLayerRows"></div></div>`;
  host.insertBefore(box,document.getElementById('mapContainer'));
  const rows=box.querySelector('#gpMapLayerRows');
  for(const [k,m] of Object.entries(LAYERS)){
    const label=document.createElement('label');label.className='gp-map-layer-row';label.innerHTML=`<input type="checkbox" data-layer-check="${k}" ${enabled[k]?'checked':''}><span class="gp-map-layer-dot" style="background:${m.color}"></span><span>${m.icon} ${m.label}</span><b id="gpMapLayerCount-${k}">0</b>`;rows.appendChild(label);
    label.querySelector('input').onchange=e=>{enabled[k]=e.target.checked;localStorage.setItem('gp.mapLayers',JSON.stringify(enabled));renderMap()};
  }
  box.querySelector('#gpMapLayers').onclick=()=>box.querySelector('#gpMapLayerPanel').classList.toggle('open');
  box.querySelector('#gpMapFit').onclick=fitAll;
  box.querySelector('#gpMapReset').onclick=()=>{query='';filter='all';enabled=Object.fromEntries(Object.keys(LAYERS).map(k=>[k,true]));localStorage.removeItem('gp.mapLayers');localStorage.removeItem('gp.mapFilter');box.querySelector('#gpMapSearch').value='';box.querySelectorAll('[data-layer-check]').forEach(x=>x.checked=true);renderMap();fitAll()};
  box.querySelector('#gpMapSearch').oninput=e=>{query=e.target.value.trim().toLowerCase();renderMap()};
}
export function initMap(){
  const el=document.getElementById('mapContainer');if(!el||map||typeof L==='undefined')return;
  map=L.map(el,{center:CONFIG.mapDefaultCenter,zoom:CONFIG.mapDefaultZoom,worldCopyJump:true,preferCanvas:true,zoomControl:true});
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
  for(const k of Object.keys(LAYERS))groups[k]=L.layerGroup().addTo(map);
  controls();setTimeout(()=>map.invalidateSize(),100);
  map.on('click',closeDetail);
}
export async function loadMapData(){
  const bust=`?v=${Date.now()}`;
  const get=async key=>{try{const r=await fetch(`${CONFIG.endpoints[key]}${bust}`,{cache:'no-store'});return r.ok?await r.json():null}catch{return null}};
  const [snapshot,events,regional,cartel,links,points]=await Promise.all(['snapshot','mapEvents','mapRegional','mapCartel','mapLinks','mapPoints'].map(get));
  mapData={snapshot,events,regional,cartel,links,points};
  renderMap();
  return mapData;
}
export function renderMap(){
  if(!map)initMap();if(!map)return;
  for(const g of Object.values(groups))g.clearLayers();
  const points=collect().filter(matches).slice(0,5000);const counts=Object.fromEntries(Object.keys(LAYERS).map(k=>[k,0]));
  for(const p of points){const k=classify(p);counts[k]++;const m=LAYERS[k];const marker=L.circleMarker([p.__lat,p.__lon],{radius:10,color:'#fff',weight:2,fillColor:m.color,fillOpacity:1,opacity:1});marker.bindTooltip(String(p.title||p.name||p.location||m.label).slice(0,120),{direction:'top'});marker.on('click',e=>{e.originalEvent?.stopPropagation();showDetail(p)});groups[k].addLayer(marker)}
  const total=points.length;const count=document.getElementById('gpMapCount');if(count)count.textContent=`${total.toLocaleString()} signals`;
  for(const k of Object.keys(LAYERS)){const e=document.getElementById(`gpMapLayerCount-${k}`);if(e)e.textContent=counts[k].toLocaleString()}
  if(total)fitAll(points);else if(!mapData)loadMapData();
  setTimeout(()=>map.invalidateSize(),50);
}
function fitAll(points=collect().filter(matches)){if(!map||!points.length)return;map.fitBounds(L.latLngBounds(points.map(p=>[p.__lat,p.__lon])).pad(.08),{maxZoom:5,animate:false})}
function closeDetail(){const p=document.getElementById('mapSidePanel');if(p){p.style.display='none';p.innerHTML=''}selected=null}
function showDetail(p){closeDetail();selected=p;const panel=document.getElementById('mapSidePanel');if(!panel)return;const k=classify(p),m=LAYERS[k],title=p.title||p.name||p.location||'Map signal',detail=p.detail||p.summary||p.description||p.reason||'No additional detail available.',url=p.url||p.sourceUrl||p.source_url||'';panel.style.display='block';panel.innerHTML=`<div class="gp-map-detail-head"><span>${m.icon}</span><div><div class="gp-card-title">${escapeHtml(title)}</div><div class="gp-map-detail-type">${escapeHtml(m.label)}</div></div><button id="gpMapClose" class="gp-btn" type="button">×</button></div><div class="gp-map-detail-coords">${p.__lat.toFixed(4)}, ${p.__lon.toFixed(4)}</div><div class="gp-map-detail-text">${escapeHtml(String(detail).slice(0,1400))}</div>${p.source?`<div class="gp-map-detail-source">Source: ${escapeHtml(p.source)}</div>`:''}${/^https?:\/\//i.test(String(url))?`<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`:''}`;panel.querySelector('#gpMapClose').onclick=closeDetail}
