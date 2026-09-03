/* Global Pulse V2.7 — intelligence quality, Morse visibility and evidence controls. */
(function(){
  'use strict';
  const A=v=>Array.isArray(v)?v:[];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeUrl=v=>{try{const u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch{return ''}};
  const age=iso=>{const t=Date.parse(iso||'');if(!Number.isFinite(t))return 'unknown';const m=Math.max(0,Math.round((Date.now()-t)/60000));if(m<2)return 'just now';if(m<60)return m+'m';if(m<1440)return Math.round(m/60)+'h';return Math.round(m/1440)+'d'};
  function css(){if(document.getElementById('gp-v27q-css'))return;const s=document.createElement('style');s.id='gp-v27q-css';s.textContent=`
.gp-v27q{display:grid;grid-template-columns:1.1fr .9fr;gap:12px}.gp-v27q-card{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:12px}.gp-v27q-title{font-size:10px;color:var(--muted);letter-spacing:.12em;text-transform:uppercase;margin-bottom:9px}.gp-v27q-meter{display:grid;grid-template-columns:62px 1fr;gap:10px;align-items:center}.gp-v27q-num{font-size:30px;font-weight:950;line-height:1;color:var(--green)}.gp-v27q-track{height:9px;background:#06101a;border:1px solid var(--line);border-radius:99px;overflow:hidden}.gp-v27q-fill{height:100%;background:linear-gradient(90deg,var(--red),var(--amber),var(--green));border-radius:99px}.gp-v27q-small{font-size:9px;color:var(--muted);line-height:1.5}.gp-v27q-row{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);font-size:10px}.gp-v27q-row:last-child{border-bottom:0}.gp-v27q-row b{font-weight:850}.gp-v27q-morse{display:grid;gap:7px}.gp-v27q-morse a{color:var(--text);font-size:11px;font-weight:800;line-height:1.3}.gp-v27q-morse span{font-size:9px;color:var(--muted)}.gp-v27q-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:8px}.gp-v27q-actions a{border:1px solid var(--line);border-radius:7px;padding:6px 8px;font-size:9px;background:#09121c}.gp-v27q-tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 7px;font-size:8px;color:var(--muted);margin:2px}.gp-v27q-ok{color:var(--green)}.gp-v27q-warn{color:var(--amber)}@media(max-width:760px){.gp-v27q{grid-template-columns:1fr}}
`;document.head.appendChild(s)}
  function quality(d,live){
    const sh=A(d.sourceHealth);const online=sh.filter(x=>x.status==='online').length;const usable=sh.filter(x=>x.status==='online'||x.status==='degraded').length;const total=Math.max(sh.length,1);
    const stories=A(live&&live.articles).length?A(live.articles):A(d.stories);const fresh=stories.filter(x=>{const t=Date.parse(x.published_date||x.time||'');return Number.isFinite(t)&&(Date.now()-t)<86400000}).length;
    const drivers=Object.values(d.driverSignals||{});const evidence=drivers.reduce((n,x)=>n+Math.min(5,Number(x&&x.sources)||0),0);const evidenceMax=Math.max(1,drivers.length*5);
    return Math.max(0,Math.min(100,Math.round(online/total*55+(usable/total)*15+Math.min(1,fresh/20)*20+Math.min(1,evidence/evidenceMax)*10)));
  }
  function dedupeEarthquakes(markers){
    const seen=new Set();
    return A(markers).filter(m=>{
      const isQ=/usgs|earthquake/i.test(String(m&&m.source||'')+' '+String(m&&m.eventType||m&&m.type||''));
      if(!isQ)return true;
      const k=String(m.url||m.id||m.eventId||[m.title,m.lat??m.latitude,m.lng??m.lon].join('|'));
      if(seen.has(k))return false;seen.add(k);return true;
    });
  }
  function render(d){
    if(!d)return;css();
    const live=window.LIVE_ARTICLES||null;const articles=A(live&&live.articles);
    const morse=articles.filter(x=>/morse report/i.test(String(x.source||x.source_name||''))).slice(0,4);
    const x=A(articles.filter(x=>String(x.sourceType||x.source_type||'').toLowerCase()==='social'||x.username));
    const sh=A(d.sourceHealth);const online=sh.filter(x=>x.status==='online').length;const degraded=sh.filter(x=>x.status==='degraded').length;const failed=sh.filter(x=>x.status==='failed').length;
    const q=quality(d,live);const qc=q>=75?'gp-v27q-ok':q>=50?'gp-v27q-warn':'';
    let sec=document.getElementById('gp-v27q');if(!sec){sec=document.createElement('section');sec.id='gp-v27q';sec.className='panel wide';const anchor=document.getElementById('gp-v27-intel');if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(sec,anchor.nextSibling);else{const wrap=document.querySelector('.wrap');if(wrap)wrap.appendChild(sec)}}
    sec.innerHTML=`<div class="section-head"><div><h2>V2.7 · INTELLIGENCE QUALITY</h2><div class="muted">Separates current evidence from stale or unavailable feeds. No API keys are used by this layer.</div></div><span class="gp-v27q-tag">CHECKED ${esc(age(d.updatedAt))} AGO</span></div><div class="gp-v27q"><div class="gp-v27q-card"><div class="gp-v27q-title">Evidence confidence</div><div class="gp-v27q-meter"><div class="gp-v27q-num ${qc}">${q}</div><div><div class="gp-v27q-track"><div class="gp-v27q-fill" style="width:${q}%"></div></div><div class="gp-v27q-small" style="margin-top:6px">Confidence is a quality indicator, not a claim that every report is independently verified.</div></div></div><div style="margin-top:8px"><div class="gp-v27q-row"><b>Online sources</b><span>${online}</span></div><div class="gp-v27q-row"><b>Degraded sources</b><span>${degraded}</span></div><div class="gp-v27q-row"><b>Failed sources</b><span>${failed}</span></div><div class="gp-v27q-row"><b>Current articles</b><span>${articles.length||A(d.stories).length}</span></div><div class="gp-v27q-row"><b>OSINT/social items</b><span>${x.length}</span></div></div></div><div class="gp-v27q-card"><div class="gp-v27q-title">Morse Report</div><div class="gp-v27q-morse">${morse.map(a=>`<div><a href="${esc(safeUrl(a.url))}" target="_blank" rel="noopener noreferrer">${esc(a.title)}</a><span>${esc(a.source||'Morse Report')} · ${age(a.published_date)} ago</span></div>`).join('')||'<div class="gp-v27q-small">No Morse article was returned by the latest public feed cycle. Global Pulse will not invent a headline; use the publisher/RSS links below.</div>'}</div><div class="gp-v27q-actions"><a href="https://morsereport.com/" target="_blank" rel="noopener noreferrer">Open Morse Report ↗</a><a href="https://rss.buzzsprout.com/2637181.rss" target="_blank" rel="noopener noreferrer">Open public RSS ↗</a></div></div></div><div class="gp-v27q-small" style="margin-top:8px">Map hygiene: V2.7 collapses duplicate USGS earthquake records by event URL/ID before rendering. Source failures remain visible in Source Health instead of being converted into fake live data.</div>`;
    // Do not mutate DATA.markers. The canonical map renderer consumes DATA directly;
    // provide a temporary de-duplicated view only while it renders.
    if(Array.isArray(d.markers)&&typeof window.renderMap==='function'){
      const originalMarkers=d.markers;d.markers=dedupeEarthquakes(originalMarkers);
      try{window.renderMap()}finally{d.markers=originalMarkers}
    }
  }
  async function boot(){
    if(!window.LIVE_ARTICLES){try{const r=await fetch('data/live_articles.json?ts='+Date.now(),{cache:'no-store'});if(r.ok)window.LIVE_ARTICLES=await r.json()}catch(e){/* snapshot remains usable */}}
    if(window.DATA)render(window.DATA);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else setTimeout(boot,0);
  window.addEventListener('globalpulse:dataready',boot);setInterval(boot,30000);
})();
