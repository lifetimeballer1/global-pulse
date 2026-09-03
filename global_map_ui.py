#!/usr/bin/env python3
"""Remove the experimental self-owned map layer.

Global Pulse intentionally returns to its original dashboard map implementation.
The original map already supports the shared ``DATA.markers`` dataset, so all
new OSINT, cartel, strategic, and hazard points continue to appear there without
creating a second Leaflet instance.
"""
from pathlib import Path
import re

INDEX = Path(__file__).resolve().parent / "index.html"


def install() -> None:
    s = INDEX.read_text(encoding="utf-8")

    # Remove only the experimental map layer introduced by this installer.
    s = re.sub(r'\n<style id="gp-own-map-css">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="gp-own-map-js">.*?</script>\n?', '\n', s, flags=re.S)

    # Defensive cleanup for controls/status elements that could have been
    # persisted into the HTML by an earlier version.
    s = re.sub(r'\n<div class="gp-own-map-tools"[^>]*>.*?</div>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<div class="gp-own-map-meta"[^>]*>.*?</div>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<div class="gp-own-map-key"[^>]*>.*?</div>\n?', '\n', s, flags=re.S)

    INDEX.write_text(s, encoding="utf-8")
    print("Removed experimental map UI; original Global Pulse map restored")


if __name__ == "__main__":
    install()
