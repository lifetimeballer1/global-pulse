#!/usr/bin/env python3
"""Merge the persistent live-news database export into the public snapshot."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
LIVE = DATA / "live_articles.json"


def parse_time(value):
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def main():
    if not SNAP.exists() or not LIVE.exists():
        print("live merge skipped: snapshot or live export missing")
        return
    snapshot = json.loads(SNAP.read_text(encoding="utf-8"))
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    existing = {}
    for story in snapshot.get("stories", []):
        url = story.get("source") or story.get("url")
        if url:
            existing[url] = story

    added = 0
    for item in live.get("articles", []):
        url = item.get("url")
        if not url or url in existing:
            continue
        source = item.get("source", "Live source")
        title = item.get("title") or (f"Tweet by @{item.get('username')}" if item.get("username") else f"Update from {source}")
        summary = item.get("summary_snippet", "")
        breaking_terms = ("strike", "attack", "killed", "drone", "missile", "blockade", "escalat", "invasion", "ceasefire", "bomb", "shell", "offensive", "coup", "clash", "shooting", "airstrike")
        blob = f"{title} {summary}".lower()
        breaking = any(term in blob for term in breaking_terms)
        story = {
            "id": hashlib.sha1(url.encode("utf-8")).hexdigest()[:12],
            "sourceLabel": source,
            "sourceType": item.get("sourceType", "live-rss"),
            "title": title[:240],
            "summary": summary[:420],
            "source": url,
            "time": item.get("published_date"),
            "tag": "Breaking" if breaking else "World",
            "confidence": "DEVELOPING",
            "breaking": breaking,
            "liveDatabase": True,
            "credit": item.get("credit", {}),
        }
        existing[url] = story
        added += 1

    stories = sorted(existing.values(), key=lambda s: parse_time(s.get("time")), reverse=True)[:300]
    snapshot["stories"] = stories

    # Re-score conflict activity against the expanded live story set. Use the
    # same counter-cartel-aware matcher as the canonical snapshot builder so
    # source-specific SOUTHCOM/Southern Spear feeds cannot be erased back to 0
    # simply because the live-news merge runs in a separate process.
    try:
        import update_snapshot as base
        import update_snapshot_fast as builder
        from counter_cartel_runtime import install
        install(base, builder)
        previous = {"conflicts": snapshot.get("conflicts", [])}
        snapshot["conflicts"] = base.make_conflicts(stories, previous)
    except Exception as exc:
        print(f"conflict re-score skipped: {type(exc).__name__}: {exc}")

    snapshot["updatedAt"] = datetime.now(timezone.utc).isoformat()
    snapshot["liveDatabase"] = {
        "enabled": True,
        "articleCount": int(live.get("count", 0)),
        "lastExport": live.get("updatedAt"),
        "retentionDays": live.get("retentionDays", 7),
        "newMergedThisRun": added,
    }
    snapshot["sourceStatus"] = f"{len(stories)} stories · {added} live-db merged · persistent 7-day SQLite collector active"
    SNAP.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"live merge: {added} new rows, {len(stories)} total stories")


if __name__ == "__main__":
    main()
