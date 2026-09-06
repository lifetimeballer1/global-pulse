/** Intelligence Web (relationship layer) — simplified list + graph placeholder */

import { getState } from '../core/state.js';
import { escapeHtml, formatRelativeTime } from '../core/utils.js';

export function renderIntelligenceWeb() {
  const el = document.getElementById('intelwebBody');
  const updatedEl = document.getElementById('intelwebUpdated');
  if (!el) return;

  const { intelligenceGraph, snapshot } = getState();

  const graph = intelligenceGraph || snapshot?.intelligenceGraph || snapshot?.graph || null;

  if (!graph) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">Intelligence Web not available</div>
        <div>Evidence-linked relationship data has not been generated for this snapshot. The pipeline will rebuild it on the next successful run.</div>
      </div>`;
    return;
  }

  const nodes = graph.nodes || graph.entities || [];
  const edges = graph.edges || graph.links || graph.connections || [];

  if (updatedEl) {
    updatedEl.textContent = formatRelativeTime(graph.updatedAt || snapshot?.updatedAt);
  }

  // Show top connected nodes
  const topNodes = nodes.slice(0, 12);

  el.innerHTML = `
    <div style="font-size:12.5px;color:var(--text-secondary);margin-bottom:12px">
      Evidence-backed relationships between actors, conflicts, economic pressure and strategic interests.
      Connections require supporting public evidence; correlation is never treated as causation.
    </div>
    <div class="gp-grid gp-grid-2">
      ${topNodes.map(n => {
        const name = n.label || n.name || n.id || 'Node';
        const type = n.type || n.category || 'entity';
        const degree = n.degree ?? n.connections ?? (edges.filter(e => e.source === n.id || e.target === n.id).length);
        return `
          <div class="gp-card">
            <div class="gp-card-title">${escapeHtml(name)}</div>
            <div class="gp-card-meta">
              <span class="gp-badge category">${escapeHtml(type)}</span>
              <span>${degree} links</span>
            </div>
          </div>`;
      }).join('') || '<div class="gp-state">No nodes in current graph</div>'}
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--muted-2)">
      ${edges.length} total evidence-backed connections · Full interactive graph coming in a later polish pass
    </div>
  `;
}
