/* Global Pulse — first-class intelligence layers */
(function(){
  'use strict';
  const esc = window.gpEsc || (v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])));
  const safe = window.gpSafeUrl || (v=>{try{const u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch{return ''}});
  let mode='all', region='all', severity='all', query='';
  const layerLabels={all:'ALL REPORTING','us-politics':'U.S. POLITICS','world-politics':'WORLD POLITICS','economics':'ECONOMICS','general':'GENERAL'};
  const impact=s=>{const t=`${s.title||''} ${s.summary||''}`;if(/invasion|missile barrage|blockade|major offensive|coup|market crash|bank failure/i.test(t))return'critical';if(/strike|attack|sanction|tariff|oil shock|inflation|killed|election result|rate decision/i.test(t))return'high';if(/warning|talks|vote|market|trade|currency|diplom/i.test(t))return'medium';return'low'};
  function current(){
    const all=Array.isArray(window.DATA?.stories)?window.DATA.stories:[];
    return all.filter(s=>{
      const l=s.intelligenceLayer||'general';
      const hitMode=mode==='all'||l===mode||(mode==='politics'&&(l==='us-politics'||l==='world-politics'));
      const text=`${s.title||''} ${s.summary||''} ${s.sourceLabel||''}`.toLowerCase();
      const hitQ=!query||text.includes(query);
      const r=String(s.region||s.country||'').toLowerCase();
      const hitR=region==='all'||r.includes(region.toLowerCase());
      const hitS=severity==='all'||impact(s)===severity;
      return hitMode&&hitQ&&hitR&&hitS;
    }).sort((a,b)=>new Date(b.time||0)-new Date(a.time||0));
  }
  function render(){
    const root=document.getElementById('stories'); if(!root)return;
    const rows=current().slice(0,30);
    root.innerHTML=rows.length?rows.map(s=>{
      const l=s.intelligenceLayer||'general', imp=impact(s), url=safe(s.source);
      return `<article class="story"><div><span class="tag ${l==='economics'?'amber':l==='general'?'blue':'green'}">${esc(layerLabels[l]||'GENERAL')}</span><span class="tag ${imp==='critical'||imp==='high'?'red':imp==='medium'?'amber':'blue'}">${imp.toUpperCase()}</span>${s.breaking?'<span class="tag red">BREAKING</span>':''}</div><a class="story-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer"><h3>${esc(s.title)}</h3></a><div class="source">${esc(s.sourceLabel||'Public source')} · ${esc(s.time||'')}</div><p class="muted">${esc(s.summary||'')}</p>${url?`<a class="open" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open primary report ↗</a>`:''}</article>`;
    }).join(''):`<div class="empty">No ${esc(layerLabels[mode]||'')} stories match the current filters.</div>`;
    const count=document.getElementById('gpLayerCount'); if(count)count.textContent=`${current().length} matching signals`;
  }
  function boot(){
    const panel=document.querySelector('#reporting .panel'); if(!panel||document.getElementById('gpLayerControls'))return;
    const tabs=document.createElement('div');tabs.id='gpLayerControls';tabs.className='gp-layer-controls';
    tabs.innerHTML=`<div class="gp-layer-tabs">${[['all','All'],['us-politics','U.S. Politics'],['world-politics','World Politics'],['economics','Economics']].map(([v,t])=>`<button class="filter ${v==='all'?'active':''}" data-layer-news="${v}">${t}</button>`).join('')}</div><div class="gp-layer-filters"><input id="gpLayerSearch" placeholder="Search political/economic reporting…" aria-label="Search reporting"><select id="gpSeverity"><option value="all">All impact</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select><span id="gpLayerCount" class="gp-layer-count"></span></div><div class="gp-layer-note">Political/economic classification preserves source provenance. Impact is an analytical display aid, not a claim of causality.</div>`;
    const old=panel.querySelector('.news-tabs'); if(old)old.replaceWith(tabs); else panel.querySelector('h2')?.after(tabs);
    tabs.querySelectorAll('[data-layer-news]').forEach(b=>b.onclick=()=>{tabs.querySelectorAll('[data-layer-news]').forEach(x=>x.classList.remove('active'));b.classList.add('active');mode=b.dataset.layerNews;render()});
    tabs.querySelector('#gpLayerSearch').oninput=e=>{query=e.target.value.toLowerCase().trim();render()};
    tabs.querySelector('#gpSeverity').onchange=e=>{severity=e.target.value;render()};
    render();
  }
  const oldRender=window.renderStories; window.renderStories=function(){if(typeof oldRender==='function'&&window.DATA&&!document.getElementById('gpLayerControls'))oldRender(); if(document.getElementById('gpLayerControls'))render()};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else setTimeout(boot,0);
  setInterval(()=>{if(window.DATA)render()},60000);
})();
