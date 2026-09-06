/** Global Pulse — Application boot */
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
import { initMap, renderMap } from './modules/map.js';

function renderAll(){
  renderOverview(); renderBreaking(); renderConflicts(); renderIntelligenceBrain(); renderIntelligenceWeb(); renderMarkets(); renderStatus(); renderMap();
}
function setupNav(){
  const items=document.querySelectorAll('.gp-nav-item');
  items.forEach(item=>item.addEventListener('click',()=>{items.forEach(i=>i.classList.remove('active'));item.classList.add('active');}));
  const sections=document.querySelectorAll('[data-section]');
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){const id=entry.target.dataset.section;items.forEach(i=>i.classList.toggle('active',i.dataset.nav===id));}}),{threshold:0.35});
  sections.forEach(s=>observer.observe(s));
}
async function boot(){
  setupNav(); initMap(); await loadCoreData({force:true}); renderAll(); subscribe(()=>renderAll());
  setInterval(async()=>{if(document.visibilityState==='visible'){await loadCoreData({force:false});renderAll();}},CONFIG.refresh.snapshot);
  window.addEventListener('online',()=>loadCoreData({force:true}));
}
boot().catch(err=>{console.error('Boot failed',err);const target=document.getElementById('overviewBody');if(target)target.innerHTML=`<div class="gp-state"><div class="gp-state-title">Failed to start</div><div>${String(err.message||'Unknown error').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</div></div>`;});
