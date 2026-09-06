#!/usr/bin/env python3
"""Phase 8 operational health gate for the canonical Global Pulse refresh.

Checks that the published intelligence bundle is internally coherent, fresh,
and traceable without replacing or inventing source data.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ARTIFACTS = ("snapshot.json", "live_articles.json", "map_points.json", "intelligence_graph.json", "intelligence_brain.json")

def load(name):
    p = DATA / name
    if not p.is_file() or p.stat().st_size == 0:
        raise SystemExit(f"OPERATIONAL HEALTH FAILED: missing {name}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"OPERATIONAL HEALTH FAILED: invalid JSON {name}: {exc}") from exc

def stamp(obj, name):
    value = obj.get("updatedAt") or obj.get("generatedAt") or obj.get("lastSuccessfulRefresh")
    if not value:
        raise SystemExit(f"OPERATIONAL HEALTH FAILED: {name} has no freshness timestamp")
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"OPERATIONAL HEALTH FAILED: {name} has invalid timestamp") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
    if age < -120 or age > 1800:
        raise SystemExit(f"OPERATIONAL HEALTH FAILED: {name} timestamp age={age:.0f}s")
    return dt

def main():
    objs = {name: load(name) for name in ARTIFACTS}
    for name, obj in objs.items():
        stamp(obj, name)

    snapshot = objs["snapshot.json"]
    live = objs["live_articles.json"]
    points = objs["map_points.json"]
    graph = objs["intelligence_graph.json"]
    brain = objs["intelligence_brain.json"]

    stories = snapshot.get("stories") or []
    articles = live.get("articles") or []
    markers = points.get("markers") or []
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    brain_nodes = brain.get("nodes") or []
    brain_edges = brain.get("edges") or []

    if not stories or not articles:
        raise SystemExit("OPERATIONAL HEALTH FAILED: published news bundle is empty")
    if len(markers) < 10:
        raise SystemExit("OPERATIONAL HEALTH FAILED: published map bundle is too small")
    if len(nodes) < 10 or len(edges) < 3:
        raise SystemExit("OPERATIONAL HEALTH FAILED: intelligence graph is too small")
    if len(brain_nodes) < 10 or len(brain_edges) < 5:
        raise SystemExit("OPERATIONAL HEALTH FAILED: Intelligence Brain is too small")
    if brain.get("complete") is not True or brain.get("sourceBackedOnly") is not True or brain.get("consolidated") is not True:
        raise SystemExit("OPERATIONAL HEALTH FAILED: Brain source/consolidation contract missing")

    node_ids = {str(n.get("id")) for n in brain_nodes}
    for edge in brain_edges:
        if str(edge.get("source")) not in node_ids or str(edge.get("target")) not in node_ids:
            raise SystemExit("OPERATIONAL HEALTH FAILED: Brain edge endpoint missing")
        if not edge.get("evidence"):
            raise SystemExit("OPERATIONAL HEALTH FAILED: Brain relationship lacks evidence")

    story_keys = set()
    for item in stories:
        key = str(item.get("url") or item.get("title") or "").strip()
        if not key:
            raise SystemExit("OPERATIONAL HEALTH FAILED: story lacks provenance identity")
        story_keys.add(key)
    if len(story_keys) < max(1, len(stories) * 0.9):
        raise SystemExit("OPERATIONAL HEALTH FAILED: excessive duplicate story identities")

    bad_coords = 0
    for marker in markers:
        try:
            lat = float(marker.get("lat", marker.get("latitude")))
            lng = float(marker.get("lng", marker.get("lon", marker.get("longitude"))))
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                bad_coords += 1
        except (TypeError, ValueError):
            bad_coords += 1
    if bad_coords:
        raise SystemExit(f"OPERATIONAL HEALTH FAILED: {bad_coords} invalid map coordinates")

    required_snapshot_fields = ("updatedAt", "lastSuccessfulRefresh", "freshness", "sourceFailover")
    missing = [x for x in required_snapshot_fields if not snapshot.get(x)]
    if missing:
        raise SystemExit("OPERATIONAL HEALTH FAILED: snapshot missing " + ", ".join(missing))

    print("PASS: Phase 8 operational health gate")
    print(f"stories={len(stories)} liveArticles={len(articles)} mapPoints={len(markers)} graph={len(nodes)}/{len(edges)} brain={len(brain_nodes)}/{len(brain_edges)}")

if __name__ == "__main__":
    main()
