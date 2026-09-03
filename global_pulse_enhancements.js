/* Global Pulse — stable UI enhancement layer. */
(function(){
  'use strict';
  const esc=v=>String(v==null?'':v).replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
  const n=v=>Number.isFinite(Number(v))?Number(v):0;
  function applyCore(){
    const d=window.DATA||{};
    const score=n(d.tension??d.globalIndex??d.globalTension??d.score);
    const scoreEl=document.getElementById('globalScore');if(scoreEl)scoreEl.textContent=Math.round(score);
    const delta=document.getElementById('globalDelta');if(delta)delta.textContent=score>=70?'Elevated global pressure':score>=45?'Moderate global pressure':'Lower global pressure';
    const b=d.breakdownScores||d.breakdown||d.tensionBreakdown||d.drivers||{};
    const keys=[['Conflict activity','conflictActivity','conflict_activity'],['Diplomatic strain','diplomaticStrain','diplomatic_strain'],['Economic pressure','economicPressure','economic_pressure'],['Market volatility','marketVolatility','market_volatility'],['Military posture','militaryPosture','military_posture']];
    document.querySelectorAll('#breakdown .bar').forEach((row,i)=>{if(!keys[i])return;let v=0;for(const k of keys[i])if(b[k]!=null){v=n(b[k]);break}v=Math.max(0,Math.min(100,v));const fill=row.querySelector('.fill'),val=row.querySelector('b');if(fill)fill.style.width=v+'%';if(val)val.textContent=Math.round(v)});
    const conflicts=Array.isArray(d.conflicts)?d.conflicts:[];
    const list=document.getElementById('conflictList');
    if(list){let expanded=list.dataset.expanded==='true';const visible=expanded?conflicts.slice(0,30):conflicts.slice(0,5);list.innerHTML=visible.map((c,i)=>{const s=Math.max(0,Math.min(100,n(c.activityScore??c.score??c.tension??c.priority)));const sev=String(c.escalation||c.severity||c.status||'MONITOR');return '<article class="ccard" tabindex="0"><span class="tag red">'+esc(sev)+'</span><h3>'+esc(c.name||c.title||c.conflict||('Conflict '+(i+1)))+'</h3><div class="muted">'+esc(c.region||c.location||'Global')+' · '+esc(c.confidence||'OPEN-DATA SIGNAL')+'</div><div class="scoreline"><span>Activity signal</span><b>'+Math.round(s)+'</b></div><div class="track"><div class="fill" style="width:'+s+'%"></div></div><div class="muted" style="margin-top:7px">'+esc(c.recent||'Current reporting signal')+'</div></article>'}).join('');if(conflicts.length>5){const btn=document.createElement('button');btn.className='gp-list-more';btn.type='button';btn.textContent=expanded?'Show Less ↑':'See More ('+conflicts.length+') ↓';btn.onclick=()=>{list.dataset.expanded=expanded?'false':'true';applyCore()};list.appendChild(btn)}if(!visible.length)list.innerHTML='<div class="empty">No active conflict records in the current snapshot.</div>'}
    const cc=document.getElementById('conflictCount');if(cc)cc.textContent=conflicts.length;
    const sc=document.getElementById('storyCount');if(sc)sc.textContent=Array.isArray(d.stories)?d.stories.length:0;
    const mc=document.getElementById('markerCount');if(mc)mc.textContent=Array.isArray(d.markers)?d.markers.length:0;
    if(!document.getElementById('gp-list-more-css')){const s=document.createElement('style');s.id='gp-list-more-css';s.textContent='.gp-list-more{display:block;width:100%;margin:10px 0 2px;padding:10px;border:1px solid var(--line);border-radius:9px;background:var(--panel2);color:var(--text);font-weight:700;cursor:pointer}.gp-list-more:hover{filter:brightness(1.15)}';document.head.appendChild(s)}
  }
  function addStatus(){if(document.getElementById('gp-production-status'))return;const wrap=document.querySelector('.wrap');if(!wrap)return;const bar=document.createElement('div');bar.id='gp-production-status';bar.className='gp-statusbar';bar.innerHTML='<span class="gp-status-live"><i></i><strong>OPEN-DATA MONITOR</strong> <span>auto-checks every 60s</span></span><span>Dashboard initialized</span>';wrap.insertBefore(bar,wrap.firstElementChild)}
  function ready(){addStatus();applyCore()}
  document.addEventListener('globalpulse:dataready',applyCore);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else setTimeout(ready,0);
})();
