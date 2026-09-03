(() => {
  'use strict';
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = (x) => {
    if (x == null || Number.isNaN(Number(x))) return '—';
    const n = Number(x); return n.toLocaleString(undefined, {maximumFractionDigits: 6});
  };
  const pct = (x) => x == null ? '—' : `${Number(x) >= 0 ? '+' : ''}${Number(x).toFixed(2)}%`;
  async function load() {
    const r = await fetch(`data/snapshot.json?markets=${Date.now()}`, {cache:'no-store'});
    if (!r.ok) throw new Error(`snapshot ${r.status}`);
    return r.json();
  }
  function render(data) {
    const m = data.marketData || {};
    const items = Array.isArray(m.indicators) ? m.indicators : [];
    let el = document.getElementById('gp-markets-panel');
    if (!el) {
      el = document.createElement('section'); el.id='gp-markets-panel'; el.className='panel wide';
      const wrap=document.querySelector('.wrap'); if (wrap) wrap.prepend(el); else document.body.prepend(el);
    }
    const live=Number(m.liveCount||0), stale=Number(m.staleCount||0);
    el.innerHTML = `<div class="section-head"><div><h2>Live Markets</h2><div class="gp-mkt-status"><span class="gp-mkt-dot"></span>${live} live · ${stale} stale · ${esc(m.provider||'Public market feed')}</div></div><div class="gp-mkt-time">Updated ${esc(m.updatedAt||'—')}</div></div>`+
      `<div class="gp-mkt-grid">${items.map(x => `<article class="gp-mkt-card"><div class="gp-mkt-name">${esc(x.name)}</div><div class="gp-mkt-price">${esc(fmt(x.price))}<small>${esc(x.currency||x.unit||'')}</small></div><div class="gp-mkt-change ${Number(x.change)>=0?'up':'down'}">${esc(pct(x.changePercent))} <span>${esc(x.status||'')}</span></div><div class="gp-mkt-meta">${esc(x.symbol)} · ${esc(x.exchange||'')} · ${esc(x.marketTime||x.checkedAt||'')}</div></article>`).join('')}</div>`+
      `<div class="gp-mkt-note">Keyless public quotes. “Live” means the provider reports an active market state; closed/stale values are labeled rather than fabricated.</div>`;
  }
  const style=document.createElement('style'); style.textContent=`#gp-markets-panel{margin-bottom:14px}.gp-mkt-status{font-size:11px;color:var(--muted)}.gp-mkt-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:5px;box-shadow:0 0 0 3px rgba(72,223,131,.08)}.gp-mkt-time{font-size:10px;color:var(--muted);max-width:300px;text-align:right}.gp-mkt-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.gp-mkt-card{padding:11px;background:var(--panel2);border:1px solid var(--line);border-radius:10px;min-width:0}.gp-mkt-name{font-size:11px;font-weight:800;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.gp-mkt-price{font-size:20px;font-weight:900;margin-top:4px}.gp-mkt-price small{font-size:9px;color:var(--muted);margin-left:4px}.gp-mkt-change{font-size:11px;font-weight:800;margin-top:3px}.gp-mkt-change.up{color:var(--green)}.gp-mkt-change.down{color:var(--red)}.gp-mkt-change span{font-size:8px;text-transform:uppercase;color:var(--muted);margin-left:4px}.gp-mkt-meta{font-size:8px;color:var(--muted);margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.gp-mkt-note{font-size:9px;color:var(--muted);margin-top:9px}@media(max-width:900px){.gp-mkt-grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:600px){.gp-mkt-grid{grid-template-columns:repeat(2,1fr)}.gp-mkt-time{max-width:170px}.gp-mkt-price{font-size:18px}}`;
  document.head.appendChild(style);
  async function refresh(){try{render(await load())}catch(e){const el=document.getElementById('gp-markets-panel'); if(el) el.querySelector('.gp-mkt-note')?.insertAdjacentHTML('afterend',`<div class="gp-mkt-note" style="color:var(--red)">Market refresh unavailable; showing last published snapshot.</div>`); console.warn('Global Pulse markets:',e)}}
  document.addEventListener('DOMContentLoaded',()=>{refresh();setInterval(refresh,60000)});
})();
