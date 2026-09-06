(()=>{
'use strict';

const DATA='data/intelligence_graph.json';
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

// Centralized visual vocabulary. Colors describe intelligence domains; they are never random.
const INTELLIGENCE_NODE_COLORS=Object.freeze({
  conflict:'#ff4d5f',
  war:'#ff4d5f',
  military:'#ff8a3d',
  economic:'#ffd166',
  market:'#ffd166',
  finance:'#ffd166',
  organization:'#49e28b',
  coalition:'#49e28b',
  actor:'#65a7ff',
  country:'#65a7ff',
  geopolitical:'#4dc9ff',
  political:'#b18cff',
  infrastructure:'#31d7c5',
  strategic:'#31d7c5',
  chokepoint:'#31d7c5',
  'organized-crime':'#c66cff',
  cartel:'#c66cff',
  criminal:'#c66cff',
  location:'#43c8ff',
  event:'#ff6f91',
  evidence:'#d9e5ef',
  source:'#d9e5ef',
  operation:'#ff8a3d',
  default:'#8da5b8'
});

const RELATION_COLORS=Object.freeze({
  conflict:'#ff4d5f',
  military:'#ff8a3d',
  economic:'#ffd166',
  market:'#ffd166',
  geopolitical:'#4dc9ff',
  criminal:'#c66cff',
  infrastructure:'#31d7c5',
  evidence:'#9bb0c2',
  default:'#58748b'
});

let graph=null;
let state={nodes:[],links:[],updatedAt:'',caution:'',selected:null,hovered:null,filters:{kind:'all',period:'24h',search:''},labels:true,relationships:true,orbit:false,mode:'3d'};
let lastPositions=new Map();

function normalize(d){
  const rawNodes=Array.isArray(d.nodes)?d.nodes:[];
  const rawEdges=Array.isArray(d.edges)?d.edges:[];
  const nodes=[]; const ids=new Set();
  for(const n of rawNodes){
    const id=String(n?.id??'').trim();
    if(!id||ids.has(id))continue;
    const evidence=Array.isArray(n.evidence)?n.evidence.filter(Boolean):[];
    if(!evidence.length)continue;
    ids.add(id);
    const mentions=Number(n.mentions??n.weight??0);
    const importance=Number(n.importance??n.significance??0);
    const confidence=typeof n.confidence==='number'?n.confidence:(String(n.confidence||'').toLowerCase()==='high'?1:String(n.confidence||'').toLowerCase()==='medium'?.65:.35);
    const time=n.updatedAt||n.time||n.timestamp||evidence.map(e=>e.time).filter(Boolean).sort().pop()||'';
    nodes.push({
      ...n,id,label:String(n.label||n.name||id),kind:String(n.kind||'default').toLowerCase(),
      mentions:Number.isFinite(mentions)?mentions:0,importance:Number.isFinite(importance)?importance:0,
      confidence:Number.isFinite(confidence)?Math.max(0,Math.min(1,confidence)):0.35,
      evidence,summary:String(n.summary||n.description||''),time
    });
  }
  const links=[]; const seen=new Set();
  for(const e of rawEdges){
    const source=String(e?.source?.id??e?.source??'').trim();
    const target=String(e?.target?.id??e?.target??'').trim();
    if(!ids.has(source)||!ids.has(target)||source===target)continue;
    const evidence=Array.isArray(e.evidence)?e.evidence.filter(Boolean):[];
    if(!evidence.length)continue;
    const key=source+'>'+target+'|'+String(e.relationship||e.type||'');
    if(seen.has(key))continue; seen.add(key);
    links.push({...e,source,target,evidence,weight:Number(e.weight||1),relationship:String(e.relationship||e.type||'evidence-backed relationship')});
  }
  // Prefer connected/high-value records if a pathological source publishes an enormous graph.
  if(nodes.length>5000){
    const degree=new Map(nodes.map(n=>[n.id,0])); links.forEach(l=>{degree.set(l.source,(degree.get(l.source)||0)+1);degree.set(l.target,(degree.get(l.target)||0)+1)});
    nodes.sort((a,b)=>(degree.get(b.id)||0)+(b.importance||0)*2-(degree.get(a.id)||0)-(a.importance||0)*2);
    nodes.length=5000;
    const keep=new Set(nodes.map(n=>n.id));
    return {nodes,links:links.filter(l=>keep.has(l.source)&&keep.has(l.target)),updatedAt:d.updatedAt||'',caution:d.caution||''};
  }
  return {nodes,links,updatedAt:d.updatedAt||'',caution:d.caution||''};
}

function nodeColor(n){return INTELLIGENCE_NODE_COLORS[n.kind]||INTELLIGENCE_NODE_COLORS.default}
function relationColor(l){
  const s=String(l.relationship||'').toLowerCase()+' '+String((l.types||[]).join(' ')).toLowerCase();
  for(const k of Object.keys(RELATION_COLORS))if(k!=='default'&&s.includes(k))return RELATION_COLORS[k];
  return RELATION_COLORS.default;
}
function ageFactor(n){
  const t=Date.parse(n.time||''); if(!Number.isFinite(t))return .55;
  const hours=Math.max(0,(Date.now()-t)/36e5); return Math.max(.18,Math.min(1,Math.exp(-hours/72)));
}
function nodeVal(n){
  const degree=n.__degree||0;
  return Math.max(1.5,Math.min(70,2+Math.sqrt(degree+1)*2.7+(Number(n.mentions)||0)*.45+(Number(n.importance)||0)*2+Number(n.confidence||0)*2));
}
function currentNodes(){
  const q=state.filters.search.trim().toLowerCase(); const period=state.filters.period;
  const cutoff=period==='all'?0:Date.now()-({ '1h':36e5,'6h':216e5,'24h':864e5,'7d':6048e5,'30d':2592e6,'90d':7776e6 }[period]||864e5);
  return state.nodes.filter(n=>{
    const kind=state.filters.kind;
    const kindOK=kind==='all'||n.kind===kind||String(n.kind).includes(kind);
    const textOK=!q||[n.label,n.kind,n.country,n.group,n.summary].join(' ').toLowerCase().includes(q);
    const time=Date.parse(n.time||'');
    const timeOK=!cutoff||!Number.isFinite(time)||time>=cutoff;
    return kindOK&&textOK&&timeOK;
  });
}
function buildGraphData(){
  const nodes=currentNodes(); const keep=new Set(nodes.map(n=>n.id));
  const links=state.links.filter(l=>keep.has(l.source)&&keep.has(l.target));
  const degree=new Map(nodes.map(n=>[n.id,0])); links.forEach(l=>{degree.set(l.source,(degree.get(l.source)||0)+1);degree.set(l.target,(degree.get(l.target)||0)+1)});
  nodes.forEach(n=>{n.__degree=degree.get(n.id)||0;const p=lastPositions.get(n.id);if(p){n.x=p.x;n.y=p.y;n.z=p.z}});
  return {nodes,links};
}
function style(){
  if(document.getElementById('gp3d-style'))return;
  const s=document.createElement('style');s.id='gp3d-style';s.textContent=`
#graph{position:fixed!important;inset:0!important;width:100%!important;height:100%!important;border:0!important;border-radius:0!important;background:#01050a!important;overflow:hidden!important}
#graph canvas{display:block;touch-action:none}
.gp-hud{position:absolute;left:14px;top:14px;z-index:30;pointer-events:none;display:flex;gap:8px;align-items:flex-start}.gp-title,.gp-badge,.gp-reset{background:rgba(2,7,12,.86);border:1px solid #193041;backdrop-filter:blur(14px);box-shadow:0 10px 40px #0009;border-radius:9px}.gp-title{padding:9px 11px}.gp-title b{display:block;color:#67ffab;font:900 10px/1 system-ui;letter-spacing:.16em}.gp-title span{display:block;color:#7890a2;font:700 8px/1.5 system-ui;margin-top:4px}.gp-badge{padding:8px;color:#9bb0bf;font:800 8px system-ui}.gp-reset{pointer-events:auto;color:#dbe8f1;padding:8px 10px;font:800 8px system-ui;cursor:pointer}.gp-tooltip{position:fixed;z-index:60;pointer-events:none;max-width:260px;padding:7px 9px;border:1px solid #294357;border-radius:8px;background:rgba(2,7,12,.96);color:#edf6ff;font:800 10px system-ui;box-shadow:0 12px 45px #000b}.gpfocus{position:absolute;right:14px;top:14px;z-index:50;width:min(410px,calc(100vw - 28px));max-height:calc(100vh - 28px);overflow:auto;background:rgba(3,9,15,.96);border:1px solid #284255;border-radius:13px;padding:14px;box-shadow:0 20px 80px #000c;backdrop-filter:blur(18px);color:#e9f3fb}.gpfocus h3{margin:0 35px 3px 0;font:900 19px system-ui}.gpfocus .close{position:absolute;right:9px;top:6px;background:none;border:0;color:#91a6b5;font-size:24px;cursor:pointer}.gpkind{color:#7e98aa;font:800 8px system-ui;letter-spacing:.12em}.gppills{display:flex;gap:5px;flex-wrap:wrap;margin-top:10px}.gppill{padding:5px 7px;border:1px solid #243c4e;border-radius:7px;color:#b8c8d4;font:800 8px system-ui}.gpsummary,.gpsource,.gprel{margin-top:10px;padding:9px;border:1px solid #1a3141;border-radius:8px;background:#06111a;font:500 9px/1.45 system-ui}.gprel b{font-size:10px}.gpsource a{display:block;margin-top:5px;color:#65a7ff;font-weight:900;text-decoration:none}.gpline{border-top:1px solid #172b39;margin-top:10px;padding-top:10px}@media(max-width:700px){.gp-hud{left:8px;top:54px;right:8px}.gp-title{max-width:calc(100vw - 100px)}.gp-badge{display:none}.gpfocus{left:8px;right:8px;top:auto;bottom:8px;width:auto;max-height:58%}.gp-title span{display:none}}
`;
  document.head.appendChild(s);
}
function addOverlay(){
  const host=$('graph');
  let h=host.querySelector('.gp-hud');
  if(!h){h=document.createElement('div');h.className='gp-hud';h.innerHTML='<div class="gp-title"><b>GLOBAL PULSE // INTELLIGENCE BRAIN</b><span>Living evidence-linked knowledge graph · 3D spatial network</span></div><div class="gp-badge" id="gp-badge">0 NODES · 0 LINKS</div><button class="gp-reset" id="gp-reset">RESET VIEW</button>';host.appendChild(h);$('gp-reset').onclick=resetView}
}
function inspector(n){
  const host=$('graph');let p=host.querySelector('.gpfocus');if(!p){p=document.createElement('div');p.className='gpfocus';host.appendChild(p)}
  const connected=state.links.filter(l=>l.source===n.id||l.target===n.id); const related=connected.slice(0,12);
  let html='<button class="close" id="gp-close">×</button><h3>'+esc(n.label)+'</h3><div class="gpkind">'+esc(String(n.kind).toUpperCase())+'</div>';
  html+='<div class="gppills"><span class="gppill">'+connected.length+' connections</span><span class="gppill">'+(n.mentions||0)+' signals</span><span class="gppill">'+n.evidence.length+' evidence records</span><span class="gppill">'+Math.round((n.confidence||0)*100)+'% confidence</span></div>';
  if(n.summary)html+='<div class="gpsummary">'+esc(n.summary)+'</div>';
  if(n.time)html+='<div class="gpline"><div class="gpkind">LATEST OBSERVATION</div><div class="gpsource">'+esc(n.time)+'</div></div>';
  if(related.length){html+='<div class="gpline"><div class="gpkind">RELATIONSHIPS</div>';for(const l of related){const other=state.nodes.find(x=>x.id===(l.source===n.id?l.target:l.source));if(!other)continue;html+='<div class="gprel"><b>'+esc(other.label)+'</b><div class="gpkind">'+esc(l.relationship)+'</div>';for(const ev of (l.evidence||[]).slice(0,2)){let u='';try{const x=new URL(ev.url||'');if(/^https?:$/.test(x.protocol))u=x.href}catch(_){}html+='<div class="gpsource"><b>'+esc(ev.source||'Public source')+'</b><br>'+esc(ev.title||'Evidence record')+(u?'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">OPEN SOURCE ↗</a>':'')+'</div>'}html+='</div>'}html+='</div>'}
  if(n.evidence.length){html+='<div class="gpline"><div class="gpkind">SOURCE EVIDENCE</div>';for(const ev of n.evidence.slice(0,8)){let u='';try{const x=new URL(ev.url||'');if(/^https?:$/.test(x.protocol))u=x.href}catch(_){}html+='<div class="gpsource"><b>'+esc(ev.source||'Public source')+'</b><br>'+esc(ev.title||'Evidence record')+(ev.summary?'<div>'+esc(ev.summary)+'</div>':'')+(u?'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">OPEN SOURCE ↗</a>':'')+'</div>'}html+='</div>'}
  p.innerHTML=html;p.hidden=false;$('gp-close').onclick=clearSelection;
}
function clearSelection(){state.selected=null;const p=document.querySelector('.gpfocus');if(p)p.hidden=true;if(graph)graph.refresh()}
function selectNode(n){state.selected=n;inspector(n);graph.centerAt(n.x,n.y,700);graph.zoom(5,700);graph.refresh()}
function resetView(){state.selected=null;const p=document.querySelector('.gpfocus');if(p)p.hidden=true;if(graph){graph.zoomToFit(900,60);graph.refresh()}}
function installGraph(){
  if(typeof ForceGraph3D!=='function')throw new Error('3D graph renderer unavailable');
  graph=ForceGraph3D()(document.getElementById('graph'))
    .backgroundColor('#01050a')
    .showNavInfo(false)
    .nodeId('id')
    .nodeLabel(n=>state.labels?`<b>${esc(n.label)}</b><br><small>${esc(String(n.kind).toUpperCase())}</small>`:'')
    .nodeColor(n=>{if(state.selected){const connected=new Set([state.selected.id]);state.links.forEach(l=>{if(l.source===state.selected.id)connected.add(l.target);if(l.target===state.selected.id)connected.add(l.source)});if(!connected.has(n.id))return '#14212b'}return nodeColor(n)})
    .nodeVal(n=>nodeVal(n))
    .nodeOpacity(n=>Math.max(.25,ageFactor(n)))
    .linkColor(l=>state.relationships?relationColor(l):'rgba(0,0,0,0)')
    .linkOpacity(l=>state.relationships?Math.max(.08,Math.min(.55,(Number(l.weight)||1)*.18)):0)
    .linkWidth(l=>Math.min(2.2,.35+(Number(l.weight)||1)*.18))
    .linkDirectionalParticles(l=>state.orbit?1:0)
    .linkDirectionalParticleWidth(1.4)
    .linkDirectionalParticleSpeed(.003)
    .cooldownTicks(260)
    .warmupTicks(80)
    .d3AlphaDecay(.028)
    .d3VelocityDecay(.32)
    .onNodeHover(n=>{state.hovered=n;document.body.style.cursor=n?'pointer':'default';if(n){let t=document.querySelector('.gp-tooltip');if(!t){t=document.createElement('div');t.className='gp-tooltip';document.body.appendChild(t)}t.textContent=n.label;t.style.left='0px';t.style.top='0px';t.style.transform='translate(12px,12px)'}else{const t=document.querySelector('.gp-tooltip');if(t)t.remove()};graph.refresh()})
    .onNodeClick(n=>selectNode(n))
    .onNodeDragEnd(n=>{lastPositions.set(n.id,{x:n.x,y:n.y,z:n.z})});
  const controls=graph.controls();if(controls){controls.enableDamping=true;controls.dampingFactor=.08;controls.rotateSpeed=.55;controls.zoomSpeed=.8;controls.panSpeed=.65;controls.minDistance=25;controls.maxDistance=10000}
  graph.d3Force('charge').strength(-95).distanceMax(800);
  graph.d3Force('link').distance(l=>Math.max(25,80-(Number(l.weight)||1)*8)).strength(l=>Math.min(.7,.08+(Number(l.weight)||1)*.08));
  graph.onEngineStop(()=>{for(const n of state.nodes)if(Number.isFinite(n.x))lastPositions.set(n.id,{x:n.x,y:n.y,z:n.z});updateStats()});
  window.addEventListener('pointermove',e=>{const t=document.querySelector('.gp-tooltip');if(t&&state.hovered){t.style.left=e.clientX+'px';t.style.top=e.clientY+'px'}});
  addOverlay();
}
function updateStats(){const b=$('gp-badge'),s=$('stats');const d=graph?.graphData?.()||{nodes:[],links:[]};const text=`${d.nodes.length.toLocaleString()} nodes · ${d.links.length.toLocaleString()} evidence-backed relationships · refreshed ${state.updatedAt?new Date(state.updatedAt).toLocaleString():'unknown'}`;if(b)b.textContent=`${d.nodes.length.toLocaleString()} NODES · ${d.links.length.toLocaleString()} LINKS`;if(s)s.textContent=text}
function redraw(reheat=true){if(!graph)return;const d=buildGraphData();graph.graphData(d);if(reheat)graph.d3ReheatSimulation();updateStats();const l=$('loading');if(l)l.style.display='none';}
async function loadData(){const r=await fetch(DATA+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);return normalize(await r.json())}
function bindControls(){
  document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');state.filters.kind=b.dataset.kind||'all';redraw(true)}));
  const search=$('search');if(search)search.addEventListener('input',()=>{state.filters.search=search.value;redraw(false)});
  $('clear')?.addEventListener('click',()=>{if(search)search.value='';state.filters.search='';document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x.dataset.kind==='all'));redraw(false)});
  $('reset')?.addEventListener('click',resetView);
  $('refresh')?.addEventListener('click',async()=>{const btn=$('refresh');if(btn)btn.disabled=true;try{state=Object.assign(state,await loadData());redraw(true)}catch(e){showError(e)}finally{if(btn)btn.disabled=false}});
  $('orbit')?.addEventListener('click',()=>{state.orbit=!state.orbit;document.getElementById('orbit').classList.toggle('active',state.orbit);graph?.linkDirectionalParticles(state.orbit?1:0);graph?.refresh()});
  $('flow')?.addEventListener('click',()=>{state.relationships=!state.relationships;document.getElementById('flow').classList.toggle('active',state.relationships);graph?.refresh()});
  document.querySelectorAll('.period').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.period').forEach(x=>x.classList.remove('active'));b.classList.add('active');state.filters.period=b.dataset.period||'24h';redraw(true)}));
  // Progressive label control without adding another required DOM dependency.
  const row=document.querySelector('#controls .row');if(row){const b=document.createElement('button');b.id='labels';b.textContent='LABELS ON';b.className='active';b.onclick=()=>{state.labels=!state.labels;b.textContent=state.labels?'LABELS ON':'LABELS OFF';b.classList.toggle('active',state.labels);graph?.nodeLabel(n=>state.labels?`<b>${esc(n.label)}</b><br><small>${esc(String(n.kind).toUpperCase())}</small>`:'');graph?.refresh()};row.appendChild(b)}
}
function showError(e){const l=$('loading');if(l){l.classList.add('error');l.style.display='grid';l.innerHTML='INTELLIGENCE BRAIN UNAVAILABLE<br><small>'+esc(e?.message||e)+'</small><br><small>Last valid graph state is preserved when available.</small>'}}
(async function(){
  style();
  try{
    state=Object.assign(state,await loadData());
    installGraph();
    bindControls();
    redraw(true);
  }catch(e){showError(e)}
})();
})();
