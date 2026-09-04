/* Global Pulse — stable 3D evidence intelligence web.
 * Uses Vasturiano's MIT-licensed 3d-force-graph bundle.
 * Designed for GitHub Pages + iPhone: lazy loading, bounded animation,
 * one label RAF loop, pause/resume when off-screen, and a graceful fallback.
 */
(function () {
  'use strict';

  if (window.__GLOBAL_PULSE_GRAPH_STABLE_V3__) return;
  window.__GLOBAL_PULSE_GRAPH_STABLE_V3__ = true;

  const esc = v => String(v == null ? '' : v).replace(/[&<>\"']/g, m => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'
  }[m]));
  const safeUrl = v => {
    try {
      const u = new URL(String(v || '').trim(), location.href);
      return /^https?:$/.test(u.protocol) ? u.href : '';
    } catch (_) { return ''; }
  };
  const num = (v, d = 0) => Number.isFinite(Number(v)) ? Number(v) : d;

  const COLORS = {
    country:'#5da8ff', actor:'#5da8ff', political:'#b58cff', economic:'#ffc857',
    resource:'#39df88', military:'#ff5f73', strategic:'#48d9ff', oil:'#ff922e', connection:'#5d8dca'
  };
  const COUNTRY_NAMES = new Set([
    'United States','China','Russia','Ukraine','Iran','Israel','Palestinians','Saudi Arabia','Turkey',
    'India','Pakistan','Taiwan','North Korea','South Korea','Japan','United Kingdom','Mexico','Canada',
    'Brazil','Venezuela','Colombia','Haiti','Sudan','Democratic Republic of Congo','Somalia','Nigeria',
    'Sahel','Yemen','Syria','Iraq','Lebanon','Egypt','Ethiopia','Kenya','Libya','Mali','Niger','Chad',
    'Myanmar','Bangladesh','Sri Lanka','Nepal','Afghanistan'
  ]);

  function kindOf(n) {
    const k = String(n.kind || n.type || 'actor').toLowerCase();
    const label = String(n.label || n.name || n.id || '');
    if (COUNTRY_NAMES.has(label) || /country|nation|state/.test(k)) return 'country';
    if (/economic|market|company|finance/.test(k)) return 'economic';
    if (/resource|oil|energy|mineral/.test(k)) return 'resource';
    if (/military|defense/.test(k)) return 'military';
    if (/political|government/.test(k)) return 'political';
    if (/strategic/.test(k)) return 'strategic';
    return k === 'actor' ? 'actor' : k;
  }

  function edgeKind(e) {
    const evidence = Array.isArray(e.evidence) ? e.evidence.map(x =>
      `${x.title || ''} ${x.source || ''} ${x.source_name || ''}`
    ).join(' ') : '';
    const t = `${e.relationship || e.type || e.category || e.topic || e.label || ''} ${evidence}`.toLowerCase();
    if (/oil|crude|petroleum|lng|natural gas|energy|opec|brent|wti|pipeline/.test(t)) return 'oil';
    if (/rare earth|lithium|cobalt|critical mineral|mineral|nickel|uranium|critical resource/.test(t)) return 'resource';
    if (/economic|trade|market|finance|investment|currency|supply|shipping|commodity|tariff|inflation|gdp/.test(t)) return 'economic';
    if (/military|defense|weapons|troop|missile|conflict|war|airstrike|drone/.test(t)) return 'military';
    if (/politic|government|election|diplomacy|treaty|sanction|alliance|president|congress|senate/.test(t)) return 'political';
    return 'connection';
  }

  function makeData(raw) {
    const rn = Array.isArray(raw.nodes) ? raw.nodes : [];
    const re = Array.isArray(raw.edges) ? raw.edges : [];
    const nodes = rn.map((n, i) => {
      const label = String(n.label || n.name || n.id || `Node ${i + 1}`);
      const kind = kindOf(Object.assign({}, n, { label }));
      return Object.assign({}, n, {
        id:String(n.id || label), label, __kind:kind,
        __color:COLORS[kind] || COLORS.connection,
        __mentions:Math.max(0, num(n.mentions, 0))
      });
    });
    const ids = new Set(nodes.map(n => n.id));
    const byLabel = new Map(nodes.map(n => [n.label, n.id]));
    const links = re.map(e => {
      const a0 = String(e.source || e.from || '');
      const b0 = String(e.target || e.to || '');
      const source = ids.has(a0) ? a0 : byLabel.get(a0);
      const target = ids.has(b0) ? b0 : byLabel.get(b0);
      if (!source || !target || source === target) return null;
      const k = edgeKind(e);
      return Object.assign({}, e, {
        source, target, __kind:k, __color:COLORS[k] || COLORS.connection,
        __weight:Math.max(1, num(e.weight, 1))
      });
    }).filter(Boolean);
    return { nodes, links };
  }

  function evidenceUrl(e) {
    return safeUrl(e && (e.url || e.source_url || e.original_link || e.link || e.sourceUrl || e.href));
  }

  function loadLibrary(timeoutMs = 9000) {
    if (window.ForceGraph3D) return Promise.resolve(window.ForceGraph3D);
    return new Promise((resolve, reject) => {
      let done = false;
      const finish = (fn, value) => { if (done) return; done = true; clearTimeout(timer); fn(value); };
      const existing = document.querySelector('script[data-gp-force-graph]');
      const onload = () => window.ForceGraph3D ? finish(resolve, window.ForceGraph3D) : finish(reject, new Error('3D renderer loaded without ForceGraph3D'));
      const onerror = () => finish(reject, new Error('3D renderer CDN unavailable'));
      const timer = setTimeout(() => finish(reject, new Error('3D renderer timed out')), timeoutMs);
      if (existing) {
        existing.addEventListener('load', onload, { once:true });
        existing.addEventListener('error', onerror, { once:true });
        if (window.ForceGraph3D) onload();
        return;
      }
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/3d-force-graph@1.80.0/dist/3d-force-graph.min.js';
      s.async = true;
      s.dataset.gpForceGraph = '1';
      s.onload = onload; s.onerror = onerror;
      document.head.appendChild(s);
    });
  }

  function installCss() {
    if (document.getElementById('gp-intel-web-stable-css')) return;
    const s = document.createElement('style');
    s.id = 'gp-intel-web-stable-css';
    s.textContent = `
      #gp-intel-web.gp-stable{position:relative;overflow:hidden}
      #gp-intel-web.gp-stable .gp-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:12px}
      #gp-intel-web.gp-stable .gp-kicker{font-size:9px;letter-spacing:.2em;color:#5da8ff;font-weight:900;margin-bottom:5px}
      #gp-intel-web.gp-stable h2{margin:0;font-size:18px;letter-spacing:.12em;font-weight:950}
      #gp-intel-web.gp-stable .gp-sub{margin-top:6px;max-width:720px;color:var(--muted);font-size:10px;line-height:1.55}
      #gp-intel-web.gp-stable .gp-count{text-align:right;white-space:nowrap;color:#dcecff;font-size:10px;font-weight:800}.gp-count b{font-size:15px;color:#5da8ff}
      #gp-intel-web.gp-stable .gp-legend{display:flex;flex-wrap:wrap;gap:8px 14px;padding:9px 10px;margin:9px 0;border:1px solid var(--line);border-radius:10px;background:rgba(4,12,20,.75)}
      #gp-intel-web.gp-stable .gp-legend span{display:inline-flex;align-items:center;gap:5px;color:var(--muted);font-size:8px;font-weight:750}.gp-legend i{width:7px;height:7px;border-radius:50%;box-shadow:0 0 8px currentColor}
      #gp-intel-web.gp-stable .gp-controls{display:grid;grid-template-columns:minmax(0,1fr) 170px auto auto;gap:7px;margin:8px 0}
      #gp-intel-web.gp-stable .gp-controls input,#gp-intel-web.gp-stable .gp-controls select,#gp-intel-web.gp-stable .gp-controls button{min-height:37px}
      #gp-intel-web.gp-stable .gp-controls input,#gp-intel-web.gp-stable .gp-controls select{background:#07111b;color:#eafff2;border:1px solid var(--line);border-radius:8px;padding:0 10px;outline:0}
      #gp-intel-web.gp-stable .gp-controls button,#gp-intel-web.gp-stable .gp-orbit{background:#091522;color:#dcecff;border:1px solid var(--line);border-radius:8px;padding:0 10px;font-size:8px;font-weight:900;letter-spacing:.06em}
      #gp-intel-web.gp-stable .gp-controls button:hover,#gp-intel-web.gp-stable .gp-orbit:hover{border-color:#5da8ff;color:#5da8ff}
      #gp-intel-web.gp-stable .gp-toolbar{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:6px 0 8px}.gp-live{font-size:8px;letter-spacing:.1em;color:#7f9f91;font-weight:850}.gp-live:before{content:'';display:inline-block;width:6px;height:6px;margin-right:5px;border-radius:50%;background:#39ff88;box-shadow:0 0 9px #39ff88}
      #gp-intel-web.gp-stable .gp-stage{position:relative;height:620px;border:1px solid #193046;border-radius:14px;overflow:hidden;background:radial-gradient(circle at 50% 45%,rgba(17,52,78,.32),#02080e 68%);box-shadow:inset 0 0 100px rgba(0,0,0,.58)}
      #gp-intel-web.gp-stable .gp-stage:before{content:'';position:absolute;inset:0;pointer-events:none;background:linear-gradient(rgba(93,168,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(93,168,255,.025) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,#000,transparent 92%)}
      #gp-intel-web.gp-stable .gp-canvas{position:absolute;inset:0}.gp-canvas canvas{display:block!important;width:100%!important;height:100%!important;touch-action:none}
      #gp-intel-web.gp-stable .gp-labels{position:absolute;inset:0;pointer-events:none;overflow:hidden}.gp-node-label{position:absolute;transform:translate(-50%,-50%);display:flex;align-items:center;gap:5px;white-space:nowrap;padding:3px 6px;border:1px solid rgba(120,170,215,.25);border-radius:6px;background:rgba(1,7,12,.78);color:#e4efff;font-size:9px;line-height:1;box-shadow:0 3px 14px rgba(0,0,0,.28);backdrop-filter:blur(4px);text-shadow:0 1px 2px #000}.gp-node-label i{width:6px;height:6px;border-radius:50%;box-shadow:0 0 8px currentColor}.gp-node-label small{color:#7f9f91;font-size:7px}.gp-node-label.dim{opacity:.16}.gp-node-label.near{border-color:#5da8ff88}.gp-node-label.selected{border-color:#fff;box-shadow:0 0 18px #5da8ff55;transform:translate(-50%,-50%) scale(1.06);z-index:5}
      #gp-intel-web.gp-stable .gp-hud{position:absolute;left:10px;bottom:9px;display:flex;gap:6px;pointer-events:none}.gp-chip{padding:5px 7px;border:1px solid #5da8ff2e;border-radius:999px;background:#02090fc9;color:#7f9f91;font-size:7px;letter-spacing:.07em;backdrop-filter:blur(6px)}
      #gp-intel-web.gp-stable .gp-detail{margin-top:9px;padding:12px;border:1px solid var(--line);border-radius:12px;background:rgba(4,12,19,.9);min-height:70px}.gp-empty{font-size:10px;color:var(--muted);line-height:1.5}.gp-detail-top{display:flex;justify-content:space-between;gap:12px}.gp-detail-name{font-size:16px;font-weight:950}.gp-detail-kind{font-size:7px;color:#7f9f91;letter-spacing:.12em;text-transform:uppercase;margin-top:3px}.gp-metrics{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.gp-metric{min-width:58px;text-align:center;border:1px solid var(--line);border-radius:7px;padding:4px 6px}.gp-metric b{display:block;font-size:11px}.gp-metric span{display:block;font-size:7px;color:#7f9f91;text-transform:uppercase;letter-spacing:.08em}.gp-summary{margin-top:8px;color:#a8bdb4;font-size:9px;line-height:1.45}.gp-conns{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:6px;margin-top:8px}.gp-conn{border:1px solid #5da8ff20;background:#07111a;color:#dcecff;border-radius:7px;padding:7px;text-align:left;cursor:pointer}.gp-conn strong{display:block;font-size:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.gp-conn small{font-size:7px;color:#7f9f91}.gp-evidence{margin-top:8px;padding-top:8px;border-top:1px solid var(--line)}.gp-evidence-row{display:flex;justify-content:space-between;gap:7px;padding:6px 0;border-bottom:1px solid #153026}.gp-evidence-title{font-size:8px;line-height:1.3}.gp-evidence-source{font-size:7px;color:#7f9f91;margin-top:2px}.gp-open{align-self:center;border:1px solid #5da8ff45;border-radius:6px;padding:5px 6px;color:#5da8ff;font-size:7px;font-weight:900;text-decoration:none}.gp-error{height:100%;display:grid;place-items:center;text-align:center;padding:30px;color:#a8bdb4;font-size:10px}.gp-error b{display:block;color:#ff6678;margin-bottom:5px}.gp-fallback-list{display:grid;gap:5px;margin-top:10px;max-height:360px;overflow:auto}.gp-fallback-item{display:flex;justify-content:space-between;gap:8px;padding:7px 8px;border:1px solid #193046;border-radius:7px;background:#07111a}.gp-fallback-item strong{font-size:8px}.gp-fallback-item span{font-size:7px;color:#7f9f91}
      @media(max-width:700px){#gp-intel-web.gp-stable .gp-head{display:block}.gp-count{text-align:left!important;margin-top:7px}.gp-controls{grid-template-columns:1fr 1fr!important}.gp-controls input{grid-column:1/-1}.gp-stage{height:520px!important}.gp-node-label{font-size:8px;padding:3px 5px}.gp-node-label small{display:none}.gp-detail-top{display:block}.gp-metrics{justify-content:flex-start;margin-top:7px}.gp-toolbar{align-items:flex-start!important;flex-direction:column}.gp-sub{max-width:none!important}}
    `;
    document.head.appendChild(s);
  }

  function boot() {
    if (document.getElementById('gp-intel-web')) return true;
    const source = window.DATA && window.DATA.intelligenceGraph;
    if (!source || !Array.isArray(source.nodes) || !source.nodes.length) return false;
    const wrap = document.querySelector('.wrap');
    if (!wrap) return false;
    installCss();

    const data = makeData(source);
    const sec = document.createElement('section');
    sec.className = 'panel wide gp-stable';
    sec.id = 'gp-intel-web';
    sec.innerHTML = `
      <div class="gp-head"><div><div class="gp-kicker">GLOBAL PULSE / NETWORK INTELLIGENCE</div><h2>INTELLIGENCE WEB</h2><div class="gp-sub">Evidence-linked relationships across countries, politics, economics, energy, resources and military activity. Every point is visible; tap a point for its evidence trail.</div></div><div class="gp-count"><b>${data.nodes.length}</b> nodes<br>${data.links.length} evidence links</div></div>
      <div class="gp-legend"><span><i style="background:#5da8ff;color:#5da8ff"></i>Countries / actors</span><span><i style="background:#b58cff;color:#b58cff"></i>Politics</span><span><i style="background:#ffc857;color:#ffc857"></i>Economic</span><span><i style="background:#ff922e;color:#ff922e"></i>Oil / energy</span><span><i style="background:#39df88;color:#39df88"></i>Resources</span><span><i style="background:#ff5f73;color:#ff5f73"></i>Military</span></div>
      <div class="gp-controls"><input id="gp-search" placeholder="Search country, actor, issue…" aria-label="Search intelligence web"><select id="gp-kind"><option value="all">All categories</option><option value="country">Countries</option><option value="actor">Actors</option><option value="political">Politics</option><option value="economic">Economics</option><option value="resource">Resources</option><option value="military">Military</option><option value="strategic">Strategic</option></select><button id="gp-fit" type="button">FIT NETWORK</button><button id="gp-reset" type="button">RESET</button></div>
      <div class="gp-toolbar"><div class="gp-live">3D NETWORK · DRAG · ROTATE · ZOOM</div><button class="gp-orbit" id="gp-orbit" type="button">AUTO ORBIT</button></div>
      <div class="gp-stage" id="gp-stage"><div class="gp-canvas" id="gp-canvas"></div><div class="gp-labels" id="gp-labels"></div><div class="gp-hud"><span class="gp-chip" id="gp-selected-chip">NO NODE SELECTED</span><span class="gp-chip">LIVE DATA GRAPH</span></div></div>
      <div class="gp-detail" id="gp-detail"><div class="gp-empty">Tap a node to inspect its network position, connections, mention volume and public evidence. Dragging changes only its visual position.</div></div>
    `;
    wrap.appendChild(sec);

    const canvas = sec.querySelector('#gp-canvas');
    const labelsLayer = sec.querySelector('#gp-labels');
    const stage = sec.querySelector('#gp-stage');
    const detail = sec.querySelector('#gp-detail');
    const search = sec.querySelector('#gp-search');
    const kind = sec.querySelector('#gp-kind');
    const selectedChip = sec.querySelector('#gp-selected-chip');
    let Graph = null, selected = null, activeData = data, orbitRaf = 0, labelRaf = 0, labelLoopOn = false, visible = true;
    let labelEls = new Map();

    const linkEnds = l => [typeof l.source === 'object' ? l.source.id : l.source, typeof l.target === 'object' ? l.target.id : l.target];
    const nodeById = id => activeData.nodes.find(n => String(n.id) === String(id));
    const connected = id => selected && activeData.links.some(l => { const [a,b] = linkEnds(l); return String(a)===String(selected.id)&&String(b)===String(id) || String(b)===String(selected.id)&&String(a)===String(id); });

    function rebuildLabels() {
      labelsLayer.innerHTML = '';
      labelEls = new Map();
      activeData.nodes.forEach(n => {
        const el = document.createElement('div');
        el.className = 'gp-node-label';
        el.innerHTML = `<i style="background:${n.__color};color:${n.__color}"></i><span>${esc(n.label)}</span><small>${n.__mentions ? `${esc(n.__mentions)}m` : ''}</small>`;
        labelsLayer.appendChild(el); labelEls.set(n.id, el);
      });
    }

    function project(n) {
      if (!Graph || !Number.isFinite(n.x) || !Number.isFinite(n.y) || !Number.isFinite(n.z)) return null;
      const cam = Graph.camera && Graph.camera();
      if (!cam || !cam.projectionMatrix || !cam.matrixWorldInverse) return null;
      const p=cam.projectionMatrix.elements, v=cam.matrixWorldInverse.elements, x=n.x,y=n.y,z=n.z;
      const vx=v[0]*x+v[4]*y+v[8]*z+v[12], vy=v[1]*x+v[5]*y+v[9]*z+v[13], vz=v[2]*x+v[6]*y+v[10]*z+v[14], vw=v[3]*x+v[7]*y+v[11]*z+v[15];
      const cx=p[0]*vx+p[4]*vy+p[8]*vz+p[12]*vw, cy=p[1]*vx+p[5]*vy+p[9]*vz+p[13]*vw, cw=p[3]*vx+p[7]*vy+p[11]*vz+p[15]*vw;
      if (!Number.isFinite(cw) || cw <= .05) return null;
      const r=stage.getBoundingClientRect();
      return {x:(cx/cw*.5+.5)*r.width,y:(-cy/cw*.5+.5)*r.height,z:vz};
    }

    function updateLabels() {
      if (!Graph || !visible) return;
      activeData.nodes.forEach(n => {
        const el=labelEls.get(n.id); if(!el) return;
        const pos=project(n); if(!pos){el.style.display='none';return;}
        el.style.display='flex'; el.style.left=`${pos.x}px`; el.style.top=`${pos.y+15}px`;
        const sel=!!selected&&String(selected.id)===String(n.id), near=!!connected(n.id);
        el.classList.toggle('selected',sel); el.classList.toggle('near',near); el.classList.toggle('dim',!!selected&&!sel&&!near);
        el.style.opacity=pos.z>0 ? (selected&&!sel&&!near?'.15':'1') : '.22';
      });
    }

    function startLabelLoop() {
      if (labelLoopOn) return;
      labelLoopOn = true;
      const tick = () => {
        if (!labelLoopOn) { labelRaf=0; return; }
        updateLabels();
        labelRaf=requestAnimationFrame(tick);
      };
      labelRaf=requestAnimationFrame(tick);
    }
    function stopLabelLoop() { labelLoopOn=false; if(labelRaf){cancelAnimationFrame(labelRaf);labelRaf=0;} }

    function connections(n) {
      return activeData.links.map(l=>{const[a,b]=linkEnds(l);if(String(a)!==String(n.id)&&String(b)!==String(n.id))return null;const other=nodeById(String(a)===String(n.id)?b:a);return other?{node:other,link:l}:null;}).filter(Boolean).sort((a,b)=>b.link.__weight-a.link.__weight);
    }
    function evidenceFor(n) {
      const out=[],seen=new Set();
      const add=e=>{const u=evidenceUrl(e),key=u||e.title||JSON.stringify(e);if(!seen.has(key)){seen.add(key);out.push(e);}};
      (Array.isArray(n.evidence)?n.evidence:[]).forEach(add);
      connections(n).forEach(x=>(Array.isArray(x.link.evidence)?x.link.evidence:[]).forEach(add));
      return out.slice(0,8);
    }
    function updateDetail(n) {
      if(!n){detail.innerHTML='<div class="gp-empty">Tap a node to inspect its network position, connections, mention volume and public evidence.</div>';selectedChip.textContent='NO NODE SELECTED';return;}
      const con=connections(n), ev=evidenceFor(n); selectedChip.textContent=n.label.toUpperCase().slice(0,25);
      let h=`<div class="gp-detail-top"><div><div class="gp-detail-name">${esc(n.label)}</div><div class="gp-detail-kind">${esc(n.__kind)} · evidence-linked entity</div></div><div class="gp-metrics"><div class="gp-metric"><b>${esc(n.__mentions||0)}</b><span>mentions</span></div><div class="gp-metric"><b>${con.length}</b><span>connections</span></div><div class="gp-metric"><b>${ev.length}</b><span>evidence</span></div></div></div>`;
      if(n.description)h+=`<div class="gp-summary">${esc(n.description)}</div>`;
      if(con.length){h+='<div class="gp-conns">';con.slice(0,8).forEach(x=>{h+=`<button class="gp-conn" data-id="${esc(x.node.id)}"><strong>${esc(x.node.label)}</strong><small>${esc(edgeKind(x.link))} · weight ${esc(x.link.__weight)}</small></button>`});h+='</div>';}
      if(ev.length){h+='<div class="gp-evidence">';ev.forEach(e=>{const u=evidenceUrl(e);h+=`<div class="gp-evidence-row"><div><div class="gp-evidence-title">${esc(e.title||'Public report')}</div><div class="gp-evidence-source">${esc(e.source||e.source_name||'Public source')}</div></div>${u?`<a class="gp-open" href="${esc(u)}" target="_blank" rel="noopener noreferrer">OPEN ↗</a>`:''}</div>`});h+='</div>';}
      detail.innerHTML=h; detail.querySelectorAll('[data-id]').forEach(b=>b.addEventListener('click',()=>selectNode(nodeById(b.getAttribute('data-id')))));
    }
    function selectNode(n) {
      if(!n||!Graph)return;
      selected=n; updateDetail(n);
      Graph.nodeColor(x=>String(x.id)===String(n.id)?'#ffffff':(connected(x.id)?x.__color:'#203445'));
      Graph.linkColor(l=>{const[a,b]=linkEnds(l);return String(a)===String(n.id)||String(b)===String(n.id)?l.__color:'#10202d';});
      Graph.linkOpacity(l=>{const[a,b]=linkEnds(l);return String(a)===String(n.id)||String(b)===String(n.id)?.88:.08;});
      Graph.linkWidth(l=>{const[a,b]=linkEnds(l);return String(a)===String(n.id)||String(b)===String(n.id)?Math.max(1.5,Math.min(5,l.__weight*.8)):.35;});
      const d=55, len=Math.hypot(n.x||0,n.y||0,n.z||0)||1, r=(len+d)/len;
      Graph.cameraPosition({x:(n.x||0)*r,y:(n.y||0)*r,z:(n.z||0)*r},{x:n.x||0,y:n.y||0,z:n.z||0},700);
      updateLabels();
    }
    function clearSelection(){selected=null;updateDetail(null);if(!Graph)return;Graph.nodeColor(n=>n.__color).linkColor(l=>l.__color).linkOpacity(.48).linkWidth(l=>Math.max(.6,Math.min(3.5,l.__weight*.7)));updateLabels();}
    function applyFilter(){
      const q=String(search.value||'').trim().toLowerCase(), k=kind.value;
      const keep=data.nodes.filter(n=>(!q||`${n.label} ${n.description||''} ${n.kind||''}`.toLowerCase().includes(q))&&(k==='all'||n.__kind===k));
      const ids=new Set(keep.map(n=>n.id));
      activeData={nodes:keep,links:data.links.filter(l=>ids.has(String(typeof l.source==='object'?l.source.id:l.source))&&ids.has(String(typeof l.target==='object'?l.target.id:l.target)))};
      selected=null;updateDetail(null);rebuildLabels();if(Graph){Graph.graphData(activeData);Graph.d3ReheatSimulation();setTimeout(()=>Graph.zoomToFit(600,60),80);}updateLabels();
    }
    function stopOrbit(){if(orbitRaf){cancelAnimationFrame(orbitRaf);orbitRaf=0;}sec.querySelector('#gp-orbit').textContent='AUTO ORBIT';}
    function startOrbit(){if(!Graph)return;stopOrbit();let a=0;const tick=()=>{if(!Graph||!visible){orbitRaf=0;return;}const c=Graph.camera(),p=c.position,dist=Math.max(480,Math.hypot(p.x,p.y,p.z));a+=.0018;Graph.cameraPosition({x:dist*Math.sin(a),y:p.y,z:dist*Math.cos(a)},{x:0,y:0,z:0},0);orbitRaf=requestAnimationFrame(tick);};sec.querySelector('#gp-orbit').textContent='STOP ORBIT';orbitRaf=requestAnimationFrame(tick);}

    function showFallback(message) {
      const items=data.nodes.slice(0,40).map(n=>`<div class="gp-fallback-item"><strong>${esc(n.label)}</strong><span>${esc(n.__kind)} · ${esc(n.__mentions||0)} mentions</span></div>`).join('');
      canvas.innerHTML=`<div class="gp-error"><div><b>3D NETWORK COULD NOT START</b>${esc(message)}<div class="gp-fallback-list">${items}</div></div></div>`;
    }

    function initGraph(){
      loadLibrary().then(ForceGraph3D=>{
        if(!document.body.contains(sec))return;
        Graph=new ForceGraph3D(canvas,{controlType:'orbit',rendererConfig:{antialias:false,alpha:true,powerPreference:'high-performance'}})
          .backgroundColor('#020812').showNavInfo(false).nodeId('id').nodeLabel(n=>`<b>${esc(n.label)}</b><br><span style="opacity:.7">${esc(n.__kind)} · ${esc(n.__mentions||0)} mentions</span>`)
          .nodeColor(n=>n.__color).nodeVal(n=>Math.max(3,Math.min(22,3+Math.sqrt(Math.max(1,n.__mentions||1))*1.5))).nodeResolution(10)
          .linkColor(l=>l.__color).linkOpacity(.48).linkWidth(l=>Math.max(.6,Math.min(3.5,l.__weight*.7)))
          .linkDirectionalParticles(l=>Math.min(3,Math.max(0,Math.round(l.__weight)))).linkDirectionalParticleWidth(1)
          .linkDirectionalParticleSpeed(l=>.0025+Math.min(.006,l.__weight*.0006)).enablePointerInteraction(true).enableNodeDrag(true)
          .onNodeClick(selectNode).onNodeHover(n=>{canvas.style.cursor=n?'pointer':'grab';}).onNodeDragEnd(updateLabels)
          .d3VelocityDecay(.5).d3AlphaDecay(.04).warmupTicks(35).cooldownTime(3500);
        Graph.graphData(activeData);rebuildLabels();startLabelLoop();setTimeout(()=>Graph&&Graph.zoomToFit(600,60),120);
      }).catch(err=>showFallback(err.message));
    }

    search.addEventListener('input',applyFilter);kind.addEventListener('change',applyFilter);
    sec.querySelector('#gp-fit').addEventListener('click',()=>Graph&&Graph.zoomToFit(700,65));
    sec.querySelector('#gp-reset').addEventListener('click',()=>{stopOrbit();search.value='';kind.value='all';activeData=data;clearSelection();rebuildLabels();if(Graph){Graph.graphData(data);Graph.d3ReheatSimulation();setTimeout(()=>Graph&&Graph.zoomToFit(700,65),80);}});
    sec.querySelector('#gp-orbit').addEventListener('click',()=>orbitRaf?stopOrbit():startOrbit());
    const ro=new ResizeObserver(()=>{if(Graph){Graph.width(stage.clientWidth).height(stage.clientHeight);updateLabels();}});ro.observe(stage);
    const io=new IntersectionObserver(entries=>{const e=entries[0];visible=!!e&&e.isIntersecting;if(Graph){if(visible&&Graph.resumeAnimation)Graph.resumeAnimation();if(!visible&&Graph.pauseAnimation)Graph.pauseAnimation();}if(visible){startLabelLoop();}else{stopLabelLoop();stopOrbit();}}, {threshold:0.05});io.observe(sec);
    window.addEventListener('beforeunload',()=>{stopOrbit();stopLabelLoop();ro.disconnect();io.disconnect();});
    initGraph();
    return true;
  }

  function waitForData(){
    if(boot())return;
    document.addEventListener('globalpulse:dataready',()=>boot(),{once:true});
    let tries=0;const t=setInterval(()=>{if(boot()||++tries>30)clearInterval(t);},1000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',waitForData,{once:true});else waitForData();
})();