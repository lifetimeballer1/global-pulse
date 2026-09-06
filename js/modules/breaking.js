/** Breaking / Latest Reporting — uses stories + live_articles */

import { getState } from '../core/state.js';
import { formatRelativeTime, escapeHtml } from '../core/utils.js';
import { CONFIG, CONFIDENCE_LABELS } from '../core/config.js';

export function renderBreaking() {
  const el = document.getElementById('breakingBody');
  const updatedEl = document.getElementById('breakingUpdated');
  if (!el) return;

  const { liveArticles, snapshot } = getState();

  let items = [];
  if (Array.isArray(liveArticles)) {
    items = liveArticles;
  } else if (liveArticles?.articles) {
    items = liveArticles.articles;
  } else if (Array.isArray(snapshot?.stories)) {
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

  items = [...items].sort((a, b) => {
    const ta = new Date(a.published || a.publishedAt || a.published_date || a.publishedDate || a.time || a.date || 0).getTime();
    const tb = new Date(b.published || b.publishedAt || b.published_date || b.publishedDate || b.time || b.date || 0).getTime();
    return tb - ta;
  }).slice(0, CONFIG.maxBreakingItems);

  if (updatedEl && items[0]) {
    const t = items[0].published || items[0].publishedAt || items[0].published_date || items[0].publishedDate || items[0].time;
    updatedEl.textContent = formatRelativeTime(t);
  }

  el.innerHTML = items.map(item => {
    const title = item.title || item.headline || 'Untitled';
    const summary = item.summary || item.summary_snippet || item.description || item.snippet || '';
    const source = item.sourceLabel || item.sourceName || item.source || item.publisher || 'Unknown source';
    const url = item.url || item.link || item.sourceUrl || '#';
    const time = item.published || item.publishedAt || item.published_date || item.publishedDate || item.time || item.date;
    const confRaw = (item.confidence || item.conf || 'limited').toString().toLowerCase();
    const confKey = confRaw.includes('high') || confRaw === 'confirmed' ? 'high'
      : confRaw.includes('mod') || confRaw === 'likely' ? 'moderate'
      : confRaw.includes('unver') ? 'unverified'
      : confRaw.includes('conflict') ? 'conflicting' : 'limited';
    const conf = CONFIDENCE_LABELS[confKey] || CONFIDENCE_LABELS.limited;
    const category = item.tag || item.category || item.topic || (item.breaking ? 'BREAKING' : '');

    return `
      <article class="gp-news-item">
        <h3 class="gp-news-title">
          <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>
        </h3>
        ${summary ? `<p class="gp-news-summary">${escapeHtml(summary)}</p>` : ''}
        <div class="gp-card-meta">
          <span class="gp-badge ${conf.class}">${conf.label}</span>
          ${category ? `<span class="gp-badge category">${escapeHtml(String(category))}</span>` : ''}
          <span class="gp-source">${escapeHtml(source)}</span>
          <span class="gp-time">${formatRelativeTime(time)}</span>
        </div>
      </article>`;
  }).join('');
}
