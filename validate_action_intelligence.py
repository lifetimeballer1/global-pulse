#!/usr/bin/env python3
"""Validate actor/action intelligence produced by the Brain enrichment step."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BRAIN = Path("data/intelligence_brain.json")
ACTORS = ("United States", "China")


def main() -> int:
    if not BRAIN.exists():
        print(f"ERROR: missing {BRAIN}")
        return 1
    try:
        data = json.loads(BRAIN.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: invalid JSON: {exc}")
        return 1

    records = data.get("action_intelligence", [])
    if not isinstance(records, list):
        print("ERROR: action_intelligence must be a list")
        return 1

    failures = []
    actor_counts = {actor: 0 for actor in ACTORS}
    evidence_counts = {actor: 0 for actor in ACTORS}

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            failures.append(f"record {i}: not an object")
            continue
        actor = record.get("actor")
        if actor in actor_counts:
            actor_counts[actor] += 1
            evidence = record.get("evidence", [])
            if isinstance(evidence, list) and evidence:
                evidence_counts[actor] += len(evidence)
        if actor in ACTORS:
            for field in ("action", "category", "target"):
                if not str(record.get(field, "")).strip():
                    failures.append(f"record {i}: missing {field}")
            evidence = record.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                failures.append(f"record {i}: missing evidence")

    for actor in ACTORS:
        if actor_counts[actor] == 0:
            failures.append(f"{actor}: no action records")
        if evidence_counts[actor] == 0:
            failures.append(f"{actor}: no evidence-backed actions")

    print("Action intelligence validation")
    print(f"  records: {len(records)}")
    for actor in ACTORS:
        print(f"  {actor}: {actor_counts[actor]} records / {evidence_counts[actor]} evidence items")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
