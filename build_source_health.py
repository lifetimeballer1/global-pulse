#!/usr/bin/env python3
"""Build durable, per-source freshness/health telemetry from the live collector.

No API key is required.  The collector writes data/live_status.json on every
poll; this layer keeps the previous successful check so a transient failure
cannot make a source appear to have been offline forever.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATUS = DATA / "live_status.json"
OUT = DATA / "source_health.json"

PRIMARY = [
    ("CNN", "news", "international", "Google News — CNN Politics"),
    ("Fox News Politics", "news", "us-politics", "Google News — U.S. Politics"),
    ("NPR Politics", "news", "us-politics", "Google News — U.S. Politics"),
    ("BBC World", "news", "international", "Google News — World Politics"),
    ("The Guardian World", "news", "international", "Google News — World Politics"),
    ("Al Jazeera", "news", "international", "Google News — World Politics"),
    ("DW World", "news", "international", "Google News — World Politics"),
    ("France 24", "news", "international", "Google News — World Politics"),
    ("CNA World", "news", "international", "Google News — World Politics"),
    ("Stars and Stripes", "news", "security", "Google News — Global Conflict"),
    ("Morse Report", "podcast/news", "us-politics", "Google News — Morse Report"),
    ("Morse Report — Google News", "news-mirror", "us-politics", "Google News — Morse Report"),
    ("Axios Politics", "news-mirror", "us-politics", "Google News — Axios Politics"),
    ("CNN Politics", "news-mirror", "us-politics", "Google News — CNN Politics"),
    ("Morse Report — GDELT Mirror", "news-mirror", "us-politics", "Google News — Morse Report"),
    ("X @NASA", "social", "osint", "Google News — World Politics"),
    ("X @WhiteHouse", "social", "osint", "Google News — U.S. Politics"),
    ("X @POTUS", "social", "osint", "Google News — U.S. Politics"),
    ("X @NATO", "social", "osint", "Google News — World Politics"),
    ("X @UN", "social", "osint", "Google News — World Politics"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def age_minutes(value: str | None, now: datetime) -> float | None:
    dt = parse_dt(value)
    if not dt:
        return None
    return round(max(0.0, (now - dt.astimezone(timezone.utc)).total_seconds() / 60.0), 1)


def main() -> None:
    now = datetime.now(timezone.utc)
    current = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    previous = {}
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            previous = {}
    previous_by = {str(x.get("name")): x for x in previous.get("sources", []) if isinstance(x, dict)}

    errors = {
        str(x.get("source")): str(x.get("error", ""))
        for x in current.get("failedSources", [])
        if isinstance(x, dict)
    }
    checked_at = str(current.get("updatedAt") or now.isoformat())
    sources = []
    for name, kind, category, fallback in PRIMARY:
        old = previous_by.get(name, {})
        error = errors.get(name, "")
        failed = bool(error)
        old_failures = int(old.get("consecutiveFailures", 0) or 0)
        if failed:
            status = "failed" if old_failures >= 1 else "degraded"
            consecutive = old_failures + 1
            last_success = old.get("lastSuccess")
        else:
            status = "online"
            consecutive = 0
            last_success = checked_at
        sources.append({
            "name": name,
            "type": kind,
            "category": category,
            "status": status,
            "lastChecked": checked_at,
            "lastSuccess": last_success,
            "freshnessMinutes": age_minutes(last_success, now),
            "consecutiveFailures": consecutive,
            "error": error,
            "fallback": fallback,
            "fallbackCoverage": bool(fallback),
        })

    online = sum(x["status"] == "online" for x in sources)
    degraded = sum(x["status"] == "degraded" for x in sources)
    failed = sum(x["status"] == "failed" for x in sources)
    covered = sum(x["status"] != "online" and x["fallbackCoverage"] for x in sources)
    result = {
        "version": 1,
        "updatedAt": now.isoformat(),
        "collectorUpdatedAt": checked_at,
        "feedsChecked": int(current.get("feedsChecked", len(sources)) or len(sources)),
        "rowsFetched": int(current.get("rowsFetched", 0) or 0),
        "newArticles": int(current.get("newArticles", 0) or 0),
        "databaseArticles": int(current.get("databaseArticles", 0) or 0),
        "pollSeconds": int(current.get("pollSeconds", 300) or 300),
        "summary": {
            "total": len(sources),
            "online": online,
            "degraded": degraded,
            "failed": failed,
            "fallbackCovered": covered,
            "coveragePercent": round(100 * (online + covered) / len(sources), 1) if sources else 0,
        },
        "sources": sources,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
