/* Global Pulse — canonical page layout
 * One stable layout controller. Uses CSS order; never reparents dynamic modules.
 */
(() => {
  'use strict';
  if (window.__GLOBAL_PULSE_LAYOUT__) return;
  window.__GLOBAL_PULSE_LAYOUT__ = true;

  const SELECTORS = {
    root: '#global-pulse-app, main, .app, .container',
    sections: [
      { key: 'breaking', order: 10, selectors: ['#breaking-intelligence', '#breaking-news', '[data-section="breaking"]'] },
      { key: 'changed', order: 20, selectors: ['#what-changed', '[data-section="what-changed"]'] },
      { key: 'assessment', order: 30, selectors: ['#global-index', '#global-assessment', '[data-section="assessment"]'] },
      { key: 'conflicts', order: 40, selectors: ['#active-conflicts', '#conflict-watch', '[data-section="conflicts"]'] },
      { key: 'evidence', order: 50, selectors: ['#event-intelligence', '#investigation', '[data-section="evidence"]'] },
      { key: 'map', order: 60, selectors: ['#global-map', '#situation-map', '[data-section="map"]'] },
      { key: 'regional', order: 70, selectors: ['#regional-intelligence', '[data-section="regional"]'] },
      { key: 'reporting', order: 80, selectors: ['#latest-reporting', '#news-feed', '[data-section="reporting"]'] },
      { key: 'history', order: 90, selectors: ['#event-history', '#historical-trends', '[data-section="history"]'] },
      { key: 'markets', order: 100, selectors: ['#market-context', '#markets', '[data-section="markets"]'] },
      { key: 'graph', order: 110, selectors: ['#intelligence-web', '#intelligence-graph', '[data-section="graph"]'] },
      { key: 'watchlist', order: 120, selectors: ['#watchlist', '[data-section="watchlist"]'] },
      { key: 'sources', order: 130, selectors: ['#source-health', '#sources-health', '[data-section="source-health"]'] }
    ]
  };

  const find = (selectors, root) => {
    for (const selector of selectors) {
      try { const el = root.querySelector(selector); if (el) return el; } catch (_) {}
    }
    return null;
  };

  function apply() {
    const root = document.querySelector(SELECTORS.root);
    if (!root) return false;
    root.classList.add('gp-canonical-layout');
    root.style.setProperty('--gp-layout-managed', '1');

    let found = 0;
    for (const section of SELECTORS.sections) {
      const el = find(section.selectors, root);
      if (!el) continue;
      found += 1;
      el.dataset.gpLayoutKey = section.key;
      el.style.order = String(section.order);
      el.classList.add('gp-layout-section');
    }
    return found > 0;
  }

  const boot = () => {
    apply();
    let queued = false;
    const schedule = () => {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => { queued = false; apply(); });
    };
    const root = document.querySelector(SELECTORS.root) || document.body;
    new MutationObserver(schedule).observe(root, { childList: true, subtree: true });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
