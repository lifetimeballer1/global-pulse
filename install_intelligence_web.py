#!/usr/bin/env python3
"""Install the standalone 3D Intelligence Web without touching the canonical map."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
PAGE = ROOT / "intelligence-web.html"

PAGE_TEXT = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#03070a">
<title>Global Pulse — Intelligence Web</title>
<style>
:root{--bg:#03070a;--panel:rgba(5,12,16,.92);--line:#17302a;--text:#dfffea;--muted:#7fa998;--green:#39ff88;--red:#ff5368;--amber:#ffc857;--blue:#62a0ff;--purple:#b58cff;--cyan:#48d9ff}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:var(--bg);color:var(--text);font:13px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}#graph{position:fixed;inset:0}#hud{position:fixed;z-index:5;left:12px;top:12px;width:min(390px,calc(100vw - 24px));pointer-events:none}.card{pointer-events:auto;background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:0 12px 40px #0009;backdrop-filter:blur(12px);padding:11px}.title{font-weight:950;letter-spacing:.13em;color:var(--green)}.sub{color:var(--muted);font-size:10px;margin-top:3px}.row{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}button{border:1px solid var(--line);background:#07120f;color:var(--text);border-radius:8px;padding:7px 9px;font-weight:800;font-size:10px}button.active{border-color:var(--green);color:var(--green)}#stats{margin-top:8px;color:var(--muted);font-size:10px}#details{position:fixed;z-index:6;right:12px;top:12px;width:min(340px,calc(100vw - 24px));display:none}.detail-title{font-weight:900;font-size:16px}.pill{display:inline-block;padding:3px 6px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:9px;margin:5px 4px 0 0}.evidence{margin-top:8px;padding-top:8px;border-top:1px solid var(--line);font-size:10px;color:var(--muted)}.evidence a{color:var(--blue);display:block;margin-top:5px}.hint{position:fixed;z-index:4;bottom:12px;left:50%;transform:translateX(-50%);background:#020805d9;border:1px solid var(--line);border-radius:999px;padding:7px 11px;color:var(--muted);font-size:10px;white-space:nowrap}.error{color:var(--red)}@media(max-width:700px){#details{top:auto;bottom:54px}.hint{bottom:10px;font-size:9px}.title{font-size:12px}}
</style>
<script id="gp-forcegraph-loader">
(function(){
  function load(src,ok,bad){var s=document.createElement('script');s.src=src;s.onload=ok;s.onerror=bad;document.head.appendChild(s)}
  window.gpLoadForceGraph=function(done){
    if(window.ForceGraph3D)return done();
    load('https://unpkg.com/3d-force-graph',done,function(){load('https://cdn.jsdelivr.net/npm/3d-force-graph',done,function(){done(new Error('3D graph library failed to load'))})})
  };
})();
</script>
</head>
<body>
<div id="graph"></div>
<div id="hud"><div class="card"><div class="title">GLOBAL PULSE // INTELLIGENCE WEB</div><div class="sub">Evidence-linked relationships. Shared reporting is not proof of causation, coordination, or alliance.</div><div class="row"><button id="all" class="active">ALL</button><button data-kind="actor">ACTORS</button><button data-kind="political">POLITICAL</button><button data-kind="economic">ECONOMIC</button><button data-kind="strategic">STRATEGIC</button></div><div class="row"><button id="reset">RESET VIEW</button><button id="orbit">AUTO ORBIT</button><button id="particles">RELATION FLOW</button></div><div id="stats">Loading intelligence graph…</div></div></div>
<div id="details"><div class="card"><div id="detailContent"></div><div class="row"><button id="close">CLOSE</button></div></div></div>
<div class="hint">DRAG A NODE · CONNECTED NODES REACT · CLICK A NODE FOR EVIDENCE</div>
<script>
(function(){
'use strict';
var graph=null, raw=null, visibleKind='all', orbit=false, particles=false;
var $=function(id){return document.getElementById(id)};
var esc=function(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})};
var safeUrl=function(v){try{var u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch(e){return ''}};
function kindColor(k){return ({actor:'#39ff88',political:'#b58cff',economic:'#ffc857',strategic:'#48d9ff'}[k]||'#62a0ff')}
function buildFallback(d){
 var nodes=[],links=[],by={};
 function add(id,label,kind){if(!by[id]){by[id]={id:id,label:label,kind:kind,mentions:1};nodes.push(by[id])}else by[id].mentions++}
 var conflicts=Array.isArray(d.conflicts)?d.conflicts:[];
 conflicts.forEach(function(c,i){var label=c.name||c.title||('Conflict '+(i+1));var id='conflict-'+i;add(id,label,'strategic');var region=String(c.region||'');if(region){var rid='region-'+region.toLowerCase().replace(/[^a-z0-9]+/g,'-');add(rid,region,'political');links.push({source:id,target:rid,weight:2,type:'conflict'})}});
 (Array.isArray(d.markers)?d.markers:[]).slice(0,300).forEach(function(m,i){var label=m.title||m.name||m.region||('Signal '+(i+1));var id='signal-'+(m.id||i);add(id,label,'strategic')});
 return {nodes:nodes.slice(0,500),links:links.slice(0,700)}
}
function normalize(d){
 var g=d&&d.intelligenceGraph; if(g&&Array.isArray(g.nodes)&&g.nodes.length&&Array.isArray(g.edges)&&g.edges.length){return {nodes:g.nodes.map(function(n){return Object.assign({},n,{id:String(n.id),label:n.label||n.id,kind:n.kind||'actor'})}),links:g.edges.map(function(e){return {source:String(e.source),target:String(e.target),weight:Number(e.weight)||1,types:e.types||[],evidence:e.evidence||[]}})}}
 return buildFallback(d||{});
}
function filtered(){var g=normalize(raw);if(visibleKind==='all')return g;var keep={};g.nodes.forEach(function(n){if(n.kind===visibleKind)keep[n.id]=1});var links=g.links.filter(function(l){return keep[l.source]||keep[l.target]});var ids={};links.forEach(function(l){ids[l.source]=1;ids[l.target]=1});return {nodes:g.nodes.filter(function(n){return ids[n.id]}),links:links}}
function render(){
 var data=filtered();
 if(!window.ForceGraph3D){$('stats').innerHTML='<span class="error">3D renderer failed to load. Try refreshing.</span>';return}
 if(!graph){graph=ForceGraph3D({controlType:'orbit'})($('graph')).backgroundColor('#03070a').showNavInfo(false).nodeId('id').nodeLabel(function(n){return esc(n.label)+' · '+esc(n.kind||'signal')}).nodeColor(function(n){return kindColor(n.kind)}).nodeVal(function(n){return Math.max(1,Math.min(14,Number(n.mentions)||1))}).linkColor(function(){return 'rgba(57,255,136,.28)'}).linkWidth(function(l){return Math.max(.4,Math.min(3,Number(l.weight)||1))}).linkDirectionalParticles(function(){return particles?2:0}).linkDirectionalParticleSpeed(function(l){return .004+Math.min(.012,(Number(l.weight)||1)*.001)}).enableNodeDrag(true).onNodeClick(select).onNodeHover(function(n){$('graph').style.cursor=n?'pointer':'default'}).d3VelocityDecay(.32).d3AlphaDecay(.018).warmupTicks(40).cooldownTime(12000)}
 graph.graphData(data); graph.d3ReheatSimulation(); $('stats').textContent=data.nodes.length+' nodes · '+data.links.length+' relationships · '+(raw.updatedAt?'data '+new Date(raw.updatedAt).toLocaleString():'live snapshot');
}
function select(n){var c=$('detailContent');var ev=Array.isArray(n.evidence)?n.evidence:[];var html='<div class="detail-title">'+esc(n.label)+'</div><div><span class="pill">'+esc(n.kind||'signal')+'</span><span class="pill">'+esc(n.mentions||0)+' mentions</span></div>';if(ev.length){html+='<div class="evidence"><b>Evidence</b>';ev.slice(0,5).forEach(function(e){var u=safeUrl(e.url);html+='<div style="margin-top:7px">'+esc(e.title||'Public report')+'<br><span>'+esc(e.source||'Public source')+'</span>'+(u?'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">Open source ↗</a>':'')+'</div>'});html+='</div>'}c.innerHTML=html;$('details').style.display='block';if(graph&&n.x!=null)graph.cameraPosition({x:n.x*2,y:n.y*2,z:n.z*2},n,900)}
function loadData(){fetch('data/snapshot.json?gp_intel='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('snapshot '+r.status);return r.json()}).then(function(d){raw=d;render()}).catch(function(e){$('stats').innerHTML='<span class="error">Snapshot unavailable: '+esc(e.message)+'</span>'})}
$('all').onclick=function(){visibleKind='all';document.querySelectorAll('[data-kind]').forEach(function(b){b.classList.remove('active')});$('all').classList.add('active');render()};
document.querySelectorAll('[data-kind]').forEach(function(b){b.onclick=function(){visibleKind=b.getAttribute('data-kind');document.querySelectorAll('[data-kind],#all').forEach(function(x){x.classList.remove('active')});b.classList.add('active');render()}});
$('reset').onclick=function(){if(graph)graph.zoomToFit(900,80)};
$('orbit').onclick=function(){orbit=!orbit;$('orbit').classList.toggle('active',orbit);if(graph){if(orbit){graph.enableNavigationControls(false);(function tick(){if(!orbit)return;graph.cameraPosition({x:0,y:0,z:Math.max(350,graph.camera().position.z)},{x:0,y:0,z:0},0);requestAnimationFrame(tick)})()}else graph.enableNavigationControls(true)}};
$('particles').onclick=function(){particles=!particles;$('particles').classList.toggle('active',particles);if(graph)graph.linkDirectionalParticles(function(){return particles?2:0}).refresh()};
$('close').onclick=function(){$('details').style.display='none'};
window.addEventListener('resize',function(){if(graph)graph.width(window.innerWidth).height(window.innerHeight)});
gpLoadForceGraph(function(err){if(err){$('stats').innerHTML='<span class="error">3D library unavailable. The 2D map remains unaffected.</span>';return}loadData()});
})();
</script>
</body>
</html>
'''

BUTTON = '<!-- GP-INTELLIGENCE-WEB-START --><div class="gp-intel-web-entry" style="display:flex;justify-content:center;margin:4px 0"><a href="intelligence-web.html" style="display:inline-block;padding:9px 14px;border:1px solid #39ff88;border-radius:9px;background:rgba(57,255,136,.08);color:#39ff88;font-weight:900;letter-spacing:.08em;font-size:11px">◈ INTELLIGENCE WEB — 3D</a></div><!-- GP-INTELLIGENCE-WEB-END -->'

PAGE.write_text(PAGE_TEXT, encoding='utf-8')
html = INDEX.read_text(encoding='utf-8')
start='<!-- GP-INTELLIGENCE-WEB-START -->'; end='<!-- GP-INTELLIGENCE-WEB-END -->'
if start in html and end in html:
    a=html.index(start); b=html.index(end,a)+len(end); html=html[:a]+BUTTON+html[b:]
elif '</body>' in html:
    html=html.replace('</body>', BUTTON+'</body>', 1)
else:
    raise SystemExit('index.html has no </body>')
INDEX.write_text(html, encoding='utf-8')
print('Installed standalone 3D Intelligence Web and main-dashboard entry point.')
