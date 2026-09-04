/* Global Pulse Intelligence Web v1
 * Uses the proven 3d-force-graph API pattern from vasturiano's open-source project.
 * The component is intentionally isolated from the 2D map and fails closed.
 */
(function(){
'use strict';
const DATA_URL='data/snapshot.json';
let graph=null, loaded=false;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const typeColor=t=>({conflict:'#ff304f',military:'#ff7a00',political:'#b56cff',economic:'#ffd400',osint:'#00e5ff',country:'#39ff88',event:'#fff'}[t]||'#39ff88');
function buildData(d){
 const nodes=[],links=[],byId=new Map();
 const add=(id,name,type,extra={})=>{if(!id||byId.has(id))return byId.get(id);const n={id:String(id),name:String(name||id),type:type||'event',...extra};byId.set(n.id,n);nodes.push(n);return n};
 const markers=Array.isArray(d?.markers)?d.markers:[];
 markers.slice(0,450).forEach((m,i)=>{const title=m.title||m.name||m.location||m.region||`Signal ${i+1}`;const type=/conflict|war|military|strike|attack/i.test(`${m.layer} ${m.eventType} ${title}`)?'conflict':/market|economic|oil|trade/i.test(`${m.layer} ${m.eventType} ${title}`)?'economic':/politic|diplomat/i.test(`${m.layer} ${m.eventType} ${title}`)?'political':'osint';const id='signal:'+String(m.id||m.url||i);add(id,title,type,{region:m.region||'',source:m.source||m.sourceLabel||'',url:m.url||m.sourceUrl||''});if(m.region){const r=add('region:'+m.region,m.region,'country');links.push({source:id,target:r.id,type:'located-in'});}});
 const watch=d?.conflictCoverage?.watchlist||[];watch.forEach(w=>{const id='conflict:'+w.id;add(id,w.title,'conflict',{region:w.region,status:w.status,confidence:w.confidence});if(w.region){const r=add('region:'+w.region,w.region,'country');links.push({source:id,target:r.id,type:'in-region'});}});
 const seen=new Set();return {nodes,links:links.filter(l=>{const k=`${l.source}|${l.target}`;if(seen.has(k))return false;seen.add(k);return true})};
}
function mount(d){
 const host=$('intelligence-web-3d');if(!host||typeof window.ForceGraph3D!=='function')return false;
 const gd=buildData(d);if(!gd.nodes.length){host.innerHTML='<div class="iw-empty">NO VERIFIED RELATIONSHIPS AVAILABLE</div>';return false;}
 host.innerHTML='';graph=window.ForceGraph3D(host,{controlType:'orbit'})(gd)
 .backgroundColor('#020805').showNavInfo(false).nodeLabel(n=>`<b>${esc(n.name)}</b><br>${esc(n.type)}${n.region?` · ${esc(n.region)}`:''}${n.status?`<br>${esc(n.status)}`:''}`)
 .nodeColor(n=>typeColor(n.type)).nodeRelSize(5).nodeOpacity(.92)
 .linkColor(l=>l.type==='in-region'?'rgba(57,255,136,.28)':'rgba(0,229,255,.38)').linkWidth(1)
 .linkDirectionalParticles(1).linkDirectionalParticleWidth(2)
 .enableNodeDrag(true).enableNavigationControls(true)
 .onNodeClick(n=>{const box=$('intelligence-web-detail');if(box)box.innerHTML=`<b>${esc(n.name)}</b><br><small>${esc(n.type)}${n.region?' · '+esc(n.region):''}${n.source?' · '+esc(n.source):''}</small>${n.url?`<br><a href="${esc(n.url)}" target="_blank" rel="noopener">Open source</a>`:''}`;});
 graph.d3Force('charge').strength(-85);graph.d3Force('link').distance(80);graph.d3ReheatSimulation();return true;
}
function loadLib(cb){if(typeof window.ForceGraph3D==='function')return cb(true);const scripts=['https://cdn.jsdelivr.net/npm/3d-force-graph@1.79.0/dist/3d-force-graph.min.js','https://unpkg.com/3d-force-graph@1.79.0/dist/3d-force-graph.min.js'];let i=0;const next=()=>{if(i>=scripts.length)return cb(false);const s=document.createElement('script');s.src=scripts[i++];s.onload=()=>cb(typeof window.ForceGraph3D==='function');s.onerror=next;document.head.appendChild(s)};next()}
async function start(){if(loaded)return;loaded=true;const host=$('intelligence-web-3d');if(!host)return;host.innerHTML='<div class="iw-loading">LOADING INTELLIGENCE WEB…</div>';let d=window.DATA;if(!d){try{const r=await fetch(DATA_URL,{cache:'no-store'});d=await r.json()}catch(e){host.innerHTML='<div class="iw-error">DATA LINK OFFLINE</div>';return}}
 loadLib(ok=>{if(!ok){host.innerHTML='<div class="iw-error">3D ENGINE UNAVAILABLE — 2D MAP IS STILL ACTIVE</div>';return}mount(d)})}
window.GlobalPulseIntelligenceWeb={start,mount,buildData};
})();
