#!/usr/bin/env python3
"""Final browser-side map cleanup and cache busting for GitHub Pages."""
from pathlib import Path
import re

INDEX = Path('index.html')
VERSION = '20260906-mapfix3'


def main() -> None:
    text = INDEX.read_text(encoding='utf-8')
    patterns = [
        r'\n<style id="gp-map-rescue-css">.*?</style>\n?',
        r'\n<script id="gp-map-rescue-js">.*?</script>\n?',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '\n', text, flags=re.S | re.I)
    text = re.sub(r'(?:js/app\.js)(?:\?[^"\']*)?', f'js/app.js?v={VERSION}', text, count=1)
    # The module imports the canonical map renderer; a versioned app URL also
    # forces iOS Safari/GitHub Pages to pick up the new renderer.
    INDEX.write_text(text, encoding='utf-8')
    print(f'Finalized map UI and cache-busted js/app.js as {VERSION}')


if __name__ == '__main__':
    main()
