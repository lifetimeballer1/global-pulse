/* Global Pulse — first-class politics/economics reporting layer. */
(function(){
  'use strict';
  const esc=window.gpEsc||(v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])));
  const safe=window.gpSafeUrl||(v=>{try{const u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch{return ''}});
  let mode='all',severity='all',query='';
  const labels={all:'ALL REPORTING','us-politics':'U.S. POLITICS','world-politics':'WORLD POLITICS','economics':'ECONOMICS',general:'GENERAL'};
  const impact=s=>{const t=`${s.title||''} ${s.summary||''}`;if(/invasion|missile barrage|blockade|major offensive|coup|market crash|bank failure/i.test(t))return'critical';if(/strike|attack|sanction|tariff|oil shock|inflation|killed|election result|rate decision/i.test(t))return'high';if(/warning|talks|vote|market|trade|currency|diplom/i.test(t))return'medium';return'low'};
  function current(){return(Array.isArray(window.DATA?.stories)?window.DATA.stories:[]).filter(s=>{const l=s.intelligenceLayer||'general',text=`${s.title||''} ${s.summary||''} ${s.sourceLabel||''}`.toLowerCase();return(mode==='all'||l===mode)&&(!query||text.includes(query))&&(severity==='all'||impact(s)===severity)}).sort((a,b)=>new Date(b.time||0)-new Date(a.time||0))}
  function render(root){const rows=current().slice(0,40);root.innerHTML=rows.length?rows.map(s=>{const l=s.intelligenceLayer||'general',imp=impact(s),url=safe(s.source||s.url);return `<article class="story"><div><span class="tag ${l==='economics'?'amber':l==='general'?'blue':'green'}">${esc(labels[l]||'GENERAL')}</span><span class="tag ${imp==='critical'||imp==='high'?'red':imp==='medium'?'amber':'blue'}">${imp.toUpperCase()}</span>${s.breaking?'<span class="tag red">BREAKING</span>':''}</div><a class="story-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer"><h3>${esc(s.title)}</h3></a><div class="source">${esc(s.sourceLabel||s.sourceName||'Public source')} · ${esc(s.time||'')}</div><p class="muted">${esc(s.summary||'')}</p>${url?`<a class="open" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open primary report ↗</a>`:''}</article>`}).join(''):`<div class="empty">No ${esc(labels[mode])} stories match these filters.</div>`;const c=document.getElementById('gpLayerCount');if(c)c.textContent=`${current().length} matching signals`}
  function boot(){
    if(document.getElementById('gpLayerControls'))return true;
    const root=document.getElementById('stories');if(!root)return false;
    const host=root.closest('.panel')||root.parentElement;if(!host)return false;
    const head=host.querySelector('.section-head')||host.querySelector('h2');
    const controls=document.createElement('div');controls.id='gpLayerControls';controls.className='gp-layer-controls';
    controls.innerHTML=`<div class="gp-layer-title"><strong>POLITICS & ECONOMICS INTELLIGENCE</strong><span>Live reporting separated by analytical domain</span></div><div class="gp-layer-tabs">${[['all','All'],['us-politics','U.S. Politics'],['world-politics','World Politics'],['economics','Economics']].map(([v,t])=>`<button class="filter ${v==='all'?'active':''}" data-layer-news="${v}">${t}</button>`).join('')}</div><div class="gp-layer-filters"><input id="gpLayerSearch" placeholder="Search politics, economics, countries, issues…" aria-label="Search reporting"><select id="gpSeverity"><option value="all">All impact</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select><span id="gpLayerCount" class="gp-layer-count"></span></div><div class="gp-layer-note">Classification follows source/feed provenance first and conservative text rules second. Impact is an analytical display aid, not a claim of causality.</div>`;
    if(head)head.after(controls);else host.prepend(controls);
    controls.querySelectorAll('[data-layer-news]').forEach(b=>b.onclick=()=>{controls.querySelectorAll('[data-layer-news]').forEach(x=>x.classList.remove('active'));b.classList.add('active');mode=b.dataset.layerNews;render(root)});
    controls.querySelector('#gpLayerSearch').oninput=e=>{query=e.target.value.toLowerCase().trim();render(root)};
    controls.querySelector('#gpSeverity').onchange=e=>{severity=e.target.value;render(root)};
    render(root);return true;
  }
  let tries=0;const timer=setInterval(()=>{tries++;if(boot()||tries>120)clearInterval(timer)},250);
  const old=window.renderStories;window.renderStories=function(){if(typeof old==='function'&&!document.getElementById('gpLayerControls'))old.apply(this,arguments);if(document.getElementById('gpLayerControls'))render(document.getElementById('stories'))};
  setInterval(()=>{if(document.getElementById('gpLayerControls')&&document.getElementById('stories'))render(document.getElementById('stories'))},60000);
})();
