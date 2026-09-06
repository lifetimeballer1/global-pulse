/** Breaking / Latest Reporting */

import { getState } from '../core/state.js';
import { formatRelativeTime, escapeHtml } from '../core/utils.js';
import { CONFIG, CONFIDENCE_LABELS } from '../core/config.js';

export function renderBreaking() {
  const el = document.getElementById('breakingBody');
  const updatedEl = document.getElementById('breakingUpdated');
  if (!el) return;

  const { liveArticles, snapshot } = getState();

  // Prefer dedicated live_articles, fall back to snapshot stories
  let items = [];
  if (Array.isArray(liveArticles)) {
    items = liveArticles;
  } else if (liveArticles?.articles) {
    items = liveArticles.articles;
  } else if (snapshot?.stories) {
    items = snapshot.stories;
  } else if (snapshot?.liveArticles) {
    items = snapshot.liveArticles;
  }

  if (!items.length) {
    el.innerHTML = `
      <div class="gp-state">
        <div class="gp-state-title">No recent reports</div>
        <div>Live article feed is empty or unavailable. Check source health below.</div>
      </div>`;
    return;
  }

  // Sort by time desc if possible
  items = [...items].sort((a, b) => {
    const ta = new Date(a.published || a.publishedAt || a.date || 0).getTime();
    const tb = new Date(b.published || b.publishedAt || b.date || 0).getTime();
    return tb - ta;
  }).slice(0, CONFIG.maxBreakingItems);

  if (updatedEl && items[0]) {
    const t = items[0].published || items[0].publishedAt || items[0].date;
    updatedEl.textContent = formatRelativeTime(t);
  }

  el.innerHTML = items.map(item => {
    const title = item.title || item.headline || 'Untitled';
    const summary = item.summary || item.description || item.snippet || '';
    const source = item.source || item.sourceName || item.publisher || 'Unknown source';
    const url = item.url || item.link || item.sourceUrl || '#';
    const time = item.published || item.publishedAt || item.date;
    const confKey = (item.confidence || item.conf || 'limited').toLowerCase();
    const conf = CONFIDENCE_LABELS[confKey] || CONFIDENCE_LABELS.limited;
    const category = item.category || item.topic || '';

    return `
      <article class="gp-news-item">
        <h3 class="gp-news-title">
          <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>
        </h3>
        ${summary ? `<p class="gp-news-summary">${escapeHtml(summary)}</p>` : ''}
        <div class="gp-card-meta">
          <span class="gp-badge ${conf.class}">${conf.label}</span>
          ${category ? `<span class="gp-badge category">${escapeHtml(category)}</span>` : ''}
          <span class="gp-source">${escapeHtml(source)}</span>
          <span class="gp-time">${formatRelativeTime(time)}</span>
        </div>
      </article>`;
  }).join('');
}
