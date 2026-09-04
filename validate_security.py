#!/usr/bin/env python3
"""Fail-closed security/privacy checks for Global Pulse CI."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TRACKING = re.compile(r"google-analytics|googletagmanager|gtag\(|analytics\.js|sentry\.io|hotjar|mixpanel|segment\.com|clarity\.ms", re.I)
CLIENT_TELEMETRY = re.compile(r"navigator\.sendBeacon|new\s+Image\s*\(|fetch\s*\([^)]*(telemetry|analytics|track)", re.I)
SECRET_LIKE = re.compile(r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]", re.I)


def main() -> None:
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    assert not TRACKING.search(index), "Unexpected analytics/tracking code in index.html"
    assert not CLIENT_TELEMETRY.search(index), "Unexpected client telemetry in index.html"

    for path in ROOT.glob(".github/workflows/*.yml"):
        text = path.read_text(encoding="utf-8")
        assert not SECRET_LIKE.search(text), f"Secret-like literal found in {path}"
        # Reject dangerous privileged PR execution patterns unless explicitly
        # reviewed. Global Pulse does not need pull_request_target.
        assert "pull_request_target" not in text, f"Unsafe pull_request_target in {path}"

    for path in ROOT.glob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert not CLIENT_TELEMETRY.search(text), f"Client telemetry pattern in {path}"

    print("SECURITY VALIDATION PASSED")


if __name__ == "__main__":
    main()
