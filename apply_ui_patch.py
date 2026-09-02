from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

css = '''
/* Global Pulse UI stability patch */
html.gp-modal-open,body.gp-modal-open{overflow:hidden!important;overscroll-behavior:none!important}
body.gp-modal-open{position:fixed!important;width:100%!important;left:0;right:0}
.drawer-backdrop{display:none!important;position:fixed!important;inset:0!important;z-index:9998!important;background:#02060b!important;opacity:1!important;visibility:hidden!important;pointer-events:none!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
.drawer-backdrop.open{display:block!important;visibility:visible!important;pointer-events:auto!important}
.drawer{position:fixed!important;z-index:9999!important;background:#07101a!important;opacity:1!important;visibility:visible!important;isolation:isolate!important;box-shadow:-24px 0 60px rgba(0,0,0,.55)!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
.drawer *{opacity:1}
@media(max-width:720px){.drawer{background:#07101a!important;box-shadow:0 -20px 50px rgba(0,0,0,.6)!important}}
.gp-focus-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;padding:10px 12px;border:1px solid #315274;background:#081827;color:#eef5ff;border-radius:10px}
.gp-focus-bar b{color:#62a0ff;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
.gp-focus-bar button{min-height:32px;padding:6px 10px}
'''

if 'Global Pulse UI stability patch' not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

js = r'''
<script>
/* Global Pulse: reliable theater modal + map focus */
(function(){
  const theaterCoords={
    'ukraine-russia-war':[49.0,31.2,5.2],'gaza-israel-hamas':[31.4,34.4,4.5],'israel-iran-regional-front':[32.0,44.0,6.0],'iran-strait-of-hormuz':[26.3,53.4,5.0],'yemen-red-sea':[15.4,44.2,6.0],'syria-conflict-residual-fronts':[35.0,38.9,5.5],'iraq-militia-security-risk':[33.2,43.8,5.5],
    'sudan-civil-war':[15.5,30.2,5.5],'south-sudan-instability':[6.8,31.3,5.8],'eastern-drc-conflict':[-1.5,29.2,5.2],'somalia-al-shabaab':[5.8,46.2,5.5],'ethiopia-internal-conflict-risk':[9.1,40.5,5.8],'nigeria-insurgency-banditry':[9.0,8.7,5.8],'mali-sahel-insurgency':[17.0,-3.0,6.0],'burkina-faso-insurgency':[12.4,-1.6,5.8],'niger-insurgency-coup-fallout':[17.6,8.1,5.8],'cameroon-separatist-conflict':[5.9,10.2,5.5],'chad-security-sahel-spillover':[15.3,18.7,5.8],'libya-political-militia-risk':[27.0,17.0,5.5],'mozambique-cabo-delgado':[-12.3,40.5,5.5],
    'myanmar-civil-war':[21.0,96.0,5.8],'afghanistan-security-risk':[33.9,67.7,5.8],'pakistan-militancy-border-risk':[30.4,69.3,5.8],'taiwan-strait-pressure':[24.0,120.7,5.0],'korean-peninsula':[38.5,127.9,5.2],'south-china-sea-flashpoint':[12.0,114.0,6.0],
    'haiti-gang-conflict':[18.97,-72.3,5.5],'mexico-cartel-conflict':[23.6,-102.5,5.5],'ecuador-organized-crime-conflict':[-1.8,-78.2,5.5],'colombia-armed-groups':[4.6,-74.1,5.5]
  };
  function coordsFor(c){
    if(theaterCoords[c.id])return theaterCoords[c.id];
    const r=(c.region||'').toLowerCase();
    return r.includes('europe')?[50,20,5]:r.includes('middle east')?[30,45,5]:r.includes('africa')?[5,20,5]:r.includes('indo-pacific')?[18,115,5]:[10,0,2.8];
  }
  function hitsFor(c){
    const markers=Array.isArray(DATA?.markers)?DATA.markers:[];
    const aliases=(c.name+' '+(c.actors||'')).toLowerCase().split(/[^a-z0-9]+/).filter(x=>x.length>3);
    return markers.filter(m=>{
      if(String(m.conflictId||'')===String(c.id))return true;
      const text=(m.title+' '+m.detail+' '+m.why+' '+m.region+' '+m.country).toLowerCase();
      return aliases.some(a=>text.includes(a));
    });
  }
  window.openConflict=function(id){
    const c=typeof findConflict==='function'?findConflict(id):null;if(!c)return;
    document.querySelectorAll('.ccard').forEach(x=>x.classList.toggle('selected',x.dataset.id===id));
    const hits=hitsFor(c);
    const related=hits.length?`<div class="drawer-section"><div class="label">Map signals</div><p>${hits.length} linked signal${hits.length===1?'':'s'} found for this theater.</p></div>`:'<div class="drawer-section"><div class="label">Map signals</div><p>No directly linked source-map markers yet. The map will still center on this theater.</p></div>';
    $('drawerBody').innerHTML=`<button class="drawer-close" id="drawerInnerClose" aria-label="Close">✕</button><span class="tag ${/HIGH|CRITICAL/.test(c.escalation||'')?'red':'amber'}">${esc(c.escalation||'MONITORING')}</span><span class="tag blue">${esc(c.region||'')}</span><h3>${esc(c.name)}</h3><div class="muted">${esc(c.category||'')} · ${esc(c.status||'Monitoring')} · ${esc(c.confidence||'MONITORING')}</div><div class="scoreline"><span>Activity signal</span><b>${Math.round(Number(c.activityScore||0))}</b></div><div class="track"><div class="fill" style="width:${Math.max(0,Math.min(100,Number(c.activityScore||0)))}%"></div></div><div class="drawer-section"><div class="label">Actors / coverage</div><p>${esc(c.actors||'Not available')}</p></div><div class="drawer-section"><div class="label">Facts</div><p>${esc(c.facts||'No fact summary available.')}</p></div><div class="drawer-section"><div class="label">Analysis</div><p>${esc(c.analysis||'No analysis available.')}</p></div><div class="drawer-section"><div class="label">Latest signal</div><p>${esc(c.recent||'No recent signal.')}</p></div>${related}<button class="filter active" id="focusConflict" style="margin-top:12px;width:100%">Focus theater on map</button>`;
    $('drawerBackdrop').classList.add('open');$('drawer').classList.add('open');document.documentElement.classList.add('gp-modal-open');document.body.classList.add('gp-modal-open');
    $('drawerInnerClose').onclick=closeDrawer; $('focusConflict').onclick=()=>focusConflictOnMap(c);
  };
  window.closeDrawer=function(){
    $('drawerBackdrop').classList.remove('open');$('drawer').classList.remove('open');document.documentElement.classList.remove('gp-modal-open');document.body.classList.remove('gp-modal-open');
    document.querySelectorAll('.ccard.selected').forEach(x=>x.classList.remove('selected'));
  };
  window.focusConflictOnMap=function(c){
    const hits=hitsFor(c), [lat,lng,z]=coordsFor(c);
    activeLayer='all';document.querySelectorAll('[data-layer]').forEach(x=>x.classList.toggle('active',x.dataset.layer==='all'));
    if(typeof renderMap==='function')renderMap();
    closeDrawer();
    setTimeout(()=>{
      if(!map)return;
      map.invalidateSize(true);
      const pts=hits.map(m=>[Number(m.lat),Number(m.lng)]).filter(p=>Number.isFinite(p[0])&&Number.isFinite(p[1]));
      if(pts.length)map.flyToBounds(L.latLngBounds(pts),{padding:[70,70],maxZoom:6,duration:.8});
      else map.flyTo([lat,lng],z,{duration:.8});
      const ms=$('mapSection');if(ms)ms.scrollIntoView({behavior:'smooth',block:'start'});
      let bar=$('gpFocusBar');if(!bar){bar=document.createElement('div');bar.id='gpFocusBar';bar.className='gp-focus-bar';const mapHead=$('mapSection')?.querySelector('.section-head');if(mapHead)mapHead.insertAdjacentElement('afterend',bar)}
      bar.innerHTML=`<div><b>Theater focus</b><div>${esc(c.name)} · ${esc(c.region||'')} · ${hits.length} linked map signal${hits.length===1?'':'s'}</div></div><button class="filter" id="clearGpFocus">Clear focus</button>`;
      $('clearGpFocus').onclick=()=>{bar.remove();if(map){map.flyTo([24,10],2,{duration:.7});renderMap();}};
    },300);
  };
  const backdrop=$('drawerBackdrop');if(backdrop)backdrop.addEventListener('click',e=>{if(e.target===backdrop)closeDrawer()});
})();
</script>
'''

if 'Global Pulse: reliable theater modal + map focus' not in s:
    s = s.replace('</body>', js + '\n</body>', 1)

p.write_text(s, encoding='utf-8')
print('UI patch applied')
