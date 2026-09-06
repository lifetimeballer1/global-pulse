/** Active Conflict Watch — uses real conflicts array */

import { getState } from '../core/state.js';
import { formatRelativeTime, escapeHtml, scoreToLevel } from '../core/utils.js';
import { CONFIG, CONFIDENCE_LABELS } from '../core/config.js';

export function renderConflicts() {
  const el = document.getElementById('conflictsBody');
  const updatedEl = document.getElementById('conflictsUpdated');
  if (!el) return;

  const { snapshot } = getState();

  let conflicts = [];
  if (Array.isArray(snapshot?.conflicts)) {
    conflicts = snapshot.conflicts;
  } else if (snapshot?.conflictWatch) {
    conflicts = snapshot.conflictWatch;
  } else if (snapshot?.activeConflicts) {
    conflicts = snapshot.activeConflicts;
  } else if (Array.isArray(snapshot?.cfrConflicts)) {
    conflicts = snapshot.cfrConflicts;
  }

  if (!conflicts.length) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">No ranked conflict signals</div>
        <div>Conflict layer is empty or not yet generated in the current snapshot.</div>
      </div>`;
    return;
  }

  conflicts = [...conflicts].sort((a, b) => {
    const sa = a.activityScore ?? a.escalation ?? a.score ?? a.risk ?? 0;
    const sb = b.activityScore ?? b.escalation ?? b.score ?? b.risk ?? 0;
    return sb - sa;
  }).slice(0, CONFIG.maxConflictCards);

  if (updatedEl) {
    updatedEl.textContent = formatRelativeTime(snapshot?.updatedAt);
  }

  el.innerHTML = `
    <div class="gp-grid gp-grid-2">
      ${conflicts.map(c => {
        const name = c.name || c.title || c.conflict || 'Unnamed conflict';
        const location = c.region || c.location || (Array.isArray(c.countries) ? c.countries.join(', ') : '');
        const status = c.status || c.state || c.category || 'Active monitoring';
        const score = c.activityScore ?? c.escalation ?? c.score ?? c.risk ?? null;
        const level = scoreToLevel(score);
        const confRaw = (c.confidence || 'limited').toString().toLowerCase();
        const confKey = confRaw.includes('high') ? 'high' : confRaw.includes('mod') ? 'moderate' : confRaw.includes('unver') ? 'unverified' : 'limited';
        const conf = CONFIDENCE_LABELS[confKey] || CONFIDENCE_LABELS.limited;
        const recent = c.recent || c.latest || c.summary || (c.facts && c.facts[0]) || '';
        const analysis = c.analysis || '';
        const signals = c.signalCount ?? c.signals?.length ?? null;
        const sources = c.sourceCount ?? null;

        return `
          <div class="gp-card">
            <div class="gp-card-title">${escapeHtml(name)}</div>
            ${location ? `<div style="font-size:12px;color:var(--muted);margin-bottom:6px">${escapeHtml(location)}</div>` : ''}
            <div class="gp-card-meta" style="margin-bottom:8px">
              <span class="gp-badge ${conf.class}">${conf.label}</span>
              <span class="gp-badge category">${escapeHtml(status)}</span>
              ${score != null ? `<span style="font-weight:700">${Math.round(score)}</span>` : ''}
            </div>
            ${score != null ? `
              <div class="gp-meter" style="margin-bottom:8px">
                <div class="gp-meter-bar">
                  <div class="gp-meter-fill ${level}" style="width:${Math.min(100, Number(score))}%"></div>
                </div>
              </div>` : ''}
            ${recent ? `<div style="font-size:12.5px;color:var(--text-secondary);margin-bottom:4px">${escapeHtml(String(recent).slice(0, 220))}</div>` : ''}
            ${analysis ? `<div style="font-size:11px;color:var(--muted);margin-top:4px"><strong>Analysis:</strong> ${escapeHtml(String(analysis).slice(0, 160))}</div>` : ''}
            <div style="font-size:11px;color:var(--muted-2);margin-top:6px">
              ${signals != null ? `${signals} signals` : ''} ${sources != null ? `· ${sources} sources` : ''}
            </div>
          </div>`;
      }).join('')}
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--muted-2)">
      Rankings are analytical signals derived from open data. They are not official designations. Facts and analysis are separated where available.
    </div>
  `;
}
