#!/usr/bin/env python3
from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')
tag='<script src="global_pulse_source_health.js" defer></script>'
s=re.sub(r'<script src="global_pulse_source_health\.js" defer></script>','',s)
if '</body>' not in s: raise SystemExit('index.html has no </body>')
s=s.replace('</body>',tag+'</body>',1)
p.write_text(s,encoding='utf-8')
print('Installed source-health UI repair.')
