#!/usr/bin/env python3
"""Run the snapshot builder with the resilient feed catalog without losing live state."""
from __future__ import annotations
import json
from pathlib import Path

SNAP = Path("data/snapshot.json")

# Import the original module, replace only its feed catalog, then run it in the
# same process. This avoids maintaining a second copy of the large scoring model.
import update_snapshot as base
from resilient_feed_catalog import FEEDS
base.FEEDS = FEEDS
import update_snapshot_fast as builder

old = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
preserved = {}
for key in ("marketData", "osintMaps"):
    if isinstance(old.get(key), dict):
        preserved[key] = old[key]

builder.main()

new = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
for key, value in preserved.items():
    # The market collector and map collectors have their own writers. A news
    # refresh must never erase their latest successful state.
    if key not in new or not isinstance(new.get(key), dict):
        new[key] = value
SNAP.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("RESILIENT SNAPSHOT: preserved", ", ".join(sorted(preserved)) or "nothing")
