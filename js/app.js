/** Global Pulse — resilient application boot */
import { loadCoreData } from './core/fetch.js';
import { subscribe } from './core/state.js';
import { CONFIG } from './core/config.js';
import { renderOverview } from './modules/overview.js';
import { renderBreaking } from './modules/breaking.js';
import { renderConflicts } from './modules/conflicts.js';
import { renderIntelligenceBrain } from './modules/intelligence-brain.js';
import { renderIntelligenceWeb } from './modules/intelligence-web.js';
import { renderMarkets } from './modules/markets.js';
import { renderStatus } from './modules/status.js';
import { initMap, loadMapData, renderMap } from './modules/map.js';

function showModuleError(id, err) {
  const el=document.getElementById(id);
  if(!el)return;
  const message=String(err?.message||err||'Module failed to render').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]||c));
  el.innerHTML=`<div class="gp-state"><div class="gp-state-title">Temporarily unavailable</div><div>${message}</div></div>`;
}

function safeRender(label, fn, targetId) {
  try { fn(); }
  catch(err) { console.error(`Global Pulse render failed: ${label}`,err); showModuleError(targetId,err); }
}

function renderAll(){
  safeRender('overview',renderOverview,'overviewBody');
  safeRender('breaking',renderBreaking,'breakingBody');
  safeRender('conflicts',renderConflicts,'conflictsBody');
  safeRender('brain',renderIntelligenceBrain,'brainBody');
  safeRender('intelligence web',renderIntelligenceWeb,'intelweb');
  safeRender('markets',renderMarkets,'marketsBody');
  safeRender('status',renderStatus,'statusBody');
  safeRender('map',renderMap,'mapContainer');
}

function setupNav(){
  const items=document.querySelectorAll('.gp-nav-item');
  items.forEach(item=>item.addEventListener('click',()=>{items.forEach(i=>i.classList.remove('active'));item.classList.add('active')}));
  const sections=document.querySelectorAll('[data-section]');
  if(typeof IntersectionObserver==='undefined')return;
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){const id=entry.target.dataset.section;items.forEach(i=>i.classList.toggle('active',i.dataset.nav===id))}}),{threshold:.35});
  sections.forEach(s=>observer.observe(s));
}

async function refresh(force=false){
  const results=await Promise.allSettled([loadCoreData({force}),loadMapData()]);
  for(const result of results){if(result.status==='rejected')console.error('Global Pulse data refresh failed',result.reason)}
  renderAll();
}

async function boot(){
  setupNav();
  initMap();
  await refresh(true);
  subscribe(()=>renderAll());
  setInterval(()=>{
    if(document.visibilityState==='visible')refresh(false).catch(err=>console.error('Refresh failed',err));
  },CONFIG.refresh.snapshot);
  window.addEventListener('online',()=>refresh(true).catch(err=>console.error('Online refresh failed',err)));
  // Leaflet is loaded by a deferred CDN script. Retry map initialization after the module boot
  // so a slow CDN never prevents the rest of the dashboard from rendering.
  setTimeout(()=>{try{initMap();renderMap()}catch(err){console.error('Map retry failed',err)}},500);
}

boot().catch(err=>{
  console.error('Boot failed',err);
  renderAll();
});
