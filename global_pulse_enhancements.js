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
    renderEarlyWarning(d);
    if(!document.getElementById('gp-list-more-css')){const s=document.createElement('style');s.id='gp-list-more-css';s.textContent='.gp-list-more{display:block;width:100%;margin:10px 0 2px;padding:10px;border:1px solid var(--line);border-radius:9px;background:var(--panel2);color:var(--text);font-weight:700;cursor:pointer}.gp-list-more:hover{filter:brightness(1.15)}';document.head.appendChild(s)}
  }
  function renderEarlyWarning(d){
    let panel=document.getElementById('gp-early-warning');
    const wrap=document.querySelector('.wrap');if(!wrap)return;
    if(!panel){
      panel=document.createElement('section');panel.id='gp-early-warning';panel.className='panel wide';
      const anchor=document.getElementById('conflictSection')||document.getElementById('newsSection');
      wrap.insertBefore(panel,anchor||null);
    }
    const ew=d.earlyWarning||{};const level=String(ew.level||'WATCH').toUpperCase();const direction=String(ew.direction||'stable').toLowerCase();
    const arrow=direction==='rising'?'↑':direction==='falling'?'↓':'→';
    const cls=level==='HIGH'?'high':level==='ELEVATED'?'elevated':'watch';
    panel.innerHTML='<div class="section-head"><div><h2>EARLY WARNING</h2><div class="muted">Trend signal derived from recent Global Pulse snapshots — not a prediction.</div></div><div class="gp-ew-badge '+cls+'">'+esc(level)+'</div></div><div class="gp-ew-grid"><div><span class="muted">Current tension</span><strong>'+Math.round(n(ew.score||d.tension))+'</strong></div><div><span class="muted">Momentum</span><strong>'+arrow+' '+(n(ew.momentum)>0?'+':'')+n(ew.momentum).toFixed(1)+'</strong></div><div><span class="muted">Strongest driver</span><strong>'+esc(ew.strongestDriver||'—')+'</strong></div><div><span class="muted">Driver score</span><strong>'+Math.round(n(ew.strongestDriverScore))+'</strong></div></div><div class="muted gp-ew-method">'+esc(ew.method||'Waiting for trend history to accumulate.')+'</div>';
    if(!document.getElementById('gp-ew-css')){const s=document.createElement('style');s.id='gp-ew-css';s.textContent='#gp-early-warning{margin-bottom:12px}.gp-ew-badge{padding:6px 10px;border-radius:999px;font-size:10px;font-weight:900;letter-spacing:.08em}.gp-ew-badge.watch{background:rgba(98,160,255,.14);color:#62a0ff}.gp-ew-badge.elevated{background:rgba(255,200,87,.14);color:#ffc857}.gp-ew-badge.high{background:rgba(255,102,120,.14);color:#ff6678}.gp-ew-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.gp-ew-grid>div{border:1px solid var(--line);border-radius:10px;padding:10px;background:var(--panel2)}.gp-ew-grid span,.gp-ew-grid strong{display:block}.gp-ew-grid span{font-size:9px}.gp-ew-grid strong{margin-top:5px;font-size:15px}.gp-ew-method{margin-top:9px;font-size:9px}@media(max-width:620px){.gp-ew-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}';document.head.appendChild(s)}
  }
  function addStatus(){if(document.getElementById('gp-production-status'))return;const wrap=document.querySelector('.wrap');if(!wrap)return;const bar=document.createElement('div');bar.id='gp-production-status';bar.className='gp-statusbar';bar.innerHTML='<span class="gp-status-live"><i></i><strong>OPEN-DATA MONITOR</strong> <span>auto-checks every 60s</span></span><span>Dashboard initialized</span>';wrap.insertBefore(bar,wrap.firstElementChild)}
  function ready(){addStatus();applyCore()}
  document.addEventListener('globalpulse:dataready',applyCore);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else setTimeout(ready,0);
})();
