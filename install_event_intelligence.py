#!/usr/bin/env python3
"""Install event-intelligence and compact-list UI once; safe to rerun."""
from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
tags=[
 '<script src="global_pulse_event_intelligence.js?v=1"></script>',
 '<script src="global_pulse_event_consistency.js?v=1"></script>',
 '<link rel="stylesheet" href="global_pulse_list_density.css">',
 '<script src="global_pulse_list_density.js"></script>'
]
for tag in tags:
    if tag in s: continue
    marker='<script src="global_pulse_events.js?v=1"></script>'
    if marker in s:
        s=s.replace(marker, marker+'\n'+tag, 1)
    else:
        s=s.replace('</body>', tag+'\n</body>', 1)
p.write_text(s,encoding='utf-8')
print('Event intelligence, consistency review and compact list UX installed')
