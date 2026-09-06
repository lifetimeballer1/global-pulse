#!/usr/bin/env python3
"""Publish a small, browser-friendly geographic marker artifact.

The full snapshot is intentionally large. The map should never depend on
parsing that entire document just to draw points, so this creates a compact
markers-only payload after the canonical refresh has finished.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
OUT = DATA / "map_points.json"


def coord(item):
    if not isinstance(item, dict):
        return None
    try:
        lat = float(item.get("lat", item.get("latitude")))
        lng = float(item.get("lng", item.get("lon", item.get("longitude"))))
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return round(lat, 5), round(lng, 5)


def main() -> int:
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    markers = snap.get("markers") or []
    out = []
    seen = set()
    for marker in markers:
        c = coord(marker)
        if c is None:
            continue
        key = (
            str(marker.get("id") or marker.get("datasetEventId") or marker.get("title") or "").strip().lower(),
            c[0], c[1],
        )
        if key in seen:
            continue
        seen.add(key)
        item = dict(marker)
        item["lat"], item["lng"] = c
        out.append(item)
    payload = {
        "version": 1,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(out),
        "markers": out,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    if not out:
        raise RuntimeError("map_points.json contains zero valid geographic markers")
    print(f"Map points: {len(out)} valid geographic markers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
