"""Validate canonical intelligence JSON artifacts.

Usage: python validate_intelligence_schema.py [path]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from intelligence_schema import validate_document


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/canonical_intelligence.json")
    if not path.exists():
        print(f"ERROR: intelligence artifact not found: {path}")
        return 2
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}")
        return 2

    errors = validate_document(document)
    if errors:
        print(f"FAIL: {len(errors)} schema validation error(s)")
        for error in errors[:100]:
            print(f" - {error}")
        return 1

    print(
        "PASS: canonical intelligence schema valid "
        f"(entities={len(document.get('entities', []))}, "
        f"events={len(document.get('events', []))}, "
        f"relationships={len(document.get('relationships', []))}, "
        f"evidence={len(document.get('evidence', []))}, "
        f"signals={len(document.get('signals', []))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
