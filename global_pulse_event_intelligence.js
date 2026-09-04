(function(){'use strict';
const esc=v=>String(v??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
async function load(){
  try{
    const r=await fetch('data/event_intelligence.json?ts='+Date.now(),{cache:'no-store'}); if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json(); window.GP_EVENT_INTELLIGENCE=d;
    install();
  }catch(e){console.warn('Global Pulse event intelligence unavailable',e)}
}
function install(){
  if(document.getElementById('gp-event-intel')) return;
  const host=document.createElement('section'); host.id='gp-event-intel'; host.className='panel'; host.innerHTML='<div class="section-head"><div><h2>EVENT INTELLIGENCE</h2><div class="muted">Evidence, entities, timeline and regional context</div></div><span class="tag blue">RULE-BASED</span></div><div id="gp-ei-content"></div>';
  const target=document.querySelector('.wrap'); if(!target) return; target.appendChild(host); render();
}
function render(){
 const el=document.getElementById('gp-ei-content'), d=window.GP_EVENT_INTELLIGENCE||{}, events=Array.isArray(d.events)?d.events:[];
 if(!events.length){el.innerHTML='<div class="empty">No enriched events available yet.</div>';return}
 el.innerHTML=events.slice(0,12).map(e=>{
   const ent=(e.entityCandidates||[]).slice(0,5).map(x=>'<span class="tag amber">'+esc(x)+'</span>').join('');
   const reg=(e.regionalContext||[]).map(x=>'<span class="tag blue">'+esc(x.region)+'</span>').join('');
   const spill=(e.spilloverCandidates||[]).slice(0,4).map(x=>esc(x)).join(', ')||'None detected';
   const cave=(e.caveats||[]).slice(0,2).map(x=>'<li>'+esc(x)+'</li>').join('');
   const urls=(e.evidenceUrls||[]).slice(0,4).filter(Boolean).map(u=>'<a class="open" target="_blank" rel="noopener noreferrer" href="'+esc(u)+'">Source</a>').join('');
   return '<article class="item" style="margin-bottom:9px"><div><span class="tag '+(e.confidence==='high'?'green':e.confidence==='moderate'?'amber':'red')+'">'+esc(e.confidence||'unknown')+' confidence</span><span class="tag">'+esc(e.category||'general')+'</span></div><strong>'+esc(e.title||'Untitled event')+'</strong><div class="muted">'+Number(e.reportCount||0)+' reports · '+Number(e.uniqueSourceDomains||0)+' unique domains · source independence: '+esc(e.sourceIndependence||'unknown')+'</div><div style="margin-top:7px">'+ent+reg+'</div><div class="muted" style="margin-top:7px"><b>Spillover candidates:</b> '+spill+'</div><details style="margin-top:7px"><summary>Evidence & caveats</summary><div class="muted" style="margin-top:7px"><b>Source mix:</b> '+esc(Object.entries(e.sourceBreakdown||{}).map(x=>x[0]+' ('+x[1]+')').join(', ')||'None')+'</div><ul class="muted">'+cave+'</ul>'+urls+'</details></article>';
 }).join('');
}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',load); else load();
})();
