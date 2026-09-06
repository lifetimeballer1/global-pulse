#!/usr/bin/env python3
"""Build evidence-backed strategic signals from the canonical Intelligence Brain."""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATA = Path('data')
INPUT = DATA / 'intelligence_brain.json'
OUTPUT = DATA / 'strategic_signals.json'

MAJOR_ACTORS = {'United States', 'China'}

def main() -> int:
    brain = json.loads(INPUT.read_text(encoding='utf-8'))
    signals = []
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    for node in brain.get('nodes', []):
        actor = node.get('label')
        if actor not in MAJOR_ACTORS:
            continue
        actions = node.get('actions') or []
        categories = Counter()
        targets = Counter()
        evidence = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            category = str(action.get('category') or 'security').lower()
            categories[category] += 1
            target = str(action.get('target') or '').strip()
            if target:
                targets[target] += 1
            for item in action.get('evidence') or []:
                if isinstance(item, dict) and (item.get('url') or item.get('source')):
                    evidence.append(item)
        if not actions or not evidence:
            continue
        dominant_category, category_count = categories.most_common(1)[0]
        dominant_target, target_count = targets.most_common(1)[0] if targets else ('', 0)
        intensity = min(100, len(actions) * 10 + category_count * 5 + target_count * 5)
        signals.append({
            'actor': actor,
            'signal': f'{actor} shows concentrated {dominant_category} activity',
            'category': dominant_category,
            'dominantTarget': dominant_target,
            'actionCount': len(actions),
            'categoryCount': category_count,
            'targetCount': target_count,
            'intensity': intensity,
            'evidence': evidence[:20],
            'sourceBacked': True,
        })
    result = {
        'version': 1,
        'generatedAt': now,
        'sourceBackedOnly': True,
        'signals': signals,
        'majorActorCoverage': {actor: any(s['actor'] == actor for s in signals) for actor in MAJOR_ACTORS},
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: strategic signals={len(signals)}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
