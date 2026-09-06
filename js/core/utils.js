/** Shared utilities */

export function formatRelativeTime(iso) {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diff = Date.now() - then;
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  return `${day}d ago`;
}

export function formatAbsoluteTime(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch {
    return '—';
  }
}

export function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

export function scoreToLevel(score) {
  if (score == null || Number.isNaN(score)) return 'low';
  if (score >= 75) return 'critical';
  if (score >= 55) return 'high';
  if (score >= 35) return 'mid';
  return 'low';
}

export function confidenceFromScore(score, sources = 1) {
  if (score >= 0.8 && sources >= 3) return 'high';
  if (score >= 0.6 && sources >= 2) return 'moderate';
  if (score >= 0.4) return 'limited';
  return 'unverified';
}
