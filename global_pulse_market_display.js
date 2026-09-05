/* Global Pulse — Market Data Display Panel & Live Ticker */
(function() {
  'use strict';
  const ID='gp-market-display';
  const esc=v=>String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  function formatPrice(val,decimals=2){if(!Number.isFinite(val))return '—';return val.toLocaleString('en-US',{minimumFractionDigits:decimals,maximumFractionDigits:decimals});}
  function colorForChange(pct){if(!Number.isFinite(pct))return 'var(--muted)';if(pct>0.5)return 'var(--green)';if(pct< -0.5)return 'var(--red)';return 'var(--amber)';}
  function marketRows(data){
    const raw=data?.marketData;
    if(Array.isArray(raw))return raw;
    if(raw&&Array.isArray(raw.indicators))return raw.indicators;
    if(raw&&Array.isArray(raw.quotes))return raw.quotes;
    return [];
  }
  function renderMarketCard(m){
    const price=Number(m.price),change=Number(m.change),pct=Number(m.changePercent??m.percentChange),status=String(m.status||m.sessionStatus||'stale').toLowerCase();
    const color=colorForChange(pct),symbol=String(m.symbol||m.ticker||''),name=String(m.name||symbol||'Market');
    const unit=String(m.unit||m.currency||'USD'),dec=Number.isFinite(Number(m.decimals))?Number(m.decimals):2;
    return '<article class="gp-market-card" data-symbol="'+esc(symbol)+'"><div class="gp-market-head"><div class="gp-market-info"><strong>'+esc(name)+'</strong><span class="gp-market-unit">'+esc(unit)+'</span></div><span class="gp-market-status" title="'+esc(status)+'">'+(status==='live'?'🔴':status==='closed'?'⚫':'⚪')+'</span></div><div class="gp-market-price" style="color:'+color+'">'+formatPrice(price,dec)+'</div><div class="gp-market-delta" style="color:'+color+'">'+(change>=0?'+':'')+formatPrice(change,dec)+' <span class="gp-market-pct">('+(pct>=0?'+':'')+formatPrice(pct,2)+'%)</span></div><div class="gp-market-meta"><span>'+esc(m.marketTime||m.updatedAt||'')+'</span></div></article>';
  }
  function install(){
    const top=document.getElementById('top');if(!top||document.getElementById('marketSection'))return !!document.getElementById('marketSection');
    const section=document.createElement('section');section.id='marketSection';section.className='panel wide gp-market-section';section.setAttribute('aria-labelledby','market-title');
    section.innerHTML='<div class="section-head"><div><h2 id="market-title">Market Pulse</h2><div class="muted">Live global market indicators and economic risk context</div></div><a href="markets.html" class="open" aria-label="Open full markets page">OPEN MARKETS ↗</a></div><div id="'+ID+'" class="gp-market-grid"></div><div class="gp-market-note"><small>Public market data; live when the relevant exchange is open. <a href="markets.html" class="gp-link">Open full market dashboard</a></small></div>';
    const wrap=document.querySelector('.wrap');if(wrap){const t=wrap.querySelector('#top');if(t)t.insertAdjacentElement('afterend',section);else wrap.prepend(section);}return true;
  }
  function render(){const data=window.DATA||{};const rows=marketRows(data),box=document.getElementById(ID);if(!box)return;if(!rows.length){box.innerHTML='<div class="status">Market data is unavailable in this snapshot.</div>';return}box.innerHTML=rows.slice(0,12).map(renderMarketCard).join('');const time=document.getElementById('gp-market-time');if(time)time.textContent='Updated '+new Date(data.marketData?.updatedAt||Date.now()).toLocaleTimeString();}
  document.addEventListener('globalpulse:dataready',render);
  function wait(){if(install())render();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wait);else setTimeout(wait,100);
})();
