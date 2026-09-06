#!/usr/bin/env python3
"""Keep the Global Pulse map HTML canonical.

The interactive map is owned by js/modules/map.js and css/map.css. This
installer only removes obsolete experimental/rescue map fragments so the
canonical renderer is not overwritten during data refreshes.
"""
from pathlib import Path
import re

INDEX = Path(__file__).resolve().parent / "index.html"

REMOVE_PATTERNS = [
    r'\n<style id="gp-own-map-css">.*?</style>\n?',
    r'\n<script id="gp-own-map-js">.*?</script>\n?',
    r'\n<script id="gp-map-pro-js">.*?</script>\n?',
    r'\n<style id="gp-map-pro-css">.*?</style>\n?',
    r'\n<style id="gp-evidence-css">.*?</style>\n?',
    r'\n<script id="gp-evidence-js">.*?</script>\n?',
    r'\n<style id="gp-analysis-css">.*?</style>\n?',
    r'\n<script id="gp-analysis-js">.*?</script>\n?',
    r'\n<style id="gp-graph-css">.*?</style>\n?',
    r'\n<script id="gp-graph-js">.*?</script>\n?',
    r'\n<section[^>]*id="evidenceCenter"[^>]*>.*?</section>\n?',
    r'\n<section[^>]*id="analysisCenter"[^>]*>.*?</section>\n?',
    r'\n<section[^>]*id="globalGraph"[^>]*>.*?</section>\n?',
    r'\n<div[^>]*id="gpMapTools"[^>]*>.*?</div>\n?',
    r'\n<div[^>]*id="gpMapLegend"[^>]*>.*?</div>\n?',
    r'\n<section[^>]*id="gpBrief"[^>]*>.*?</section>\n?',
    r'\n<style id="gp-map-rescue-css">.*?</style>\n?',
    r'\n<script id="gp-map-rescue-js">.*?</script>\n?',
]


def install() -> None:
    s = INDEX.read_text(encoding="utf-8")
    for pattern in REMOVE_PATTERNS:
        s = re.sub(pattern, "\n", s, flags=re.S | re.I)
    s = re.sub(r"\n{4,}", "\n\n", s)
    INDEX.write_text(s, encoding="utf-8")
    print("Removed obsolete map rescue/experimental fragments; canonical map stays in js/modules/map.js")


if __name__ == "__main__":
    install()
