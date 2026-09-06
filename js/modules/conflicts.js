/** Active Conflict Watch */

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
  }

  if (!conflicts.length) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">No ranked conflict signals</div>
        <div>Conflict layer is empty or not yet generated in the current snapshot.</div>
      </div>`;
    return;
  }

  conflicts = conflicts.slice(0, CONFIG.maxConflictCards);

  if (updatedEl) {
    updatedEl.textContent = formatRelativeTime(snapshot?.updatedAt);
  }

  el.innerHTML = `
    <div class="gp-grid gp-grid-2">
      ${conflicts.map(c => {
        const name = c.name || c.title || c.conflict || 'Unnamed conflict';
        const location = c.location || c.region || c.countries?.join(', ') || '';
        const status = c.status || c.state || 'Active monitoring';
        const score = c.score ?? c.risk ?? c.tension ?? null;
        const level = scoreToLevel(score);
        const confKey = (c.confidence || 'limited').toLowerCase();
        const conf = CONFIDENCE_LABELS[confKey] || CONFIDENCE_LABELS.limited;
        const recent = c.recent || c.latest || c.summary || '';
        const actors = c.actors || c.parties || [];

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
                  <div class="gp-meter-fill ${level}" style="width:${Math.min(100, score)}%"></div>
                </div>
              </div>` : ''}
            ${recent ? `<div style="font-size:12.5px;color:var(--text-secondary)">${escapeHtml(recent)}</div>` : ''}
            ${actors.length ? `<div style="font-size:11px;color:var(--muted);margin-top:6px">Actors: ${escapeHtml(actors.slice(0, 4).join(', '))}</div>` : ''}
          </div>`;
      }).join('')}
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--muted-2)">
      Rankings are analytical signals derived from open data. They are not official designations.
    </div>
  `;
}
