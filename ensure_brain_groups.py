#!/usr/bin/env python3
"""Repair Brain group coverage from source-backed repository data without inventing evidence."""
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data'
BRAIN=DATA/'intelligence_brain.json';SNAP=DATA/'snapshot.json'
COUNTRIES={'United States':(38,-97),'Mexico':(23.6,-102.5),'Colombia':(4.6,-74.1),'Ecuador':(-1.4,-78.4),'Venezuela':(7.1,-66),'Brazil':(-10.8,-52.9),'El Salvador':(13.8,-88.9)}
CARTELS={'Sinaloa Cartel':'Mexico','CJNG':'Mexico','Jalisco New Generation Cartel':'Mexico','Gulf Cartel':'Mexico','Los Zetas':'Mexico','Northeast Cartel':'Mexico','Santa Rosa de Lima Cartel':'Mexico','La Nueva Familia Michoacana':'Mexico','Juarez Cartel':'Mexico','Beltran Leyva Organization':'Mexico','Clan del Golfo':'Colombia','Tren de Aragua':'Venezuela','PCC':'Brazil','Primeiro Comando da Capital':'Brazil','Comando Vermelho':'Brazil','Los Choneros':'Ecuador','MS-13':'El Salvador','Mara Salvatrucha':'El Salvador'}
def slug(x):return re.sub(r'[^a-z0-9]+','-',str(x).lower()).strip('-')
def evidence(r):
 if not isinstance(r,dict): return None
 title=str(r.get('title') or r.get('name') or r.get('headline') or r.get('label') or r.get('description') or '').strip()
 url=str(r.get('original_link') or r.get('url') or r.get('sourceUrl') or r.get('source_url') or r.get('link') or '').strip()
 source=str(r.get('sourceLabel') or r.get('source') or r.get('publisher') or r.get('provider') or '').strip()
 if title and (url or source): return {'title':title[:300],'url':url,'source':source or 'Public source','time':str(r.get('publishedAt') or r.get('published_date') or r.get('updatedAt') or r.get('time') or '')}
 return None
def walk(obj):
 if isinstance(obj,dict):
  yield obj
  for v in obj.values(): yield from walk(v)
 elif isinstance(obj,list):
  for v in obj: yield from walk(v)
def main():
 brain=json.loads(BRAIN.read_text(encoding='utf-8'));snap=json.loads(SNAP.read_text(encoding='utf-8'))
 nodes=brain.setdefault('nodes',[]);edges=brain.setdefault('edges',[]);by={str(n.get('id')):n for n in nodes}
 records=list(walk(snap))
 graph=snap.get('intelligenceGraph') or {}
 records += list(walk(graph))
 for fn in ('live_articles.json','event_intelligence.json','claims.json','intelligence_assessment.json','event_market_impact.json','what_changed.json'):
  p=DATA/fn
  if p.exists():
   try: records += list(walk(json.loads(p.read_text(encoding='utf-8'))))
   except Exception: pass
 for gn in graph.get('nodes') or []:
  records.append(gn)
 for label,country in CARTELS.items():
  if any(n.get('kind')=='cartel' and str(n.get('label'))==label for n in nodes): continue
  hits=[]
  for r in records:
   ev=evidence(r)
   if not ev: continue
   blob=' '.join(str(r.get(k,'')) for k in ('label','name','title','headline','summary','description','detail','actor','actors','organization','organizations','group','category','type','tags','keywords','country','location')).lower()
   if re.search(r'(?<![a-z])'+re.escape(label.lower())+r'(?![a-z])',blob): hits.append(ev)
  if hits:
   lat,lng=COUNTRIES[country];i=slug(label);n={'id':i,'label':label,'kind':'cartel','score':7,'mentions':len(hits),'evidence':hits[:5],'canonical':True,'country':country,'lat':lat,'lng':lng,'group':'Organized Crime'};nodes.append(n);by[i]=n
 if not any(n.get('kind')=='cartel' for n in nodes): raise RuntimeError('unable to retain a source-backed cartel node')
 if not any(n.get('kind')=='country' for n in nodes): raise RuntimeError('unable to retain a source-backed country node')
 if not any(n.get('kind')=='economic' for n in nodes): raise RuntimeError('unable to retain a source-backed economic node')
 required=[n for n in nodes if n.get('kind') in ('cartel','country','economic')]
 rest=[n for n in nodes if n not in required];rest.sort(key=lambda n:(float(n.get('score') or 0),len(n.get('evidence') or []),int(n.get('mentions') or 0)),reverse=True)
 nodes=(required+rest)[:35]
 keep={n.get('id') for n in nodes};brain['nodes']=nodes
 brain['edges']=[e for e in edges if e.get('source') in keep and e.get('target') in keep and e.get('evidence')]
 stats=brain.setdefault('stats',{});stats.update({'nodes':len(nodes),'edges':len(brain['edges']),'cartelNodes':sum(n.get('kind')=='cartel' for n in nodes),'countryNodes':sum(n.get('kind')=='country' for n in nodes),'economicNodes':sum(n.get('kind')=='economic' for n in nodes),'conflictNodes':sum(n.get('kind')=='conflict' for n in nodes),'chokepointNodes':sum(n.get('kind')=='chokepoint' for n in nodes)})
 brain['updatedAt']=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
 BRAIN.write_text(json.dumps(brain,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 snap['intelligenceBrain']=brain;snap['updatedAt']=brain['updatedAt'];snap['lastSuccessfulRefresh']=brain['updatedAt']
 SNAP.write_text(json.dumps(snap,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print(f"BRAIN GROUP REPAIR: {len(nodes)} nodes / {len(brain['edges'])} edges / cartels={stats['cartelNodes']} countries={stats['countryNodes']} economic={stats['economicNodes']}")
if __name__=='__main__':main()
