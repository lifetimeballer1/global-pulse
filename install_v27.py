#!/usr/bin/env python3
"""Install the V2.7 frontend intelligence layers deterministically."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
ASSETS = [ROOT / "global_pulse_v27.js", ROOT / "global_pulse_v27_quality.js"]


def install() -> None:
    html = INDEX.read_text(encoding="utf-8")
    for asset in ASSETS:
        name = asset.name
        html = re.sub(rf'\n?\s*<script[^>]+src="{re.escape(name)}(?:\?[^\"]*)?"[^>]*></script>\s*', '\n', html, flags=re.I)
    tags = []
    for asset in ASSETS:
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        tags.append(f'<script src="{asset.name}?v={digest}" defer></script>')
    html = html.replace('</body>', '\n'.join(tags) + '\n</body>', 1)
    INDEX.write_text(html, encoding="utf-8")
    print('Installed V2.7 frontend layers:')
    for asset in ASSETS:
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        print(f'  {asset.name}?v={digest}')


if __name__ == '__main__':
    install()
