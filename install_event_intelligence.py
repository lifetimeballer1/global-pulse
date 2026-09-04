#!/usr/bin/env python3
"""Install the event-intelligence panel once; safe to rerun."""
from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
tag='<script src="global_pulse_event_intelligence.js?v=1"></script>'
if tag not in s:
    marker='<script src="global_pulse_events.js?v=1"></script>'
    s=s.replace(marker, marker+'\n'+tag, 1) if marker in s else s.replace('</body>', tag+'\n</body>', 1)
p.write_text(s,encoding='utf-8')
print('Event intelligence UI installed')
