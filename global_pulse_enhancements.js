/* Global Pulse — stable UI enhancement layer. */
(function(){
  'use strict';
  const esc=v=>String(v==null?'':v).replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
  const n=v=>Number.isFinite(Number(v))?Number(v):0;
  function applyCore(){
    const d=window.DATA||{};
    const score=n(d.tension??d.globalIndex??d.globalTension??d.score);
    const scoreEl=document.getElementById('globalScore'); if(scoreEl)scoreEl.textContent=Math.round(score);
    const delta=document.getElementById('globalDelta'); if(delta)delta.textContent=score>=70?'Elevated global pressure':score>=45?'Moderate global pressure':'Lower global pressure';
    const b=d.breakdownScores||d.breakdown||d.tensionBreakdown||d.drivers||{};
    const keys=[['Conflict activity','Conflict activity','conflictActivity','conflict_activity'],['Diplomatic strain','Diplomatic strain','diplomaticStrain','diplomatic_strain'],['Economic pressure','Economic pressure','economicPressure','economic_pressure'],['Market volatility','Market volatility','marketVolatility','market_volatility'],['Military posture','Military posture','militaryPosture','military_posture']];
    document.querySelectorAll('#breakdown .bar').forEach((row,i)=>{let v=0;for(const k of keys[i])if(b[k]!=null){v=n(b[k]);break}v=Math.max(0,Math.min(100,v));const fill=row.querySelector('.fill'),val=row.querySelector('b');if(fill)fill.style.width=v+'%';if(val)val.textContent=Math.round(v)});
    const conflicts=Array.isArray(d.conflicts)?d.conflicts:[];
    const list=document.getElementById('conflictList');
    if(list){list.innerHTML=conflicts.slice(0,30).map((c,i)=>{const s=Math.max(0,Math.min(100,n(c.score??c.tension??c.priority)));return '<article class="ccard"><span class="tag red">'+esc(c.status||c.severity||'MONITOR')+'</span><h3>'+esc(c.name||c.title||c.conflict||('Conflict '+(i+1)))+'</h3><div class="muted">'+esc(c.region||c.location||'Global')+'</div><div class="scoreline"><span>Tension</span><b>'+Math.round(s)+'</b></div><div class="track"><div class="fill" style="width:'+s+'%"></div></div></article>'}).join('')||'<div class="empty">No active conflict records in the current snapshot.</div>'}
    const cc=document.getElementById('conflictCount');if(cc)cc.textContent=conflicts.length;
    const sc=document.getElementById('storyCount');if(sc)sc.textContent=Array.isArray(d.stories)?d.stories.length:0;
    const mc=document.getElementById('markerCount');if(mc)mc.textContent=Array.isArray(d.markers)?d.markers.length:0;
  }
  function addStatus(){
    if(document.getElementById('gp-production-status'))return;
    const wrap=document.querySelector('.wrap');if(!wrap)return;
    const bar=document.createElement('div');bar.id='gp-production-status';bar.className='gp-statusbar';
    bar.innerHTML='<span class="gp-status-live"><i></i><strong>OPEN-DATA MONITOR</strong> <span>auto-checks every 60s</span></span><span>Dashboard initialized</span>';
    wrap.insertBefore(bar,wrap.firstElementChild);
  }
  function ready(){addStatus();applyCore()}
  document.addEventListener('globalpulse:dataready',applyCore);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else setTimeout(ready,0);
})();
