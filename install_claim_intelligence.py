#!/usr/bin/env python3
from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<script src="claim_intelligence.js?v=1"></script>'
if marker not in s:
    s=s.replace('</body>', marker+'\n</body>') if '</body>' in s else s+'\n'+marker+'\n'
css='''\n<style id="gp-claims-css">.gp-claims-list{display:grid;gap:9px}.gp-claim details{margin-top:8px}.gp-claim summary{cursor:pointer;color:var(--blue);font-size:11px;font-weight:800}.gp-claim-evidence{display:grid;gap:6px;margin-top:7px}.gp-claim-evidence .item{padding:8px}.gp-claim a{font-size:10px}</style>\n'''
if 'id="gp-claims-css"' not in s:
    s=s.replace('</head>',css+'</head>') if '</head>' in s else css+s
p.write_text(s,encoding='utf-8')
print('claim intelligence UI installed')
