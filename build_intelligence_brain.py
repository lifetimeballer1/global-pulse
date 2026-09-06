#!/usr/bin/env python3
"""Build the complete, source-backed Global Pulse Intelligence Brain.

The stored graph keeps every usable source-backed record. It also creates
canonical entity/category/country hubs so the UI can form readable clusters.
A node is retained only when it has at least one attributable source record.
Relationships are evidence/context links and never imply causation.
"""
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; OUT=DATA/'intelligence_brain.json'
COUNTRIES={
'United States':(38.0,-97.0),'Mexico':(23.6,-102.5),'Canada':(56.1,-106.3),'Colombia':(4.6,-74.1),'Ecuador':(-1.4,-78.4),'Venezuela':(7.1,-66.0),'Brazil':(-10.8,-52.9),'Peru':(-9.2,-75.0),'Bolivia':(-16.3,-63.6),'Chile':(-33.4,-70.7),'Argentina':(-38.4,-63.6),'Panama':(8.5,-80.8),'Costa Rica':(9.9,-84.2),'Haiti':(19.0,-72.3),'Dominican Republic':(18.7,-70.2),'Cuba':(21.5,-79.5),'Guatemala':(15.8,-90.2),'Honduras':(14.1,-87.2),'El Salvador':(13.8,-88.9),'Nicaragua':(12.9,-85.2),
'Ukraine':(49.0,32.0),'Russia':(61.5,105.3),'Belarus':(53.7,27.9),'Poland':(52.1,19.1),'Germany':(51.2,10.5),'France':(46.2,2.2),'United Kingdom':(55.4,-3.4),'Italy':(41.9,12.6),'Spain':(40.5,-3.7),'Turkey':(39.0,35.2),'Greece':(39.1,21.8),'Romania':(45.9,24.9),'Serbia':(44.0,21.0),'Israel':(31.0,34.9),'Palestine':(31.9,35.2),'Lebanon':(33.9,35.9),'Syria':(35.0,38.0),'Iraq':(33.2,43.7),'Iran':(32.4,53.7),'Saudi Arabia':(23.9,45.1),'Yemen':(15.6,48.5),'Jordan':(31.2,36.5),'Egypt':(26.8,30.8),'Libya':(26.3,17.2),'Sudan':(12.9,30.2),'Somalia':(5.2,46.2),'Ethiopia':(9.1,40.5),'Nigeria':(9.1,8.7),'Mali':(17.6,-4.0),'Niger':(17.6,8.1),'Burkina Faso':(12.4,-1.6),'Ghana':(7.9,-1.0),'South Africa':(-30.6,22.9),'Kenya':(0.2,37.9),'Democratic Republic of the Congo':(-2.9,23.7),'Mozambique':(-18.7,35.5),
'China':(35.9,104.2),'India':(22.9,79.0),'Pakistan':(30.4,69.3),'Afghanistan':(33.9,67.7),'North Korea':(40.3,127.5),'South Korea':(35.9,127.8),'Japan':(36.2,138.3),'Taiwan':(23.7,120.9),'Philippines':(12.9,121.8),'Indonesia':(-2.0,118.0),'Australia':(-25.3,133.8),'Myanmar':(21.9,95.9),'Thailand':(15.9,100.9),'Vietnam':(14.1,108.3)
}
CARTELS={'Sinaloa Cartel':'Mexico','Jalisco New Generation Cartel':'Mexico','CJNG':'Mexico','Gulf Cartel':'Mexico','Los Zetas':'Mexico','Northeast Cartel':'Mexico','Santa Rosa de Lima Cartel':'Mexico','La Nueva Familia Michoacana':'Mexico','Knights Templar Cartel':'Mexico','Juarez Cartel':'Mexico','Arellano Felix Organization':'Mexico','Beltran Leyva Organization':'Mexico','Clan del Golfo':'Colombia','Tren de Aragua':'Venezuela','Primeiro Comando da Capital':'Brazil','PCC':'Brazil','Comando Vermelho':'Brazil','Los Choneros':'Ecuador','MS-13':'El Salvador','Mara Salvatrucha':'El Salvador'}
GROUPS={
'oil':['oil','crude','brent','wti','petroleum','refinery','refining','pipeline','opec','barrel','lng','natural gas','gas field','gasoline','diesel'],
'food':['food','grain','wheat','corn','maize','rice','soy','soybean','fertilizer','famine','hunger','food security','food supply','cattle','beef'],
'energy':['energy','electricity','power grid','nuclear','uranium','solar','wind power','coal','gas'],
'minerals':['lithium','cobalt','copper','nickel','rare earth','gold','iron ore','mineral','mining'],
'shipping':['shipping','cargo','container','port','maritime','vessel','tanker','strait','canal','red sea','hormuz','suez'],
'finance':['stock','stocks','market','nasdaq','s&p 500','dow jones','bond','yield','currency','forex','bank','financial','vix','bitcoin','crypto'],
'military':['military','missile','drone','airstrike','navy','army','troops','weapons','defense','defence','warship'],
'politics':['election','president','parliament','government','minister','sanction','diplomatic','political'],
'cyber':['cyber','hack','malware','ransomware','digital attack','cyberattack'],
'organized-crime':['cartel','gang','organized crime','drug trafficking','trafficking','smuggling','extortion','kidnapping'],
'migration':['migration','migrant','refugee','asylum','border crossing'],
'water':['water','drought','river','dam','reservoir','flood','water supply'],
'health':['outbreak','epidemic','pandemic','disease','cholera','malaria','health','hospital']
}

def load(name,default=None):
 p=DATA/name
 if not p.exists(): return default
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return default

def slug(v):return re.sub(r'[^a-z0-9]+','-',str(v or '').lower()).strip('-')

def evidence(record):
 if not isinstance(record,dict):return None
 title=str(record.get('title') or record.get('name') or record.get('headline') or '').strip()
 url=str(record.get('original_link') or record.get('url') or record.get('sourceUrl') or record.get('source_url') or record.get('link') or '').strip()
 source=str(record.get('sourceLabel') or record.get('source') or record.get('publisher') or '').strip()
 if not title and not url:return None
 if not url and not source:return None
 return {'title':title or 'Public intelligence record','url':url,'source':source or 'Public source','time':str(record.get('publishedAt') or record.get('published_date') or record.get('time') or record.get('updatedAt') or '')}

def text_of(r):return ' '.join(str(r.get(k,'')) for k in ('title','headline','summary','description','content','detail','name','region','country','location','category','type','tags','keywords','eventType','layer','actor','actors','organization','organizations')).lower()

def country_for(text,label=''):
 t=(text+' '+str(label)).lower()
 for c in sorted(COUNTRIES,key=len,reverse=True):
  if c.lower() in t:return c
 for alias,c in [('us','United States'),('u.s.','United States'),('usa','United States'),('uk','United Kingdom'),('uae','United Arab Emirates'),('drc','Democratic Republic of the Congo')]:
  if re.search(r'(?<![a-z])'+re.escape(alias)+r'(?![a-z])',t):return c
 return None

def main():
 snap=load('snapshot.json',{}) or {};graph=load('intelligence_graph.json',{}) or {};nodes={};edges={};pending=[]
 def add_node(label,kind='signal',ev=None,weight=1,meta=None):
  label=str(label or '').strip()
  if not label:return None
  sid=slug(label) or 'node-'+str(len(nodes)+1)
  n=nodes.setdefault(sid,{'id':sid,'label':label,'kind':kind,'weight':0,'mentions':0,'evidence':[]})
  n['weight']+=max(1,int(weight or 1));n['mentions']+=max(1,int(weight or 1))
  if meta:
   for k,v in meta.items():
    if v is not None:n[k]=v
  if ev and not any(x.get('title')==ev.get('title') and x.get('url')==ev.get('url') for x in n['evidence']):n['evidence'].append(ev)
  return sid
 def add_edge(a,b,relationship,ev=None,weight=1,types=None):
  if not a or not b or a==b:return
  key='|'.join(sorted((a,b)));e=edges.setdefault(key,{'source':a,'target':b,'weight':0,'types':set(),'relationship':relationship,'evidence':[]})
  e['weight']+=max(1,int(weight or 1));e['types'].update(types or ['contextual'])
  if relationship:e['relationship']=relationship
  if ev and not any(x.get('title')==ev.get('title') and x.get('url')==ev.get('url') for x in e['evidence']):e['evidence'].append(ev)
 # Existing authoritative graph.
 legacy={}
 for n in graph.get('nodes',[]):
  if isinstance(n,dict) and n.get('id'):
   evs=[x for x in (n.get('evidence') or []) if isinstance(x,dict) and (x.get('url') or x.get('source'))]
   sid=add_node(n.get('label') or n.get('id'),n.get('kind','actor'),evs[0] if evs else None,n.get('mentions',1),{'legacyId':str(n.get('id'))})
   legacy[str(n.get('id'))]=sid
 for e in graph.get('edges',[]):
  if not isinstance(e,dict):continue
  s=legacy.get(str(e.get('source')),slug(e.get('source')));t=legacy.get(str(e.get('target')),slug(e.get('target')))
  if s in nodes and t in nodes:
   for x in (e.get('evidence') or []):
    if isinstance(x,dict) and (x.get('url') or x.get('source')):add_edge(s,t,e.get('relationship','Evidence-linked relationship'),x,e.get('weight',1),e.get('types') or ['graph'])
 # Every current report is retained and used to build canonical entities/groups.
 reports=[]
 for collection,kind in ((snap.get('stories') or [],'news'),(snap.get('conflicts') or [],'conflict'),):
  if not isinstance(collection,list):continue
  for r in collection:
   if not isinstance(r,dict):continue
   ev=evidence(r)
   if not ev:continue
   reports.append((r,kind,ev))
 for fname,kind,keys in [('event_intelligence.json','event',['events']),('claims.json','claim',['claims']),('intelligence_assessment.json','assessment',['assessments']),('event_market_impact.json','event-market',['events']),('historical_trends.json','trend',['events','trends']),('what_changed.json','change',['changes','events'])]:
  obj=load(fname,{})
  if isinstance(obj,list):records=obj
  else:
   records=[]
   for k in keys:
    if isinstance(obj,dict) and isinstance(obj.get(k),list):records=obj[k];break
  for r in records:
   if isinstance(r,dict) and evidence(r):reports.append((r,kind,evidence(r)))
 for r,kind,ev in reports:
  label=r.get('title') or r.get('name') or r.get('headline') or kind+' record';rid=add_node(label,'report',ev,1,{'reportKind':kind,'ephemeral':True});txt=text_of(r)
  # Existing named entities.
  for sid,n in list(nodes.items()):
   if sid==rid or n.get('ephemeral'):continue
   lab=n['label'];
   if len(lab)>2 and re.search(r'(?<![a-z0-9])'+re.escape(lab.lower())+r'(?![a-z0-9])',txt):
    n['evidence'].append(ev) if not any(x.get('title')==ev.get('title') and x.get('url')==ev.get('url') for x in n['evidence']) else None
    add_edge(rid,sid,'Current source references this entity.',ev,1,[kind])
  # Explicit cartel/org entity extraction.
  for cartel,country in CARTELS.items():
   if cartel.lower() in txt:
    cid=add_node(cartel,'cartel',ev,2,{'country':country,'lat':COUNTRIES.get(country,(0,0))[0],'lng':COUNTRIES.get(country,(0,0))[1],'group':'organized-crime','canonical':True})
    add_edge(rid,cid,'Source names or describes this organization.',ev,2,[kind,'organized-crime'])
  # Country anchor derived only from this sourced report.
  country=country_for(txt)
  if country and country in COUNTRIES:
   lat,lng=COUNTRIES[country];co=add_node(country,'country',ev,1,{'country':country,'lat':lat,'lng':lng,'clusterKey':'country:'+country,'canonical':True,'derived':True});add_edge(rid,co,'Source places this intelligence in or materially references this country.',ev,1,['geography'])
  # Commodity/domain hubs.
  for group,terms in GROUPS.items():
   hits=[x for x in terms if x in txt]
   if not hits:continue
   gid=add_node(group.replace('-',' ').title(), 'group', ev, 1, {'group':group,'canonical':True})
   add_edge(rid,gid,'Source contains signals in this intelligence domain.',ev,1,[group,'group'])
   if country and country in COUNTRIES:
    co=slug(country);add_edge(gid,co,'Domain is geographically anchored by sourced reporting.',ev,1,['geography','group'])
 # Map markers: only source-backed markers become nodes.
 for m in (snap.get('markers') or []):
  if not isinstance(m,dict):continue
  ev=evidence(m)
  if not ev:continue
  label=m.get('title') or m.get('name') or m.get('eventType') or 'Mapped signal';mid=add_node(label,'map-signal',ev,1,{'lat':m.get('lat',m.get('latitude')),'lng':m.get('lng',m.get('lon',m.get('longitude'))),'region':m.get('region'),'eventType':m.get('eventType'),'layer':m.get('layer'),'country':country_for(text_of(m))})
  txt=text_of(m);country=country_for(txt)
  if country in COUNTRIES:add_edge(mid,slug(country),'Mapped source is geographically associated with this country.',ev,1,['map','geography'])
 # Markets are sourced from the market feed; retain every valid indicator.
 market=(snap.get('marketData') or {}) if isinstance(snap.get('marketData'),dict) else {}
 for q in market.get('indicators') or []:
  if not isinstance(q,dict) or q.get('price') is None:continue
  ev={'title':str(q.get('name') or q.get('symbol') or 'Market indicator'),'url':str(q.get('sourceUrl') or q.get('url') or ''),'source':str(q.get('source') or 'Yahoo Finance public market feed'),'time':str(q.get('marketTime') or q.get('updatedAt') or '')}
  mid=add_node(q.get('name') or q.get('symbol'),'market',ev,1,{'symbol':q.get('symbol'),'price':q.get('price'),'changePercent':q.get('changePercent'),'marketTime':q.get('marketTime'),'sessionStatus':q.get('sessionStatus') or q.get('status'),'currency':q.get('currency'),'group':'finance'})
  for group,terms in GROUPS.items():
   if group=='finance':continue
   # Market indicators get a domain hub only when the name itself is explicit.
   if any(term in str(q.get('name','')).lower() for term in terms):
    gid=add_node(group.title(),'group',ev,1,{'group':group,'canonical':True});add_edge(mid,gid,'Market instrument is directly associated with this domain.',ev,1,['market',group])
 # Backfill group/country metadata for all sourced entity nodes and link known country anchors.
 for sid,n in list(nodes.items()):
  if not n.get('evidence'):continue
  blob=(n.get('label','')+' '+n.get('kind','')).lower()
  if n.get('kind')!='group' and not n.get('group'):
   for g,terms in GROUPS.items():
    if any(t in blob for t in terms):n['group']=g;break
  if not n.get('country'):
   c=country_for(n.get('label',''))
   if c:n['country']=c
  c=n.get('country')
  if c in COUNTRIES:
   n['lat'],n['lng']=COUNTRIES[c];n['clusterKey']='country:'+c
   if n.get('kind') not in ('country','report') and slug(c) in nodes:add_edge(sid,slug(c),'Entity is geographically anchored to its sourced country context.',n['evidence'][0],1,['geography'])
 # Drop anything without an actual source and drop relationships without evidence.
 valid={sid for sid,n in nodes.items() if any((x.get('url') or x.get('source')) for x in n.get('evidence',[]) if isinstance(x,dict))}
 nodes={sid:n for sid,n in nodes.items() if sid in valid}
 out=[]
 for e in edges.values():
  if e['source'] not in nodes or e['target'] not in nodes or not e.get('evidence'):continue
  e['types']=sorted(e['types']);e['evidenceCount']=len(e['evidence']);out.append(e)
 # Remove orphaned non-report nodes after source/edge pruning, except sourced canonical hubs.
 degree={sid:0 for sid in nodes}
 for e in out:degree[e['source']]+=1;degree[e['target']]+=1
 nodes={sid:n for sid,n in nodes.items() if degree.get(sid,0)>0 or n.get('kind')=='report'}
 out=[e for e in out if e['source'] in nodes and e['target'] in nodes]
 nl=list(nodes.values());nl.sort(key=lambda n:(n.get('canonical',False),n['weight'],n['mentions']),reverse=True);out.sort(key=lambda e:(e['evidenceCount'],e['weight']),reverse=True)
 now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
 groups=sorted({n.get('group') for n in nl if n.get('group')});countries=sorted({n.get('country') for n in nl if n.get('country')})
 payload={'version':3,'updatedAt':now,'complete':True,'sourceBackedOnly':True,'sourceArtifacts':['snapshot.json','intelligence_graph.json','event_intelligence.json','claims.json','intelligence_assessment.json','event_market_impact.json','historical_trends.json','what_changed.json'],'method':'Complete source-backed cross-domain graph with canonical entity, domain, and geographic grouping. Browser layout uses country anchors plus relationship forces.','grouping':{'domains':groups,'countries':countries,'entityRule':'Canonical organizations and domain hubs are created only from sourced records; related records link to the canonical node.','geographyRule':'Nodes with sourced country context inherit that country anchor; this is a visualization/context relationship, not proof of operational control.'},'caution':'Relationships are contextual/evidence links. They do not prove causation, coordination, intent, or responsibility. Market links are relevance context only.','nodes':nl,'edges':out,'stats':{'nodes':len(nl),'edges':len(out),'newsRecords':len(snap.get('stories') or []),'conflictRecords':len(snap.get('conflicts') or []),'mapSignals':len(snap.get('markers') or []),'marketIndicators':len(market.get('indicators') or []),'sourceBackedNodes':len(nl),'domainGroups':len(groups),'countryClusters':len(countries)}}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print(f'INTELLIGENCE BRAIN: {len(nl)} source-backed nodes / {len(out)} evidence relationships / {len(groups)} domains / {len(countries)} countries')
if __name__=='__main__':main()
