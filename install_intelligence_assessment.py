#!/usr/bin/env python3
from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8'); tag='<script src="global_pulse_assessment.js?v=20260904a"></script>'
if 'global_pulse_assessment.js' not in s:
    marker='</body>'
    if marker not in s: raise SystemExit('index.html has no </body> marker')
    s=s.replace(marker,tag+'\n'+marker,1)
p.write_text(s,encoding='utf-8')
print('Installed dynamic risk/impact UI')
