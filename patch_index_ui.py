from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# 1) Make the modal backdrop fully opaque so the dashboard behind it is not visible.
s = s.replace(
    '.drawer-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:90}',
    '.drawer-backdrop{display:none;position:fixed;inset:0;background:#050a10;z-index:90;opacity:1;overscroll-behavior:contain}'
)

# 2) Add modal/focus styling.
needle = '.drawer .score-big{font-size:42px;font-weight:950;color:var(--amber)}'
insert = needle + '.theater-focus{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 10px;padding:9px 11px;border:1px solid rgba(98,160,255,.35);background:rgba(98,160,255,.08);border-radius:10px}.theater-focus strong{font-size:11px}.theater-focus button{min-height:32px;padding:6px 9px}'
s = s.replace(needle, insert)

# 3) Give the map a focus banner without requiring a large HTML rewrite.
old_state = "let DATA=null,activeRegion='all',newsMode='breaking',activeLayer='all',allConflicts=false,map,markerLayer;"
new_state = "let DATA=null,activeRegion='all',newsMode='breaking',activeLayer='all',allConflicts=false,map,markerLayer,focusedConflictId=null,previousBodyOverflow='';"
s = s.replace(old_state, new_state)

# 4) Replace conflict drawer with a more useful, non-transparent modal workflow.
old = "function openConflict(id){const c=findConflict(id);if(!c)return;$('drawerBody').innerHTML=`<span class=\"tag ${/HIGH|CRITICAL/.test(c.escalation||'')?'red':'amber'}\">${esc(c.escalation||'MONITORING')}</span><span class=\"tag blue\">${esc(c.region||'')}</span><h3>${esc(c.name)}</h3><div class=\"muted\">${esc(c.category||'')} · ${esc(c.status||'Monitoring')} · ${esc(c.confidence||'MONITORING')}</div><div class=\"scoreline\"><span>Activity signal</span><b>${Math.round(Number(c.activityScore||0))}</b></div><div class=\"track\"><div class=\"fill\" style=\"width:${Math.max(0,Math.min(100,Number(c.activityScore||0)))}%\"></div></div><div class=\"drawer-section\"><div class=\"label\">Actors / coverage</div><p>${esc(c.actors||'Not available')}</p></div><div class=\"drawer-section\"><div class=\"label\">Facts</div><p>${esc(c.facts||'No fact summary available.')}</p></div><div class=\"drawer-section\"><div class=\"label\">Analysis</div><p>${esc(c.analysis||'No analysis available.')}</p></div><div class=\"drawer-section\"><div class=\"label\">Latest signal</div><p>${esc(c.recent||'No recent signal.')}</p></div><div class=\"drawer-section\"><div class=\"label\">Source breadth</div><p>${esc(c.sourceCount??0)} source(s) attached to this theater.</p></div><button class=\"filter\" id=\"focusConflict\" style=\"margin-top:12px\">Show related map signals</button>`;$('drawerBackdrop').classList.add('open');$('drawer').classList.add('open');$('focusConflict').addEventListener('click',()=>focusConflictOnMap(c))}"
new = "function openConflict(id){const c=findConflict(id);if(!c)return;document.querySelectorAll('.ccard').forEach(x=>x.classList.toggle('selected',x.dataset.id===id));$('drawerBody').innerHTML=`<span class=\"tag ${/HIGH|CRITICAL/.test(c.escalation||'')?'red':'amber'}\">${esc(c.escalation||'MONITORING')}</span><span class=\"tag blue\">${esc(c.region||'')}</span><h3>${esc(c.name)}</h3><div class=\"muted\">${esc(c.category||'')} · ${esc(c.status||'Monitoring')} · ${esc(c.confidence||'MONITORING')}</div><div class=\"scoreline\"><span>Activity signal</span><b>${Math.round(Number(c.activityScore||0))}</b></div><div class=\"track\"><div class=\"fill\" style=\"width:${Math.max(0,Math.min(100,Number(c.activityScore||0)))}%\"></div></div><div class=\"drawer-section\"><div class=\"label\">Actors / coverage</div><p>${esc(c.actors||'Not available')}</p></div><div class=\"drawer-section\"><div class=\"label\">Facts</div><p>${esc(c.facts||'No fact summary available.')}</p></div><div class=\"drawer-section\"><div class=\"label\">Analysis</div><p>${esc(c.analysis||'No analysis available.')}</p></div><div class=\"drawer-section\"><div class=\"label\">Latest signal</div><p>${esc(c.recent||'No recent signal.')}</p></div><div class=\"drawer-section\"><div class=\"label\">Source breadth</div><p>${esc(c.sourceCount??0)} source(s) attached to this theater.</p></div><button class=\"filter\" id=\"focusConflict\" style=\"margin-top:12px\">Focus this theater on map</button>`;previousBodyOverflow=document.body.style.overflow;document.body.style.overflow='hidden';$('drawerBackdrop').classList.add('open');$('drawer').classList.add('open');setTimeout(()=>document.getElementById('drawerClose')?.focus(),40);$('focusConflict').addEventListener('click',()=>focusConflictOnMap(c))}"
if old not in s:
    raise SystemExit('openConflict target not found')
s = s.replace(old, new)

# 5) Replace map-focus behavior so only the selected theater's signals remain visible and a clear control appears.
old = "function closeDrawer(){$('drawerBackdrop').classList.remove('open');$('drawer').classList.remove('open')}"
new = "function closeDrawer(){$('drawerBackdrop').classList.remove('open');$('drawer').classList.remove('open');document.body.style.overflow=previousBodyOverflow;document.querySelectorAll('.ccard.selected').forEach(x=>x.classList.remove('selected'))}"
s = s.replace(old, new)

old = "function focusConflictOnMap(c){const markers=Array.isArray(DATA?.markers)?DATA.markers:[];const needle=`${c.name} ${c.region||''}`.toLowerCase();const hits=markers.filter(m=>`${m.title||''} ${m.detail||''} ${m.why||''} ${m.region||''}`.toLowerCase().includes(needle)||String(m.conflictId||'')===String(c.id));if(hits.length&&map){activeLayer='all';document.querySelectorAll('[data-layer]').forEach(x=>x.classList.toggle('active',x.dataset.layer==='all'));renderMap();const pts=hits.map(m=>[Number(m.lat),Number(m.lng)]).filter(p=>Number.isFinite(p[0])&&Number.isFinite(p[1]));if(pts.length)map.fitBounds(L.latLngBounds(pts).pad(.25));closeDrawer();$('mapSection').scrollIntoView({behavior:'smooth',block:'start'})}else{closeDrawer();$('mapSection').scrollIntoView({behavior:'smooth',block:'start'})}}"
new = "function ensureFocusBanner(){let el=$('theaterFocus');if(!el){el=document.createElement('div');el.id='theaterFocus';el.className='theater-focus';const mapEl=$('map');mapEl.parentNode.insertBefore(el,mapEl)}return el}function clearTheaterFocus(){focusedConflictId=null;const el=$('theaterFocus');if(el)el.remove();renderMap()}function focusConflictOnMap(c){const markers=Array.isArray(DATA?.markers)?DATA.markers:[];const hits=markers.filter(m=>String(m.conflictId||'')===String(c.id));focusedConflictId=c.id;activeLayer='all';document.querySelectorAll('[data-layer]').forEach(x=>x.classList.toggle('active',x.dataset.layer==='all'));const banner=ensureFocusBanner();banner.innerHTML=`<div><div class=\"label\">THEATER FOCUS</div><strong>${esc(c.name)}</strong></div><button class=\"filter\" type=\"button\">Clear focus</button>`;banner.querySelector('button').addEventListener('click',clearTheaterFocus);renderMap();const pts=hits.map(m=>[Number(m.lat),Number(m.lng)]).filter(p=>Number.isFinite(p[0])&&Number.isFinite(p[1]));if(pts.length&&map)map.fitBounds(L.latLngBounds(pts).pad(.25));closeDrawer();$('mapSection').scrollIntoView({behavior:'smooth',block:'start'})}"
if old not in s:
    raise SystemExit('focus target not found')
s = s.replace(old, new)

# 6) Make renderMap honor theater focus, while retaining all markers when no focus is active.
old = "const markers=Array.isArray(DATA?.markers)?DATA.markers:[];const visible=markers.filter(m=>activeLayer==='all'||m.layer===activeLayer);"
new = "const markers=Array.isArray(DATA?.markers)?DATA.markers:[];const visible=markers.filter(m=>(activeLayer==='all'||m.layer===activeLayer)&&(!focusedConflictId||String(m.conflictId||'')===String(focusedConflictId)));"
if old not in s:
    raise SystemExit('renderMap target not found')
s = s.replace(old, new)

# 7) Selected card styling.
needle = '.ccard:hover{border-color:#315274;transform:translateY(-1px)}'
insert = needle + '.ccard.selected{border-color:var(--blue);box-shadow:0 0 0 1px rgba(98,160,255,.35),0 8px 24px rgba(0,0,0,.22)}'
s = s.replace(needle, insert)

# 8) Close modal cleanly when the browser navigates back/forward or page visibility changes.
needle = "document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDrawer()});"
insert = needle + "window.addEventListener('popstate',closeDrawer);"
s = s.replace(needle, insert)

p.write_text(s, encoding='utf-8')
print('index.html patched successfully')
