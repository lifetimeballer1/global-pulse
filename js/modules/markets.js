/** Market Context (clearly labeled DELAYED) */

import { getState } from '../core/state.js';
import { escapeHtml } from '../core/utils.js';

export function renderMarkets() {
  const el = document.getElementById('marketsBody');
  if (!el) return;

  const { snapshot, markets } = getState();

  let items = [];
  if (Array.isArray(markets)) items = markets;
  else if (markets?.indicators) items = markets.indicators;
  else if (snapshot?.markets) items = Array.isArray(snapshot.markets) ? snapshot.markets : Object.entries(snapshot.markets || {}).map(([k, v]) => ({ name: k, ...v }));
  else if (snapshot?.marketPulse) items = snapshot.marketPulse;

  if (!items.length) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">Market data unavailable</div>
        <div>Public delayed market feed is not present in the current snapshot. This is expected if the market adapter has not run.</div>
      </div>`;
    return;
  }

  el.innerHTML = `
    <div class="gp-grid gp-grid-3">
      ${items.slice(0, 12).map(m => {
        const name = m.name || m.symbol || m.ticker || '—';
        const price = m.price ?? m.last ?? m.close ?? '—';
        const change = m.change ?? m.changePct ?? m.pct ?? null;
        const changeStr = change != null ? (Number(change) > 0 ? `+${Number(change).toFixed(2)}%` : `${Number(change).toFixed(2)}%`) : '—';
        const color = change == null ? 'var(--muted)' : Number(change) >= 0 ? 'var(--green)' : 'var(--red)';

        return `
          <div class="gp-card">
            <div style="font-size:11px;color:var(--muted);margin-bottom:4px">${escapeHtml(name)}</div>
            <div style="font-size:18px;font-weight:700;font-variant-numeric:tabular-nums">${escapeHtml(String(price))}</div>
            <div style="font-size:13px;font-weight:600;color:${color};margin-top:2px">${changeStr}</div>
          </div>`;
      }).join('')}
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--muted-2)">
      All prices DELAYED / END-OF-DAY or public free-tier. Not real-time. Not investment advice.
    </div>
  `;
}
