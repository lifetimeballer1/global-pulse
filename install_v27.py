#!/usr/bin/env python3
"""Install the V2.7 frontend repair/intelligence layer deterministically."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
ASSET = ROOT / "global_pulse_v27.js"


def install() -> None:
    html = INDEX.read_text(encoding="utf-8")
    # Remove prior V2.7 injections so repeated scheduled runs never stack scripts.
    html = re.sub(r'\n?\s*<script[^>]+src="global_pulse_v27\.js(?:\?[^\"]*)?"[^>]*></script>\s*', '\n', html, flags=re.I)
    digest = hashlib.sha256(ASSET.read_bytes()).hexdigest()[:12]
    tag = f'<script src="global_pulse_v27.js?v={digest}" defer></script>'
    html = html.replace('</body>', tag + '\n</body>', 1)
    INDEX.write_text(html, encoding="utf-8")
    print(f"Installed V2.7 frontend layer: global_pulse_v27.js?v={digest}")


if __name__ == '__main__':
    install()
