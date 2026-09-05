#!/usr/bin/env python3
"""Validate the CURRENT live collector result before publication.

This gate must consume live_status.json because refresh_pipeline.py runs the
collector immediately before this check. source_health.json is a downstream
presentation artifact and may intentionally still describe the previous
published snapshot at this point in the pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
STATUS = DATA / "live_status.json"

MIN_FEEDS = 20
MIN_ROWS = 1
MIN_HEALTHY_RATIO = 0.70
MAX_FAILURE_RATIO = 0.35
REQUIRED_CATEGORIES = {"international", "us-politics", "security"}
USABLE_MODES = {"native", "gdelt-domain-fallback"}


def main() -> int:
    if not STATUS.is_file() or STATUS.stat().st_size == 0:
        raise SystemExit("SOURCE HEALTH GATE FAILED: live_status.json missing/empty")

    d = json.loads(STATUS.read_text(encoding="utf-8"))
    feeds = int(d.get("feedsChecked") or 0)
    rows = int(d.get("rowsFetched") or 0)
    results = d.get("sourceResults") or []
    if feeds < MIN_FEEDS or rows < MIN_ROWS:
        raise SystemExit(f"SOURCE HEALTH GATE FAILED: feeds={feeds}, rows={rows}")
    if not isinstance(results, list) or not results:
        raise SystemExit("SOURCE HEALTH GATE FAILED: no current source results")

    total = len(results)
    healthy = sum(1 for s in results if s.get("httpOk") is True)
    failed = sum(1 for s in results if s.get("httpOk") is not True)
    healthy_ratio = healthy / total
    failure_ratio = failed / total

    if healthy_ratio < MIN_HEALTHY_RATIO:
        raise SystemExit(f"SOURCE HEALTH GATE FAILED: current healthy ratio={healthy_ratio:.1%} < {MIN_HEALTHY_RATIO:.0%}")
    if failure_ratio > MAX_FAILURE_RATIO:
        raise SystemExit(f"SOURCE HEALTH GATE FAILED: current failure ratio={failure_ratio:.1%} > {MAX_FAILURE_RATIO:.0%}")

    uncovered = []
    for category in REQUIRED_CATEGORIES:
        candidates = [s for s in results if s.get("category") == category]
        usable = [s for s in candidates if s.get("httpOk") is True and s.get("mode") in USABLE_MODES]
        if not usable:
            uncovered.append(category)
    if uncovered:
        raise SystemExit("SOURCE HEALTH GATE FAILED: no usable current source for " + ", ".join(sorted(uncovered)))

    fallback = sum(1 for s in results if s.get("mode") == "gdelt-domain-fallback")
    empty = sum(1 for s in results if s.get("httpOk") is True and s.get("emptyFeed") is True)
    print("PASS: current source health gate")
    print(f"feeds={feeds} results={total} rows={rows} healthy={healthy}/{total} ({healthy_ratio:.1%}) failed={failed} ({failure_ratio:.1%})")
    print(f"empty={empty} gdeltFallback={fallback} required-categories={','.join(sorted(REQUIRED_CATEGORIES))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
