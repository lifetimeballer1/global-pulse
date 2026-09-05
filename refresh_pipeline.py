#!/usr/bin/env python3
"""Global Pulse canonical refresh pipeline."""
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data'
def run(label,*cmd):
 print(f"\n=== {label} ===",flush=True);print("$"," ".join(cmd),flush=True);subprocess.run(cmd,cwd=ROOT,check=True);print(f"PASS: {label}",flush=True)
def load(name):
 p=DATA/name
 if not p.is_file() or p.stat().st_size==0:raise RuntimeError(f"missing/empty artifact: {name}")
 return json.loads(p.read_text(encoding='utf-8'))
def fresh(obj,field='updatedAt',max_age=900):
 stamp=obj.get(field)
 if not stamp:raise RuntimeError(f"artifact has no {field}")
 dt=datetime.fromisoformat(str(stamp).replace('Z','+00:00'));age=(datetime.now(timezone.utc)-dt).total_seconds()
 if age < -120 or age > max_age:raise RuntimeError(f"artifact timestamp invalid/stale: age={age:.0f}s")
def verify_json(name,*,min_list=None,fresh_required=True,max_age=900):
 d=load(name)
 if fresh_required:fresh(d,max_age=max_age)
 if min_list:
  key,minimum=min_list
  if not isinstance(d.get(key),list) or len(d[key])<minimum:raise RuntimeError(f"{name}: {key} has fewer than {minimum} entries")
 return d
def verify_live_content(live,max_age_minutes=90,min_recent=3):
 now=datetime.now(timezone.utc);articles=live.get('articles') or [];recent=[]
 for item in articles:
  try:
   stamp=item.get('published_date');dt=datetime.fromisoformat(str(stamp).replace('Z','+00:00'))
   if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
   age=(now-dt.astimezone(timezone.utc)).total_seconds()/60
   if -5<=age<=max_age_minutes:recent.append(item)
  except Exception:continue
 if len(recent)<min_recent:
  raise RuntimeError(f"live news freshness gate failed: only {len(recent)} articles published within {max_age_minutes} minutes (rows={len(articles)})")
 newest=max((datetime.fromisoformat(str(x['published_date']).replace('Z','+00:00')) for x in recent),default=now)
 print(f"PASS: live content freshness recent={len(recent)} newestAge={(now-newest.astimezone(timezone.utc)).total_seconds()/60:.1f}m",flush=True)
def main():
 run('Expand feeds',sys.executable,'update_feed_expansion.py')
 sources=DATA/'sources.json'
 if not sources.is_file() or sources.stat().st_size==0:raise RuntimeError('sources.json was not generated')
 print('PASS: feed expansion',flush=True)
 last_error=None
 for attempt in range(1,4):
  try:run(f'Poll live news {attempt}/3',sys.executable,'news_feed_db.py','--once');last_error=None;break
  except subprocess.CalledProcessError as exc:
   last_error=exc
   if attempt<3:print('retrying live-news poll...',flush=True)
 if last_error:raise last_error
 live=verify_json('live_status.json');
 if live.get('feedsChecked',0)<20 or live.get('rowsFetched',0)<=0:raise RuntimeError('live news gate failed: insufficient feeds/rows')
 verify_live_content(live if 'articles' in live else load('live_articles.json'))
 print(f"PASS: live news feeds={live.get('feedsChecked')} rows={live.get('rowsFetched')} new={live.get('newArticles')}",flush=True)
 run('Validate source health',sys.executable,'validate_source_health.py')
 run('Refresh base snapshot',sys.executable,'run_snapshot_counter_cartel.py');snap=verify_json('snapshot.json')
 run('Update market data',sys.executable,'update_market_data.py');snap=verify_json('snapshot.json');market=snap.get('marketData') or {};fresh(market,max_age=900);indicators=market.get('indicators') or []
 if len(indicators)<20:raise RuntimeError(f'market data gate failed: only {len(indicators)} indicators')
 if not market.get('provider') or not market.get('source'):raise RuntimeError('market data gate failed: provider/source missing')
 print(f"PASS: market data indicators={len(indicators)} live={market.get('liveCount')} closed={market.get('closedCount')} stale={market.get('staleCount')} errors={len(market.get('errors',[]))}",flush=True)
 run('Merge live news',sys.executable,'merge_live_news.py');snap=verify_json('snapshot.json')
 if not snap.get('news') and not snap.get('stories'):raise RuntimeError('merged snapshot contains no news/stories')
 print('PASS: merged news',flush=True)
 stages=[('Breaking intelligence','breaking_news.py','breaking_news.json',None),('Live events','build_live_events.py','live_events.json',('events',0)),('Source evidence','build_source_evidence.py','source_evidence.json',('eventSourceEvidence',0)),('Event intelligence','build_event_intelligence.py','event_intelligence.json',('events',0)),('Event consistency','build_event_consistency.py','event_consistency.json',('events',0))]
 for label,script,artifact,minimum in stages:run(label,sys.executable,script);verify_json(artifact,min_list=minimum)
 run('Political layer',sys.executable,'update_political_layer.py');verify_json('snapshot.json')
 run('Political intelligence',sys.executable,'update_political_intelligence.py');verify_json('snapshot.json')
 run('OSINT maps',sys.executable,'update_osint.py');snap=verify_json('snapshot.json');osint=snap.get('osintMaps') or {}
 if osint.get('version') not in (2,3,4):raise RuntimeError('OSINT verification failed')
 run('CFR conflict coverage',sys.executable,'update_cfr.py');snap=verify_json('snapshot.json')
 if not isinstance(snap.get('markers'),list) or not snap['markers']:raise RuntimeError('conflict coverage verification failed')
 run('Strategic layers',sys.executable,'update8_global_layers.py');verify_json('snapshot.json')
 run('Intelligence web',sys.executable,'update_intelligence_web.py')
 run('Southern Spear relationship + map layer',sys.executable,'enhance_counter_cartel_intelligence.py')
 snap=verify_json('snapshot.json')
 campaign=snap.get('counterCartelLayer') or {}
 if campaign.get('campaign')!='Operation Southern Spear':raise RuntimeError('Southern Spear campaign layer missing')
 if len(snap.get('markers') or [])<10:raise RuntimeError('Southern Spear map layer verification failed')
 graph_data=snap.get('intelligenceGraph') or {}
 if len(graph_data.get('edges') or [])<10:raise RuntimeError('Southern Spear relationship layer verification failed')
 print(f"PASS: Southern Spear layer markers={len(snap.get('markers') or [])} edges={len(graph_data.get('edges') or [])}",flush=True)
 run('Intelligence graph',sys.executable,'build_intelligence_graph.py');graph=verify_json('intelligence_graph.json')
 if len(graph.get('nodes',[]))<10 or len(graph.get('edges',[]))<3:raise RuntimeError('intelligence graph verification failed')
 for edge in graph['edges']:
  if not edge.get('source') or not edge.get('target') or not edge.get('evidence'):raise RuntimeError('intelligence graph contains unevidenced edge')
 run('Install intelligence web',sys.executable,'install_intelligence_web.py')
 if not (ROOT/'intelligence-web.html').exists() and not (ROOT/'index.html').exists():raise RuntimeError('intelligence web renderer missing')
 run('Install live event layers',sys.executable,'install_live_events.py');run('Install event intelligence',sys.executable,'install_event_intelligence.py')
 if not (ROOT/'global_pulse_event_intelligence.js').is_file():raise RuntimeError('live event renderer missing')
 run('Build assessments',sys.executable,'build_intelligence_assessment.py');verify_json('intelligence_assessment.json');run('Install assessment UI',sys.executable,'install_intelligence_assessment.py')
 if not (ROOT/'global_pulse_assessment.js').is_file():raise RuntimeError('assessment UI missing')
 run('Dashboard integrations',sys.executable,'update7_live_branding.py');run('Dashboard reporting',sys.executable,'update9_live_reporting.py');run('Breaking alerts',sys.executable,'install_breaking_alerts.py');run('Health finalizer',sys.executable,'install_health_finalizer.py')
 if not (ROOT/'index.html').is_file() or (ROOT/'index.html').stat().st_size==0:raise RuntimeError('index.html missing after dashboard integration')
 run('Source health',sys.executable,'finalize_intelligence_health.py')
 if not (DATA/'source_health.json').is_file():raise RuntimeError('source_health.json missing')
 run('Claims',sys.executable,'claim_intelligence.py');run('Install claims',sys.executable,'install_claim_intelligence.py');verify_json('claims.json')
 run('V2.7 install',sys.executable,'install_v27.py');run('Canonical map install',sys.executable,'install_map_v3.py');run('Install source-age filter',sys.executable,'install_map_age_filter.py')
 if not (ROOT/'global_pulse_v27.js').is_file():raise RuntimeError('V2.7 renderer missing')
 html=(ROOT/'index.html').read_text(encoding='utf-8')
 if 'gp-source-age-filter-css' not in html or 'gp-source-age-filter-js' not in html or 'gpSourceAge' not in html:raise RuntimeError('source-age map filter was not installed')
 print('PASS: source-age map filter installed',flush=True)
 run('Normalize generated HTML',sys.executable,'clean_index.py');run('Repository validation',sys.executable,'validate_repository.py')
 final=verify_json('snapshot.json');market=final.get('marketData') or {};fresh(market,max_age=900)
 if len(market.get('indicators') or [])<20:raise RuntimeError('final market-data gate failed')
 if not isinstance(final.get('markers'),list) or not final['markers']:raise RuntimeError('final conflict-data gate failed')
 if not (ROOT/'index.html').is_file() or (ROOT/'index.html').stat().st_size==0:raise RuntimeError('final site gate failed')
 print('\n=== FINAL GLOBAL PULSE GATE: PASSED ===',flush=True);print('snapshot=',final.get('updatedAt'),flush=True);print('marketIndicators=',len(market.get('indicators') or []),flush=True);print('newsRows=',live.get('rowsFetched'),'newArticles=',live.get('newArticles'),flush=True);print('markers=',len(final.get('markers') or []),flush=True);return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:print(f'\nPIPELINE FAILED: {exc}',file=sys.stderr,flush=True);raise
