#!/usr/bin/env python3
"""Global Pulse canonical refresh pipeline."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data'
REQUIRED_ARTIFACTS=('snapshot.json','history.json','sources.json','live_articles.json','intelligence_graph.json','intelligence_brain.json','map_points.json')
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
def verify_live_content(live,max_age_minutes=90,min_recent=2):
 now=datetime.now(timezone.utc);recent=[]
 for item in live.get('articles') or []:
  try:
   dt=datetime.fromisoformat(str(item.get('published_date')).replace('Z','+00:00'));dt=dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc);age=(now-dt.astimezone(timezone.utc)).total_seconds()/60
   if -5<=age<=max_age_minutes:recent.append(item)
  except Exception:continue
 if len(recent)<min_recent:raise RuntimeError(f'live news freshness gate failed: only {len(recent)} recent articles')
 print(f'PASS: live content freshness recent={len(recent)}',flush=True)
def verify_brain(brain):
 if brain.get('complete') is not True or brain.get('sourceBackedOnly') is not True or brain.get('consolidated') is not True:raise RuntimeError('intelligence brain completeness/source/consolidation gate failed')
 nodes=brain.get('nodes') or [];edges=brain.get('edges') or []
 if len(nodes)<10 or len(nodes)>35 or brain.get('maxNodes')!=35:raise RuntimeError(f'intelligence brain size gate failed: {len(nodes)} nodes')
 if len(edges)<5:raise RuntimeError('intelligence brain verification failed: too few relationships')
 stats=brain.get('stats') if isinstance(brain.get('stats'),dict) else {}
 if stats.get('marketIndicators',0)<20:raise RuntimeError('intelligence brain market layer missing')
 kind_counts={k:sum(n.get('kind')==k for n in nodes) for k in ('cartel','country','economic','conflict','chokepoint')}
 if kind_counts['cartel']<1 or kind_counts['country']<1 or kind_counts['economic']<1:raise RuntimeError(f'intelligence brain major-node grouping missing: cartels={kind_counts["cartel"]} countries={kind_counts["country"]} economic={kind_counts["economic"]}')
 if stats and stats.get('nodes') is not None and stats.get('nodes')!=len(nodes):raise RuntimeError('intelligence brain stats mismatch: nodes')
 if stats and stats.get('edges') is not None and stats.get('edges')!=len(edges):raise RuntimeError('intelligence brain stats mismatch: edges')
 ids={str(n.get('id')) for n in nodes};allowed={'country','cartel','economic','conflict','chokepoint'}
 for n in nodes:
  ev=n.get('evidence') or []
  if not any(isinstance(x,dict) and (x.get('url') or x.get('source')) for x in ev):raise RuntimeError(f'unsourced brain node: {n.get("label")}')
  if n.get('kind') not in allowed:raise RuntimeError(f'noncanonical brain node: {n.get("label")} ({n.get("kind")})')
  if not n.get('canonical'):raise RuntimeError(f'noncanonical grouped node: {n.get("label")}')
 for e in edges:
  if str(e.get('source')) not in ids or str(e.get('target')) not in ids:raise RuntimeError('intelligence brain contains invalid relationship endpoint')
  if not e.get('evidence'):raise RuntimeError('intelligence brain contains unevidenced relationship')
 print(f'PASS: brain major-node gate nodes={len(nodes)} edges={len(edges)} cartels={kind_counts["cartel"]} countries={kind_counts["country"]} economic={kind_counts["economic"]}',flush=True)
def verify_map_points(map_points):
 markers=map_points.get('markers')
 if not isinstance(markers,list) or len(markers)<10:raise RuntimeError('map marker feed verification failed: too few markers')
 valid=[]
 for m in markers:
  if not isinstance(m,dict):continue
  lat=m.get('lat',m.get('latitude'));lng=m.get('lng',m.get('lon',m.get('longitude')))
  try:
   lat=float(lat);lng=float(lng)
   if -90<=lat<=90 and -180<=lng<=180:valid.append(m)
  except (TypeError,ValueError):continue
 if len(valid)<10:raise RuntimeError(f'map marker geographic validation failed: only {len(valid)} markers have valid coordinates')
 declared=map_points.get('count')
 if declared is not None and int(declared)!=len(markers):raise RuntimeError('map marker count mismatch')
 print(f'PASS: map geographic validation markers={len(markers)} validCoordinates={len(valid)}',flush=True)
def write_refresh_manifest():
 now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z');artifacts={}
 for name in REQUIRED_ARTIFACTS:
  p=DATA/name
  if not p.is_file() or p.stat().st_size==0:raise RuntimeError(f'required generated artifact missing: {name}')
  raw=p.read_bytes();obj=json.loads(raw.decode('utf-8'));stamp=(obj.get('updatedAt') or obj.get('lastSuccessfulRefresh')) if isinstance(obj,dict) else now
  artifacts[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'generatedAt':stamp}
 manifest={'version':6,'generatedAt':now,'pipeline':'refresh_pipeline.py','artifacts':artifacts}
 (DATA/'refresh_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS: refresh manifest',','.join(REQUIRED_ARTIFACTS),flush=True)
def main():
 run('Expand feeds',sys.executable,'update_feed_expansion.py');sources=DATA/'sources.json'
 if not sources.is_file() or sources.stat().st_size==0:raise RuntimeError('sources.json was not generated')
 for attempt in range(1,4):
  try:run(f'Poll live news {attempt}/3',sys.executable,'news_feed_db.py','--once');break
  except subprocess.CalledProcessError:
   if attempt==3:raise
 live=verify_json('live_status.json');live_articles=load('live_articles.json')
 if live.get('feedsChecked',0)<20 or live.get('rowsFetched',0)<=0:raise RuntimeError('live news gate failed')
 verify_live_content(live_articles)
 run('Validate source health',sys.executable,'validate_source_health.py')
 run('Refresh base snapshot',sys.executable,'run_snapshot_counter_cartel.py');verify_json('snapshot.json')
 run('Update market data',sys.executable,'update_market_data.py');snap=verify_json('snapshot.json');market=snap.get('marketData') or {};fresh(market,max_age=900)
 if len(market.get('indicators') or [])<20:raise RuntimeError('market data gate failed')
 if not any((x.get('price') is not None and float(x.get('price',0))>0) for x in market.get('indicators',[]) if isinstance(x,dict)):raise RuntimeError('market data contains no positive real prices')
 run('Merge live news',sys.executable,'merge_live_news.py');verify_json('snapshot.json')
 run('Source failover',sys.executable,'source_failover.py');verify_json('snapshot.json')
 run('Political layer',sys.executable,'update_political_layer.py');verify_json('snapshot.json')
 run('Political intelligence',sys.executable,'update_political_intelligence.py');verify_json('snapshot.json')
 run('OSINT maps',sys.executable,'update_osint.py');snap=verify_json('snapshot.json')
 if (snap.get('osintMaps') or {}).get('version') not in (2,3,4):raise RuntimeError('OSINT verification failed')
 run('CFR conflict coverage',sys.executable,'update_cfr.py');verify_json('snapshot.json')
 run('Strategic + hazard layers',sys.executable,'update8_global_layers.py');verify_json('snapshot.json')
 run('UCDP conflict corroboration',sys.executable,'update_conflict_dataset.py');snap=verify_json('snapshot.json')
 if not (snap.get('conflictDataset') or {}).get('provider'):raise RuntimeError('UCDP conflict layer missing')
 run('World Bank macro context',sys.executable,'update_macro_data.py');snap=verify_json('snapshot.json')
 if not (snap.get('macroData') or {}).get('provider'):raise RuntimeError('macro layer missing')
 run('Build canonical map marker feed',sys.executable,'build_map_points.py');map_points=verify_json('map_points.json');verify_map_points(map_points)
 run('Canonical event pipeline',sys.executable,'build_event_pipeline.py')
 for artifact,key in [('event_history.json',None),('event_intelligence.json','events'),('event_consistency.json','events'),('event_resolution.json','events'),('event_market_impact.json','events')]:verify_json(artifact,min_list=(key,0) if key else None)
 run('Intelligence graph enrichment',sys.executable,'enhance_counter_cartel_intelligence.py');snap=verify_json('snapshot.json');graph_data=snap.get('intelligenceGraph') or {}
 if len(graph_data.get('nodes',[]))<10 or len(graph_data.get('edges',[]))<3:raise RuntimeError('intelligence graph source enrichment failed')
 run('Intelligence graph publish',sys.executable,'build_intelligence_graph.py');graph=verify_json('intelligence_graph.json')
 if len(graph.get('nodes',[]))<10 or len(graph.get('edges',[]))<3:raise RuntimeError('intelligence graph verification failed')
 for edge in graph['edges']:
  if not edge.get('source') or not edge.get('target') or not edge.get('evidence'):raise RuntimeError('intelligence graph contains unevidenced edge')
 run('Build assessments',sys.executable,'build_intelligence_assessment.py');verify_json('intelligence_assessment.json')
 run('Claims',sys.executable,'claim_intelligence.py');verify_json('claims.json')
 run('What changed',sys.executable,'build_what_changed.py');verify_json('what_changed.json')
 run('Historical trends',sys.executable,'build_historical_trends.py');trends=verify_json('historical_trends.json',max_age=3600)
 if 'windows' not in trends:raise RuntimeError('historical trends windows missing')
 run('Build compact major-node Intelligence Brain',sys.executable,'build_intelligence_brain.py')
 run('Ensure Brain group coverage',sys.executable,'ensure_brain_groups.py')
 brain=verify_json('intelligence_brain.json');verify_brain(brain)
 run('Canonical index cleanup',sys.executable,'clean_index.py')
 run('Browser security hardening',sys.executable,'harden_site.py')
 run('Install browser QA hardening',sys.executable,'install_qa_hardening.py')
 run('Repository validation',sys.executable,'validate_repository.py')
 final=verify_json('snapshot.json')
 now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z');final['updatedAt']=now;final['lastSuccessfulRefresh']=now;final['freshness']={'status':'fresh','generatedAt':now,'maxExpectedAgeSeconds':900}
 DATA.joinpath('snapshot.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if not isinstance(final.get('markers'),list) or not final['markers']:raise RuntimeError('final conflict-data gate failed')
 write_refresh_manifest();print('\n=== FINAL GLOBAL PULSE GATE: PASSED ===',flush=True);print('snapshot=',final.get('updatedAt'),flush=True);print('newsRows=',live.get('rowsFetched'),flush=True);print('markers=',len(final.get('markers') or []),flush=True);print('mapPoints=',map_points.get('count'),flush=True);print('brain=',len(brain.get('nodes') or []),'major nodes /',len(brain.get('edges') or []),'relationships',flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
