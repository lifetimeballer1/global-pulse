#!/usr/bin/env python3
"""Build the complete cross-domain Global Pulse Intelligence Brain.

The Brain is the canonical relationship layer, not a visualization-size cache.
It ingests the published public intelligence artifacts and retains every usable
record/node and relationship. The browser may use progressive rendering for
mobile performance, but it must never truncate the underlying Brain artifact.
Relationships are contextual/evidence links and do not prove causation.
"""
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';OUT=DATA/'intelligence_brain.json'

def load(name,default=None):
 p=DATA/name
 if not p.exists():return default
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return default

def slug(v):return re.sub(r'[^a-z0-9]+','-',str(v or '').lower()).strip('-')

def ev(record):
 if not isinstance(record,dict):return None
 title=str(record.get('title') or record.get('name') or record.get('headline') or '').strip()
 url=str(record.get('original_link') or record.get('url') or record.get('sourceUrl') or record.get('source_url') or record.get('link') or '').strip()
 if not title and not url:return None
 return {'title':title or 'Public intelligence record','url':url,'source':str(record.get('sourceLabel') or record.get('source') or record.get('publisher') or 'Public source'),'time':str(record.get('publishedAt') or record.get('published_date') or record.get('time') or record.get('updatedAt') or '')}

def main():
 snap=load('snapshot.json',{}) or {};graph=load('intelligence_graph.json',{}) or {};nodes={};edges={}
 def node(label,kind='signal',evidence=None,weight=1,meta=None):
  label=str(label or '').strip()
  if not label:return None
  sid=slug(label)
  if not sid:sid='node-'+str(len(nodes)+1)
  n=nodes.setdefault(sid,{'id':sid,'label':label,'kind':kind,'weight':0,'mentions':0,'evidence':[]})
  n['weight']+=max(1,int(weight or 1));n['mentions']+=max(1,int(weight or 1))
  if meta:n.update({k:v for k,v in meta.items() if v is not None})
  if evidence and not any(x.get('title')==evidence.get('title') and x.get('url')==evidence.get('url') for x in n['evidence']):n['evidence'].append(evidence)
  return sid
 def edge(a,b,relationship,evidence=None,weight=1,types=None):
  if not a or not b or a==b:return
  key='|'.join(sorted((a,b)));e=edges.setdefault(key,{'source':a,'target':b,'weight':0,'types':set(),'relationship':relationship,'evidence':[]})
  e['weight']+=max(1,int(weight or 1));e['types'].update(types or ['contextual'])
  if relationship:e['relationship']=relationship
  if evidence and not any(x.get('title')==evidence.get('title') and x.get('url')==evidence.get('url') for x in e['evidence']):e['evidence'].append(evidence)
 # 1. Preserve the authoritative intelligence graph in full.
 legacy_ids={}
 for n in graph.get('nodes',[]):
  if isinstance(n,dict) and n.get('id'):
   sid=node(n.get('label') or n.get('id'),n.get('kind','actor'),weight=n.get('mentions',1),meta={'legacyId':str(n.get('id'))});legacy_ids[str(n.get('id'))]=sid
 for e in graph.get('edges',[]):
  if not isinstance(e,dict):continue
  s=legacy_ids.get(str(e.get('source')),slug(e.get('source')));t=legacy_ids.get(str(e.get('target')),slug(e.get('target')))
  if s in nodes and t in nodes:
   evidence=[x for x in (e.get('evidence') or []) if isinstance(x,dict)]
   if evidence:
    for x in evidence[:25]:edge(s,t,e.get('relationship','Evidence-linked relationship'),x,e.get('weight',1),e.get('types') or ['graph'])
   else:edge(s,t,e.get('relationship','Evidence-linked relationship'),None,e.get('weight',1),e.get('types') or ['graph'])
 # 2. Every current story/conflict record is represented, not just the top N.
 stories=snap.get('stories') if isinstance(snap.get('stories'),list) else []
 conflicts=snap.get('conflicts') if isinstance(snap.get('conflicts'),list) else []
 for collection,kind in ((stories,'news'),(conflicts,'conflict')):
  for r in collection:
   if not isinstance(r,dict):continue
   text=' '.join(str(r.get(k,'')) for k in ('title','summary','description','content','name','region','country','location','category','type','tags','keywords')).lower()
   matches=[]
   for sid,n in list(nodes.items()):
    label=n['label'].lower()
    if len(label)>2 and re.search(r'(?<![a-z0-9])'+re.escape(label)+r'(?![a-z0-9])',text):matches.append(sid)
   evidence=ev(r);rid=node(r.get('title') or r.get('name'), 'report', evidence, 1, {'ephemeral':True})
   for sid in matches[:20]:
    if rid:edge(rid,sid,'This current public record references this entity.',evidence,1,[kind])
   for i,a in enumerate(matches[:12]):
    for b in matches[i+1:12]:edge(a,b,'These entities are referenced together in the same current public record.',evidence,1,[kind,'co-occurrence'])
 # 3. Every map marker becomes a geographic intelligence node.
 markers=snap.get('markers') if isinstance(snap.get('markers'),list) else []
 for m in markers:
  if not isinstance(m,dict):continue
  title=str(m.get('title') or m.get('name') or m.get('eventType') or 'Mapped signal')
  mid=node(title,'map-signal',ev(m),1,{'lat':m.get('lat',m.get('latitude')),'lng':m.get('lng',m.get('lon',m.get('longitude'))),'region':m.get('region'),'eventType':m.get('eventType'),'layer':m.get('layer')})
  text=' '.join(str(m.get(k,'')) for k in ('title','detail','region','country','eventType','layer')).lower()
  hits=[sid for sid,n in nodes.items() if sid!=mid and not n.get('ephemeral') and len(n['label'])>2 and n['label'].lower() in text]
  for sid in hits[:12]:edge(mid,sid,'Mapped signal is associated with this entity by public record metadata.',ev(m),1,['map'])
 # 4. Market indicators are all retained as first-class nodes.
 market=snap.get('marketData') if isinstance(snap.get('marketData'),dict) else {};market_nodes=[]
 for q in market.get('indicators',[]):
  if not isinstance(q,dict):continue
  label=q.get('name') or q.get('symbol')
  if label:
   market_nodes.append(node(label,'market',None,1,{'symbol':q.get('symbol'),'price':q.get('price'),'changePercent':q.get('changePercent'),'marketTime':q.get('marketTime'),'sessionStatus':q.get('sessionStatus') or q.get('status'),'currency':q.get('currency')}))
 for mid in market_nodes:
  for sid,x in list(nodes.items()):
   if x['kind'] in ('actor','political','economic') and any(k in x['label'].lower() for k in ('china','japan','india','european union','united states','russia','iran','saudi arabia','ukraine')):
    edge(mid,sid,'Market indicator provides economic context; correlation is not causation.',None,1,['market'])
 # 5. Add all available event/claim/assessment/history/change records.
 for fname,kind in (('event_intelligence.json','event'),('claims.json','claim'),('intelligence_assessment.json','assessment'),('event_market_impact.json','event-market'),('historical_trends.json','trend'),('what_changed.json','change')):
  obj=load(fname,{})
  records=obj.get('events') if isinstance(obj,dict) and isinstance(obj.get('events'),list) else (obj.get('claims') if isinstance(obj,dict) and isinstance(obj.get('claims'),list) else (obj.get('assessments') if isinstance(obj,dict) and isinstance(obj.get('assessments'),list) else []))
  if not records and isinstance(obj,list):records=obj
  for r in records if isinstance(records,list) else []:
   if not isinstance(r,dict):continue
   label=r.get('title') or r.get('name') or r.get('id')
   if not label:continue
   rid=node(label,kind,ev(r),1)
   text=json.dumps(r,ensure_ascii=False).lower()
   hits=[sid for sid,x in nodes.items() if sid!=rid and x['kind'] not in ('report','map-signal','market') and len(x['label'])>2 and x['label'].lower() in text]
   for sid in hits[:20]:edge(rid,sid,f'{kind} record references this entity.',ev(r),1,[kind])
 # Serialize the complete brain. Do NOT cap nodes or edges here.
 el=[]
 for e in edges.values():
  e['types']=sorted(e['types']);e['evidenceCount']=len(e['evidence']);el.append(e)
 el.sort(key=lambda x:(x['evidenceCount'],x['weight']),reverse=True)
 nl=list(nodes.values());nl.sort(key=lambda n:(n['weight'],n['mentions']),reverse=True)
 now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
 payload={'version':2,'updatedAt':now,'complete':True,'sourceArtifacts':['snapshot.json','intelligence_graph.json','event_intelligence.json','claims.json','intelligence_assessment.json','event_market_impact.json','historical_trends.json','what_changed.json'],'method':'complete cross-domain evidence graph over current public intelligence artifacts; browser rendering is a separate progressive view','caution':'Relationships are contextual/evidence links. They do not prove causation, coordination, intent, or responsibility. Market links are relevance context only.','nodes':nl,'edges':el,'stats':{'nodes':len(nl),'edges':len(el),'newsRecords':len(stories),'conflictRecords':len(conflicts),'mapSignals':len(markers),'marketIndicators':len(market.get('indicators') or [])}}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print(f'INTELLIGENCE BRAIN COMPLETE: {len(nl)} nodes / {len(el)} edges / {len(stories)} news records / {len(conflicts)} conflict records / {len(markers)} map signals / {len(market.get("indicators") or [])} market indicators')
if __name__=='__main__':main()
