/* Global Pulse — standalone politics/economics intelligence dashboard. */
(function(){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const safe=v=>{try{const u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch{return ''}};
  let mode='all',query='',evidence='all';
  const label={all:'ALL', 'us-politics':'U.S. POLITICS','world-politics':'WORLD POLITICS'};
  function rows(){
    const pi=window.DATA?.politicalIntelligence;
    let a=Array.isArray(pi?.topSignals)?pi.topSignals:[];
    if(!a.length){const all=Array.isArray(window.DATA?.stories)?window.DATA.stories:[];a=all.filter(s=>s.intelligenceLayer==='us-politics'||s.intelligenceLayer==='world-politics').sort((x,y)=>new Date(y.time||0)-new Date(x.time||0));}
    return a.filter(s=>{const text=`${s.title||''} ${s.summary||''} ${s.sourceLabel||''} ${(s.politicalTopics||[]).join(' ')}`.toLowerCase();return(mode==='all'||s.intelligenceLayer===mode)&&(!query||text.includes(query))&&(evidence==='all'||(evidence==='corroborated'?s.evidenceLevel==='CORROBORATED':s.evidenceLevel!=='CORROBORATED'))});
  }
  function card(s){
    const url=safe(s.source||s.url), cor=s.evidenceLevel==='CORROBORATED', topics=(s.politicalTopics||[]).slice(0,3), entities=(s.politicalEntities||[]).slice(0,4);
    return `<article class="gp-pintel-card"><div class="gp-pintel-meta"><span class="tag ${s.intelligenceLayer==='us-politics'?'green':'blue'}">${esc(label[s.intelligenceLayer]||'POLITICS')}</span><span class="tag ${cor?'green':'amber'}">${cor?'CORROBORATED':'SINGLE-SOURCE'}</span>${s.breaking?'<span class="tag red">BREAKING</span>':''}<span class="gp-pintel-time">${esc(s.time||'')}</span></div><a class="story-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer"><h3>${esc(s.title)}</h3></a><div class="source">${esc(s.sourceLabel||s.sourceName||'Public source')}</div><p class="muted">${esc(s.summary||'')}</p><div class="gp-pintel-tags">${topics.map(x=>`<span>${esc(x)}</span>`).join('')}${entities.map(x=>`<span>${esc(x)}</span>`).join('')}</div>${cor?`<div class="gp-pintel-evidence"><b>Independent coverage:</b> ${esc((s.corroboratingSources||[]).join(' · '))}</div>`:'<div class="gp-pintel-evidence muted">No independent matching report found in the current 24-hour window.</div>'}${url?`<a class="open" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`:''}</article>`;
  }
  function render(root){
    const a=rows(),pi=window.DATA?.politicalIntelligence||{}, count=root.querySelector('#gpPintelCount');
    root.querySelector('#gpPintelGrid').innerHTML=a.slice(0,50).map(card).join('')||'<div class="empty">No political signals match these filters. The feed may be between refresh cycles.</div>';
    if(count)count.textContent=`${a.length} signals`;
    root.querySelector('#gpPintelStats').innerHTML=`<span><b>${pi.usPoliticsSignals??a.filter(x=>x.intelligenceLayer==='us-politics').length}</b> U.S.</span><span><b>${pi.worldPoliticsSignals??a.filter(x=>x.intelligenceLayer==='world-politics').length}</b> World</span><span><b>${pi.corroboratedSignals??a.filter(x=>x.evidenceLevel==='CORROBORATED').length}</b> corroborated</span><span><b>${pi.singleSourceSignals??a.filter(x=>x.evidenceLevel!=='CORROBORATED').length}</b> developing</span>`;
  }
  function removeLegacy(){
    document.querySelectorAll('body *').forEach(el=>{if(el.children.length>12)return;const t=(el.textContent||'').replace(/\s+/g,' ').trim();if(/^Intelligence Brief/.test(t)&&/Awaiting source signals/.test(t))el.remove();});
    document.querySelectorAll('body *').forEach(el=>{if(el.children.length>8)return;const t=(el.textContent||'').replace(/\s+/g,' ').trim();if(t==='My Watchlist No theaters on your watchlist.')el.remove();});
  }
  function boot(){
    if(document.getElementById('gp-political-intelligence'))return true;
    const wrap=document.querySelector('.wrap');if(!wrap||!window.DATA)return false;
    const sec=document.createElement('section');sec.className='panel wide';sec.id='gp-political-intelligence';
    sec.innerHTML=`<div class="section-head"><div><h2>POLITICAL & ECONOMIC REPORTING</h2><div class="muted">Automatic source aggregation for U.S. politics, world politics and the political side of economics.</div></div><span class="gp-layer-count" id="gpPintelCount">— signals</span></div><div class="gp-pintel-stats" id="gpPintelStats"></div><div class="gp-pintel-controls"><div class="gp-layer-tabs"><button class="filter active" data-pintel="all">All Politics</button><button class="filter" data-pintel="us-politics">U.S. Politics</button><button class="filter" data-pintel="world-politics">World Politics</button></div><div class="gp-pintel-filters"><input id="gpPintelSearch" placeholder="Search people, countries, issues…" aria-label="Search political reporting"><select id="gpPintelEvidence"><option value="all">All evidence levels</option><option value="corroborated">Corroborated</option><option value="developing">Developing / single-source</option></select></div></div><div class="gp-pintel-grid" id="gpPintelGrid"></div><div class="gp-layer-note">Sources are displayed as reporting signals, not automatically accepted as fact. “Corroborated” means independent domains produced sufficiently similar reports within the current time window; it does not prove every claim is true.</div>`;
    const conflict=document.getElementById('conflictSection'),report=document.getElementById('reporting');
    if(conflict)conflict.after(sec);else if(report)report.before(sec);else wrap.appendChild(sec);
    sec.querySelectorAll('[data-pintel]').forEach(b=>b.onclick=()=>{sec.querySelectorAll('[data-pintel]').forEach(x=>x.classList.remove('active'));b.classList.add('active');mode=b.dataset.pintel;render(sec)});
    sec.querySelector('#gpPintelSearch').oninput=e=>{query=e.target.value.toLowerCase().trim();render(sec)};
    sec.querySelector('#gpPintelEvidence').onchange=e=>{evidence=e.target.value;render(sec)};
    render(sec);return true;
  }
  let tries=0;const timer=setInterval(()=>{tries++;removeLegacy();if(boot()||tries>120)clearInterval(timer)},250);
  setInterval(()=>{removeLegacy();if(document.getElementById('gp-political-intelligence'))render(document.getElementById('gp-political-intelligence'))},60000);
})();
