from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Idempotent: remove any previous Update 4 layer before rebuilding it.
s = re.sub(r'\n<style id="gp-analysis-css">.*?</style>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<section id="analysisCenter".*?</section>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<script id="gp-analysis-js">.*?</script>\n?', '\n', s, flags=re.S)

css = r'''
<style id="gp-analysis-css">
/* Global Pulse Update 4 — Intelligence Analysis Layer */
.analysis-panel{margin-top:14px}.analysis-grid{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:12px}.analysis-card{background:#08111b;border:1px solid var(--line);border-radius:11px;padding:12px;min-width:0}.analysis-card h3{margin:0 0 9px;font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}.analysis-lead{font-size:18px;font-weight:850;line-height:1.25;margin-bottom:7px}.analysis-copy{font-size:12px;color:#b9c9d8}.analysis-list{display:grid;gap:7px}.analysis-row{display:flex;justify-content:space-between;gap:10px;padding:8px 9px;background:#07101a;border:1px solid #172a3d;border-radius:8px}.analysis-row strong{font-size:11px}.analysis-row span{font-size:10px;color:var(--muted);text-align:right}.risk-meter{height:7px;background:#06101a;border:1px solid #172a3d;border-radius:99px;overflow:hidden;margin:6px 0}.risk-meter i{display:block;height:100%;background:linear-gradient(90deg,var(--green),var(--amber),var(--red));border-radius:99px}.analysis-tags{display:flex;gap:5px;flex-wrap:wrap}.analysis-tag{font-size:9px;text-transform:uppercase;letter-spacing:.07em;padding:4px 6px;border:1px solid #29445f;border-radius:6px;color:#b9cbe0;background:#081522}.analysis-tag.warn{border-color:rgba(255,102,120,.35);color:var(--red)}.analysis-tag.watch{border-color:rgba(255,200,87,.35);color:var(--amber)}.analysis-small{font-size:10px;color:var(--muted);margin-top:8px}.analysis-timeline{display:grid;gap:6px;max-height:290px;overflow:auto}.analysis-event{padding:8px;border-left:2px solid #315274;background:#07101a;border-radius:0 8px 8px 0}.analysis-event b{display:block;font-size:11px}.analysis-event span{display:block;font-size:9px;color:var(--muted);margin-top:2px}.analysis-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.analysis-actions button{font-size:10px;min-height:32px}.analysis-empty{font-size:11px;color:var(--muted);padding:12px;text-align:center;border:1px dashed #20364b;border-radius:8px}
@media(max-width:900px){.analysis-grid{grid-template-columns:1fr 1fr}.analysis-card:first-child{grid-column:span 2}}@media(max-width:720px){.analysis-grid{grid-template-columns:1fr}.analysis-card:first-child{grid-column:auto}.analysis-panel{margin-top:10px}}
</style>
'''
s = s.replace('</head>', css + '\n</head>', 1)

section = r'''
<section id="analysisCenter" class="panel analysis-panel">
  <div class="section-head">
    <div><h2>Intelligence Analysis</h2><div class="muted">Escalation trends, flashpoints, actors and early-warning signals derived from the current reporting set.</div></div>
    <span class="tag blue">ANALYTICAL LAYER</span>
  </div>
  <div class="analysis-grid">
    <div class="analysis-card" id="analysisLead"></div>
    <div class="analysis-card" id="analysisFlashpoints"></div>
    <div class="analysis-card" id="analysisPosture"></div>
    <div class="analysis-card" id="analysisChanges"></div>
    <div class="analysis-card" id="analysisActors"></div>
    <div class="analysis-card" id="analysisTimeline"></div>
  </div>
</section>
'''

s = s.replace('</main>', section + '\n</main>', 1)

js = r'''
<script id="gp-analysis-js">
/* Global Pulse Update 4 — analytical layer; no invented facts */
(function(){
  const esc = v => String(v ?? '').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const data = window.DATA || {};
  const conflicts = Array.isArray(data.conflicts) ? data.conflicts : [];
  const stories = Array.isArray(data.stories) ? data.stories : [];
  const history = Array.isArray(data.history) ? data.history : [];
  const byScore = conflicts.slice().sort((a,b)=>(Number(b.activityScore)||0)-(Number(a.activityScore)||0));
  const active = conflicts.filter(c=>Number(c.activityScore||0)>=60);
  const critical = conflicts.filter(c=>String(c.escalation||'').toUpperCase()==='CRITICAL');
  const regions = {};
  conflicts.forEach(c=>{const r=c.region||'Other';(regions[r]??=[]).push(c)});
  const recentStories = stories.slice().sort((a,b)=>new Date(b.time||0)-new Date(a.time||0)).slice(0,8);

  function el(id){return document.getElementById(id)}
  function level(n){return n>=80?'HIGH':n>=60?'ELEVATED':n>=40?'WATCH':'LOW'}
  function score(c){return Math.round(Number(c.activityScore)||0)}
  function delta(c){return Number(c.delta)||0}
  function sourceCount(c){return Number(c.sourceCount)||0}

  // Lead assessment: descriptive, not predictive.
  const lead = el('analysisLead');
  if(lead){
    const top = byScore[0];
    const avg = conflicts.length ? Math.round(conflicts.reduce((s,c)=>s+score(c),0)/conflicts.length) : 0;
    const rising = conflicts.filter(c=>delta(c)>0).sort((a,b)=>delta(b)-delta(a)).slice(0,3);
    lead.innerHTML = `<h3>Current Assessment</h3><div class="analysis-lead">${esc(top?top.name:'No active theater data')}</div><div class="analysis-copy">Highest current reporting activity. Global tension signal is <b>${Math.round(Number(data.tension)||0)}</b>; theater average is <b>${avg}</b>.</div><div class="analysis-tags" style="margin-top:9px"><span class="analysis-tag ${critical.length?'warn':'watch'}">${critical.length} critical</span><span class="analysis-tag">${active.length} elevated+ theaters</span><span class="analysis-tag">${conflicts.length} monitored</span></div><div class="analysis-small">This is an activity assessment based on reporting signals, not a prediction of battlefield outcomes.</div>${rising.length?`<div class="analysis-small"><b>Rising signals:</b> ${rising.map(c=>esc(c.name)+' +'+Math.round(delta(c))).join(' · ')}</div>`:''}`;
  }

  const fp = el('analysisFlashpoints');
  if(fp){
    fp.innerHTML = `<h3>Flashpoints</h3><div class="analysis-list">${byScore.slice(0,5).map(c=>`<div class="analysis-row"><div><strong>${esc(c.name)}</strong><div class="risk-meter"><i style="width:${Math.max(0,Math.min(100,score(c)))}%"></i></div></div><span>${score(c)}<br>${esc(level(score(c)))}</span></div>`).join('') || '<div class="analysis-empty">No conflict signals available.</div>'}</div>`;
  }

  const posture = el('analysisPosture');
  if(posture){
    const bd = data.breakdownScores || {};
    const keys = ['Military posture','Diplomatic strain','Economic pressure','Market volatility'];
    posture.innerHTML = `<h3>Strategic Posture</h3><div class="analysis-list">${keys.map(k=>`<div class="analysis-row"><strong>${esc(k)}</strong><span>${Math.round(Number(bd[k])||0)}</span></div>`).join('')}</div><div class="analysis-small">Posture dimensions are analytical composites from the current source set.</div>`;
  }

  const changes = el('analysisChanges');
  if(changes){
    const rising = conflicts.filter(c=>delta(c)!==0).sort((a,b)=>Math.abs(delta(b))-Math.abs(delta(a))).slice(0,6);
    changes.innerHTML = `<h3>What Changed</h3><div class="analysis-list">${rising.map(c=>`<div class="analysis-row"><strong>${esc(c.name)}</strong><span>${delta(c)>0?'+':''}${Math.round(delta(c))}</span></div>`).join('') || '<div class="analysis-empty">No theater score changes in the latest refresh.</div>'}</div><div class="analysis-small">Change values compare the latest theater activity signal with the prior stored score when available.</div>`;
  }

  const actors = el('analysisActors');
  if(actors){
    const counts = {};
    conflicts.forEach(c=>(Array.isArray(c.signals)?c.signals:[]).forEach(s=>(Array.isArray(s.match)?s.match:[]).forEach(x=>{const k=String(x).trim();if(k.length>=4)counts[k]=(counts[k]||0)+1})));
    const topActors = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,10);
    actors.innerHTML = `<h3>Actor / Keyword Signals</h3><div class="analysis-list">${topActors.map(([k,n])=>`<div class="analysis-row"><strong>${esc(k)}</strong><span>${n} linked signals</span></div>`).join('') || '<div class="analysis-empty">No actor signals available.</div>'}</div><div class="analysis-small">These are extracted signal keywords from source matching, not confirmed actor attribution.</div>`;
  }

  const tl = el('analysisTimeline');
  if(tl){
    const ev = recentStories;
    tl.innerHTML = `<h3>Recent Signal Timeline</h3><div class="analysis-timeline">${ev.map(s=>`<div class="analysis-event"><b>${esc(s.title||'Untitled report')}</b><span>${esc(s.source||'Source')} · ${esc(s.time||'Time unavailable')}</span></div>`).join('') || '<div class="analysis-empty">No recent reporting available.</div>'}</div>`;
  }

  // Region watch chips: lightweight cross-navigation into the existing conflict filter.
  const head = document.querySelector('#analysisCenter .section-head');
  if(head && !document.getElementById('analysisRegionTools')){
    const box=document.createElement('div'); box.id='analysisRegionTools'; box.className='analysis-actions';
    Object.entries(regions).sort((a,b)=>b[1].length-a[1].length).slice(0,6).forEach(([region,items])=>{
      const b=document.createElement('button'); b.className='filter'; b.textContent=region+' · '+items.length;
      b.onclick=()=>{const target=document.querySelector('.ccard[data-region="'+CSS.escape(region)+'"]'); if(target){target.scrollIntoView({behavior:'smooth',block:'center'});target.click();}else document.getElementById('conflicts')?.scrollIntoView({behavior:'smooth'});};
      box.appendChild(b);
    });
    head.appendChild(box);
  }
})();
</script>
'''
s = s.replace('</body>', js + '\n</body>', 1)
p.write_text(s, encoding='utf-8')
print('Update 4 analysis layer applied')
