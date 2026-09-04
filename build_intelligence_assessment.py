#!/usr/bin/env python3
"""Build explainable, evidence-aware risk assessments from existing public data.
No API key required. Scores are analytical indicators, not forecasts or claims of causation.
"""
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'

def load(name, default):
 p=DATA/name
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return default

def tokens(s): return set(re.findall(r'[a-z0-9]{4,}',str(s or '').lower()))

def clamp(x): return max(0,min(100,int(round(x))))

def main():
 snap=load('snapshot.json',{}); graph=load('intelligence_graph.json',{}); events=load('live_events.json',{}); breaking=load('breaking_news.json',{})
 stories=snap.get('stories') or snap.get('articles') or []; articles=breaking.get('articles') or []
 edges=graph.get('edges') or []
 # Keep scoring conservative: volume/recency/evidence density drive the indicator; no invented event causality.
 risk_terms={'conflict':8,'attack':8,'missile':9,'airstrike':9,'bombing':9,'troops':6,'military':5,'war':10,'sanction':4,'tariff':3,'protest':3,'coup':9,'crisis':4}
 names={}
 for n in graph.get('nodes') or []:
  label=str(n.get('label') or n.get('name') or n.get('id') or '').strip()
  if label:names[label]=n
 def score_for(label):
  tl=tokens(label); evidence=0; military=0; diplomacy=0; economic=0
  for r in list(stories)+list(articles):
   text=str(r.get('title') or r.get('name') or '')+' '+str(r.get('summary') or r.get('description') or '')
   low=text.lower()
   if not (tl & tokens(text)): continue
   evidence+=1
   military+=sum(1 for k in ('attack','missile','airstrike','bombing','troops','military','war','conflict') if k in low)
   diplomacy+=sum(1 for k in ('talks','ceasefire','negotiation','agreement','diplomatic') if k in low)
   economic+=sum(1 for k in ('oil','shipping','tariff','sanction','trade','inflation','market') if k in low)
  edge_count=sum(1 for e in edges if label.lower() in (str(e.get('source_label') or '')+' '+str(e.get('target_label') or '')).lower())
  live_hits=sum(1 for e in events.get('events') or [] if tl & tokens(e.get('title')))
  factors=[]
  raw=min(28,evidence*1.4)+min(24,military*2.2)+min(14,economic*1.1)+min(10,edge_count*1.5)+min(12,live_hits*4)-min(10,diplomacy*1.2)
  if military:factors.append({'label':'Conflict / military activity','delta':clamp(military*2.2)})
  if live_hits:factors.append({'label':'Live event activity','delta':clamp(live_hits*4)})
  if economic:factors.append({'label':'Economic / energy signals','delta':clamp(economic*1.1)})
  if edge_count:factors.append({'label':'Evidence-backed network exposure','delta':clamp(edge_count*1.5)})
  if diplomacy:factors.append({'label':'Diplomatic / de-escalation signals','delta':-clamp(diplomacy*1.2)})
  factors=sorted(factors,key=lambda x:abs(x['delta']),reverse=True)[:6]
  return clamp(raw),factors,evidence
 assessments=[]
 for label in names:
  score,factors,evidence=score_for(label)
  if evidence<2 and score<15: continue
  level='CRITICAL' if score>=85 else 'HIGH' if score>=70 else 'ELEVATED' if score>=45 else 'WATCH'
  assessments.append({'entity':label,'score':score,'level':level,'delta':0,'factors':factors,'evidenceCount':evidence,'method':'Volume, live-event activity, network exposure, economic signals and de-escalation signals from current public reporting. Indicator only; not a causal forecast.'})
 assessments.sort(key=lambda x:x['score'],reverse=True)
 # Event impact cards are deliberately framed as implications, not asserted outcomes.
 impact=[]
 for e in (events.get('events') or [])[:30]:
  cat=e.get('category','general'); title=e.get('title','Live event'); implications={
   'conflict':['regional military escalation risk','energy and shipping exposure','NATO / alliance-response monitoring'],
   'economic':['market and supply-chain sensitivity','energy / trade exposure','inflation and logistics monitoring'],
   'diplomatic':['negotiation / escalation monitoring','sanctions and policy exposure','alliance-response monitoring'],
   'political':['political stability monitoring','policy and alliance exposure','protest / governance risk monitoring'],
   'disaster':['humanitarian and infrastructure pressure','transport / supply-chain disruption','emergency response monitoring'],
  }.get(cat,['regional spillover monitoring','market and policy sensitivity','humanitarian / infrastructure exposure'])
  impact.append({'eventId':e.get('id'),'title':title,'category':cat,'confidence':e.get('confidence','unknown'),'reportCount':e.get('reportCount',0),'sourceCount':e.get('sourceCount',0),'whyThisMatters':{'immediate':implications[0],'shortTerm':implications[1],'mediumTerm':implications[2]},'urls':e.get('urls',[])[:5]})
 out={'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'method':'Explainable indicator layer using current public reporting, clustered events and evidence-backed network data. Scores are not forecasts and market relationships are not treated as causal.','assessments':assessments[:60],'eventImpacts':impact[:20]}
 (DATA/'intelligence_assessment.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'ASSESSMENT: {len(out["assessments"])} entity indicators / {len(out["eventImpacts"])} event impacts')
if __name__=='__main__': main()
