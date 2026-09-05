/* Global Pulse — Market Data Display Panel & Live Ticker */
(function() {
  'use strict';
  
  const ID = 'gp-market-display';
  
  function formatPrice(val, decimals = 2) {
    if (!Number.isFinite(val)) return '—';
    return val.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }
  
  function colorForChange(pct) {
    if (!Number.isFinite(pct)) return 'var(--muted)';
    if (pct > 0.5) return 'var(--green)';
    if (pct < -0.5) return 'var(--red)';
    return 'var(--amber)';
  }
  
  function renderMarketCard(market) {
    if (!market) return '';
    
    const price = Number(market.price || 0);
    const prev = Number(market.previousClose || price);
    const change = Number(market.change || 0);
    const pct = Number(market.changePercent || 0);
    const status = String(market.status || 'stale').toLowerCase();
    
    const statusIcon = {
      'live': '🔴',
      'stale': '⚪',
      'closed': '⚫'
    }[status] || '⚪';
    
    const color = colorForChange(pct);
    const symbol = String(market.symbol || market.name || '');
    const name = String(market.name || '');
    const unit = String(market.unit || 'USD');
    
    return `
      <div class="gp-market-card" data-symbol="${symbol}" data-status="${status}">
        <div class="gp-market-head">
          <div class="gp-market-info">
            <strong>${name || symbol}</strong>
            <span class="gp-market-unit">${unit}</span>
          </div>
          <span class="gp-market-status" title="${status}">${statusIcon}</span>
        </div>
        <div class="gp-market-price" style="color: ${color}">
          ${formatPrice(price, market.decimals || 2)}
        </div>
        <div class="gp-market-delta" style="color: ${color}">
          ${change >= 0 ? '+' : ''}${formatPrice(change, market.decimals || 2)}
          <span class="gp-market-pct">(${pct >= 0 ? '+' : ''}${formatPrice(pct, 2)}%)</span>
        </div>
        <div class="gp-market-meta">
          <span class="gp-market-time">${market.marketTime ? new Date(market.marketTime).toLocaleTimeString() : 'N/A'}</span>
        </div>
      </div>
    `;
  }
  
  function install() {
    const top = document.getElementById('top');
    if (!top || document.getElementById(ID)) return false;
    
    // Find or create market section
    const existing = document.getElementById('marketSection');
    if (existing) return true;
    
    // Insert after top section
    const section = document.createElement('section');
    section.id = 'marketSection';
    section.className = 'panel wide gp-market-section';
    section.setAttribute('aria-labelledby', 'market-title');
    section.innerHTML = `
      <div class="section-head">
        <div>
          <h2 id="market-title">Market Pulse</h2>
          <div class="muted">Real-time global market indicators synchronized with conflict signals and economic tension</div>
        </div>
        <span class="gp-market-update-time" id="gp-market-time">—</span>
      </div>
      <div id="${ID}" class="gp-market-grid"></div>
      <div class="gp-market-note">
        <small>Markets sourced from public endpoints. Live when exchange is active in local time. 
        <a href="#intelligenceWebSection" class="gp-link">View market relationships in Intelligence Web</a></small>
      </div>
    `;
    
    // Insert after the top section
    const wrap = document.querySelector('.wrap');
    if (wrap) {
      const topSection = wrap.querySelector('#top');
      if (topSection && topSection.nextElementSibling) {
        topSection.nextElementSibling.insertAdjacentElement('beforebegin', section);
      } else if (topSection) {
        topSection.insertAdjacentElement('afterend', section);
      }
    }
    
    return true;
  }
  
  function render() {
    const data = window.DATA || {};
    const markets = Array.isArray(data.marketData) ? data.marketData : [];
    const container = document.getElementById(ID);
    
    if (!container) return;
    
    if (markets.length === 0) {
      container.innerHTML = '<div class="status">No market data available</div>';
      return;
    }
    
    container.innerHTML = markets.map(renderMarketCard).join('');
    
    // Update timestamp
    const timeEl = document.getElementById('gp-market-time');
    if (timeEl && data.marketData && data.marketData[0]) {
      const market = data.marketData[0];
      const time = new Date(market.marketTime || Date.now());
      timeEl.textContent = `Updated ${time.toLocaleTimeString()}`;
      timeEl.title = time.toLocaleString();
    }
  }
  
  // Listen for data updates
  document.addEventListener('globalpulse:dataready', render);
  
  // Install and render on load
  const wait = () => {
    if (install()) {
      render();
    }
  };
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wait);
  } else {
    setTimeout(wait, 100);
  }
})();
