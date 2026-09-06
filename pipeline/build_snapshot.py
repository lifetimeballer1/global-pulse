#!/usr/bin/env python3
"""
Global Pulse — single clean snapshot orchestrator.

This replaces the previous explosion of build_*/update_*/install_* scripts.
Run from repo root:

    python pipeline/build_snapshot.py

It should:
1. Call modular source adapters
2. Normalize + attach confidence
3. Write atomic JSON artifacts into /data
4. Write refresh_manifest.json with timestamps + hashes
5. Exit non-zero on critical failure (so GitHub Actions can fail safely)
"""

from __future__ import annotations
import json
import hashlib
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write_json(path: Path, obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, indent=2)
    path.write_text(raw, encoding="utf-8")
    return hashlib.sha256(raw.encode()).hexdigest()

def main() -> int:
    print("Global Pulse clean pipeline — starting")

    # In a full implementation this would call real adapters.
    # For now we only ensure the directory and a minimal manifest exist
    # so the UI can run against existing data artifacts.

    manifest = {
        "generatedAt": now_iso(),
        "pipeline": "clean-v1",
        "artifacts": {}
    }

    for name in ["snapshot.json", "live_articles.json", "intelligence_graph.json",
                 "sources.json", "source_health.json"]:
        p = DATA / name
        if p.exists():
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            manifest["artifacts"][name] = {
                "sha256": h,
                "bytes": p.stat().st_size,
                "present": True
            }
        else:
            manifest["artifacts"][name] = {"present": False}

    write_json(DATA / "refresh_manifest.json", manifest)
    print("Wrote data/refresh_manifest.json")
    print("Pipeline complete (stub). Replace adapters for full production refresh.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
