/** Intelligence Web — uses intelligenceGraph from snapshot */

import { getState } from '../core/state.js';
import { escapeHtml, formatRelativeTime } from '../core/utils.js';

export function renderIntelligenceWeb() {
  const el = document.getElementById('intelwebBody');
  const updatedEl = document.getElementById('intelwebUpdated');
  if (!el) return;

  const { intelligenceGraph, snapshot } = getState();

  const graph = intelligenceGraph
    || snapshot?.intelligenceGraph
    || snapshot?.graph
    || null;

  if (!graph || (!graph.nodes && !graph.entities)) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">Intelligence Web not available</div>
        <div>Evidence-linked relationship data has not been generated for this snapshot.</div>
      </div>`;
    return;
  }

  const nodes = graph.nodes || graph.entities || [];
  const edges = graph.edges || graph.links || graph.connections || [];
  const caution = graph.caution || '';

  if (updatedEl) {
    updatedEl.textContent = formatRelativeTime(graph.updatedAt || snapshot?.updatedAt);
  }

  const degree = {};
  edges.forEach(e => {
    const s = e.source || e.from;
    const t = e.target || e.to;
    if (s) degree[s] = (degree[s] || 0) + 1;
    if (t) degree[t] = (degree[t] || 0) + 1;
  });

  const topNodes = [...nodes]
    .map(n => ({ ...n, _deg: degree[n.id] || n.degree || n.connections || 0 }))
    .sort((a, b) => b._deg - a._deg)
    .slice(0, 14);

  el.innerHTML = `
    <div style="font-size:12.5px;color:var(--text-secondary);margin-bottom:12px">
      Evidence-backed relationships between actors, conflicts, economic pressure and strategic interests.
      Connections require supporting public evidence; correlation is never treated as causation.
    </div>
    ${caution ? `<div class="gp-card" style="margin-bottom:12px;font-size:12px;color:var(--amber)">${escapeHtml(caution)}</div>` : ''}
    <div class="gp-grid gp-grid-2">
      ${topNodes.map(n => {
        const name = n.label || n.name || n.id || 'Node';
        const type = n.type || n.category || 'entity';
        return `
          <div class="gp-card">
            <div class="gp-card-title">${escapeHtml(String(name))}</div>
            <div class="gp-card-meta">
              <span class="gp-badge category">${escapeHtml(String(type))}</span>
              <span>${n._deg} links</span>
            </div>
          </div>`;
      }).join('') || '<div class="gp-state">No nodes in current graph</div>'}
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--muted-2)">
      ${edges.length} total evidence-backed connections · ${nodes.length} entities · Method: ${escapeHtml(graph.method || 'evidence graph')}
    </div>
  `;
}
