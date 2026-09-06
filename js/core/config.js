/** Global Pulse configuration */

export const CONFIG = {
  // Data endpoints (relative for GitHub Pages)
  endpoints: {
    snapshot: './data/snapshot.json',
    liveArticles: './data/live_articles.json',
    intelligenceGraph: './data/intelligence_graph.json',
    sources: './data/sources.json',
    sourceHealth: './data/source_health.json',
    markets: './data/markets.json', // optional generated
    refreshManifest: './data/refresh_manifest.json'
  },

  // Refresh intervals (ms)
  refresh: {
    snapshot: 5 * 60 * 1000,      // 5 min check
    breaking: 10 * 60 * 1000,
    markets: 15 * 60 * 1000
  },

  // Confidence thresholds (used by normalizer)
  confidence: {
    high: 0.75,
    moderate: 0.5,
    limited: 0.3
  },

  // UI
  maxBreakingItems: 12,
  maxConflictCards: 8,
  mapDefaultCenter: [20, 10],
  mapDefaultZoom: 2
};

export const CONFIDENCE_LABELS = {
  high: { label: 'CONFIRMED', class: 'conf-high' },
  moderate: { label: 'LIKELY', class: 'conf-mod' },
  limited: { label: 'LIMITED', class: 'conf-low' },
  unverified: { label: 'UNVERIFIED', class: 'conf-unver' },
  conflicting: { label: 'CONFLICTING', class: 'conf-conflict' }
};
