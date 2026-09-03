/* Global Pulse — live reporting bridge
 * Connects to a local FastAPI news API when available and falls back to the
 * repository's generated live article snapshot so GitHub Pages never looks broken.
 */
(function () {
  "use strict";

  var POLL_MS = 60000;
  var TIMEOUT_MS = 12000;
  var FEED_ID = "pulse-reporting-feed";
  var COUNT_ID = "pulse-reporting-count";
  var FALLBACK_URLS = [
    "data/live_articles.json",
    "data/snapshot.json"
  ];

  function qs(id) { return document.getElementById(id); }

  function safeText(value, fallback) {
    var text = String(value == null ? "" : value).trim();
    return text || (fallback || "");
  }

  function safeUrl(value) {
    try {
      var u = new URL(String(value || ""), location.href);
      if (u.protocol !== "http:" && u.protocol !== "https:") return "";
      return u.href;
    } catch (e) {
      return "";
    }
  }

  function relativeTime(value) {
    var t = Date.parse(value || "");
    if (!isFinite(t)) return "Time unavailable";
    var delta = Math.max(0, Date.now() - t);
    var minutes = Math.floor(delta / 60000);
    var hours = Math.floor(minutes / 60);
    var days = Math.floor(hours / 24);
    if (minutes < 1) return "just now";
    if (minutes < 60) return minutes + "m ago";
    if (hours < 24) return hours + "h ago";
    if (days < 7) return days + "d ago";
    return new Date(t).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  function sourceIcon(source) {
    var s = String(source || "").toLowerCase();
    if (/twitter|x\.com|^x$/.test(s)) return "🐦";
    if (/youtube/.test(s)) return "▶️";
    if (/cnn|bbc|reuters|fox|npr|axios|guardian|morse|al jazeera/.test(s)) return "📡";
    return "📰";
  }

  function normalizeArticle(article) {
    if (!article || typeof article !== "object") return null;
    var credit = article.credit || {};
    var url = safeUrl(article.original_link || article.url || article.link || credit.source_url);
    return {
      title: safeText(article.title, "Untitled report"),
      published_date: safeText(article.published_date || article.time || article.publishedAt),
      summary_snippet: safeText(article.summary_snippet || article.summary || article.description, "No summary was provided by the source."),
      original_link: url,
      source: safeText(credit.source || article.source_name || article.sourceLabel || article.source, "Unknown Source")
    };
  }

  function normalizePayload(payload) {
    if (!payload || typeof payload !== "object") return [];
    if (Array.isArray(payload.articles)) return payload.articles.map(normalizeArticle).filter(Boolean);
    if (Array.isArray(payload.stories)) return payload.stories.map(function (story) {
      return normalizeArticle({
        title: story.title,
        published_date: story.time || story.published_date,
        summary_snippet: story.summary,
        original_link: story.url || story.link || story.sourceUrl,
        credit: { source: story.sourceLabel || story.source || "Open Data", source_url: story.url || story.link }
      });
    }).filter(Boolean);
    if (Array.isArray(payload.data && payload.data.articles)) return payload.data.articles.map(normalizeArticle).filter(Boolean);
    return [];
  }

  function setStatus(count, source) {
    var el = qs(COUNT_ID);
    if (!el) return;
    el.textContent = count + " ACTIVE" + (source === "fallback" ? " · SNAPSHOT" : "");
  }

  function createCard(article) {
    var card = document.createElement("article");
    card.className = "gp-reporting-card";

    var badge = document.createElement("div");
    badge.className = "gp-reporting-source";
    badge.textContent = "[" + sourceIcon(article.source) + " " + article.source + "]";

    var title = document.createElement("a");
    title.className = "gp-reporting-title";
    title.textContent = article.title;
    if (article.original_link) {
      title.href = article.original_link;
      title.target = "_blank";
      title.rel = "noopener noreferrer";
    }

    var time = document.createElement("time");
    time.className = "gp-reporting-time";
    time.dateTime = article.published_date || "";
    time.textContent = relativeTime(article.published_date);
    if (article.published_date) time.title = new Date(Date.parse(article.published_date)).toLocaleString();

    var summary = document.createElement("p");
    summary.className = "gp-reporting-summary";
    summary.textContent = article.summary_snippet;

    var source = document.createElement("div");
    source.className = "gp-reporting-source-name";
    source.textContent = "Source: " + article.source;

    var read = document.createElement("a");
    read.className = "gp-reporting-action";
    read.textContent = "Read Full Source Report ↗";
    if (article.original_link) {
      read.href = article.original_link;
      read.target = "_blank";
      read.rel = "noopener noreferrer";
    } else {
      read.href = "#";
      read.setAttribute("aria-disabled", "true");
      read.addEventListener("click", function (event) { event.preventDefault(); });
    }

    card.appendChild(badge);
    card.appendChild(title);
    card.appendChild(time);
    card.appendChild(summary);
    card.appendChild(source);
    card.appendChild(read);
    return card;
  }

  function render(articles, source) {
    var feed = qs(FEED_ID);
    if (!feed) return;
    feed.replaceChildren();
    if (!articles.length) {
      var empty = document.createElement("div");
      empty.className = "gp-reporting-empty";
      empty.textContent = "No active reporting is currently available.";
      feed.appendChild(empty);
      setStatus(0, source);
      return;
    }
    var fragment = document.createDocumentFragment();
    articles.forEach(function (article) { fragment.appendChild(createCard(article)); });
    feed.appendChild(fragment);
    setStatus(articles.length, source);
  }

  function showAlert(keepExisting) {
    var feed = qs(FEED_ID);
    if (!feed) return;
    var old = feed.querySelector(".gp-reporting-alert");
    if (old) return;
    var alert = document.createElement("div");
    alert.className = "gp-reporting-alert";
    alert.setAttribute("role", "alert");
    var strong = document.createElement("strong");
    strong.textContent = "Pipeline Connection Terminated - Retrying...";
    var detail = document.createElement("span");
    detail.textContent = keepExisting ? "Last good reporting remains visible while the live connection is retried." : "The live reporting service is unavailable. Global Pulse will retry automatically.";
    alert.appendChild(strong);
    alert.appendChild(detail);
    if (keepExisting) feed.prepend(alert); else { feed.replaceChildren(alert); setStatus(0, "fallback"); }
  }

  async function fetchJSON(url) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);
    try {
      var response = await fetch(url, {
        cache: "no-store",
        headers: { "Accept": "application/json" },
        signal: controller.signal
      });
      if (!response.ok) throw new Error("HTTP " + response.status);
      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  function apiCandidates() {
    var configured = window.GLOBAL_PULSE_API;
    var candidates = [];
    if (configured) candidates.push(configured);
    if (location.hostname === "127.0.0.1" || location.hostname === "localhost") {
      candidates.push(location.origin + "/");
    }
    candidates.push("http://127.0.0.1:8000/");
    candidates.push("http://127.0.0.1:8000/api/news");
    candidates.push("http://127.0.0.1:8000/news");
    candidates.push("http://127.0.0.1:8000/articles");
    candidates.push("http://localhost:8000/");
    return candidates.filter(function (url, index, arr) { return url && arr.indexOf(url) === index; });
  }

  async function fetchFastAPI() {
    var candidates = apiCandidates();
    for (var i = 0; i < candidates.length; i++) {
      try {
        var payload = await fetchJSON(candidates[i]);
        var articles = normalizePayload(payload);
        if (payload && payload.status === "success" && Array.isArray(payload.articles)) return articles;
        if (articles.length) return articles;
      } catch (error) {
        /* Try the next endpoint without interrupting the dashboard. */
      }
    }
    throw new Error("FastAPI unavailable");
  }

  async function fetchFallback() {
    for (var i = 0; i < FALLBACK_URLS.length; i++) {
      try {
        var payload = await fetchJSON(FALLBACK_URLS[i] + "?gp=" + Date.now());
        var articles = normalizePayload(payload);
        if (articles.length) return articles;
      } catch (error) {
        /* Try the next repository snapshot. */
      }
    }
    return [];
  }

  async function fetchPulseReporting() {
    var feed = qs(FEED_ID);
    if (!feed) return;
    feed.setAttribute("aria-busy", "true");

    try {
      var articles = await fetchFastAPI();
      render(articles, "live");
      feed.classList.remove("gp-reporting-fallback");
      var alert = feed.querySelector(".gp-reporting-alert");
      if (alert) alert.remove();
    } catch (apiError) {
      var existing = feed.querySelectorAll(".gp-reporting-card").length > 0;
      var fallback = await fetchFallback();
      if (fallback.length) {
        render(fallback, "fallback");
        feed.classList.add("gp-reporting-fallback");
        showAlert(true);
      } else {
        showAlert(existing);
      }
    } finally {
      feed.setAttribute("aria-busy", "false");
    }
  }

  function refreshRelativeTimes() {
    document.querySelectorAll(".gp-reporting-time").forEach(function (el) {
      if (el.dateTime) el.textContent = relativeTime(el.dateTime);
    });
  }

  window.fetchPulseReporting = fetchPulseReporting;

  function start() {
    fetchPulseReporting();
    setInterval(fetchPulseReporting, POLL_MS);
    setInterval(refreshRelativeTimes, 30000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
})();
