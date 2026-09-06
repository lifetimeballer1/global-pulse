/** Intelligence Web — restored 3D relationship surface using the source-backed intelligence graph and Brain. */
import { getState } from '../core/state.js';
import { escapeHtml, formatRelativeTime } from '../core/utils.js';

let graphInstance = null;
let libraryPromise = null;

function typeColor(type) {
  return ({ conflict:'#ff304f', military:'#ff7a00', political:'#b56cff', economic:'#ffd400', osint:'#00e5ff', country:'#39ff88', event:'#ffffff', cartel:'#ff8a35', strategic:'#4d9aff' })[String(type||'').toLowerCase()] || '#39ff88';
}

function normalizeGraph(graph, brain) {
  const source = graph || {};
  const rawNodes = Array.isArray(source.nodes) ? source.nodes : (Array.isArray(source.entities) ? source.entities : []);
  const rawEdges = Array.isArray(source.edges) ? source.edges : (Array.isArray(source.links) ? source.links : []);
  const nodes = [];
  const byId = new Map();
  const links = [];

  const add = (id, name, type, extra={}) => {
    if (!id) return null;
    const key = String(id);
    if (byId.has(key)) return byId.get(key);
    const node = { id:key, name:String(name || id), type:type || 'event', ...extra };
    byId.set(key, node); nodes.push(node); return node;
  };

  rawNodes.slice(0, 500).forEach(n => add(
    n.id || n.key || n.name || n.label,
    n.label || n.name || n.id,
    n.type || n.kind || n.category || 'event',
    {region:n.region || n.country || '', status:n.status || '', source:n.source || n.sourceLabel || '', url:n.url || n.sourceUrl || '', evidence:n.evidence || []}
  ));

  if (brain?.sourceBackedOnly === true && Array.isArray(brain.nodes)) {
    brain.nodes.slice(0, 500).forEach(n => {
      const id = String(n.id || n.key || n.name || '');
      if (!id) return;
      const evidence = Array.isArray(n.evidence) ? n.evidence : [];
      const node = add(id, n.label || n.name || id, n.kind || n.type || 'entity', {
        region:n.region || n.country || '', status:n.status || '',
        source:n.source || n.sourceLabel || evidence[0]?.source || '',
        url:n.url || n.sourceUrl || evidence[0]?.url || '', evidence, brain:true
      });
      if (node) node.brain = true;
    });
    if (Array.isArray(brain.edges)) {
      brain.edges.slice(0, 1500).forEach(e => {
        const s=String(e.source || e.from || ''), t=String(e.target || e.to || '');
        if (!byId.has(s) || !byId.has(t) || s===t) return;
        links.push({source:s,target:t,type:e.relationship || e.label || e.type || 'related',brain:true,evidence:e.evidence || []});
      });
    }
  }

  const seen = new Set(links.map(e => `${e.source}|${e.target}`));
  rawEdges.slice(0, 1000).forEach(e => {
    const s=String(e.source || e.from || ''), t=String(e.target || e.to || '');
    if (!byId.has(s) || !byId.has(t) || s===t) return;
    const key=`${s}|${t}`;
    if (seen.has(key)) return;
    seen.add(key);
    links.push({source:s,target:t,type:e.type || e.relationship || 'related',evidence:e.evidence || []});
  });
  return {nodes,links};
}

function loadLibrary() {
  if (window.ForceGraph3D) return Promise.resolve(true);
  if (libraryPromise) return libraryPromise;
  libraryPromise = new Promise(resolve => {
    const urls = ['https://cdn.jsdelivr.net/npm/3d-force-graph@1.79.0/dist/3d-force-graph.min.js','https://unpkg.com/3d-force-graph@1.79.0/dist/3d-force-graph.min.js'];
    let i=0;
    const next=()=>{ if(i>=urls.length){resolve(false);return;} const s=document.createElement('script');s.src=urls[i++];s.async=true;s.onload=()=>resolve(typeof window.ForceGraph3D==='function');s.onerror=next;document.head.appendChild(s); };
    next();
  });
  return libraryPromise;
}

function renderFallback(el, data) {
  const nodes=Array.isArray(data?.nodes)?data.nodes:[], links=Array.isArray(data?.links)?data.links:[];
  const degree={};
  links.forEach(e=>{degree[e.source]=(degree[e.source]||0)+1;degree[e.target]=(degree[e.target]||0)+1;});
  const top=[...nodes].map(n=>({...n,_deg:degree[n.id]||0})).sort((a,b)=>b._deg-a._deg).slice(0,14);
  el.innerHTML=`<div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px">3D engine unavailable. The source-backed relationship web remains available below.</div><div class="gp-grid gp-grid-2">${top.map(n=>`<div class="gp-card"><div class="gp-card-title">${escapeHtml(n.name)}</div><div class="gp-card-meta">${escapeHtml(n.type||'entity')} · ${n._deg} links${n.brain?' · Brain':''}</div></div>`).join('')}</div><div style="margin-top:10px;font-size:11px;color:var(--muted-2)">${links.length} connections · ${nodes.length} entities</div>`;
}

function mount3D(host, detail, data) {
  if (!window.ForceGraph3D) return false;
  if (!data.nodes.length) { host.innerHTML='<div class="gp-state">NO VERIFIED RELATIONSHIPS AVAILABLE</div>'; return false; }
  host.innerHTML='';
  graphInstance=window.ForceGraph3D(host,{controlType:'orbit'})(data)
    .backgroundColor('#020805').showNavInfo(false)
    .nodeLabel(n=>`<b>${escapeHtml(n.name)}</b><br>${escapeHtml(n.type)}${n.region?' · '+escapeHtml(n.region):''}${n.status?'<br>'+escapeHtml(n.status):''}${n.brain?'<br>🧠 Brain-linked':''}`)
    .nodeColor(n=>typeColor(n.type)).nodeRelSize(5).nodeOpacity(.92)
    .linkColor(l=>l.brain?'rgba(176,140,255,.65)':'rgba(0,229,255,.38)').linkWidth(l=>l.brain?1.5:1)
    .linkDirectionalParticles(1).linkDirectionalParticleWidth(2)
    .enableNodeDrag(true).enableNavigationControls(true)
    .onNodeClick(n=>{
      const evidence=Array.isArray(n.evidence)?n.evidence:[], sourceUrl=n.url || evidence[0]?.url || '';
      detail.innerHTML=`<b>${escapeHtml(n.name)}</b><br><small>${escapeHtml(n.type)}${n.region?' · '+escapeHtml(n.region):''}${n.source?' · '+escapeHtml(n.source):''}${n.brain?' · Brain':''}</small>${sourceUrl?`<br><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">Open source</a>`:''}`;
      window.dispatchEvent(new CustomEvent('gp:brain-select',{detail:{id:String(n.id),source:'web'}}));
    });
  if(graphInstance.d3Force){graphInstance.d3Force('charge').strength(-85);graphInstance.d3Force('link').distance(80);graphInstance.d3ReheatSimulation();}
  return true;
}

export function renderIntelligenceWeb() {
  const el=document.getElementById('intelwebBody'), updated=document.getElementById('intelwebUpdated');
  if(!el)return;
  const state=getState(), graph=state.intelligenceGraph || state.snapshot?.intelligenceGraph || state.snapshot?.graph, brain=state.snapshot?.intelligenceBrain;
  if(!graph && !(brain?.sourceBackedOnly===true && Array.isArray(brain.nodes))){el.innerHTML='<div class="gp-state"><div class="gp-state-title">Intelligence Web not available</div><div>Evidence-linked relationship data has not been generated for this snapshot.</div></div>';return;}
  if(updated)updated.textContent=formatRelativeTime(graph?.updatedAt || brain?.updatedAt || state.snapshot?.updatedAt);
  const caution=graph?.caution || '';
  el.innerHTML=`<div style="font-size:12.5px;color:var(--text-secondary);margin-bottom:10px">Evidence-backed relationships between actors, conflicts, economic pressure, strategic interests and other signals. The original Intelligence Web is preserved; source-backed Brain relationships are layered into it when available. Correlation is never treated as causation.</div>${caution?`<div class="gp-card" style="margin-bottom:10px;font-size:12px;color:var(--amber)">${escapeHtml(caution)}</div>`:''}<div id="gp-intelweb-3d" class="gp-intelweb-3d"></div><div id="gp-intelweb-detail" class="gp-intelweb-detail">Select a node to inspect its source-backed details.</div>`;
  const host=document.getElementById('gp-intelweb-3d'),detail=document.getElementById('gp-intelweb-detail'),data=normalizeGraph(graph,brain);
  loadLibrary().then(ok=>{if(!host)return;if(ok){mount3D(host,detail,data);}else{renderFallback(el,data);}});
}
