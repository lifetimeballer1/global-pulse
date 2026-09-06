/** Resilient data fetcher with cache + freshness */

import { CONFIG } from './config.js';
import { setState, setError, clearError } from './state.js';

const CACHE_PREFIX = 'gp_cache_';
const CACHE_TTL_MS = 30 * 60 * 1000; // 30 min soft cache

function cacheKey(url) {
  return CACHE_PREFIX + btoa(url).slice(0, 40);
}

function getCached(url) {
  try {
    const raw = localStorage.getItem(cacheKey(url));
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL_MS) return null;
    return data;
  } catch {
    return null;
  }
}

function setCached(url, data) {
  try {
    localStorage.setItem(cacheKey(url), JSON.stringify({ data, ts: Date.now() }));
  } catch {
    // quota or private mode — ignore
  }
}

/**
 * Fetch JSON with cache fallback and clear error handling.
 * Never throws — returns { ok, data, fromCache, error }.
 */
export async function fetchJson(url, options = {}) {
  const { force = false, label = url } = options;

  if (!force) {
    const cached = getCached(url);
    if (cached) {
      return { ok: true, data: cached, fromCache: true, error: null };
    }
  }

  try {
    const res = await fetch(url, {
      cache: force ? 'reload' : 'default',
      headers: { Accept: 'application/json' }
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    setCached(url, data);
    clearError(label);
    return { ok: true, data, fromCache: false, error: null };
  } catch (err) {
    const cached = getCached(url); // even if expired, use as last resort
    if (cached) {
      setError(label, `Using cached data (${err.message})`);
      return { ok: true, data: cached, fromCache: true, error: err.message };
    }
    setError(label, err.message || 'Fetch failed');
    return { ok: false, data: null, fromCache: false, error: err.message };
  }
}

/**
 * Load core intelligence snapshot + related artifacts.
 */
export async function loadCoreData({ force = false } = {}) {
  setState({ status: 'loading' });

  const results = await Promise.allSettled([
    fetchJson(CONFIG.endpoints.snapshot, { force, label: 'snapshot' }),
    fetchJson(CONFIG.endpoints.liveArticles, { force, label: 'liveArticles' }),
    fetchJson(CONFIG.endpoints.intelligenceGraph, { force, label: 'intelligenceGraph' }),
    fetchJson(CONFIG.endpoints.sources, { force, label: 'sources' }),
    fetchJson(CONFIG.endpoints.sourceHealth, { force, label: 'sourceHealth' })
  ]);

  const [snap, arts, graph, srcs, health] = results.map(r =>
    r.status === 'fulfilled' ? r.value : { ok: false, data: null, error: r.reason?.message }
  );

  const hasAny = snap.ok || arts.ok || graph.ok;

  setState({
    snapshot: snap.data,
    liveArticles: arts.data,
    intelligenceGraph: graph.data,
    sources: srcs.data,
    sourceHealth: health.data,
    lastSuccessfulFetch: hasAny ? new Date().toISOString() : null,
    status: hasAny ? (snap.fromCache || arts.fromCache ? 'stale' : 'live') : 'error'
  });

  return { snapshot: snap, liveArticles: arts, intelligenceGraph: graph };
}
