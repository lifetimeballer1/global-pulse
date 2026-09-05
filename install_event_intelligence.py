#!/usr/bin/env python3
"""Install event-intelligence, historical timeline and compact-list UI once; safe to rerun."""
from pathlib import Path
import subprocess,sys

# Build the history artifact here because this installer is already part of the
# canonical refresh pipeline. Keeping it here avoids a second workflow path.
subprocess.run([sys.executable,'build_event_history.py'],check=True)

p=Path('index.html'); s=p.read_text(encoding='utf-8')
tags=[
 '<script src="global_pulse_event_intelligence.js?v=1"></script>',
 '<script src="global_pulse_event_consistency.js?v=1"></script>',
 '<link rel="stylesheet" href="global_pulse_list_density.css">',
 '<link rel="stylesheet" href="global_pulse_phase3.css?v=1">',
 '<script src="global_pulse_list_density.js"></script>',
 '<script src="global_pulse_event_history.js?v=1"></script>',
 '<script src="global_pulse_ux_hardening.js?v=1"></script>'
]
for tag in tags:
    if tag in s: continue
    marker='<script src="global_pulse_events.js?v=1"></script>'
    if marker in s:
        s=s.replace(marker, marker+'\n'+tag, 1)
    else:
        s=s.replace('</body>', tag+'\n</body>', 1)
p.write_text(s,encoding='utf-8')
print('Event intelligence, consistency review, historical timeline, compact list UX and Phase 3 mobile interaction hardening installed')
