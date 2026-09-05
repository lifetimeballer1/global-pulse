#!/usr/bin/env python3
"""Install the final browser QA layer into the generated dashboard."""
from pathlib import Path
import re

INDEX=Path(__file__).resolve().parent/'index.html'
TAG='<script src="global_pulse_qa.js?v=1" defer></script>'

def main():
    s=INDEX.read_text(encoding='utf-8')
    s=re.sub(r'\s*<script[^>]*src=["\']global_pulse_qa\.js(?:\?[^"\']*)?["\'][^>]*>\s*</script>', '', s, flags=re.I)
    if '</body>' not in s: raise RuntimeError('index.html has no closing body tag')
    s=s.replace('</body>',TAG+'\n</body>',1)
    INDEX.write_text(s,encoding='utf-8')
    print('QA HARDENING INSTALLED')

if __name__=='__main__': main()
