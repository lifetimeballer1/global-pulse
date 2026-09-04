/* Global Pulse — professional 3D evidence intelligence web.
 * Built around Vasturiano's open-source 3d-force-graph renderer.
 * No API key is required. Labels are rendered as a lightweight DOM overlay so
 * they remain readable while the 3D network rotates, zooms and is dragged.
 */
(function () {
  'use strict';

  if (window.__GLOBAL_PULSE_GRAPH_V2__) return;
  window.__GLOBAL_PULSE_GRAPH_V2__ = true;

  const esc = (v) => String(v == null ? '' : v).replace(/[&<>\"']/g, (m) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#39;'
  }[m]));

  const safeUrl = (v) => {
    try {
      const raw = String(v || '').trim();
      if (!raw) return '';
      const u = new URL(raw, location.href);
      return /^https?:$/.test(u.protocol) ? u.href : '';
    } catch (_) { return ''; }
  };

  const num = (v, fallback = 0) => Number.isFinite(Number(v)) ? Number(v) : fallback;

  const evidenceUrl = (e) => safeUrl(e && (
    e.url || e.source_url || e.original_link || e.link || e.sourceUrl || e.href
  ));

  const edgeKind = (e) => {
    const evidence = Array.isArray(e.evidence)
      ? e.evidence.map(x => `${x.title || ''} ${x.source || ''} ${x.source_name || ''}`).join(' ')
      : '';
    const t = String(`${e.relationship || e.type || e.category || e.topic || e.label || ''} ${evidence}`).toLowerCase();
    if (/oil|crude|petroleum|lng|natural gas|energy|opec|brent|wti|pipeline/.test(t)) return 'oil';
    if (/rare earth|lithium|cobalt|critical mineral|mineral|nickel|uranium|critical resource/.test(t)) return 'resource';
    if (/economic|trade|market|finance|investment|currency|supply|shipping|commodity|tariff|inflation|gdp/.test(t)) return 'economic';
    if (/military|defense|weapons|troop|missile|conflict|war|airstrike|drone/.test(t)) return 'military';
    if (/politic|government|election|diplomacy|treaty|sanction|alliance|president|congress|senate/.test(t)) return 'political';
    return 'connection';
  };

  const COLORS = {
    country: '#5da8ff', actor: '#5da8ff', political: '#b58cff',
    economic: '#ffc857', resource: '#39df88', strategic: '#48d9ff',
    military: '#ff5f73', oil: '#ff922e', connection: '#5d8dca'
  };

  const COUNTRY_NAMES = new Set([
    'United States', 'China', 'Russia', 'Ukraine', 'Iran', 'Israel', 'Palestinians',
    'Saudi Arabia', 'Turkey', 'India', 'Pakistan', 'Taiwan', 'North Korea', 'South Korea',
    'Japan', 'United Kingdom', 'Mexico', 'Canada', 'Brazil', 'Venezuela', 'Colombia',
    'Haiti', 'Sudan', 'Democratic Republic of Congo', 'Somalia', 'Nigeria', 'Sahel',
    'Yemen', 'Syria', 'Iraq', 'Lebanon', 'Egypt', 'Ethiopia', 'Kenya', 'Libya',
    'Mali', 'Niger', 'Chad', 'Myanmar', 'Bangladesh', 'Sri Lanka', 'Nepal', 'Afghanistan'
  ]);

  const nodeKind = (node) => {
    const k = String(node.kind || node.type || 'actor').toLowerCase();
    const label = String(node.label || node.name || node.id || '');
    if (COUNTRY_NAMES.has(label) || /country|nation|state/.test(k)) return 'country';
    if (/economic|market|company|finance/.test(k)) return 'economic';
    if (/resource|oil|energy|mineral/.test(k)) return 'resource';
    if (/military|defense/.test(k)) return 'military';
    if (/political|government/.test(k)) return 'political';
    if (/strategic/.test(k)) return 'strategic';
    return k === 'actor' ? 'actor' : k;
  };

  function loadGraphLibrary() {
    if (window.ForceGraph3D) return Promise.resolve(window.ForceGraph3D);
    return new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-global-pulse-3d-graph]');
      if (existing) {
        existing.addEventListener('load', () => window.ForceGraph3D ? resolve(window.ForceGraph3D) : reject(new Error('3D graph library loaded without ForceGraph3D')));
        existing.addEventListener('error', () => reject(new Error('3D graph library failed to load')));
        return;
      }
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/3d-force-graph@1.80.0/dist/3d-force-graph.min.js';
      s.async = true;
      s.dataset.globalPulse3dGraph = '1';
      s.onload = () => window.ForceGraph3D ? resolve(window.ForceGraph3D) : reject(new Error('ForceGraph3D unavailable'));
      s.onerror = () => reject(new Error('Unable to load 3D graph renderer'));
      document.head.appendChild(s);
    });
  }

  function makeData(raw) {
    const rawNodes = Array.isArray(raw.nodes) ? raw.nodes : [];
    const rawEdges = Array.isArray(raw.edges) ? raw.edges : [];
    const nodes = rawNodes.map((node, i) => {
      const label = String(node.label || node.name || node.id || `Node ${i + 1}`);
      const kind = nodeKind(Object.assign({}, node, { label }));
      return Object.assign({}, node, {
        id: String(node.id || label),
        label,
        __kind: kind,
        __color: COLORS[kind] || COLORS.connection,
        __mentions: Math.max(0, num(node.mentions, 0))
      });
    });

    const ids = new Set(nodes.map(x => x.id));
    const labels = new Map(nodes.map(x => [x.label, x.id]));
    const links = rawEdges.map((edge) => {
      const sourceRaw = String(edge.source || edge.from || '');
      const targetRaw = String(edge.target || edge.to || '');
      const source = ids.has(sourceRaw) ? sourceRaw : labels.get(sourceRaw);
      const target = ids.has(targetRaw) ? targetRaw : labels.get(targetRaw);
      if (!source || !target || source === target) return null;
      const kind = edgeKind(edge);
      return Object.assign({}, edge, {
        source,
        target,
        __kind: kind,
        __color: COLORS[kind] || COLORS.connection,
        __weight: Math.max(1, num(edge.weight, 1))
      });
    }).filter(Boolean);

    return { nodes, links };
  }

  function installStyle() {
    if (document.getElementById('gp-intel-web-style-v2')) return;
    const style = document.createElement('style');
    style.id = 'gp-intel-web-style-v2';
    style.textContent = `
      #gp-intel-web.gp-v2{position:relative;overflow:hidden}
      #gp-intel-web.gp-v2 .gp-web-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:12px}
      #gp-intel-web.gp-v2 .gp-web-kicker{font-size:10px;letter-spacing:.18em;color:#5da8ff;font-weight:900;margin-bottom:5px}
      #gp-intel-web.gp-v2 h2{margin:0;font-size:18px;letter-spacing:.12em;font-weight:950}
      #gp-intel-web.gp-v2 .gp-web-sub{margin-top:6px;max-width:720px;color:var(--muted);font-size:10px;line-height:1.55}
      #gp-intel-web.gp-v2 .gp-web-count{text-align:right;white-space:nowrap;color:#dcecff;font-size:11px;font-weight:850}
      #gp-intel-web.gp-v2 .gp-web-count b{color:#5da8ff;font-size:15px}
      #gp-intel-web.gp-v2 .gp-web-legend{display:flex;gap:10px 15px;flex-wrap:wrap;margin:9px 0 11px;padding:9px 10px;border:1px solid var(--line);border-radius:11px;background:rgba(5,13,21,.7)}
      #gp-intel-web.gp-v2 .gp-web-legend span{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:9px;font-weight:750}
      #gp-intel-web.gp-v2 .gp-web-legend i{width:8px;height:8px;border-radius:50%;box-shadow:0 0 8px currentColor;display:inline-block}
      #gp-intel-web.gp-v2 .gp-web-controls{display:grid;grid-template-columns:minmax(0,1fr) 190px auto auto;gap:8px;margin:9px 0}
      #gp-intel-web.gp-v2 .gp-web-controls input,#gp-intel-web.gp-v2 .gp-web-controls select,#gp-intel-web.gp-v2 .gp-web-controls button{min-height:39px}
      #gp-intel-web.gp-v2 .gp-web-controls input,#gp-intel-web.gp-v2 .gp-web-controls select{background:#07111b;color:#eafff2;border:1px solid var(--line);border-radius:9px;padding:0 11px;outline:none}
      #gp-intel-web.gp-v2 .gp-web-controls input:focus,#gp-intel-web.gp-v2 .gp-web-controls select:focus{border-color:#5da8ff;box-shadow:0 0 0 2px #5da8ff18}
      #gp-intel-web.gp-v2 .gp-web-toolbar{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:7px 0 8px}
      #gp-intel-web.gp-v2 .gp-live{display:inline-flex;align-items:center;gap:6px;color:#7f9f91;font-size:8px;letter-spacing:.1em;font-weight:850}
      #gp-intel-web.gp-v2 .gp-live-dot{width:7px;height:7px;border-radius:50%;background:#39ff88;box-shadow:0 0 10px #39ff88;animation:gpPulse 1.8s infinite}
      @keyframes gpPulse{0%,100%{opacity:.65;transform:scale(.85)}50%{opacity:1;transform:scale(1.15)}}
      #gp-intel-web.gp-v2 .gp-web-stage{position:relative;height:650px;min-height:450px;border:1px solid #193046;border-radius:15px;overflow:hidden;background:radial-gradient(circle at 50% 46%,rgba(19,55,82,.28),rgba(2,8,14,.98) 62%);box-shadow:inset 0 0 100px rgba(0,0,0,.6),0 12px 40px rgba(0,0,0,.25)}
      #gp-intel-web.gp-v2 .gp-web-stage:before{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(rgba(93,168,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(93,168,255,.025) 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(to bottom,black,transparent 88%)}
      #gp-intel-web.gp-v2 .gp-canvas{position:absolute;inset:0}
      #gp-intel-web.gp-v2 .gp-canvas canvas{display:block;width:100%!important;height:100%!important;touch-action:none}
      #gp-intel-web.gp-v2 .gp-label-layer{position:absolute;inset:0;pointer-events:none;overflow:hidden}
      #gp-intel-web.gp-v2 .gp-node-label{position:absolute;transform:translate(-50%,-50%);white-space:nowrap;display:flex;align-items:center;gap:5px;padding:3px 6px;border:1px solid rgba(100,160,210,.22);border-radius:6px;background:rgba(1,7,12,.76);box-shadow:0 4px 16px rgba(0,0,0,.25);font-size:9px;line-height:1;color:#dcecff;text-shadow:0 1px 2px #000;backdrop-filter:blur(4px);transition:opacity .12s,transform .12s,border-color .12s,box-shadow .12s}
      #gp-intel-web.gp-v2 .gp-node-label .gp-label-dot{width:6px;height:6px;border-radius:50%;flex:0 0 6px;box-shadow:0 0 8px currentColor}
      #gp-intel-web.gp-v2 .gp-node-label .gp-label-count{color:#7f9f91;font-size:8px;margin-left:1px}
      #gp-intel-web.gp-v2 .gp-node-label.gp-selected{border-color:#fff;box-shadow:0 0 18px rgba(93,168,255,.35);transform:translate(-50%,-50%) scale(1.08);z-index:5}
      #gp-intel-web.gp-v2 .gp-node-label.gp-dim{opacity:.16}
      #gp-intel-web.gp-v2 .gp-node-label.gp-near{border-color:rgba(93,168,255,.65);opacity:1}
      #gp-intel-web.gp-v2 .gp-reticle{position:absolute;left:50%;top:50%;width:22px;height:22px;transform:translate(-50%,-50%);border:1px solid rgba(93,168,255,.13);border-radius:50%;pointer-events:none}
      #gp-intel-web.gp-v2 .gp-reticle:before,#gp-intel-web.gp-v2 .gp-reticle:after{content:"";position:absolute;background:rgba(93,168,255,.12)}
      #gp-intel-web.gp-v2 .gp-reticle:before{width:1px;height:42px;left:10px;top:-11px}.gp-reticle:after{height:1px;width:42px;left:-11px;top:10px}
      #gp-intel-web.gp-v2 .gp-stage-hud{position:absolute;left:12px;bottom:11px;display:flex;gap:7px;pointer-events:none}
      #gp-intel-web.gp-v2 .gp-stage-chip{padding:5px 8px;border:1px solid rgba(93,168,255,.18);border-radius:999px;background:rgba(2,9,15,.72);color:#7f9f91;font-size:8px;letter-spacing:.06em;backdrop-filter:blur(6px)}
      #gp-intel-web.gp-v2 .gp-detail{margin-top:10px;border:1px solid var(--line);border-radius:13px;background:rgba(4,12,19,.82);padding:13px;min-height:74px}
      #gp-intel-web.gp-v2 .gp-detail-empty{color:var(--muted);font-size:10px;line-height:1.55}
      #gp-intel-web.gp-v2 .gp-detail-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
      #gp-intel-web.gp-v2 .gp-detail-name{font-size:17px;font-weight:950;letter-spacing:-.01em}
      #gp-intel-web.gp-v2 .gp-detail-kind{font-size:8px;letter-spacing:.12em;color:#7f9f91;text-transform:uppercase;margin-top:4px}
      #gp-intel-web.gp-v2 .gp-detail-metrics{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}
      #gp-intel-web.gp-v2 .gp-metric{border:1px solid var(--line);border-radius:8px;padding:5px 7px;text-align:center;min-width:62px}
      #gp-intel-web.gp-v2 .gp-metric b{display:block;color:#eafff2;font-size:12px}.gp-metric span{display:block;color:#7f9f91;font-size:7px;text-transform:uppercase;letter-spacing:.08em;margin-top:1px}
      #gp-intel-web.gp-v2 .gp-detail-summary{margin-top:9px;color:#a8bdb4;font-size:10px;line-height:1.5}
      #gp-intel-web.gp-v2 .gp-connections{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:6px;margin-top:9px}
      #gp-intel-web.gp-v2 .gp-connection{padding:7px 8px;border:1px solid rgba(93,168,255,.13);border-radius:8px;background:#07111a;cursor:pointer;text-align:left;color:#dcecff}
      #gp-intel-web.gp-v2 .gp-connection:hover{border-color:#5da8ff55}
      #gp-intel-web.gp-v2 .gp-connection strong{font-size:9px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      #gp-intel-web.gp-v2 .gp-connection small{font-size:8px;color:#7f9f91}
      #gp-intel-web.gp-v2 .gp-evidence-list{margin-top:10px;border-top:1px solid var(--line);padding-top:9px}
      #gp-intel-web.gp-v2 .gp-evidence-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:7px;padding:7px 0;border-bottom:1px solid rgba(21,48,38,.65)}
      #gp-intel-web.gp-v2 .gp-evidence-title{font-size:9px;line-height:1.35;color:#dcecff}.gp-evidence-source{font-size:8px;color:#7f9f91;margin-top:2px}
      #gp-intel-web.gp-v2 .gp-evidence-open{align-self:center;padding:5px 7px;border:1px solid rgba(93,168,255,.28);border-radius:7px;background:transparent;color:#5da8ff;font-size:8px;font-weight:850;text-decoration:none}
      #gp-intel-web.gp-v2 .gp-web-note{margin-top:9px;color:#6f8b82;font-size:8px;line-height:1.5}
      @media(max-width:700px){
        #gp-intel-web.gp-v2 .gp-web-head{display:block}.gp-web-count{text-align:left!important;margin-top:7px}
        #gp-intel-web.gp-v2 .gp-web-controls{grid-template-columns:1fr 1fr}.gp-web-controls input{grid-column:1/-1}
        #gp-intel-web.gp-v2 .gp-web-stage{height:570px;min-height:430px}
        #gp-intel-web.gp-v2 .gp-node-label{font-size:8px;padding:3px 5px}.gp-label-count{display:none!important}
        #gp-intel-web.gp-v2 .gp-detail-top{display:block}.gp-detail-metrics{justify-content:flex-start!important;margin-top:8px}
      }
    `;
    document.head.appendChild(style);
  }

  function boot() {
    if (document.getElementById('gp-intel-web')) return true;
    const source = window.DATA && window.DATA.intelligenceGraph;
    if (!source || !Array.isArray(source.nodes) || !Array.isArray(source.edges) || !source.nodes.length) return false;
    const wrap = document.querySelector('.wrap');
    if (!wrap) return false;

    installStyle();

    const sec = document.createElement('section');
    sec.className = 'panel wide gp-v2';
    sec.id = 'gp-intel-web';
    sec.innerHTML = `
      <div class="gp-web-head">
        <div>
          <div class="gp-web-kicker">GLOBAL PULSE / NETWORK INTELLIGENCE</div>
          <h2>INTELLIGENCE WEB</h2>
          <div class="gp-web-sub">An evidence-linked network of countries, actors, political pressure, economic exposure, energy and military activity. Nodes are visible at all times; select one to expose its evidence trail and connected entities.</div>
        </div>
        <div class="gp-web-count"><b>${source.nodes.length}</b> nodes<br><span>${source.edges.length} evidence links</span></div>
      </div>
      <div class="gp-web-legend">
        <span><i style="color:#5da8ff;background:#5da8ff"></i>Countries / actors</span>
        <span><i style="color:#b58cff;background:#b58cff"></i>Politics</span>
        <span><i style="color:#ffc857;background:#ffc857"></i>Economic</span>
        <span><i style="color:#ff922e;background:#ff922e"></i>Oil / energy</span>
        <span><i style="color:#39df88;background:#39df88"></i>Resources</span>
        <span><i style="color:#ff5f73;background:#ff5f73"></i>Military</span>
      </div>
      <div class="gp-web-controls">
        <input id="gp-web-search-v2" placeholder="Search country, actor, issue…" aria-label="Search intelligence web">
        <select id="gp-web-kind-v2" aria-label="Filter intelligence web">
          <option value="all">All categories</option><option value="country">Countries</option><option value="actor">Actors</option><option value="political">Politics</option><option value="economic">Economics</option><option value="resource">Resources</option><option value="military">Military</option><option value="strategic">Strategic</option>
        </select>
        <button id="gp-web-fit-v2" type="button">FIT NETWORK</button>
        <button id="gp-web-reset-v2" type="button">RESET</button>
      </div>
      <div class="gp-web-toolbar">
        <div class="gp-live"><span class="gp-live-dot"></span>LIVE 3D NETWORK · DRAG NODES · ROTATE · ZOOM</div>
        <button id="gp-web-orbit-v2" type="button">AUTO ORBIT</button>
      </div>
      <div class="gp-web-stage" id="gp-web-stage-v2">
        <div class="gp-canvas" id="gp-web-canvas-v2"></div>
        <div class="gp-label-layer" id="gp-label-layer-v2"></div>
        <div class="gp-reticle"></div>
        <div class="gp-stage-hud"><span class="gp-stage-chip">EVIDENCE GRAPH</span><span class="gp-stage-chip" id="gp-selected-chip">NO NODE SELECTED</span></div>
      </div>
      <div class="gp-detail" id="gp-web-detail-v2"><div class="gp-detail-empty">Select a node to inspect its network position, connected entities, mention volume and public evidence. Dragging a node changes its position without changing the underlying data.</div></div>
      <div class="gp-web-note">Connections represent shared public reporting/evidence, not proof of causation, coordination or alliance. Node size reflects available mention volume. Labels are intentionally kept visible so the network can be understood without opening every point.</div>`;

    const mapSection = document.getElementById('map') && document.getElementById('map').closest('section');
    wrap.insertBefore(sec, mapSection || wrap.firstElementChild || null);

    const canvas = sec.querySelector('#gp-web-canvas-v2');
    const stage = sec.querySelector('#gp-web-stage-v2');
    const labelsLayer = sec.querySelector('#gp-label-layer-v2');
    const detail = sec.querySelector('#gp-web-detail-v2');
    const search = sec.querySelector('#gp-web-search-v2');
    const kind = sec.querySelector('#gp-web-kind-v2');
    const selectedChip = sec.querySelector('#gp-selected-chip');
    const data = makeData(source);
    let Graph = null;
    let selected = null;
    let hovered = null;
    let orbitTimer = null;
    let raf = 0;
    let labelEls = new Map();
    let activeData = { nodes: data.nodes.slice(), links: data.links.slice() };

    function nodeById(id) { return data.nodes.find(n => n.id === String(id)); }

    function linkEnds(link) {
      return [typeof link.source === 'object' ? link.source.id : link.source, typeof link.target === 'object' ? link.target.id : link.target];
    }

    function filteredData() {
      const q = String(search.value || '').toLowerCase().trim();
      const k = kind.value;
      const visible = data.nodes.filter(node => {
        const hay = `${node.label} ${node.kind || ''} ${node.type || ''} ${node.description || ''}`.toLowerCase();
        return (!q || hay.includes(q)) && (k === 'all' || node.__kind === k);
      });
      const set = new Set(visible.map(n => n.id));
      return {
        nodes: visible,
        links: data.links.filter(link => {
          const [a,b] = linkEnds(link); return set.has(String(a)) && set.has(String(b));
        })
      };
    }

    function setGraphData() {
      activeData = filteredData();
      if (!Graph) return;
      Graph.graphData(activeData);
      selected = activeData.nodes.some(n => selected && n.id === selected.id) ? selected : null;
      updateLabels();
      Graph.d3ReheatSimulation();
      setTimeout(() => Graph.zoomToFit(650, 70), 30);
      updateDetail(selected);
    }

    function makeLabel(node) {
      const el = document.createElement('div');
      el.className = 'gp-node-label';
      el.innerHTML = `<span class="gp-label-dot" style="color:${node.__color};background:${node.__color}"></span><span>${esc(node.label)}</span><span class="gp-label-count">${node.__mentions ? `${esc(node.__mentions)}m` : ''}</span>`;
      labelsLayer.appendChild(el);
      labelEls.set(node.id, el);
      return el;
    }

    function rebuildLabels() {
      labelsLayer.innerHTML = '';
      labelEls = new Map();
      activeData.nodes.forEach(makeLabel);
    }

    // Project a graph node into the label overlay without importing another THREE.js copy.
    function project(node) {
      if (!Graph || !node || !Number.isFinite(node.x) || !Number.isFinite(node.y) || !Number.isFinite(node.z)) return null;
      const cam = Graph.camera && Graph.camera();
      if (!cam || !cam.projectionMatrix || !cam.matrixWorldInverse) return null;
      const p = cam.projectionMatrix.elements;
      const v = cam.matrixWorldInverse.elements;
      const x=node.x,y=node.y,z=node.z;
      const vx=v[0]*x+v[4]*y+v[8]*z+v[12];
      const vy=v[1]*x+v[5]*y+v[9]*z+v[13];
      const vz=v[2]*x+v[6]*y+v[10]*z+v[14];
      const vw=v[3]*x+v[7]*y+v[11]*z+v[15];
      const cx=p[0]*vx+p[4]*vy+p[8]*vz+p[12]*vw;
      const cy=p[1]*vx+p[5]*vy+p[9]*vz+p[13]*vw;
      const cw=p[3]*vx+p[7]*vy+p[11]*vz+p[15]*vw;
      if (!Number.isFinite(cw) || cw <= 0.05) return null;
      const rect=stage.getBoundingClientRect();
      return {x:(cx/cw*.5+.5)*rect.width,y:(-cy/cw*.5+.5)*rect.height,z:vz};
    }

    function updateLabels() {
      if (!Graph) return;
      const visibleIds = new Set(activeData.nodes.map(n => n.id));
      activeData.nodes.forEach(node => {
        const el = labelEls.get(node.id) || makeLabel(node);
        const pos = project(node);
        if (!pos) { el.style.display='none'; return; }
        el.style.display='flex';
        el.style.left = `${pos.x}px`; el.style.top = `${pos.y + 15}px`;
        const isSelected = selected && selected.id === node.id;
        const isNear = selected && connectedToSelected(node.id);
        el.classList.toggle('gp-selected', !!isSelected);
        el.classList.toggle('gp-near', !!isNear);
        el.classList.toggle('gp-dim', !!selected && !isSelected && !isNear);
        el.style.opacity = pos.z > 0 ? (selected && !isSelected && !isNear ? '.14' : '1') : '.22';
      });
      Array.from(labelEls.keys()).forEach(id => { if (!visibleIds.has(id)) labelEls.get(id).remove(); });
      raf = requestAnimationFrame(updateLabels);
    }

    function connectedToSelected(id) {
      if (!selected) return false;
      return activeData.links.some(l => {
        const [a,b] = linkEnds(l); return String(a) === selected.id && String(b) === id || String(b) === selected.id && String(a) === id;
      });
    }

    function nodeConnections(node) {
      return activeData.links.map(l => {
        const [a,b] = linkEnds(l);
        if (String(a) !== node.id && String(b) !== node.id) return null;
        const other = String(a) === node.id ? nodeById(b) : nodeById(a);
        if (!other) return null;
        return { node: other, link: l };
      }).filter(Boolean).sort((a,b) => num(b.link.__weight,1)-num(a.link.__weight,1));
    }

    function evidenceFor(node) {
      const out=[]; const seen=new Set();
      (Array.isArray(node.evidence) ? node.evidence : []).forEach(e => { const u=evidenceUrl(e); const key=u||e.title||JSON.stringify(e); if(!seen.has(key)){seen.add(key);out.push(e)} });
      nodeConnections(node).forEach(({link}) => (Array.isArray(link.evidence)?link.evidence:[]).forEach(e => { const u=evidenceUrl(e); const key=u||e.title||JSON.stringify(e); if(!seen.has(key)){seen.add(key);out.push(e)} }));
      return out.slice(0,8);
    }

    function updateDetail(node) {
      if (!node) {
        detail.innerHTML='<div class="gp-detail-empty">Select a node to inspect its network position, connected entities, mention volume and public evidence. Dragging a node changes its position without changing the underlying data.</div>';
        selectedChip.textContent='NO NODE SELECTED';
        return;
      }
      const connections=nodeConnections(node);
      const evidence=evidenceFor(node);
      selectedChip.textContent=node.label.toUpperCase().slice(0,26);
      let html=`<div class="gp-detail-top"><div><div class="gp-detail-name">${esc(node.label)}</div><div class="gp-detail-kind">${esc(node.__kind)} · evidence-linked entity</div></div><div class="gp-detail-metrics"><div class="gp-metric"><b>${esc(node.__mentions||0)}</b><span>mentions</span></div><div class="gp-metric"><b>${connections.length}</b><span>connections</span></div><div class="gp-metric"><b>${evidence.length}</b><span>evidence</span></div></div></div>`;
      if(node.description) html+=`<div class="gp-detail-summary">${esc(node.description)}</div>`;
      if(connections.length){html+='<div class="gp-connections">';connections.slice(0,8).forEach(({node:other,link})=>{html+=`<button class="gp-connection" data-node-id="${esc(other.id)}"><strong>${esc(other.label)}</strong><small>${esc(edgeKind(link))} · weight ${esc(link.__weight)}</small></button>`});html+='</div>'}
      if(evidence.length){html+='<div class="gp-evidence-list">';evidence.forEach(e=>{const u=evidenceUrl(e);html+=`<div class="gp-evidence-row"><div><div class="gp-evidence-title">${esc(e.title||'Public report')}</div><div class="gp-evidence-source">${esc(e.source||e.source_name||'Public source')}</div></div>${u?`<a class="gp-evidence-open" href="${esc(u)}" target="_blank" rel="noopener noreferrer">OPEN ↗</a>`:''}</div>`});html+='</div>'}
      detail.innerHTML=html;
      detail.querySelectorAll('[data-node-id]').forEach(btn=>btn.addEventListener('click',()=>selectNode(nodeById(btn.getAttribute('data-node-id')))));
    }

    function selectNode(node) {
      if (!node || !Graph) return;
      selected=node;
      updateDetail(node);
      Graph.nodeColor(n => n.id === node.id ? '#ffffff' : (connectedToSelected(n.id) ? n.__color : '#203445'));
      Graph.linkColor(l => { const [a,b]=linkEnds(l); return String(a)===node.id || String(b)===node.id ? (l.__color||'#5da8ff') : '#10202d'; });
      Graph.linkOpacity(l => { const [a,b]=linkEnds(l); return String(a)===node.id || String(b)===node.id ? .9 : .1; });
      Graph.linkWidth(l => { const [a,b]=linkEnds(l); return String(a)===node.id || String(b)===node.id ? Math.max(1.5,Math.min(5,l.__weight*.8)) : .35; });
      const dist=55; const len=Math.hypot(node.x||0,node.y||0,node.z||0)||1; const ratio=(len+dist)/len;
      Graph.cameraPosition({x:(node.x||0)*ratio,y:(node.y||0)*ratio,z:(node.z||0)*ratio},{x:node.x||0,y:node.y||0,z:node.z||0},900);
      updateLabels();
    }

    function clearSelection() {
      selected=null; updateDetail(null);
      Graph.nodeColor(n => n.__color).linkColor(l => l.__color).linkOpacity(.48).linkWidth(l => Math.max(.6,Math.min(3.5,l.__weight*.7)));
      updateLabels();
    }

    function startOrbit() {
      if (!Graph) return;
      stopOrbit();
      let angle=0;
      const tick=()=>{ if(!Graph || !orbitTimer) return; const cam=Graph.camera(),p=cam.position; const dist=Math.max(520,Math.hypot(p.x,p.y,p.z)); angle+=.0018; Graph.cameraPosition({x:dist*Math.sin(angle),y:p.y,z:dist*Math.cos(angle)},{x:0,y:0,z:0},0); orbitTimer=requestAnimationFrame(tick); };
      orbitTimer=requestAnimationFrame(tick);
      sec.querySelector('#gp-web-orbit-v2').classList.add('active');
    }
    function stopOrbit(){ if(orbitTimer){cancelAnimationFrame(orbitTimer);orbitTimer=null} sec.querySelector('#gp-web-orbit-v2').classList.remove('active'); }

    loadGraphLibrary().then((ForceGraph3D) => {
      Graph = new ForceGraph3D(canvas, { controlType: 'orbit' })
        .backgroundColor('#020812')
        .showNavInfo(false)
        .nodeId('id')
        .nodeLabel(node => `<b>${esc(node.label)}</b><br><span style="opacity:.7">${esc(node.__kind)} · ${esc(node.__mentions||0)} mentions</span>`)
        .nodeColor(node => node.__color)
        .nodeVal(node => Math.max(3, Math.min(28, 3 + Math.sqrt(Math.max(1,node.__mentions||1))*1.7)))
        .nodeResolution(12)
        .linkColor(link => link.__color)
        .linkOpacity(.48)
        .linkWidth(link => Math.max(.6, Math.min(3.5, link.__weight*.7)))
        .linkDirectionalParticles(link => Math.min(4, Math.max(0, Math.round(link.__weight))))
        .linkDirectionalParticleWidth(1.2)
        .linkDirectionalParticleSpeed(link => .0025 + Math.min(.008,link.__weight*.0008))
        .enablePointerInteraction(true)
        .enableNodeDrag(true)
        .onNodeClick(selectNode)
        .onNodeHover(node => { hovered=node; canvas.style.cursor=node?'pointer':'grab'; })
        .onNodeDragEnd(() => updateLabels())
        .d3VelocityDecay(.38)
        .d3AlphaDecay(.025)
        .warmupTicks(80)
        .cooldownTime(7000);

      Graph.graphData(activeData);
      rebuildLabels();
      updateLabels();
      setTimeout(() => Graph.zoomToFit(700,70), 100);
    }).catch((err) => {
      canvas.innerHTML=`<div style="display:grid;place-items:center;height:100%;padding:25px;text-align:center;color:#ff6678;font-size:11px">3D NETWORK UNAVAILABLE<br><span style="font-size:9px;color:#7f9f91">${esc(err.message)}</span></div>`;
    });

    search.addEventListener('input',setGraphData);
    kind.addEventListener('change',setGraphData);
    sec.querySelector('#gp-web-fit-v2').addEventListener('click',()=>Graph&&Graph.zoomToFit(800,75));
    sec.querySelector('#gp-web-reset-v2').addEventListener('click',()=>{stopOrbit();clearSelection();if(Graph){Graph.zoomToFit(800,75);Graph.cameraPosition({x:0,y:0,z:750},{x:0,y:0,z:0},700)}});
    sec.querySelector('#gp-web-orbit-v2').addEventListener('click',()=>orbitTimer?stopOrbit():startOrbit());
    window.addEventListener('resize',()=>{if(Graph){Graph.width(stage.clientWidth).height(stage.clientHeight);updateLabels()}});
    window.addEventListener('beforeunload',()=>{stopOrbit();if(raf)cancelAnimationFrame(raf)});
    return true;
  }

  function waitForData() {
    if (boot()) return;
    document.addEventListener('globalpulse:dataready', () => boot(), { once: true });
    let tries=0;
    const timer=setInterval(()=>{ if(boot() || ++tries>30) clearInterval(timer); },1000);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', waitForData, { once: true });
  else waitForData();
})();
