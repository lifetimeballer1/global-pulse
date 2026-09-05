#!/usr/bin/env python3
"""Canonical snapshot runner with SOUTHCOM/counter-cartel compatibility fixes."""
from __future__ import annotations
import json
import re
from pathlib import Path

SNAP = Path("data/snapshot.json")
import update_snapshot as base
from resilient_feed_catalog import FEEDS
base.FEEDS = FEEDS
import update_snapshot_fast as builder
from counter_cartel_runtime import install

install(base, builder)

old = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
preserved = {k: old[k] for k in ("marketData", "osintMaps") if isinstance(old.get(k), dict)}
builder.main()
new = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
for key, value in preserved.items():
    if key not in new or not isinstance(new.get(key), dict):
        new[key] = value
SNAP.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("COUNTER-CARTEL SNAPSHOT: preserved", ", ".join(sorted(preserved)) or "nothing")
