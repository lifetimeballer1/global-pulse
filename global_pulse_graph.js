/* Global Pulse — 3D evidence intelligence web.
 * Built around Vasturiano's open-source 3d-force-graph renderer.
 * No API key is required: graph data comes from window.DATA.intelligenceGraph.
 */
(function () {
  'use strict';

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
  const n = (v) => Number.isFinite(Number(v)) ? Number(v) : 0;
  const evidenceUrl = (e) => safeUrl(e && (e.url || e.source_url || e.original_link || e.link || e.sourceUrl || e.href));

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

  const edgeColor = (k) => ({
    connection: '#62a0ff', political: '#aa8df7', economic: '#ffc857',
    oil: '#fb923c', resource: '#48df83', military: '#ff6678'
  }[k] || '#62a0ff');

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
    return k;
  };

  const nodeColor = (k) => ({
    country: '#62a0ff', actor: '#62a0ff', political: '#aa8df7',
    economic: '#ffc857', resource: '#48df83', strategic: '#3fc5ff',
    military: '#ff6678'
  }[k] || '#62a0ff');

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
      return Object.assign({}, node, {
        id: String(node.id || label),
        label,
        __kind: nodeKind(Object.assign({}, node, { label })),
        __color: nodeColor(nodeKind(Object.assign({}, node, { label })))
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
        __color: edgeColor(kind)
      });
    }).filter(Boolean);
    return { nodes, links };
  }

  function boot() {
    if (document.getElementById('gp-intel-web')) return true;
    const g = window.DATA && window.DATA.intelligenceGraph;
    if (!g || !Array.isArray(g.nodes) || !Array.isArray(g.edges)) return false;
    const wrap = document.querySelector('.wrap');
    if (!wrap) return false;

    const sec = document.createElement('section');
    sec.className = 'panel wide';
    sec.id = 'gp-intel-web';
    sec.innerHTML = `
      <div class="section-head">
        <div>
          <h2>INTELLIGENCE WEB</h2>
          <div class="muted">3D evidence-linked relationships across countries, politics, economics, energy, resources and military activity.</div>
        </div>
        <div class="gp-web-count">${g.nodes.length} nodes · ${g.edges.length} evidence links</div>
      </div>
      <div class="gp-web-legend">
        <span><i data-k="country"></i>Countries</span>
        <span><i data-k="political"></i>Politics</span>
        <span><i data-k="economic"></i>Economic</span>
        <span><i data-k="oil"></i>Oil / energy</span>
        <span><i data-k="resource"></i>Rare earth / resources</span>
        <span><i data-k="military"></i>Military</span>
      </div>
      <div class="gp-web-controls">
        <input id="gp-web-search" placeholder="Search actor, country, issue…" aria-label="Search intelligence web">
        <select id="gp-web-kind" aria-label="Filter intelligence web">
          <option value="all">All categories</option>
          <option value="country">Countries</option>
          <option value="actor">Actors</option>
          <option value="political">Politics</option>
          <option value="economic">Economics</option>
          <option value="resource">Resources</option>
          <option value="military">Military</option>
          <option value="strategic">Strategic</option>
        </select>
        <button id="gp-web-reset" type="button">Reset</button>
      </div>
      <div class="gp-web-toolbar">
        <span class="gp-3d-status"><b>3D</b> DRAG NODES · ROTATE · ZOOM</span>
        <button id="gp-web-fit" type="button">Fit network</button>
      </div>
      <div class="gp-web" id="gp-web-canvas" aria-label="3D interactive intelligence web"></div>
      <div class="gp-web-detail" id="gp-web-detail">Tap a node to inspect connected entities and the evidence behind each relationship.</div>
      <div class="gp-web-note">The 3D renderer is the open-source 3d-force-graph engine. Drag nodes to reposition them, pinch/scroll to zoom, and drag empty space to rotate the network. Relationship colors classify stored evidence; they do not imply causation.</div>`;

    const style = document.createElement('style');
    style.textContent = `
      #gp-intel-web .gp-web-legend{display:flex;gap:11px;flex-wrap:wrap;margin:-2px 0 10px;font-size:9px;color:var(--muted)}
      #gp-intel-web .gp-web-legend span{display:inline-flex;align-items:center;gap:5px}
      #gp-intel-web .gp-web-legend i{width:9px;height:9px;border-radius:50%;display:inline-block}
      #gp-intel-web .gp-web-legend i[data-k="country"]{background:#62a0ff}
      #gp-intel-web .gp-web-legend i[data-k="political"]{background:#aa8df7}
      #gp-intel-web .gp-web-legend i[data-k="economic"]{background:#ffc857}
      #gp-intel-web .gp-web-legend i[data-k="oil"]{background:#fb923c}
      #gp-intel-web .gp-web-legend i[data-k="resource"]{background:#48df83}
      #gp-intel-web .gp-web-legend i[data-k="military"]{background:#ff6678}
      #gp-intel-web .gp-web-controls{display:grid;grid-template-columns:minmax(0,1fr) 220px auto;gap:10px;align-items:center;margin:10px 0}
      #gp-intel-web .gp-web-controls input,#gp-intel-web .gp-web-controls select,#gp-intel-web .gp-web-controls button,#gp-intel-web .gp-web-toolbar button{min-height:42px}
      #gp-intel-web .gp-web-toolbar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:4px 0 8px}
      #gp-intel-web .gp-3d-status{font-size:9px;letter-spacing:.08em;color:var(--muted)}
      #gp-intel-web .gp-3d-status b{color:#62a0ff;margin-right:5px}
      #gp-intel-web .gp-web{height:620px;min-height:430px;position:relative;overflow:hidden;border:1px solid var(--line);border-radius:14px;background:#020812;box-shadow:inset 0 0 80px rgba(0,0,0,.45)}
      #gp-intel-web .gp-web canvas{display:block;width:100%!important;height:100%!important;touch-action:none}
      #gp-intel-web .gp-web-detail{margin-top:10px;border:1px solid var(--line);border-radius:12px;padding:12px;color:var(--muted);font-size:11px;line-height:1.5;min-height:44px}
      #gp-intel-web .gp-web-links{margin-top:9px;display:grid;gap:7px}
      #gp-intel-web .gp-link-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px;padding:8px;border-top:1px solid var(--line)}
      #gp-intel-web .gp-link-row small{grid-column:1/-1;color:var(--muted)}
      #gp-intel-web .gp-evidence-open{padding:6px 9px;border:1px solid rgba(98,160,255,.35);border-radius:8px;background:transparent;color:var(--blue);font-weight:800;font-size:9px;cursor:pointer}
      #gp-intel-web .gp-no-evidence{font-size:10px;color:var(--muted)}
      #gp-intel-web .gp-evidence-modal{position:fixed;inset:0;z-index:1000;display:flex;align-items:center;justify-content:center;padding:18px;background:rgba(0,0,0,.72);backdrop-filter:blur(6px)}
      #gp-intel-web .gp-evidence-dialog{position:relative;width:min(680px,100%);max-height:85vh;overflow:auto;background:#0b131d;color:var(--text);border:1px solid var(--line);border-radius:15px;padding:16px;box-shadow:0 20px 70px rgba(0,0,0,.5)}
      #gp-intel-web .gp-evidence-dialog h3{margin:0 40px 8px 0;font-size:14px}
      #gp-intel-web .gp-evidence-dialog p{font-size:11px;color:var(--muted);line-height:1.5}
      #gp-intel-web .gp-evidence-close{position:absolute;right:10px;top:10px;width:32px;height:32px;border-radius:50%;font-size:18px}
      #gp-intel-web .gp-evidence-row{padding:10px 0;border-top:1px solid var(--line)}
      @media(max-width:700px){
        #gp-intel-web .gp-web-controls{grid-template-columns:1fr 1fr}
        #gp-intel-web .gp-web-controls input{grid-column:1/-1}
        #gp-intel-web .gp-web-toolbar{align-items:flex-start}
        #gp-intel-web .gp-web{height:560px;min-height:420px}
      }
    `;
    document.head.appendChild(style);

    const mapSection = document.getElementById('map') && document.getElementById('map').closest('section');
    wrap.insertBefore(sec, mapSection || wrap.firstElementChild || null);

    const canvas = sec.querySelector('#gp-web-canvas');
    const search = sec.querySelector('#gp-web-search');
    const kind = sec.querySelector('#gp-web-kind');
    const fit = sec.querySelector('#gp-web-fit');
    const data = makeData(g);
    let Graph = null;

    function filteredData() {
      const q = String(search.value || '').toLowerCase().trim();
      const k = kind.value;
      const visible = data.nodes.filter(node => {
        const hay = `${node.label} ${node.kind || ''} ${node.type || ''}`.toLowerCase();
        return (!q || hay.includes(q)) && (k === 'all' || node.__kind === k);
      });
      const set = new Set(visible.map(node => node.id));
      return {
        nodes: visible,
        links: data.links.filter(link => set.has(typeof link.source === 'object' ? link.source.id : link.source) && set.has(typeof link.target === 'object' ? link.target.id : link.target))
      };
    }

    function openExternal(url) {
      const clean = safeUrl(url);
      if (!clean) return false;
      const popup = window.open(clean, '_blank', 'noopener,noreferrer');
      if (popup) { try { popup.opener = null; } catch (_) {} return true; }
      window.location.assign(clean);
      return true;
    }

    function openEvidence(edge, name) {
      const ev = Array.isArray(edge.evidence) ? edge.evidence : [];
      const other = edge.source === name ? edge.target : edge.source;
      const otherLabel = typeof other === 'object' ? other.label || other.id : other;
      const modal = document.createElement('div');
      modal.className = 'gp-evidence-modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      const dialog = document.createElement('div');
      dialog.className = 'gp-evidence-dialog';
      const close = document.createElement('button');
      close.className = 'gp-evidence-close';
      close.type = 'button';
      close.textContent = '×';
      close.setAttribute('aria-label', 'Close evidence');
      const title = document.createElement('h3');
      title.textContent = `Evidence: ${name} ↔ ${otherLabel}`;
      dialog.appendChild(close);
      dialog.appendChild(title);
      const intro = document.createElement('p');
      intro.textContent = 'Stored public reporting associated with this relationship. This is evidence of shared reporting, not proof of causation or coordination.';
      dialog.appendChild(intro);
      if (!ev.length) {
        const p = document.createElement('p');
        p.textContent = 'No source evidence is available in this snapshot.';
        dialog.appendChild(p);
      }
      ev.forEach((item) => {
        const row = document.createElement('div');
        row.className = 'gp-evidence-row';
        const h = document.createElement('strong');
        h.textContent = item.title || 'Untitled source report';
        row.appendChild(h);
        const meta = document.createElement('p');
        meta.textContent = (item.source || item.source_name || 'Public source') + (item.time ? ` · ${item.time}` : '');
        row.appendChild(meta);
        const link = evidenceUrl(item);
        if (link) {
          const a = document.createElement('button');
          a.className = 'gp-evidence-open';
          a.type = 'button';
          a.textContent = 'Open source report ↗';
          a.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); openExternal(link); });
          row.appendChild(a);
        } else {
          const missing = document.createElement('p');
          missing.textContent = 'Source URL unavailable for this record.';
          row.appendChild(missing);
        }
        dialog.appendChild(row);
      });
      modal.appendChild(dialog);
      document.body.appendChild(modal);
      const closeIt = () => { modal.remove(); document.removeEventListener('keydown', escKey); };
      const escKey = (e) => { if (e.key === 'Escape') closeIt(); };
      close.onclick = closeIt;
      modal.addEventListener('click', (e) => { if (e.target === modal) closeIt(); });
      document.addEventListener('keydown', escKey);
      close.focus();
    }

    function detail(node) {
      const detailEl = sec.querySelector('#gp-web-detail');
      const links = data.links.filter(e => {
        const s = typeof e.source === 'object' ? e.source.id : e.source;
        const t = typeof e.target === 'object' ? e.target.id : e.target;
        return s === node.id || t === node.id;
      }).sort((a, b) => n(b.weight) - n(a.weight)).slice(0, 12);
      let html = `<strong>${esc(node.label)}</strong> · ${links.length} strongest evidence links`;
      if (!links.length) { detailEl.innerHTML = html + '<br><span>No linked evidence in this snapshot.</span>'; return; }
      html += '<div class="gp-web-links">' + links.map((e, i) => {
        const s = typeof e.source === 'object' ? e.source : data.nodes.find(x => x.id === e.source);
        const t = typeof e.target === 'object' ? e.target : data.nodes.find(x => x.id === e.target);
        const other = (s && s.id === node.id) ? t : s;
        const otherName = other ? other.label : 'Unknown';
        const ev = Array.isArray(e.evidence) ? e.evidence : [];
        const latest = ev[0] || {};
        const ek = e.__kind || edgeKind(e);
        return `<div class="gp-link-row"><span>${esc(otherName)} <b style="color:${edgeColor(ek)}">${esc(ek.toUpperCase())} · ${n(e.weight)}×</b></span>${ev.length ? `<button type="button" class="gp-evidence-open" data-edge-index="${i}">Evidence ↗</button>` : '<span class="gp-no-evidence">Evidence unavailable</span>'}${latest.title ? `<small>${esc(latest.source || latest.source_name || 'Public source')} · ${esc(latest.title)}</small>` : ''}</div>`;
      }).join('') + '</div>';
      detailEl.innerHTML = html;
      detailEl.querySelectorAll('[data-edge-index]').forEach(btn => btn.addEventListener('click', () => openEvidence(links[Number(btn.dataset.edgeIndex)], node.label)));
    }

    function render() {
      if (!Graph) return;
      const fd = filteredData();
      Graph.graphData(fd);
      sec.querySelector('.gp-web-count').textContent = `${fd.nodes.length} nodes · ${fd.links.length} evidence links`;
      setTimeout(() => { try { Graph.zoomToFit(700, 50); } catch (_) {} }, 80);
    }

    loadGraphLibrary().then((ForceGraph3D) => {
      Graph = new ForceGraph3D(canvas)
        .backgroundColor('#020812')
        .nodeId('id')
        .nodeLabel(node => `<b>${esc(node.label)}</b><br><span style="opacity:.75">${esc(node.__kind)}</span>`)
        .nodeColor(node => node.__color)
        .nodeVal(node => Math.max(1, Math.sqrt(Math.max(1, n(node.mentions || node.weight || 1))) * 2.5))
        .nodeRelSize(4.5)
        .nodeOpacity(0.96)
        .linkColor(link => link.__color || edgeColor(edgeKind(link)))
        .linkOpacity(0.52)
        .linkWidth(link => Math.min(3.5, 0.8 + Math.sqrt(Math.max(1, n(link.weight || 1))) * 0.45))
        .linkDirectionalParticles(link => Math.min(3, Math.max(1, Math.round(n(link.weight || 1) / 3))))
        .linkDirectionalParticleWidth(1.4)
        .linkDirectionalParticleSpeed(0.004)
        .linkDirectionalArrowLength(3.5)
        .linkDirectionalArrowRelPos(0.92)
        .linkCurvature(0.08)
        .cooldownTicks(180)
        .d3AlphaDecay(0.022)
        .d3VelocityDecay(0.32)
        .onNodeClick((node) => {
          detail(node);
          const distance = 80;
          const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);
          Graph.cameraPosition(
            { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
            node,
            900
          );
        })
        .onNodeDragEnd((node) => {
          // Keep deliberately dragged nodes where the user put them.
          node.fx = node.x;
          node.fy = node.y;
          node.fz = node.z;
        })
        .graphData(filteredData());

      // Do not auto-rotate: users should control the network directly.
      render();
    }).catch((err) => {
      canvas.innerHTML = `<div style="height:100%;display:grid;place-items:center;padding:24px;text-align:center;color:#9aaabd;font-size:12px"><div><strong style="color:#ff6678">3D renderer unavailable</strong><br><br>Refresh once to retry the open-source renderer.<br><small>${esc(err.message)}</small></div></div>`;
    });

    sec.querySelector('#gp-web-reset').onclick = () => { search.value = ''; kind.value = 'all'; render(); };
    search.addEventListener('input', render);
    kind.addEventListener('change', render);
    fit.addEventListener('click', () => { if (Graph) Graph.zoomToFit(700, 50); });

    return true;
  }

  let tries = 0;
  const timer = setInterval(() => {
    tries++;
    if (boot() || tries > 120) clearInterval(timer);
  }, 250);
  document.addEventListener('globalpulse:dataready', () => {
    if (!document.getElementById('gp-intel-web')) boot();
  });
})();
