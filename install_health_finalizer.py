#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Force browsers to fetch the repaired frontend assets instead of serving an older
# cached copy. The version is derived from the actual file contents, so it changes
# automatically whenever either asset changes.
for asset in ('global_pulse_v22.js','global_pulse_source_health.js'):
    ap=Path(asset)
    digest=hashlib.sha256(ap.read_bytes()).hexdigest()[:12]
    pattern=rf'<script src="{re.escape(asset)}(?:\?[^" ]*)?" defer></script>'
    replacement=f'<script src="{asset}?v={digest}" defer></script>'
    s=re.sub(pattern,replacement,s)

# Keep the source-health repair installed exactly once at the end of the body.
s=re.sub(r'<script src="global_pulse_source_health\.js(?:\?[^" ]*)?" defer></script>','',s)
if '</body>' not in s: raise SystemExit('index.html has no </body>')
digest=hashlib.sha256(Path('global_pulse_source_health.js').read_bytes()).hexdigest()[:12]
s=s.replace('</body>',f'<script src="global_pulse_source_health.js?v={digest}" defer></script></body>',1)
p.write_text(s,encoding='utf-8')
print('Installed source-health UI repair with cache-busted asset versions.')
