/** System & Source Status */

import { getState } from '../core/state.js';
import { formatRelativeTime, escapeHtml } from '../core/utils.js';

export function renderStatus() {
  const el = document.getElementById('statusBody');
  const dot = document.getElementById('statusDot');
  const globalUpdated = document.getElementById('globalLastUpdated');
  if (!el) return;

  const { status, lastSuccessfulFetch, sourceHealth, sources, errors, snapshot } = getState();

  if (dot) {
    dot.className = 'gp-status-dot ' + (status === 'live' ? 'live' : status === 'error' ? 'error' : 'stale');
  }
  if (globalUpdated) {
    globalUpdated.textContent = lastSuccessfulFetch
      ? `Updated ${formatRelativeTime(lastSuccessfulFetch)}`
      : 'No successful fetch yet';
  }

  let healthHtml = '';
  if (sourceHealth?.sources || Array.isArray(sourceHealth)) {
    const list = Array.isArray(sourceHealth) ? sourceHealth : (sourceHealth.sources || []);
    healthHtml = `
      <div class="gp-grid gp-grid-2" style="margin-top:12px">
        ${list.slice(0, 10).map(s => {
          const name = s.name || s.id || s.domain || 'Source';
          const ok = s.ok ?? s.healthy ?? s.status === 'ok';
          const age = s.lastSuccess || s.last_fetched || s.updatedAt;
          return `
            <div class="gp-card" style="padding:10px">
              <div style="font-weight:600;font-size:12px">${escapeHtml(name)}</div>
              <div class="gp-card-meta">
                <span class="gp-badge ${ok ? 'conf-high' : 'conf-unver'}">${ok ? 'OK' : 'ISSUE'}</span>
                <span class="gp-time">${formatRelativeTime(age)}</span>
              </div>
            </div>`;
        }).join('')}
      </div>`;
  }

  const errorList = Object.entries(errors || {});
  el.innerHTML = `
    <div class="gp-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
        <div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em">Overall Status</div>
          <div style="font-size:16px;font-weight:700;text-transform:capitalize">${escapeHtml(status)}</div>
        </div>
        <div style="text-align:right;font-size:12px;color:var(--muted)">
          Last successful load<br>
          <strong>${formatRelativeTime(lastSuccessfulFetch)}</strong>
        </div>
      </div>
    </div>
    ${errorList.length ? `
      <div class="gp-card" style="margin-top:10px;border-color:var(--red-dim)">
        <div style="font-weight:700;color:var(--red);margin-bottom:6px">Recent errors</div>
        ${errorList.map(([k, v]) => `<div style="font-size:12px"><strong>${escapeHtml(k)}</strong>: ${escapeHtml(v)}</div>`).join('')}
      </div>` : ''}
    ${healthHtml}
    <div style="margin-top:14px;font-size:11px;color:var(--muted-2)">
      Global Pulse uses only public open sources. Source availability can change. Always verify critical claims against primary sources.
    </div>
  `;
}
