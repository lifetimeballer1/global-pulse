#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent; INDEX=ROOT/'index.html'; s=INDEX.read_text(encoding='utf-8')
marker='<!-- GP-BREAKING-INTEL -->'; s=s.replace(marker,'')
s=s.replace('</body>',marker+'\n<script src="global_pulse_breaking.js?v=20260904a" defer></script>\n</body>',1)
INDEX.write_text(s,encoding='utf-8'); print('Installed rapid breaking intelligence layer')
