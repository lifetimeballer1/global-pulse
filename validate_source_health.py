#!/usr/bin/env python3
"""Validate source health before a production snapshot can be published.

The gate is intentionally based on coverage and fallback health, not raw feed
count. Social/mirror failures cannot make the whole pipeline fail when a
configured fallback is healthy, while broad primary-source degradation does.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
HEALTH = DATA / "source_health.json"

MIN_FEEDS = 20
MIN_ROWS = 1
MIN_HEALTHY_RATIO = 0.70
MAX_CRITICAL_FAILURE_RATIO = 0.35
REQUIRED_CATEGORIES = {"international", "us-politics", "security"}


def main() -> int:
    if not HEALTH.is_file() or HEALTH.stat().st_size == 0:
        raise SystemExit("SOURCE HEALTH GATE FAILED: source_health.json missing/empty")
    d = json.loads(HEALTH.read_text(encoding="utf-8"))
    summary = d.get("summary") or {}
    sources = d.get("sources") or []
    feeds = int(d.get("feedsChecked") or summary.get("total") or 0)
    rows = int(d.get("rowsFetched") or 0)
    online = int(summary.get("online") or 0)
    degraded = int(summary.get("degraded") or 0)
    failed = int(summary.get("failed") or 0)
    total = len(sources) or int(summary.get("total") or 0)

    if feeds < MIN_FEEDS or rows < MIN_ROWS:
        raise SystemExit(f"SOURCE HEALTH GATE FAILED: feeds={feeds}, rows={rows}")
    if total <= 0:
        raise SystemExit("SOURCE HEALTH GATE FAILED: no source records")

    healthy_ratio = (online + degraded) / total
    failure_ratio = failed / total
    if healthy_ratio < MIN_HEALTHY_RATIO:
        raise SystemExit(f"SOURCE HEALTH GATE FAILED: healthy ratio={healthy_ratio:.1%} < {MIN_HEALTHY_RATIO:.0%}")
    if failure_ratio > MAX_CRITICAL_FAILURE_RATIO:
        raise SystemExit(f"SOURCE HEALTH GATE FAILED: failure ratio={failure_ratio:.1%} > {MAX_CRITICAL_FAILURE_RATIO:.0%}")

    covered_categories = set()
    uncovered_required = []
    for category in REQUIRED_CATEGORIES:
        candidates = [s for s in sources if s.get("category") == category]
        usable = [s for s in candidates if s.get("status") in {"online", "degraded"} or s.get("fallbackCoverage")]
        if usable:
            covered_categories.add(category)
        else:
            uncovered_required.append(category)
    if uncovered_required:
        raise SystemExit("SOURCE HEALTH GATE FAILED: uncovered categories=" + ",".join(sorted(uncovered_required)))

    fallback_covered = sum(1 for s in sources if s.get("status") == "failed" and s.get("fallbackCoverage"))
    print("PASS: source health gate")
    print(f"feeds={feeds} rows={rows} healthy={online + degraded}/{total} ({healthy_ratio:.1%}) failed={failed} ({failure_ratio:.1%})")
    print(f"fallback-covered failures={fallback_covered} required-categories={','.join(sorted(covered_categories))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
