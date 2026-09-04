#!/usr/bin/env python3
from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parent; p=ROOT/'index.html'; asset=ROOT/'global_pulse_events.js'; s=p.read_text(encoding='utf-8')
digest=hashlib.sha256(asset.read_bytes()).hexdigest()[:12];tag=f'global_pulse_events.js?v={digest}'
s=re.sub(r'<script[^>]+src=["\']global_pulse_events\.js(?:\?[^"\']*)?["\'][^>]*></script>','',s)
marker='</body>'
if marker in s:
    s=s.replace(marker,f'<script src="{tag}"></script>{marker}',1)
else:raise SystemExit('index.html has no </body>')
p.write_text(s,encoding='utf-8')
print('LIVE EVENT LAYER INSTALLED:',tag)
