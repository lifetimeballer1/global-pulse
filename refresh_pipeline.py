#!/usr/bin/env python3
"""Global Pulse canonical refresh pipeline.

Runs every data-producing stage in order and verifies the artifact created by
that stage before continuing. A failure stops the pipeline so stale data is
never published as if it were fresh.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def run(label: str, *cmd: str) -> None:
    print(f"\n=== {label} ===", flush=True)
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)
    print(f"PASS: {label}", flush=True)


def load(name: str) -> dict:
    p = DATA / name
    if not p.is_file() or p.stat().st_size == 0:
        raise RuntimeError(f"missing/empty artifact: {name}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def fresh(obj: dict, field: str = "updatedAt", max_age: int = 900) -> None:
    stamp = obj.get(field)
    if not stamp:
        raise RuntimeError(f"artifact has no {field}")
    dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - dt).total_seconds()
    if age < -120 or age > max_age:
        raise RuntimeError(f"artifact timestamp invalid/stale: age={age:.0f}s")


def verify_json(name: str, *, min_list: tuple[str, int] | None = None, fresh_required: bool = True) -> dict:
    d = load(name)
    if fresh_required:
        fresh(d)
    if min_list:
        key, minimum = min_list
        value = d.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise RuntimeError(f"{name}: {key} has fewer than {minimum} entries")
    return d


def main() -> int:
    # Source expansion and live news are the first hard gate.
    run("Expand feeds", sys.executable, "update_feed_expansion.py")
    sources = ROOT / "data" / "sources.json"
    if not sources.is_file() or sources.stat().st_size == 0:
        raise RuntimeError("sources.json was not generated")
    print("PASS: feed expansion", flush=True)

    last_error = None
    for attempt in range(1, 4):
        try:
            run(f"Poll live news {attempt}/3", sys.executable, "news_feed_db.py", "--once")
            last_error = None
            break
        except subprocess.CalledProcessError as exc:
            last_error = exc
            if attempt < 3:
                print("retrying live-news poll...", flush=True)
    if last_error:
        raise last_error

    live = verify_json("live_status.json")
    if live.get("feedsChecked", 0) < 20 or live.get("rowsFetched", 0) <= 0:
        raise RuntimeError("live news gate failed: insufficient feeds/rows")
    print(f"PASS: live news feeds={live.get('feedsChecked')} rows={live.get('rowsFetched')} new={live.get('newArticles')}", flush=True)

    run("Refresh base snapshot", sys.executable, "run_snapshot_resilient.py")
    snap = verify_json("snapshot.json")

    # Market data is explicitly validated; merely having snapshot.json is not enough.
    run("Update market data", sys.executable, "update_market_data.py")
    snap = verify_json("snapshot.json")
    market = snap.get("marketData") or {}
    fresh(market)
    indicators = market.get("indicators") or []
    if len(indicators) < 20:
        raise RuntimeError(f"market data gate failed: only {len(indicators)} indicators")
    if not market.get("provider") or not market.get("source"):
        raise RuntimeError("market data gate failed: provider/source missing")
    print(f"PASS: market data indicators={len(indicators)} live={market.get('liveCount')} closed={market.get('closedCount')} stale={market.get('staleCount')} errors={len(market.get('errors', []))}", flush=True)

    run("Merge live news", sys.executable, "merge_live_news.py")
    snap = verify_json("snapshot.json")
    if not snap.get("news") and not snap.get("stories"):
        raise RuntimeError("merged snapshot contains no news/stories")
    print("PASS: merged news", flush=True)

    stages = [
        ("Breaking intelligence", "breaking_news.py", "breaking_news.json", None),
        ("Live events", "build_live_events.py", "live_events.json", ("events", 0)),
        ("Source evidence", "build_source_evidence.py", "source_evidence.json", ("eventSourceEvidence", 0)),
        ("Event intelligence", "build_event_intelligence.py", "event_intelligence.json", ("events", 0)),
        ("Event consistency", "build_event_consistency.py", "event_consistency.json", ("events", 0)),
    ]
    for label, script, artifact, minimum in stages:
        run(label, sys.executable, script)
        verify_json(artifact, min_list=minimum)

    run("Political layer", sys.executable, "update_political_layer.py")
    verify_json("snapshot.json")
    run("Political intelligence", sys.executable, "update_political_intelligence.py")
    verify_json("snapshot.json")

    run("OSINT maps", sys.executable, "update_osint.py")
    snap = verify_json("snapshot.json")
    osint = snap.get("osintMaps") or {}
    if osint.get("version") not in (2, 3, 4):
        raise RuntimeError("OSINT verification failed")

    run("CFR conflict coverage", sys.executable, "update_cfr.py")
    snap = verify_json("snapshot.json")
    if not isinstance(snap.get("markers"), list) or not snap["markers"]:
        raise RuntimeError("conflict coverage verification failed")

    run("Strategic layers", sys.executable, "update8_global_layers.py")
    verify_json("snapshot.json")

    run("Intelligence web", sys.executable, "update_intelligence_web.py")
    run("Intelligence graph", sys.executable, "build_intelligence_graph.py")
    graph = verify_json("intelligence_graph.json")
    if len(graph.get("nodes", [])) < 10 or len(graph.get("edges", [])) < 3:
        raise RuntimeError("intelligence graph verification failed")
    for edge in graph["edges"]:
        if not edge.get("source") or not edge.get("target") or not edge.get("evidence"):
            raise RuntimeError("intelligence graph contains unevidenced edge")

    run("Install intelligence web", sys.executable, "install_intelligence_web.py")
    if not (ROOT / "intelligence-web.html").exists() and not (ROOT / "index.html").exists():
        raise RuntimeError("intelligence web renderer missing")

    run("Install live event layers", sys.executable, "install_live_events.py")
    run("Install event intelligence", sys.executable, "install_event_intelligence.py")
    if not (ROOT / "global_pulse_event_intelligence.js").is_file():
        raise RuntimeError("live event renderer missing")

    run("Build assessments", sys.executable, "build_intelligence_assessment.py")
    verify_json("intelligence_assessment.json")
    run("Install assessment UI", sys.executable, "install_intelligence_assessment.py")
    if not (ROOT / "global_pulse_assessment.js").is_file():
        raise RuntimeError("assessment UI missing")

    run("Dashboard integrations", sys.executable, "update7_live_branding.py")
    run("Dashboard reporting", sys.executable, "update9_live_reporting.py")
    run("Breaking alerts", sys.executable, "install_breaking_alerts.py")
    run("Health finalizer", sys.executable, "install_health_finalizer.py")
    if not (ROOT / "index.html").is_file() or (ROOT / "index.html").stat().st_size == 0:
        raise RuntimeError("index.html missing after dashboard integration")

    run("Source health", sys.executable, "finalize_intelligence_health.py")
    if not (DATA / "source_health.json").is_file():
        raise RuntimeError("source_health.json missing")
    run("Claims", sys.executable, "claim_intelligence.py")
    run("Install claims", sys.executable, "install_claim_intelligence.py")
    verify_json("claims.json")

    run("V2.7 install", sys.executable, "install_v27.py")
    run("Canonical map install", sys.executable, "install_map_v3.py")
    if not (ROOT / "global_pulse_v27.js").is_file():
        raise RuntimeError("V2.7 renderer missing")

    run("Normalize generated HTML", sys.executable, "clean_index.py")
    run("Repository validation", sys.executable, "validate_repository.py")

    # Final gate: this is the only point at which publishing is allowed.
    final = verify_json("snapshot.json")
    market = final.get("marketData") or {}
    fresh(market)
    if len(market.get("indicators") or []) < 20:
        raise RuntimeError("final market-data gate failed")
    if not isinstance(final.get("markers"), list) or not final["markers"]:
        raise RuntimeError("final conflict-data gate failed")
    if not (ROOT / "index.html").is_file() or (ROOT / "index.html").stat().st_size == 0:
        raise RuntimeError("final site gate failed")
    print("\n=== FINAL GLOBAL PULSE GATE: PASSED ===", flush=True)
    print("snapshot=", final.get("updatedAt"), flush=True)
    print("marketIndicators=", len(market.get("indicators") or []), flush=True)
    print("newsRows=", live.get("rowsFetched"), "newArticles=", live.get("newArticles"), flush=True)
    print("markers=", len(final.get("markers") or []), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nPIPELINE FAILED: {exc}", file=sys.stderr, flush=True)
        raise
