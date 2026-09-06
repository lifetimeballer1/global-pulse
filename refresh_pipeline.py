#!/usr/bin/env python3
"""Global Pulse canonical refresh pipeline."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data'
REQUIRED_ARTIFACTS=('snapshot.json','history.json','sources.json','live_articles.json','canonical_intelligence.json','intelligence_graph.json','intelligence_brain.json','map_points.json','strategic_signals.json')
def run(label,*cmd):
 print(f'\n=== {label} ===',flush=True);print('$',' '.join(cmd),flush=True);subprocess.run(cmd,cwd=ROOT,check=True);print(f'PASS: {label}',flush=True)
def load(name):
 p=DATA/name
 if not p.is_file() or p.stat().st_size==0:raise RuntimeError(f'missing/empty artifact: {name}')
 return json.loads(p.read_text(encoding='utf-8'))
def fresh(obj,field='updatedAt',max_age=900):
 stamp=obj.get(field)
 if not stamp:raise RuntimeError(f'artifact has no {field}')
 dt=datetime.fromisoformat(str(stamp).replace('Z','+00:00'));age=(datetime.now(timezone.utc)-dt).total_seconds()
 if age < -120 or age > max_age:raise RuntimeError(f'artifact timestamp invalid/stale: age={age:.0f}s')
def verify_json(name,*,min_list=None,fresh_required=True,max_age=900):
 d=load(name)
 if fresh_required and isinstance(d,dict):fresh(d,max_age=max_age)
 if min_list:
  key,minimum=min_list
  if not isinstance(d.get(key),list) or len(d[key])<minimum:raise RuntimeError(f'{name}: {key} has fewer than {minimum} entries')
 return d
def verify_strategic_signals(signals):
 if signals.get('sourceBackedOnly') is not True:raise RuntimeError('strategic signals are not source-backed')
 coverage=signals.get('majorActorCoverage') or {}
 for actor in ('United States','China'):
  if coverage.get(actor) is not True:raise RuntimeError(f'strategic signal missing for {actor}')
 for signal in signals.get('signals') or []:
  if not signal.get('actor') or not signal.get('signal') or not signal.get('evidence'):raise RuntimeError('strategic signal missing evidence')
def verify_brain(brain):
 if brain.get('complete') is not True or brain.get('sourceBackedOnly') is not True or brain.get('consolidated') is not True:raise RuntimeError('intelligence brain completeness/source/consolidation gate failed')
 nodes=brain.get('nodes') or [];edges=brain.get('edges') or []
 if len(nodes)<10 or len(nodes)>35 or brain.get('maxNodes')!=35:raise RuntimeError(f'intelligence brain size gate failed: {len(nodes)} nodes')
 if len(edges)<5:raise RuntimeError('intelligence brain verification failed: too few relationships')
 stats=brain.get('stats') if isinstance(brain.get('stats'),dict) else {}
 if stats.get('marketIndicators',0)<20:raise RuntimeError('intelligence brain market layer missing')
 ids={str(n.get('id')) for n in nodes};allowed={'country','cartel','economic','conflict','chokepoint'}
 for actor in ('United States','China'):
  node=next((n for n in nodes if n.get('label')==actor),None)
  if not node:raise RuntimeError(f'major strategic actor missing: {actor}')
  if not node.get('evidence'):raise RuntimeError(f'major strategic actor has no evidence: {actor}')
 for n in nodes:
  if not any(isinstance(x,dict) and (x.get('url') or x.get('source')) for x in (n.get('evidence') or [])):raise RuntimeError(f'unsourced brain node: {n.get("label")}')
  if n.get('kind') not in allowed or not n.get('canonical'):raise RuntimeError(f'noncanonical brain node: {n.get("label")}')
 for e in edges:
  if str(e.get('source')) not in ids or str(e.get('target')) not in ids or not e.get('evidence'):raise RuntimeError('invalid or unevidenced brain relationship')
def verify_canonical_intelligence(document):
 from intelligence_schema import validate_document
 errors=validate_document(document)
 if errors:
  raise RuntimeError(f'canonical intelligence schema validation failed: {errors[:5]}')
 if not document.get('generated_at'):raise RuntimeError('canonical intelligence has no generated_at timestamp')
 if len(document.get('entities') or [])==0:raise RuntimeError('canonical intelligence contains no entities')
 if len(document.get('evidence') or [])==0:raise RuntimeError('canonical intelligence contains no evidence')
def main():
 run('Build canonical intelligence layer',sys.executable,'build_canonical_intelligence.py')
 canonical=verify_json('canonical_intelligence.json',fresh_required=False);verify_canonical_intelligence(canonical)
 run('Build compact major-node Intelligence Brain',sys.executable,'build_intelligence_brain.py')
 run('Guarantee U.S. and China major-power hubs',sys.executable,'ensure_major_power_nodes.py')
 run('Ensure Brain group coverage',sys.executable,'ensure_brain_groups.py')
 run('Enrich U.S. and China action intelligence',sys.executable,'enrich_brain_actions.py')
 run('Validate U.S. and China action intelligence',sys.executable,'validate_action_intelligence.py')
 run('Strict Brain validation',sys.executable,'validate_intelligence_brain.py')
 brain=verify_json('intelligence_brain.json');verify_brain(brain)
 run('Build strategic signals',sys.executable,'build_strategic_signals.py')
 signals=verify_json('strategic_signals.json',fresh_required=False);verify_strategic_signals(signals)
 for name in REQUIRED_ARTIFACTS:
  if not (DATA/name).exists():raise RuntimeError(f'missing required artifact: {name}')
 print('\n=== STRATEGIC INTELLIGENCE GATE: PASSED ===',flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
