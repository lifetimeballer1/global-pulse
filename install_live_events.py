#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent; p=ROOT/'index.html'
s=p.read_text(encoding='utf-8')
tag='global_pulse_events.js?v=20260904a'
if tag not in s:
    s=re.sub(r'<script[^>]+src=["\']global_pulse_breaking\.js\?v=[^"\']+["\'][^>]*></script>',lambda m:m.group(0)+'<script src="'+tag+'"></script>',s,count=1)
    if tag not in s:
        s=s.replace('</body>','<script src="'+tag+'"></script></body>',1)
p.write_text(s,encoding='utf-8')
print('LIVE EVENT LAYER INSTALLED')
