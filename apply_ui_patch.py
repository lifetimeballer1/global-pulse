from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

css = '''
/* Global Pulse UI stability patch */
html.gp-modal-open,body.gp-modal-open{overflow:hidden!important;overscroll-behavior:none!important}
.drawer-backdrop{display:none!important;position:fixed!important;inset:0!important;z-index:9998!important;background:#02060b!important;opacity:1!important;visibility:hidden!important;pointer-events:none!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
.drawer-backdrop.open{display:block!important;visibility:visible!important;pointer-events:auto!important}
.drawer{position:fixed!important;z-index:9999!important;background:#07101a!important;opacity:1!important;visibility:visible!important;isolation:isolate!important;box-shadow:-24px 0 60px rgba(0,0,0,.55)!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
.drawer *{opacity:1!important}
@media(max-width:720px){.drawer{background:#07101a!important;box-shadow:0 -20px 50px rgba(0,0,0,.6)!important}}
.gp-focus-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;padding:10px 12px;border:1px solid #315274;background:#081827;color:#eef5ff;border-radius:10px}
.gp-focus-bar b{color:#62a0ff;font-size:11px;letter-spacing:.08em;text-transform:uppercase}.gp-focus-bar button{min-height:32px;padding:6px 10px}
.gp-brief{margin:0 0 18px;padding:16px;border:1px solid #263d55;background:linear-gradient(135deg,#0b1622,#08111a);border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.18)}
.gp-brief-head{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:10px}.gp-brief-head b{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#7fb0ff}.gp-brief-head span{font-size:11px;color:#7890a8}
.gp-brief-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.gp-brief-item{padding:11px;border:1px solid #1b3045;border-radius:10px;background:#091522}.gp-brief-item strong{display:block;color:#eaf3ff;font-size:13px;line-height:1.35}.gp-brief-item small{display:block;margin-top:5px;color:#7890a8;font-size:10px;line-height:1.4}
.gp-watch{border:1px solid #243a52;background:#091522;color:#dbe9f7;border-radius:8px;padding:5px 8px;font-size:10px;cursor:pointer}.gp-watch.active{border-color:#e0b35b;color:#ffd98a;background:#17150d}
.gp-watchlist{margin-top:14px;padding:12px;border-top:1px solid #1b3045}.gp-watchlist-title{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#7890a8;margin-bottom:8px}.gp-watchlist-items{display:flex;flex-wrap:wrap;gap:7px}.gp-watch-chip{font-size:10px;padding:6px 8px;border:1px solid #315274;border-radius:20px;background:#0b1927;color:#dbe9f7;cursor:pointer}
@media(max-width:720px){.gp-brief-grid{grid-template-columns:1fr}.gp-brief{padding:13px}}
'''
if 'Global Pulse UI stability patch' not in s:s=s.replace('</style>',css+'\n</style>',1)

js=r'''
<script>
/* Global Pulse: intelligence brief + watchlist + reliable conflict focus */
(function(){
const coords={'ukraine':[49,31.2,5.2],'gaza':[31.4,34.4,5.2],'israel-iran':[32,44,5.2],'hormuz':[26.3,53.4,5.2],'yemen':[15.4,44.2,5.5],'syria':[35,38.9,5.2],'iraq':[33.2,43.8,5.2],'sudan':[15.5,30.2,5.2],'south-sudan':[6.8,31.3,5.2],'drc':[-1.5,29.2,5.2],'somalia':[5.8,46.2,5.2],'ethiopia':[9.1,40.5,5.2],'nigeria':[9,8.7,5.2],'sahel-mali':[17,-3,5.2],'sahel-burkina':[12.4,-1.6,5.2],'sahel-niger':[17.6,8.1,5.2],'cameroon':[5.9,10.2,5.2],'chad':[15.3,18.7,5.2],'libya':[27,17,5.2],'mozambique':[-12.3,40.5,5.2],'myanmar':[21,96,5.2],'afghanistan':[33.9,67.7,5.2],'pakistan':[30.4,69.3,5.2],'taiwan':[24,120.7,5.2],'korea':[38.5,127.9,5.2],'south-china-sea':[12,114,5.2],'haiti':[18.97,-72.3,5.2],'mexico':[23.6,-102.5,5.2],'ecuador':[-1.8,-78.2,5.2],'colombia':[4.6,-74.1,5.2]};
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const getC=id=>typeof findConflict==='function'?findConflict(id):null;
const getW=()=>{try{return JSON.parse(localStorage.getItem('gp_watchlist')||'[]')}catch(e){return[]}};
const setW=a=>{try{localStorage.setItem('gp_watchlist',JSON.stringify(a))}catch(e){}};
function renderWatch(){const w=getW();document.querySelectorAll('.gp-watch').forEach(b=>{const on=w.includes(b.dataset.watch);b.classList.toggle('active',on);b.textContent=on?'★ Watching':'☆ Watch'});const box=document.getElementById('gpWatchlistItems');if(!box)return;const items=w.map(getC).filter(Boolean);box.innerHTML=items.length?items.map(c=>`<button class="gp-watch-chip" data-focus="${esc(c.id)}">★ ${esc(c.name)}</button>`).join(''):'<span class="muted">No theaters on your watchlist.</span>';box.querySelectorAll('[data-focus]').forEach(b=>b.onclick=()=>show(b.dataset.focus))}
function brief(){let root=document.getElementById('gpBrief');if(!root){const main=document.querySelector('main');if(!main)return;root=document.createElement('section');root.id='gpBrief';root.className='gp-brief';main.insertBefore(root,main.firstChild)}const cs=Array.isArray(DATA?.conflicts)?DATA.conflicts:[];const top=[...cs].sort((a,b)=>Number(b.activityScore||0)-Number(a.activityScore||0)).slice(0,3);while(top.length<3)top.push({name:'Monitoring global developments',activityScore:0,escalation:'MONITORING',confidence:'Awaiting source signals'});root.innerHTML=`<div class="gp-brief-head"><b>Intelligence Brief</b><span>Signal-based · not battlefield truth</span></div><div class="gp-brief-grid">${top.map(c=>`<div class="gp-brief-item"><strong>${esc(c.name)} — ${Math.round(Number(c.activityScore||0))} activity</strong><small>${esc(c.escalation||'MONITORING')} · ${esc(c.confidence||'MONITORING')}</small></div>`).join('')}</div><div class="gp-watchlist"><div class="gp-watchlist-title">My Watchlist</div><div class="gp-watchlist-items" id="gpWatchlistItems"></div></div>`;renderWatch()}
function show(id){const c=getC(id);if(!c)return;const linked=(Array.isArray(DATA?.markers)?DATA.markers:[]).filter(x=>String(x.conflictId||'')===String(id));const on=getW().includes(id);$('drawerBody').innerHTML=`<button class="drawer-close" id="gpClose" aria-label="Close">✕</button><div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><div><span class="tag amber">${esc(c.escalation||'MONITORING')}</span> <span class="tag blue">${esc(c.region||'')}</span></div><button class="gp-watch ${on?'active':''}" id="gpWatch" data-watch="${esc(c.id)}">${on?'★ Watching':'☆ Watch'}</button></div><h3>${esc(c.name)}</h3><div class="muted">${esc(c.category||'')} · ${esc(c.status||'Monitoring')} · ${esc(c.confidence||'MONITORING')}</div><div class="scoreline"><span>Activity signal</span><b>${Math.round(Number(c.activityScore||0))}</b></div><div class="track"><div class="fill" style="width:${Math.max(0,Math.min(100,Number(c.activityScore||0)))}%"></div></div><div class="drawer-section"><div class="label">Facts</div><p>${esc(c.facts||'No fact summary available.')}</p></div><div class="drawer-section"><div class="label">Analysis</div><p>${esc(c.analysis||'No analysis available.')}</p></div><div class="drawer-section"><div class="label">Map signals</div><p>${linked.length?linked.length+' directly linked map signal'+(linked.length===1?'':'s')+'.':'No directly linked markers yet; map will center on this theater.'}</p></div><button class="filter active" id="gpFocus" style="width:100%;margin-top:12px">Focus theater on map</button>`;$('drawerBackdrop').classList.add('open');$('drawer').classList.add('open');document.documentElement.classList.add('gp-modal-open');document.body.classList.add('gp-modal-open');$('gpClose').onclick=close;$('gpWatch').onclick=()=>{const a=getW(),i=a.indexOf(c.id);i>=0?a.splice(i,1):a.push(c.id);setW(a);renderWatch()};$('gpFocus').onclick=()=>focus(c)}
function close(){$('drawerBackdrop').classList.remove('open');$('drawer').classList.remove('open');document.documentElement.classList.remove('gp-modal-open');document.body.classList.remove('gp-modal-open')}
function focus(c){const m=Array.isArray(DATA?.markers)?DATA.markers:[],linked=m.filter(x=>String(x.conflictId||'')===String(c.id)),p=coords[c.id]||[10,0,2.8];activeLayer='all';if(typeof renderMap==='function')renderMap();close();setTimeout(()=>{if(!window.map)return;map.invalidateSize(true);const pts=linked.map(x=>[+x.lat,+x.lng]).filter(x=>Number.isFinite(x[0])&&Number.isFinite(x[1]));if(pts.length)map.flyToBounds(L.latLngBounds(pts),{padding:[70,70],maxZoom:6,duration:.8});else map.flyTo([p[0],p[1]],p[2],{duration:.8});document.getElementById('mapSection')?.scrollIntoView({behavior:'smooth',block:'start'});},250)}
function boot(){brief();renderWatch()}
document.addEventListener('click',e=>{const card=e.target.closest?.('.ccard');if(card){e.preventDefault();e.stopImmediatePropagation();show(card.dataset.id)}},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('drawer')?.classList.contains('open')){e.preventDefault();e.stopImmediatePropagation();close()}},true);
const back=$('drawerBackdrop');if(back)back.addEventListener('click',e=>{if(e.target===back)close()});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else setTimeout(boot,0);
})();
</script>
'''
if 'intelligence brief + watchlist + reliable conflict focus' not in s:s=s.replace('</body>',js+'\n</body>',1)
p.write_text(s,encoding='utf-8')
print('UI patch applied')