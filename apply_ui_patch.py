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
.gp-focus-bar b{color:#62a0ff;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
.gp-focus-bar button{min-height:32px;padding:6px 10px}
'''
if 'Global Pulse UI stability patch' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

js=r'''
<script>
/* Global Pulse: capture-phase conflict click fix v2 */
(function(){
const coords={
'ukraine-russia-war':[49,31.2,5.2],'gaza-israel-hamas':[31.4,34.4,4.5],'israel-iran-regional-front':[32,44,6],'iran-strait-of-hormuz':[26.3,53.4,5],'yemen-red-sea':[15.4,44.2,6],'syria-conflict-residual-fronts':[35,38.9,5.5],'iraq-militia-security-risk':[33.2,43.8,5.5],'sudan-civil-war':[15.5,30.2,5.5],'south-sudan-instability':[6.8,31.3,5.8],'eastern-drc-conflict':[-1.5,29.2,5.2],'somalia-al-shabaab':[5.8,46.2,5.5],'ethiopia-internal-conflict-risk':[9.1,40.5,5.8],'nigeria-insurgency-banditry':[9,8.7,5.8],'mali-sahel-insurgency':[17,-3,6],'burkina-faso-insurgency':[12.4,-1.6,5.8],'niger-insurgency-coup-fallout':[17.6,8.1,5.8],'cameroon-separatist-conflict':[5.9,10.2,5.5],'chad-security-sahel-spillover':[15.3,18.7,5.8],'libya-political-militia-risk':[27,17,5.5],'mozambique-cabo-delgado':[-12.3,40.5,5.5],'myanmar-civil-war':[21,96,5.8],'afghanistan-security-risk':[33.9,67.7,5.8],'pakistan-militancy-border-risk':[30.4,69.3,5.8],'taiwan-strait-pressure':[24,120.7,5],'korean-peninsula':[38.5,127.9,5.2],'south-china-sea-flashpoint':[12,114,6],'haiti-gang-conflict':[18.97,-72.3,5.5],'mexico-cartel-conflict':[23.6,-102.5,5.5],'ecuador-organized-crime-conflict':[-1.8,-78.2,5.5],'colombia-armed-groups':[4.6,-74.1,5.5]};
function esc2(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function conflict(id){return typeof findConflict==='function'?findConflict(id):null}
function show(id){const c=conflict(id);if(!c)return;const m=Array.isArray(DATA?.markers)?DATA.markers:[];const linked=m.filter(x=>String(x.conflictId||'')===String(id));$('drawerBody').innerHTML=`<button class="drawer-close" id="gpClose" aria-label="Close">✕</button><span class="tag amber">${esc2(c.escalation||'MONITORING')}</span> <span class="tag blue">${esc2(c.region||'')}</span><h3>${esc2(c.name)}</h3><div class="muted">${esc2(c.category||'')} · ${esc2(c.status||'Monitoring')} · ${esc2(c.confidence||'MONITORING')}</div><div class="scoreline"><span>Activity signal</span><b>${Math.round(Number(c.activityScore||0))}</b></div><div class="track"><div class="fill" style="width:${Math.max(0,Math.min(100,Number(c.activityScore||0)))}%"></div></div><div class="drawer-section"><div class="label">Facts</div><p>${esc2(c.facts||'No fact summary available.')}</p></div><div class="drawer-section"><div class="label">Analysis</div><p>${esc2(c.analysis||'No analysis available.')}</p></div><div class="drawer-section"><div class="label">Map signals</div><p>${linked.length?linked.length+' directly linked map signal'+(linked.length===1?'':'s')+'.':'No directly linked markers yet; map will center on this theater.'}</p></div><button class="filter active" id="gpFocus" style="width:100%;margin-top:12px">Focus theater on map</button>`;$('drawerBackdrop').classList.add('open');$('drawer').classList.add('open');document.documentElement.classList.add('gp-modal-open');document.body.classList.add('gp-modal-open');$('gpClose').onclick=close;$('gpFocus').onclick=()=>focus(c)}
function close(){$('drawerBackdrop').classList.remove('open');$('drawer').classList.remove('open');document.documentElement.classList.remove('gp-modal-open');document.body.classList.remove('gp-modal-open')}
function focus(c){const m=Array.isArray(DATA?.markers)?DATA.markers:[],linked=m.filter(x=>String(x.conflictId||'')===String(c.id)),p=coords[c.id]||[10,0,2.8];activeLayer='all';if(typeof renderMap==='function')renderMap();close();setTimeout(()=>{if(!map)return;map.invalidateSize(true);const pts=linked.map(x=>[+x.lat,+x.lng]).filter(x=>Number.isFinite(x[0])&&Number.isFinite(x[1]));if(pts.length)map.flyToBounds(L.latLngBounds(pts),{padding:[70,70],maxZoom:6,duration:.8});else map.flyTo([p[0],p[1]],p[2],{duration:.8});$('mapSection')?.scrollIntoView({behavior:'smooth',block:'start'});let b=$('gpFocusBar');if(!b){b=document.createElement('div');b.id='gpFocusBar';b.className='gp-focus-bar';$('mapSection')?.querySelector('.section-head')?.insertAdjacentElement('afterend',b)}b.innerHTML=`<div><b>Theater focus</b><div>${esc2(c.name)} · ${esc2(c.region||'')}</div></div><button class="filter" id="gpClear">Clear focus</button>`;$('gpClear').onclick=()=>{b.remove();map.flyTo([24,10],2,{duration:.7});renderMap()};},300)}
document.addEventListener('click',e=>{const card=e.target.closest?.('.ccard');if(card){e.preventDefault();e.stopImmediatePropagation();show(card.dataset.id)}},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('drawer')?.classList.contains('open')){e.preventDefault();e.stopImmediatePropagation();close()}},true);
const back=$('drawerBackdrop');if(back)back.addEventListener('click',e=>{if(e.target===back)close()});
})();
</script>
'''
if 'capture-phase conflict click fix v2' not in s:
    s=s.replace('</body>',js+'\n</body>',1)
p.write_text(s,encoding='utf-8')
print('UI patch applied')
