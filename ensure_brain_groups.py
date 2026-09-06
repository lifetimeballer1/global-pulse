#!/usr/bin/env python3
"""Repair the human-facing Brain from the already source-backed curated graph."""
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data'
BRAIN=DATA/'intelligence_brain.json';SNAP=DATA/'snapshot.json'
COUNTRIES={'United States':(38,-97),'Mexico':(23.6,-102.5),'Colombia':(4.6,-74.1),'Ecuador':(-1.4,-78.4),'Venezuela':(7.1,-66),'Brazil':(-10.8,-52.9),'El Salvador':(13.8,-88.9)}
CARTELS={'Sinaloa Cartel':'Mexico','CJNG':'Mexico','Jalisco New Generation Cartel':'Mexico','Clan del Golfo':'Colombia','Los Choneros':'Ecuador','Tren de Aragua':'Venezuela'}
def slug(x):return re.sub(r'[^a-z0-9]+','-',x.lower()).strip('-')
def main():
 brain=json.loads(BRAIN.read_text(encoding='utf-8'));snap=json.loads(SNAP.read_text(encoding='utf-8'))
 nodes=brain.setdefault('nodes',[]);edges=brain.setdefault('edges',[]);by={str(n.get('id')):n for n in nodes};graph=snap.get('intelligenceGraph') or {}
 for gn in graph.get('nodes') or []:
  label=str(gn.get('label') or gn.get('name') or '');kind=str(gn.get('kind') or '')
  target='cartel' if kind in ('organized-crime','cartel') and label in CARTELS else ('country' if label in COUNTRIES else None)
  if not target:continue
  evidence=[x for x in (gn.get('evidence') or []) if isinstance(x,dict) and (x.get('url') or x.get('source'))]
  if not evidence:continue
  i=slug(label)
  if i not in by:
   meta={'id':i,'label':label,'kind':target,'score':8 if target=='cartel' else 2,'mentions':1,'evidence':evidence[:5],'canonical':True}
   if target=='cartel':
    meta.update({'country':CARTELS[label],'group':'Organized Crime'});meta.update({'lat':COUNTRIES[CARTELS[label]][0],'lng':COUNTRIES[CARTELS[label]][1]})
   else:
    meta.update({'country':label,'lat':COUNTRIES[label][0],'lng':COUNTRIES[label][1],'clusterKey':'country:'+label})
   nodes.append(meta);by[i]=meta
 if not any(n.get('kind')=='cartel' for n in nodes):raise RuntimeError('unable to retain a source-backed cartel node')
 if not any(n.get('kind')=='country' for n in nodes):raise RuntimeError('unable to retain a source-backed country node')
 if not any(n.get('kind')=='economic' for n in nodes):raise RuntimeError('unable to retain a source-backed economic node')
 if len(nodes)>35:
  required=[n for n in nodes if n.get('kind') in ('cartel','country','economic')]
  rest=[n for n in nodes if n not in required];rest.sort(key=lambda n:(float(n.get('score') or 0),len(n.get('evidence') or []),int(n.get('mentions') or 0)),reverse=True)
  nodes=(required+rest)[:35]
 keep={n.get('id') for n in nodes};brain['nodes']=nodes
 brain['edges']=[e for e in edges if e.get('source') in keep and e.get('target') in keep and e.get('evidence')]
 stats=brain.setdefault('stats',{});stats.update({'nodes':len(nodes),'edges':len(brain['edges']),'cartelNodes':sum(n.get('kind')=='cartel' for n in nodes),'countryNodes':sum(n.get('kind')=='country' for n in nodes),'economicNodes':sum(n.get('kind')=='economic' for n in nodes),'conflictNodes':sum(n.get('kind')=='conflict' for n in nodes),'chokepointNodes':sum(n.get('kind')=='chokepoint' for n in nodes)})
 brain['updatedAt']=datetime.now(timezone.utc).isoformat().replace('+00:00','Z');BRAIN.write_text(json.dumps(brain,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print(f"BRAIN GROUP REPAIR: {len(nodes)} nodes / {len(brain['edges'])} edges / cartels={stats['cartelNodes']} countries={stats['countryNodes']} economic={stats['economicNodes']}")
if __name__=='__main__':main()
