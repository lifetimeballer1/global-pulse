#!/usr/bin/env python3
"""Idempotently clean generated index.html without changing application behavior."""
from __future__ import annotations

import re
from pathlib import Path

INDEX = Path(__file__).resolve().parent / "index.html"


def main() -> None:
    s = INDEX.read_text(encoding="utf-8")

    # The map enhancement generator historically left the original and
    # enhanced block with the same id. Keep the enhanced block only.
    style_re = re.compile(r'<style\s+id=["\']gp-map-v3-css["\'][^>]*>.*?</style\s*>', re.I | re.S)
    styles = style_re.findall(s)
    if len(styles) > 1:
        # The enhanced block is the last one and contains the media/actions CSS.
        first = styles[0]
        s = s.replace(first, "", 1)

    # Remove duplicate external script tags while preserving the first load.
    # Query-string cache versions are ignored when deciding whether a script is
    # duplicated; the first tag remains the canonical inclusion.
    script_re = re.compile(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>\s*</script\s*>', re.I)
    seen: set[str] = set()

    def script_sub(m: re.Match[str]) -> str:
        full, src = m.group(0), m.group(1)
        key = src.split("?", 1)[0]
        if key.startswith(("http://", "https://", "//")) or key in seen:
            if key in seen:
                return ""
            seen.add(key)
            return full
        seen.add(key)
        return full

    s = script_re.sub(script_sub, s)
    INDEX.write_text(s, encoding="utf-8")
    print("INDEX CLEANUP PASSED")


if __name__ == "__main__":
    main()
