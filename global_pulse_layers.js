/* Global Pulse — standalone politics/economics intelligence dashboard. */
(function(){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const safe=v=>{try{const u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch{return ''}};
  let mode='all',query='',evidence='all';
  const label={'us-politics':'U.S. POLITICS','world-politics':'WORLD POLITICS','economics':'ECONOMICS'};
  function addStyles(){if(document.getElementById('gp-pintel-css'))return;const s=document.createElement('style');s.id='gp-pintel-css';s.textContent='.gp-pintel-stats{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 11px}.gp-pintel-stats span{padding:7px 9px;border:1px solid var(--line);border-radius:8px;background:var(--panel2);font-size:10px;color:var(--muted)}.gp-pintel-stats b{color:var(--text);margin-right:3px}.gp-pintel-controls{display:grid;gap:8px;margin-bottom:11px}.gp-pintel-filters{display:flex;gap:7px}.gp-pintel-filters input{flex:1;min-width:0}.gp-pintel-filters select{border:1px solid var(--line);background:#09121c;color:var(--text);border-radius:9px;padding:8px 10px;min-height:36px}.gp-pintel-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;max-height:720px;overflow:auto;padding-right:2px}.gp-pintel-card{background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:11px;min-width:0}.gp-pintel-card h3{margin:3px 0 5px;font-size:13px;line-height:1.3}.gp-pintel-meta{display:flex;gap:4px;align-items:center;flex-wrap:wrap}.gp-pintel-time{font-size:9px;color:var(--muted);margin-left:auto}.gp-pintel-tags{display:flex;gap:4px;flex-wrap:wrap;margin-top:7px}.gp-pintel-tags span{font-size:8px;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:2px 5px}.gp-pintel-evidence{margin-top:8px;padding:7px 8px;border-left:2px solid var(--green);background:#07111a;font-size:9px;color:var(--muted);line-height:1.4}.gp-pintel-evidence b{color:var(--text)}@media(max-width:720px){.gp-pintel-grid{grid-template-columns:1fr;max-height:none}.gp-pintel-filters{align-items:stretch}.gp-pintel-filters select{width:145px}.gp-pintel-time{margin-left:0}}';document.head.appendChild(s)}
  function rows(){
    const pi=window.DATA?.politicalIntelligence;
    let a=Array.isArray(pi?.topSignals)?pi.topSignals:[];
    if(mode==='economics'){
      const all=Array.isArray(window.DATA?.stories)?window.DATA.stories:[];
      a=all.filter(s=>s.intelligenceLayer==='economics'||String(s.sourceLabel||'').toLowerCase().includes('economics')).sort((x,y)=>new Date(y.time||0)-new Date(x.time||0));
    }else if(!a.length){
      const all=Array.isArray(window.DATA?.stories)?window.DATA.stories:[];
      a=all.filter(s=>s.intelligenceLayer==='us-politics'||s.intelligenceLayer==='world-politics').sort((x,y)=>new Date(y.time||0)-new Date(x.time||0));
    }
    return a.filter(s=>{
      const text=`${s.title||''} ${s.summary||''} ${s.sourceLabel||''} ${(s.politicalTopics||[]).join(' ')}`.toLowerCase();
      return(mode==='all'||s.intelligenceLayer===mode||mode==='economics'&&s.intelligenceLayer==='economics')&&(!query||text.includes(query))&&(evidence==='all'||(evidence==='corroborated'?s.evidenceLevel==='CORROBORATED':s.evidenceLevel!=='CORROBORATED'))
    });
  }
  function card(s){const url=safe(s.source||s.url),cor=s.evidenceLevel==='CORROBORATED',topics=(s.politicalTopics||[]).slice(0,3),entities=(s.politicalEntities||[]).slice(0,4);return `<article class="gp-pintel-card"><div class="gp-pintel-meta"><span class="tag ${s.intelligenceLayer==='us-politics'?'green':s.intelligenceLayer==='economics'?'amber':'blue'}">${esc(label[s.intelligenceLayer]||'POLITICS')}</span><span class="tag ${cor?'green':'amber'}">${cor?'CORROBORATED':'SINGLE-SOURCE'}</span>${s.breaking?'<span class="tag red">BREAKING</span>':''}<span class="gp-pintel-time">${esc(s.time||'')}</span></div><a class="story-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer"><h3>${esc(s.title)}</h3></a><div class="source">${esc(s.sourceLabel||s.sourceName||'Public source')}</div><p class="muted">${esc(s.summary||'')}</p><div class="gp-pintel-tags">${topics.map(x=>`<span>${esc(x)}</span>`).join('')}${entities.map(x=>`<span>${esc(x)}</span>`).join('')}</div>${cor?`<div class="gp-pintel-evidence"><b>Independent coverage:</b> ${esc((s.corroboratingSources||[]).join(' · '))}</div>`:'<div class="gp-pintel-evidence">No independent matching report found in the current 24-hour window.</div>'}${url?`<a class="open" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`:''}</article>`}
  function render(root){const a=rows(),pi=window.DATA?.politicalIntelligence||{},grid=root.querySelector('#gpPintelGrid');if(!grid)return;grid.innerHTML=a.slice(0,50).map(card).join('')||'<div class="empty">No signals match these filters. The feed may be between refresh cycles.</div>';const count=root.querySelector('#gpPintelCount');if(count)count.textContent=`${a.length} signals`;const stats=root.querySelector('#gpPintelStats');if(stats)stats.innerHTML=`<span><b>${pi.usPoliticsSignals??a.filter(x=>x.intelligenceLayer==='us-politics').length}</b> U.S.</span><span><b>${pi.worldPoliticsSignals??a.filter(x=>x.intelligenceLayer==='world-politics').length}</b> World</span><span><b>${a.filter(x=>x.intelligenceLayer==='economics').length}</b> Economics</span><span><b>${pi.corroboratedSignals??a.filter(x=>x.evidenceLevel==='CORROBORATED').length}</b> corroborated</span>`}
  function removeLegacy(){
    const brief=document.getElementById('gpBrief');
    if(brief)brief.remove();
    const watch=document.getElementById('gpWatchlistItems');
    if(watch){const parent=watch.closest('.gp-watchlist');if(parent)parent.remove()}
  }
  function boot(){
    addStyles();
    removeLegacy();
    if(document.getElementById('gp-political-intelligence'))return true;
    const wrap=document.querySelector('.wrap');if(!wrap||!window.DATA)return false;
    const sec=document.createElement('section');sec.className='panel wide';sec.id='gp-political-intelligence';
    sec.innerHTML=`<div class="section-head"><div><h2>POLITICAL & ECONOMIC REPORTING</h2><div class="muted">Automatic source aggregation for U.S. politics, world politics and economics.</div></div><span class="gp-layer-count" id="gpPintelCount">— signals</span></div><div class="gp-pintel-stats" id="gpPintelStats"></div><div class="gp-pintel-controls"><div class="gp-layer-tabs"><button class="filter active" data-pintel="all">All</button><button class="filter" data-pintel="us-politics">U.S. Politics</button><button class="filter" data-pintel="world-politics">World Politics</button><button class="filter" data-pintel="economics">Economics</button></div><div class="gp-pintel-filters"><input id="gpPintelSearch" placeholder="Search people, countries, issues…" aria-label="Search political and economic reporting"><select id="gpPintelEvidence"><option value="all">All evidence levels</option><option value="corroborated">Corroborated</option><option value="developing">Developing / single-source</option></select></div></div><div class="gp-pintel-grid" id="gpPintelGrid"></div><div class="gp-layer-note">Sources are displayed as reporting signals, not automatically accepted as fact. “Corroborated” means independent domains produced sufficiently similar reports within the current time window; it does not prove every claim is true.</div>`;
    const conflict=document.getElementById('conflictSection'),report=document.getElementById('reporting');if(conflict)conflict.after(sec);else if(report)report.before(sec);else wrap.appendChild(sec);
    sec.querySelectorAll('[data-pintel]').forEach(b=>b.onclick=()=>{sec.querySelectorAll('[data-pintel]').forEach(x=>x.classList.remove('active'));b.classList.add('active');mode=b.dataset.pintel;render(sec)});
    sec.querySelector('#gpPintelSearch').oninput=e=>{query=e.target.value.toLowerCase().trim();render(sec)};
    sec.querySelector('#gpPintelEvidence').onchange=e=>{evidence=e.target.value;render(sec)};
    render(sec);return true
  }
  let tries=0;const timer=setInterval(()=>{if(boot()||++tries>40)clearInterval(timer)},500);
})();
