/** Market Context — uses real marketData.indicators, labeled DELAYED */

import { getState } from '../core/state.js';
import { formatRelativeTime, escapeHtml } from '../core/utils.js';

export function renderMarkets() {
  const el = document.getElementById('marketsBody');
  if (!el) return;

  const { snapshot, markets } = getState();

  let items = [];
  let meta = {};

  if (Array.isArray(markets)) {
    items = markets;
  } else if (markets?.indicators) {
    items = markets.indicators;
    meta = markets;
  } else if (snapshot?.marketData?.indicators) {
    items = snapshot.marketData.indicators;
    meta = snapshot.marketData;
  } else if (snapshot?.markets) {
    items = Array.isArray(snapshot.markets) ? snapshot.markets : Object.entries(snapshot.markets || {}).map(([k, v]) => ({ name: k, ...v }));
  } else if (snapshot?.marketPulse) {
    items = snapshot.marketPulse;
  }

  if (!items.length) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">Market data unavailable</div>
        <div>Public delayed market feed is not present in the current snapshot.</div>
      </div>`;
    return;
  }

  const updated = meta.updatedAt || snapshot?.updatedAt;
  const provider = meta.provider || meta.source || 'Public delayed feed';

  el.innerHTML = `
    <div style="font-size:11px;color:var(--muted);margin-bottom:10px">
      ${escapeHtml(provider)} · Updated ${formatRelativeTime(updated)} · <span class="gp-badge delayed">DELAYED</span>
    </div>
    <div class="gp-grid gp-grid-3">
      ${items.slice(0, 15).map(m => {
        const name = m.name || m.symbol || m.ticker || m.exchange || '—';
        const price = m.price ?? m.last ?? m.close ?? '—';
        const change = m.changePercent ?? m.changePct ?? m.pct ?? m.change ?? null;
        let changeStr = '—';
        let color = 'var(--muted)';
        if (change != null && !Number.isNaN(Number(change))) {
          const n = Number(change);
          changeStr = (n > 0 ? '+' : '') + n.toFixed(2) + '%';
          color = n >= 0 ? 'var(--green)' : 'var(--red)';
        }
        const state = m.sessionStatus || m.marketState || '';

        return `
          <div class="gp-card">
            <div style="font-size:11px;color:var(--muted);margin-bottom:4px">${escapeHtml(String(name))}</div>
            <div style="font-size:18px;font-weight:700;font-variant-numeric:tabular-nums">${escapeHtml(String(typeof price === 'number' ? price.toLocaleString(undefined, {maximumFractionDigits: 2}) : price))}</div>
            <div style="font-size:13px;font-weight:600;color:${color};margin-top:2px">${changeStr}</div>
            ${state ? `<div style="font-size:10px;color:var(--muted-2);margin-top:2px">${escapeHtml(state)}</div>` : ''}
          </div>`;
      }).join('')}
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--muted-2)">
      All prices are DELAYED / END-OF-DAY or public free-tier. Not real-time. Not investment advice. No API key required.
    </div>
  `;
}
