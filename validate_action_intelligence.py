#!/usr/bin/env python3
"""Validate source-backed U.S./China action intelligence in the canonical Brain."""
from __future__ import annotations
import json,sys
from pathlib import Path
BRAIN=Path('data/intelligence_brain.json')
ACTORS=('United States','China')

def main():
    if not BRAIN.exists(): print(f'ERROR: missing {BRAIN}'); return 1
    try: data=json.loads(BRAIN.read_text(encoding='utf-8'))
    except Exception as exc: print(f'ERROR: invalid JSON: {exc}'); return 1
    layer=data.get('actionLayer') or {}
    if layer.get('sourceBackedOnly') is not True:
        print('ERROR: action layer is not source-backed-only'); return 1
    nodes={str(n.get('label')):n for n in data.get('nodes',[]) if isinstance(n,dict)}
    failures=[]
    for actor in ACTORS:
        node=nodes.get(actor)
        if not node: failures.append(f'{actor}: major Brain node missing'); continue
        actions=node.get('actions')
        if not isinstance(actions,dict) or not actions: failures.append(f'{actor}: no action categories'); continue
        total=0
        for category,items in actions.items():
            if not isinstance(items,list): failures.append(f'{actor}: {category} is not a list'); continue
            for i,item in enumerate(items):
                if not isinstance(item,dict): failures.append(f'{actor}/{category}/{i}: invalid evidence object'); continue
                if not str(item.get('title','')).strip(): failures.append(f'{actor}/{category}/{i}: missing title')
                if not (str(item.get('url','')).strip() or str(item.get('source','')).strip()): failures.append(f'{actor}/{category}/{i}: missing source/url')
                total+=1
        declared=int(node.get('actionEvidenceCount') or 0)
        if declared!=total: failures.append(f'{actor}: actionEvidenceCount mismatch ({declared} != {total})')
        if total==0: failures.append(f'{actor}: no evidence-backed actions')
        print(f'{actor}: {total} evidence items across {len(actions)} categories')
    if failures:
        print('FAIL')
        for x in failures: print(f'  - {x}')
        return 1
    print('PASS: U.S./China action layer is present and evidence-backed')
    return 0
if __name__=='__main__': raise SystemExit(main())
