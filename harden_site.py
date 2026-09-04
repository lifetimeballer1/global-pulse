#!/usr/bin/env python3
"""Apply safe, idempotent browser-facing hardening to index.html.

GitHub Pages cannot set arbitrary HTTP response headers from repository files,
so this provides defense-in-depth in the document itself: PWA/iOS metadata,
icon declarations, referrer policy, and removal of duplicate third-party map
assets. It intentionally does not add analytics, fingerprinting, or visitor IDs.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"


def main() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if '<link rel="manifest" href="site.webmanifest?v=2">' not in text:
        marker = '<meta name="theme-color" content="#050a10">'
        additions = '''\n<meta name="application-name" content="Global Pulse">\n<meta name="apple-mobile-web-app-title" content="Global Pulse">\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n<meta name="referrer" content="strict-origin-when-cross-origin">\n<link rel="manifest" href="site.webmanifest?v=2">\n<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png?v=2">\n<link rel="icon" type="image/png" sizes="512x512" href="assets/icons/icon-512.png?v=2">\n<link rel="icon" type="image/png" sizes="192x192" href="assets/icons/icon-192.png?v=2">'''
        text = text.replace(marker, marker + additions, 1)

    # Remove the duplicated MarkerCluster CSS/JS block while preserving the
    # first dependency declarations. This reduces duplicate downloads and
    # prevents multiple plugin registrations on mobile Safari.
    text = re.sub(r'\n<!-- GP-MARKER-CLUSTER-START -->.*?<!-- GP-MARKER-CLUSTER-END -->\n', '\n', text, flags=re.S)

    INDEX.write_text(text, encoding="utf-8")
    print("SITE HARDENING APPLIED")


if __name__ == "__main__":
    main()
