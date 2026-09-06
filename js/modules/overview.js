/** Global Situation Overview renderer */

import { getState } from '../core/state.js';
import { formatRelativeTime, escapeHtml, scoreToLevel } from '../core/utils.js';
import { CONFIDENCE_LABELS } from '../core/config.js';

export function renderOverview() {
  const el = document.getElementById('overviewBody');
  const updatedEl = document.getElementById('overviewUpdated');
  if (!el) return;

  const { snapshot, status } = getState();

  if (!snapshot) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">${status === 'error' ? 'Data unavailable' : 'Loading…'}</div>
        <div>Public intelligence snapshot could not be loaded. Showing last known state if available.</div>
      </div>`;
    return;
  }

  const updated = snapshot.updatedAt || snapshot.lastUpdated || null;
  if (updatedEl) updatedEl.textContent = formatRelativeTime(updated);

  // Support both current Global Pulse shape and a cleaner future shape
  const tension = snapshot.globalTension ?? snapshot.tension ?? snapshot.score ?? null;
  const drivers = snapshot.drivers || snapshot.tensionDrivers || {};
  const note = snapshot.dataNote || snapshot.sourceStatus || '';

  const driverKeys = [
    { key: 'conflict', label: 'Conflict activity' },
    { key: 'diplomatic', label: 'Diplomatic strain' },
    { key: 'economic', label: 'Economic pressure' },
    { key: 'market', label: 'Market volatility' },
    { key: 'military', label: 'Military posture' }
  ];

  let driversHtml = '';
  for (const d of driverKeys) {
    const val = drivers[d.key] ?? drivers[d.label] ?? null;
    const num = typeof val === 'number' ? val : (val?.score ?? null);
    const level = scoreToLevel(num);
    const display = num != null ? Math.round(num) : '—';
    driversHtml += `
      <div class="gp-meter">
        <div class="gp-meter-label">
          <span>${escapeHtml(d.label)}</span>
          <strong>${display}</strong>
        </div>
        <div class="gp-meter-bar">
          <div class="gp-meter-fill ${level}" style="width:${num != null ? clampPct(num) : 0}%"></div>
        </div>
      </div>`;
  }

  const tensionLevel = scoreToLevel(tension);
  const tensionDisplay = tension != null ? Math.round(tension) : '—';

  el.innerHTML = `
    <div class="gp-grid gp-grid-2" style="margin-bottom:16px">
      <div class="gp-card">
        <div style="font-size:11px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px">Global Tension Index</div>
        <div style="font-size:32px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1">${tensionDisplay}</div>
        <div class="gp-meter" style="margin-top:10px">
          <div class="gp-meter-bar" style="height:8px">
            <div class="gp-meter-fill ${tensionLevel}" style="width:${tension != null ? clampPct(tension) : 0}%"></div>
          </div>
        </div>
        <div style="font-size:11px;color:var(--muted);margin-top:8px">Composite open-data signal. Higher = greater combined pressure.</div>
      </div>
      <div class="gp-card">
        <div style="font-size:11px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px">Key Drivers</div>
        ${driversHtml || '<div style="color:var(--muted)">No driver breakdown available</div>'}
      </div>
    </div>
    ${note ? `<div class="gp-card" style="font-size:12px;color:var(--text-secondary)">${escapeHtml(note)}</div>` : ''}
    <div style="margin-top:12px;font-size:11px;color:var(--muted-2)">
      Analytical indicator only — not an official government risk rating. Always verify against primary sources.
    </div>
  `;
}

function clampPct(n) {
  return Math.max(0, Math.min(100, Number(n) || 0));
}
