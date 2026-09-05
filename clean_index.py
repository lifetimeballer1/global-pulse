#!/usr/bin/env python3
"""Idempotently clean generated index.html and install canonical UI assets."""
from __future__ import annotations
import re
from pathlib import Path
INDEX=Path(__file__).resolve().parent/'index.html'
OLD_JS=('global_pulse_v22.js','global_pulse_v23.js','global_pulse_v24.js','global_pulse_v25.js','global_pulse_v26.js','global_pulse_v27.js','global_pulse_v27_quality.js','global_pulse_event_history.js','global_pulse_event_consistency.js','global_pulse_event_resolution.js')

def main():
 s=INDEX.read_text(encoding='utf-8')
 for asset in OLD_JS:
  s=re.sub(rf'\s*<script\b[^>]*src=["\']{re.escape(asset)}(?:\?[^"\']*)?["\'][^>]*>\s*</script\s*>','',s,flags=re.I)
 s=re.sub(r'\s*<link\b[^>]*href=["\']global_pulse_(?:intelligence|list_density|phase3)\.css(?:\?[^"\']*)?["\'][^>]*>','',s,flags=re.I)
 if 'global_pulse_core.js' not in s:
  s=s.replace('</body>','<script src="global_pulse_core.js?v=1" defer></script>\n</body>',1)
 if 'global_pulse_tokens.css' not in s:
  s=s.replace('</head>','<link rel="stylesheet" href="global_pulse_tokens.css?v=1">\n</head>',1)
 script_re=re.compile(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>\s*</script\s*>',re.I);seen=set()
 def dedupe(m):
  src=m.group(1);key=src.split('?',1)[0]
  if key in seen:return ''
  seen.add(key);return m.group(0)
 s=script_re.sub(dedupe,s);s=re.sub(r'\n{4,}','\n\n',s);INDEX.write_text(s,encoding='utf-8');print('INDEX CLEANUP PASSED')
if __name__=='__main__':main()
