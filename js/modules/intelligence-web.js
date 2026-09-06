/** Intelligence Web — restored 3D relationship surface using the source-backed intelligence graph. */
import { getState } from '../core/state.js';
import { escapeHtml, formatRelativeTime } from '../core/utils.js';

let graphInstance = null;
let libraryPromise = null;

function typeColor(type) {
  return ({ conflict:'#ff304f', military:'#ff7a00', political:'#b56cff', economic:'#ffd400', osint:'#00e5ff', country:'#39ff88', event:'#ffffff' })[type] || '#39ff88';
}

function buildGraphData(graph, snapshot) {
  const source = graph || snapshot?.intelligenceGraph || snapshot?.graph || {};
  const rawNodes = Array.isArray(source.nodes) ? source.nodes : (Array.isArray(source.entities) ? source.entities : []);
  const rawEdges = Array.isArray(source.edges) ? source.edges : (Array.isArray(source.links) ? source.links : []);
  const nodes = [];
  const byId = new Map();
  const add = (id, name, type, extra={}) => {
    if (!id) return null;
    const key = String(id);
    if (byId.has(key)) return byId.get(key);
    const node = { id:key, name:String(name || id), type:type || 'event', ...extra };
    byId.set(key, node); nodes.push(node); return node;
  };
  rawNodes.slice(0, 500).forEach(n => {
    add(n.id || n.key || n.name || n.label, n.label || n.name || n.id, n.type || n.kind || n.category || 'event', {
      region:n.region || n.country || '', status:n.status || '', source:n.source || n.sourceLabel || '', url:n.url || n.sourceUrl || '', evidence:n.evidence || []
    });
  });
  rawEdges.slice(0, 1000).forEach(e => {
    const s=e.source || e.from, t=e.target || e.to;
    if (!s || !t) return;
    if (!byId.has(String(s)) || !byId.has(String(t))) return;
  });
  const links=[];
  const seen=new Set();
  rawEdges.forEach(e=>{
    const s=String(e.source || e.from || ''), t=String(e.target || e.to || '');
    if (!byId.has(s) || !byId.has(t)) return;
    const key=s+'|'+t; if(seen.has(key)) return; seen.add(key);
    links.push({source:s,target:t,type:e.type || e.relationship || 'related'});
  });
  return { nodes, links };
}

function loadLibrary() {
  if (window.ForceGraph3D) return Promise.resolve(true);
  if (libraryPromise) return libraryPromise;
  libraryPromise = new Promise(resolve => {
    const urls = [
      'https://cdn.jsdelivr.net/npm/3d-force-graph@1.79.0/dist/3d-force-graph.min.js',
      'https://unpkg.com/3d-force-graph@1.79.0/dist/3d-force-graph.min.js'
    ];
    let i=0;
    const next=()=>{
      if(i>=urls.length){resolve(false);return;}
      const s=document.createElement('script');s.src=urls[i++];s.async=true;
      s.onload=()=>resolve(typeof window.ForceGraph3D==='function');s.onerror=next;
      document.head.appendChild(s);
    };
    next();
  });
  return libraryPromise;
}

function renderFallback(el, graph, snapshot) {
  const nodes=Array.isArray(graph?.nodes)?graph.nodes:[];
  const edges=Array.isArray(graph?.edges)?graph.edges:[];
  const degree={};
  edges.forEach(e=>{const s=e.source||e.from,t=e.target||e.to;if(s)degree[s]=(degree[s]||0)+1;if(t)degree[t]=(degree[t]||0)+1;});
  const top=[...nodes].map(n=>({...n,_deg:degree[n.id]||0})).sort((a,b)=>b._deg-a._deg).slice(0,14);
  el.innerHTML=`<div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px">3D engine unavailable. Evidence-backed relationships remain available below.</div><div class="gp-grid gp-grid-2">${top.map(n=>`<div class="gp-card"><div class="gp-card-title">${escapeHtml(n.label||n.name||n.id)}</div><div class="gp-card-meta">${escapeHtml(n.type||n.kind||'entity')} · ${n._deg} links</div></div>`).join('')}</div><div style="margin-top:10px;font-size:11px;color:var(--muted-2)">${edges.length} evidence-backed connections · ${nodes.length} entities</div>`;
}

function mount3D(host, detail, graph, snapshot) {
  if (!window.ForceGraph3D) return false;
  const data=buildGraphData(graph,snapshot);
  if (!data.nodes.length) { host.innerHTML='<div class="gp-state">NO VERIFIED RELATIONSHIPS AVAILABLE</div>'; return false; }
  host.innerHTML='';
  graphInstance=window.ForceGraph3D(host,{controlType:'orbit'})(data)
    .backgroundColor('#020805').showNavInfo(false)
    .nodeLabel(n=>`<b>${escapeHtml(n.name)}</b><br>${escapeHtml(n.type)}${n.region?' · '+escapeHtml(n.region):''}${n.status?'<br>'+escapeHtml(n.status):''}`)
    .nodeColor(n=>typeColor(n.type)).nodeRelSize(5).nodeOpacity(.92)
    .linkColor(()=> 'rgba(0,229,255,.38)').linkWidth(1)
    .linkDirectionalParticles(1).linkDirectionalParticleWidth(2)
    .enableNodeDrag(true).enableNavigationControls(true)
    .onNodeClick(n=>{
      detail.innerHTML=`<b>${escapeHtml(n.name)}</b><br><small>${escapeHtml(n.type)}${n.region?' · '+escapeHtml(n.region):''}${n.source?' · '+escapeHtml(n.source):''}</small>${n.url?`<br><a href="${escapeHtml(n.url)}" target="_blank" rel="noopener noreferrer">Open source</a>`:''}`;
    });
  if(graphInstance.d3Force){graphInstance.d3Force('charge').strength(-85);graphInstance.d3Force('link').distance(80);graphInstance.d3ReheatSimulation();}
  return true;
}

export function renderIntelligenceWeb() {
  const el=document.getElementById('intelwebBody'), updated=document.getElementById('intelwebUpdated');
  if(!el)return;
  const state=getState(), graph=state.intelligenceGraph || state.snapshot?.intelligenceGraph || state.snapshot?.graph;
  if(!graph){el.innerHTML='<div class="gp-state"><div class="gp-state-title">Intelligence Web not available</div><div>Evidence-linked relationship data has not been generated for this snapshot.</div></div>';return;}
  if(updated)updated.textContent=formatRelativeTime(graph.updatedAt || state.snapshot?.updatedAt);
  const caution=graph.caution || '';
  el.innerHTML=`<div style="font-size:12.5px;color:var(--text-secondary);margin-bottom:10px">Evidence-backed relationships between actors, conflicts, economic pressure and strategic interests. Connections require supporting public evidence; correlation is never treated as causation.</div>${caution?`<div class="gp-card" style="margin-bottom:10px;font-size:12px;color:var(--amber)">${escapeHtml(caution)}</div>`:''}<div id="gp-intelweb-3d" class="gp-intelweb-3d"></div><div id="gp-intelweb-detail" class="gp-intelweb-detail">Select a node to inspect its source-backed details.</div>`;
  const host=document.getElementById('gp-intelweb-3d'),detail=document.getElementById('gp-intelweb-detail');
  loadLibrary().then(ok=>{if(!host)return;if(ok){mount3D(host,detail,graph,state.snapshot);}else{renderFallback(el,graph,state.snapshot);}});
}
