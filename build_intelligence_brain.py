#!/usr/bin/env python3
"""Build the compact Global Pulse Intelligence Brain.

Only major, source-backed things become nodes: major countries, major
cartels/organizations, core economic factors, and a few major conflicts and
strategic chokepoints. Raw records remain upstream as evidence.
"""
from __future__ import annotations
import json,re
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';OUT=DATA/'intelligence_brain.json';MAX_NODES=35
COUNTRIES={'United States':(38,-97),'Mexico':(23.6,-102.5),'Canada':(56.1,-106.3),'Colombia':(4.6,-74.1),'Ecuador':(-1.4,-78.4),'Venezuela':(7.1,-66),'Brazil':(-10.8,-52.9),'Peru':(-9.2,-75),'Chile':(-33.4,-70.7),'Argentina':(-38.4,-63.6),'Panama':(8.5,-80.8),'Costa Rica':(9.9,-84.2),'Haiti':(19,-72.3),'Dominican Republic':(18.7,-70.2),'Guatemala':(15.8,-90.2),'Honduras':(14.1,-87.2),'El Salvador':(13.8,-88.9),'Nicaragua':(12.9,-85.2),'Ukraine':(49,32),'Russia':(61.5,105.3),'Belarus':(53.7,27.9),'Poland':(52.1,19.1),'Germany':(51.2,10.5),'France':(46.2,2.2),'United Kingdom':(55.4,-3.4),'Italy':(41.9,12.6),'Spain':(40.5,-3.7),'Turkey':(39,35.2),'Greece':(39.1,21.8),'Romania':(45.9,24.9),'Israel':(31,34.9),'Palestine':(31.9,35.2),'Lebanon':(33.9,35.9),'Syria':(35,38),'Iraq':(33.2,43.7),'Iran':(32.4,53.7),'Saudi Arabia':(23.9,45.1),'Yemen':(15.6,48.5),'Jordan':(31.2,36.5),'Egypt':(26.8,30.8),'Libya':(26.3,17.2),'Sudan':(12.9,30.2),'Somalia':(5.2,46.2),'Ethiopia':(9.1,40.5),'Nigeria':(9.1,8.7),'Mali':(17.6,-4),'Niger':(17.6,8.1),'Burkina Faso':(12.4,-1.6),'Ghana':(7.9,-1),'South Africa':(-30.6,22.9),'Kenya':(.2,37.9),'DR Congo':(-2.9,23.7),'Mozambique':(-18.7,35.5),'China':(35.9,104.2),'India':(22.9,79),'Pakistan':(30.4,69.3),'Afghanistan':(33.9,67.7),'North Korea':(40.3,127.5),'South Korea':(35.9,127.8),'Japan':(36.2,138.3),'Taiwan':(23.7,120.9),'Philippines':(12.9,121.8),'Indonesia':(-2,118),'Australia':(-25.3,133.8),'Myanmar':(21.9,95.9),'Thailand':(15.9,100.9),'Vietnam':(14.1,108.3)}
CARTELS={'Sinaloa Cartel':'Mexico','CJNG':'Mexico','Jalisco New Generation Cartel':'Mexico','Gulf Cartel':'Mexico','Los Zetas':'Mexico','Northeast Cartel':'Mexico','Santa Rosa de Lima Cartel':'Mexico','La Nueva Familia Michoacana':'Mexico','Juarez Cartel':'Mexico','Beltran Leyva Organization':'Mexico','Clan del Golfo':'Colombia','Tren de Aragua':'Venezuela','PCC':'Brazil','Primeiro Comando da Capital':'Brazil','Comando Vermelho':'Brazil','Los Choneros':'Ecuador','MS-13':'El Salvador','Mara Salvatrucha':'El Salvador'}
ECONOMIC={'Oil':['oil','crude','brent','wti','petroleum','refinery','pipeline','opec','barrel','lng','natural gas','gas field','gasoline','diesel'],'Food':['food','grain','wheat','corn','maize','rice','soy','soybean','fertilizer','famine','hunger','food security','food supply','cattle','beef'],'Energy':['energy','electricity','power grid','nuclear','uranium','solar','wind power','coal','gas'],'Minerals':['lithium','cobalt','copper','nickel','rare earth','gold','iron ore','mineral','mining'],'Shipping':['shipping','cargo','container','port','maritime','vessel','tanker','strait','canal','red sea','hormuz','suez'],'Markets':['stock','stocks','market','nasdaq','s&p 500','dow jones','bond','yield','currency','forex','bank','financial','vix','bitcoin','crypto'],'Trade':['trade','tariff','export','import','sanction','customs','trade war'],'Inflation':['inflation','consumer prices','cost of living','interest rate','central bank','rate cut','rate hike'],'Supply Chains':['supply chain','logistics','shortage','disruption','manufacturing','semiconductor','chip supply'],'Commodities':['commodity','commodities','raw materials','commodity prices']}
CONFLICTS={'Russia-Ukraine War':['ukraine','russia','zelensky','putin','donbas','crimea'],'Israel-Gaza War':['gaza','israel','hamas','palestinian','west bank'],'Sudan War':['sudan','rsf','rapid support forces','saf'],'Myanmar Conflict':['myanmar','burma','junta','resistance force'],'Sahel Conflicts':['mali','niger','burkina faso','sahel','jihadist']}
CHOKEPOINTS={'Strait of Hormuz':['hormuz','strait of hormuz'],'Red Sea':['red sea','bab el-mandeb','houthi','houthi rebels'],'Suez Canal':['suez canal','suez'],'Panama Canal':['panama canal']}
def load(n,d=None):
 try:return json.loads((DATA/n).read_text(encoding='utf-8')) if (DATA/n).exists() else d
 except:return d
def ev(r):
 if not isinstance(r,dict):return None
 t=str(r.get('title') or r.get('name') or r.get('headline') or '').strip();u=str(r.get('original_link') or r.get('url') or r.get('sourceUrl') or r.get('source_url') or r.get('link') or '').strip();s=str(r.get('sourceLabel') or r.get('source') or r.get('publisher') or '').strip()
 return {'title':t or 'Public intelligence record','url':u,'source':s or 'Public source','time':str(r.get('publishedAt') or r.get('published_date') or r.get('time') or r.get('updatedAt') or '')} if (t or u) and (u or s) else None
def text(r):return ' '.join(str(r.get(k,'')) for k in ('title','headline','summary','description','content','detail','name','region','country','location','category','type','tags','keywords','eventType','layer','actor','actors','organization','organizations')).lower()
def slug(x):return re.sub(r'[^a-z0-9]+','-',str(x).lower()).strip('-')
def main():
 snap=load('snapshot.json',{}) or {};nodes={};rels=defaultdict(lambda:{'weight':0,'types':set(),'evidence':[]});reports=[]
 def add(label,kind,source,score=1,meta=None):
  if not label or not source:return None
  i=slug(label);n=nodes.setdefault(i,{'id':i,'label':label,'kind':kind,'score':0,'mentions':0,'evidence':[]});n['score']+=score;n['mentions']+=1
  if meta:n.update(meta)
  if not any(x.get('title')==source.get('title') and x.get('url')==source.get('url') for x in n['evidence']):n['evidence'].append(source)
  return i
 def link(a,b,reason,source,typ):
  if not a or not b or a==b or not source:return
  k='|'.join(sorted((a,b)));r=rels[k];r['weight']+=1;r['types'].add(typ);r['relationship']=reason
  if not any(x.get('title')==source.get('title') and x.get('url')==source.get('url') for x in r['evidence']):r['evidence'].append(source)
 for arr,typ in ((snap.get('stories') or [],'news'),(snap.get('conflicts') or [],'conflict')):
  if isinstance(arr,list):reports += [(r,typ) for r in arr if isinstance(r,dict)]
 for fn,typ,keys in [('event_intelligence.json','event',['events']),('claims.json','claim',['claims']),('intelligence_assessment.json','assessment',['assessments']),('event_market_impact.json','event-market',['events']),('what_changed.json','change',['changes','events'])]:
  o=load(fn,{}) or {};a=o if isinstance(o,list) else next((o.get(k) for k in keys if isinstance(o.get(k),list)),[]);reports += [(r,typ) for r in a if isinstance(r,dict)]
 for r,typ in reports:
  source=ev(r)
  if not source:continue
  t=text(r);hits=[]
  for c,(lat,lng) in COUNTRIES.items():
   if re.search(r'(?<![a-z])'+re.escape(c.lower())+r'(?![a-z])',t):hits.append(add(c,'country',source,2,{'country':c,'lat':lat,'lng':lng,'clusterKey':'country:'+c,'canonical':True}))
  for cartel,country in CARTELS.items():
   if re.search(r'(?<![a-z])'+re.escape(cartel.lower())+r'(?![a-z])',t):
    lat,lng=COUNTRIES[country];hits.append(add(cartel,'cartel',source,7,{'country':country,'lat':lat,'lng':lng,'group':'Organized Crime','canonical':True}))
  for g,terms in ECONOMIC.items():
   if any(x in t for x in terms):hits.append(add(g,'economic',source,3,{'group':'Economic Factor','canonical':True}))
  for c,terms in CONFLICTS.items():
   if any(x in t for x in terms):hits.append(add(c,'conflict',source,3,{'group':'Major Conflict','canonical':True}))
  for c,terms in CHOKEPOINTS.items():
   if any(x in t for x in terms):hits.append(add(c,'chokepoint',source,3,{'group':'Strategic Chokepoint','canonical':True}))
  hits=[x for x in dict.fromkeys(hits) if x]
  for i,a in enumerate(hits):
   for b in hits[i+1:]:link(a,b,'These major intelligence entities/factors are co-mentioned in the same sourced record.',source,typ)
 market=snap.get('marketData') or {};market_sources=[]
 for q in market.get('indicators') or []:
  if isinstance(q,dict) and q.get('price') is not None:market_sources.append({'title':str(q.get('name') or q.get('symbol') or 'Market indicator'),'url':str(q.get('sourceUrl') or q.get('url') or ''),'source':str(q.get('source') or 'Yahoo Finance public market feed'),'time':str(q.get('marketTime') or q.get('updatedAt') or '')})
 if market_sources:
  mid=add('Markets','economic',market_sources[0],4,{'group':'Economic Factor','canonical':True,'marketIndicators':len(market_sources)})
  if mid:
   for x in market_sources[1:]:
    if not any(y.get('title')==x.get('title') and y.get('url')==x.get('url') for y in nodes[mid]['evidence']):nodes[mid]['evidence'].append(x)
 quotas={'cartel':18,'country':8,'economic':6,'conflict':2,'chokepoint':1};chosen=[]
 for kind in ('cartel','country','economic','conflict','chokepoint'):
  pool=[n for n in nodes.values() if n['kind']==kind];pool.sort(key=lambda n:(n['score'],len(n['evidence']),n['mentions']),reverse=True);chosen.extend(pool[:quotas[kind]])
 chosen=chosen[:MAX_NODES];keep={n['id'] for n in chosen};edges=[]
 for k,r in rels.items():
  a,b=k.split('|',1)
  if a in keep and b in keep and r['evidence']:edges.append({'source':a,'target':b,'weight':r['weight'],'types':sorted(r['types']),'relationship':r['relationship'],'evidence':r['evidence'],'evidenceCount':len(r['evidence'])})
 edges.sort(key=lambda e:(e['evidenceCount'],e['weight']),reverse=True)
 now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z');stats={'nodes':len(chosen),'edges':len(edges),'newsRecords':sum(t=='news' for _,t in reports),'conflictRecords':sum(t=='conflict' for _,t in reports),'marketIndicators':len(market.get('indicators') or []),'sourceBackedCandidates':len(nodes),'cartelNodes':sum(n['kind']=='cartel' for n in chosen),'countryNodes':sum(n['kind']=='country' for n in chosen),'economicNodes':sum(n['kind']=='economic' for n in chosen),'conflictNodes':sum(n['kind']=='conflict' for n in chosen),'chokepointNodes':sum(n['kind']=='chokepoint' for n in chosen)}
 payload={'version':9,'updatedAt':now,'complete':True,'sourceBackedOnly':True,'consolidated':True,'maxNodes':MAX_NODES,'nodePolicy':'Only major canonical nodes: countries, major cartels/organizations, core economic factors, a few major conflicts and strategic chokepoints. Raw records remain evidence upstream. No source means no node.','sourceArtifacts':['snapshot.json','intelligence_graph.json','event_intelligence.json','claims.json','intelligence_assessment.json','event_market_impact.json','what_changed.json'],'method':'Compact human-facing intelligence graph. One node aggregates many underlying reports, map observations, claims and market observations.','caution':'Relationships are contextual evidence links and do not prove causation, coordination, intent or responsibility. Market links are context only.','nodes':chosen,'edges':edges,'stats':stats}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8');print(f'INTELLIGENCE BRAIN: {len(chosen)} major nodes / {len(edges)} relationships / {len(nodes)} sourced candidates')
if __name__=='__main__':main()
