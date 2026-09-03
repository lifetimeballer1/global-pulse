from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Idempotent cleanup of any previous Update 3 injection.
s=re.sub(r'<style id="gp-evidence-css">.*?</style>','',s,flags=re.S)
s=re.sub(r'<script id="gp-evidence-js">.*?</script>','',s,flags=re.S)
s=re.sub(r'<section id="evidenceCenter".*?</section>','',s,flags=re.S)

css='''<style id="gp-evidence-css">
/* Global Pulse Update 3 — OSINT & Evidence Center */
.evidence-panel{margin-top:14px}.evidence-grid{display:grid;grid-template-columns:1.05fr 1.4fr 1fr;gap:12px}.evidence-card{background:#08111b;border:1px solid var(--line);border-radius:11px;padding:12px;min-width:0}.evidence-card h3{margin:0 0 9px;font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}.evidence-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.evidence-kpi{padding:9px;border:1px solid var(--line);border-radius:9px;background:#091622}.evidence-kpi b{display:block;font-size:19px}.evidence-kpi span{display:block;color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.08em}.evidence-list{display:grid;gap:7px;max-height:390px;overflow:auto}.evidence-row{padding:9px;border:1px solid var(--line);border-radius:9px;background:#091521}.evidence-row strong{display:block;font-size:11px;line-height:1.35}.evidence-meta{font-size:9px;color:var(--muted);margin-top:4px}.evidence-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.evidence-link{display:inline-block;padding:5px 7px;border:1px solid rgba(98,160,255,.3);border-radius:6px;color:var(--blue);font-size:9px}.evidence-state{font-size:9px;font-weight:850;letter-spacing:.06em;padding:3px 5px;border-radius:5px;display:inline-block;margin-bottom:5px}.evidence-state.verified{color:var(--green);background:rgba(72,223,131,.1)}.evidence-state.multi{color:var(--blue);background:rgba(98,160,255,.1)}.evidence-state.unverified{color:var(--amber);background:rgba(255,200,87,.1)}.evidence-state.map{color:#e0ad54;background:rgba(224,173,84,.1)}.evidence-bar{height:7px;background:#06101a;border:1px solid #142334;border-radius:99px;overflow:hidden}.evidence-bar i{display:block;height:100%;background:linear-gradient(90deg,var(--red),var(--amber),var(--green))}.evidence-note{font-size:10px;color:var(--muted);line-height:1.5;margin:8px 0 0}.evidence-filter{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px}.evidence-filter button{min-height:30px;padding:5px 8px;font-size:9px}.evidence-timeline{position:relative;padding-left:15px}.evidence-timeline:before{content:"";position:absolute;left:4px;top:3px;bottom:3px;width:1px;background:#29445f}.evidence-event{position:relative;padding:0 0 11px 8px}.evidence-event:before{content:"";position:absolute;left:-14px;top:4px;width:7px;height:7px;border-radius:50%;background:var(--blue);box-shadow:0 0 0 3px rgba(98,160,255,.1)}.evidence-event b{font-size:10px}.evidence-event div{font-size:9px;color:var(--muted);margin-top:2px}.contradiction{border-left:2px solid var(--amber)}
@media(max-width:1050px){.evidence-grid{grid-template-columns:1fr 1fr}.evidence-card:last-child{grid-column:span 2}}@media(max-width:720px){.evidence-grid{grid-template-columns:1fr}.evidence-card:last-child{grid-column:auto}.evidence-kpis{grid-template-columns:repeat(3,1fr)}.evidence-list{max-height:330px}}
</style>'''
s=s.replace('</head>',css+'\n</head>',1)

section='''<section class="panel evidence-panel" id="evidenceCenter">
<div class="section-head"><div><h2>OSINT &amp; Evidence Center</h2><div class="muted">Provenance-first view of public reporting and source-map signals. Reported does not mean verified.</div></div><span class="tag amber">EVIDENCE LAYER</span></div>
<div class="evidence-grid">
<div class="evidence-card"><h3>Evidence posture</h3><div class="evidence-kpis"><div class="evidence-kpi"><b id="evTotal">—</b><span>Signals</span></div><div class="evidence-kpi"><b id="evSources">—</b><span>Sources</span></div><div class="evidence-kpi"><b id="evUnverified">—</b><span>Unverified</span></div></div><p class="evidence-note" id="evNote">Loading provenance data…</p></div>
<div class="evidence-card"><h3>Recent evidence</h3><div class="evidence-filter"><button class="filter active" data-evfilter="all">All</button><button class="filter" data-evfilter="osint">OSINT</button><button class="filter" data-evfilter="news">Reporting</button></div><div class="evidence-list" id="evidenceList"></div></div>
<div class="evidence-card"><h3>Verification &amp; timeline</h3><div id="verificationBars"></div><div class="drawer-section" style="margin-top:10px"><div class="label">Latest signal timeline</div><div class="evidence-timeline" id="evidenceTimeline"></div></div></div>
</div></section>'''
s=s.replace('</main>',section+'\n</main>',1)

js=r'''<script id="gp-evidence-js">
/* Global Pulse Update 3 — provenance and evidence UI */
(function(){
 const esc3=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
 const url3=v=>{try{const u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch{return ''}};
 const allMarkers=()=>Array.isArray(window.DATA?.markers)?window.DATA.markers:[];
 const allStories=()=>Array.isArray(window.DATA?.stories)?window.DATA.stories:[];
 let mode='all';
 function state(m){const c=String(m?.confidence||'').toLowerCase(),s=String(m?.source||m?.sourceLabel||'').toLowerCase();if(/source map|global war news map/.test(s)||/source map/.test(c))return['map','SOURCE-MAP / UNVERIFIED'];if(/corroborated|verified/.test(c))return['verified','CORROBORATED'];if(/multi-source/.test(c))return['multi','MULTI-SOURCE'];return['unverified','UNVERIFIED / REPORTED'];}
 function render(){
  const markers=allMarkers(),stories=allStories();
  const total=markers.length+stories.length;const sourceSet=new Set([...markers.map(x=>x.sourceLabel||x.source||''),...stories.map(x=>x.sourceLabel||x.source||'')].filter(Boolean));
  const unv=markers.length+stories.filter(x=>String(x.confidence||'').toLowerCase().includes('single')).length;
  const a=document.getElementById('evTotal'),b=document.getElementById('evSources'),c=document.getElementById('evUnverified');if(a)a.textContent=total;b.textContent=sourceSet.size;c.textContent=unv;
  const note=document.getElementById('evNote');if(note)note.textContent='OSINT map reports are retained as unverified source signals. News is evidence of reporting, not automatic confirmation.';
  const rows=[];
  markers.slice().sort((a,b)=>new Date(b.timestamp||b.time||0)-new Date(a.timestamp||a.time||0)).slice(0,40).forEach(m=>{const [cls,label]=state(m);rows.push({kind:'osint',time:m.timestamp||m.time,title:m.title||'Map report',source:m.sourceLabel||m.source||'Global War News Map',detail:m.detail||m.description||'Source-map point; independent corroboration pending.',url:m.url||m.sourceUrl,cls,label});});
  stories.slice().sort((a,b)=>new Date(b.time||0)-new Date(a.time||0)).slice(0,40).forEach(x=>{const [cls,label]=state(x);rows.push({kind:'news',time:x.time,title:x.title,source:x.sourceLabel||x.source||'Public feed',detail:x.summary||'Public reporting signal.',url:x.source,cls,label});});
  rows.sort((a,b)=>new Date(b.time||0)-new Date(a.time||0));
  const visible=rows.filter(x=>mode==='all'||x.kind===mode).slice(0,18);
  document.getElementById('evidenceList').innerHTML=visible.length?visible.map(x=>`<article class="evidence-row"><span class="evidence-state ${x.cls}">${esc3(x.label)}</span><strong>${esc3(x.title)}</strong><div class="evidence-meta">${esc3(x.source)} · ${esc3(x.time||'Time unavailable')}</div><div class="evidence-meta">${esc3(x.detail)}</div>${url3(x.url)?`<div class="evidence-actions"><a class="evidence-link" href="${esc3(url3(x.url))}" target="_blank" rel="noopener noreferrer">Open source ↗</a></div>`:''}</article>`).join(''):'<div class="empty">No evidence matches this filter.</div>';
  const counts={verified:0,multi:0,unverified:0,map:markers.length};stories.forEach(x=>counts[state(x)[0]]++);const denom=Math.max(1,stories.length+markers.length);document.getElementById('verificationBars').innerHTML=[['Corroborated',counts.verified,'verified'],['Multi-source',counts.multi,'multi'],['Unverified reporting',counts.unverified,'unverified'],['Source-map reports',counts.map,'map']].map(x=>`<div style="margin:7px 0"><div class="scoreline"><span>${x[0]}</span><b>${x[1]}</b></div><div class="evidence-bar"><i style="width:${Math.min(100,x[1]/denom*100)}%"></i></div></div>`).join('')+'<p class="evidence-note">Verification labels describe the evidence available to Global Pulse, not the truth of an event.</p>';
  const timeline=rows.slice(0,8);document.getElementById('evidenceTimeline').innerHTML=timeline.length?timeline.map(x=>`<div class="evidence-event"><b>${esc3(x.title)}</b><div>${esc3(x.source)} · ${esc3(x.time||'Time unavailable')}</div></div>`).join(''):'<div class="empty">No recent evidence.</div>';
 }
 function boot(){document.querySelectorAll('[data-evfilter]').forEach(b=>b.onclick=()=>{mode=b.dataset.evfilter;document.querySelectorAll('[data-evfilter]').forEach(x=>x.classList.toggle('active',x===b));render()});render()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,350));else setTimeout(boot,350);
})();
</script>'''
s=s.replace('</body>',js+'\n</body>',1)
p.write_text(s,encoding='utf-8')
print('Update 3 evidence center installed')