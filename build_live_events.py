#!/usr/bin/env python3
"""Cluster recent public reports into deduplicated live events.
No API key required; consumes the existing snapshot and rapid open-data layer."""
from __future__ import annotations
import json,re,hashlib
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; SNAP=DATA/'snapshot.json'; RAPID=DATA/'breaking_news.json'; OUT=DATA/'live_events.json'
STOP=set('the a an and or of to in on for from with by as at is are was were has have had this that report reports reported says said after before over into near amid during its their his her'.split())
KEYWORDS={'conflict':{'attack','airstrike','missile','bomb','bombing','strike','war','fighting','invasion','clash','military','troops'},'diplomatic':{'nato','ceasefire','talks','summit','diplomatic','sanction','sanctions','agreement','negotiation'},'economic':{'tariff','trade','inflation','market','stocks','oil','crude','shipping','supply','economy','rate'},'disaster':{'earthquake','tsunami','hurricane','wildfire','flood','volcano','storm'},'political':{'election','president','parliament','congress','coup','government'}}
def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def tokens(s): return {x for x in re.findall(r'[a-z0-9]{4,}',clean(s).lower()) if x not in STOP}
def kind(text):
 t=tokens(text); scores={k:len(t&v) for k,v in KEYWORDS.items()}; return max(scores,key=scores.get) if max(scores.values(),default=0) else 'general'
def source_domain(url):
 try:return urlparse(url).netloc.lower().removeprefix('www.')
 except:return ''
def main():
 stories=[]
 if SNAP.exists():
  d=json.loads(SNAP.read_text(encoding='utf-8')); stories += [x for x in d.get('stories',[]) if isinstance(x,dict)][:800]
 if RAPID.exists():
  d=json.loads(RAPID.read_text(encoding='utf-8')); stories += [x for x in d.get('articles',[]) if isinstance(x,dict)][:150]
 unique={}
 for r in stories:
  title=clean(r.get('title') or r.get('name')); url=clean(r.get('original_link') or r.get('url') or r.get('link'))
  if not title: continue
  key=url or hashlib.sha1(title.lower().encode()).hexdigest(); unique[key]=r
 reports=list(unique.values())
 clusters=[]
 for r in reports:
  title=clean(r.get('title') or r.get('name')); ts=tokens(title); placed=False
  for c in clusters:
   if ts and len(ts & c['tokens'])/max(1,len(ts|c['tokens'])) >= .38 and kind(title)==c['kind']:
    c['reports'].append(r); c['tokens'] |= ts; placed=True; break
  if not placed: clusters.append({'tokens':ts,'kind':kind(title),'reports':[r]})
 events=[]
 for c in clusters:
  rs=c['reports']; rs.sort(key=lambda x:str(x.get('publishedAt') or x.get('published_date') or x.get('time') or ''),reverse=True)
  lead=clean(rs[0].get('title') or rs[0].get('name'))
  domains=[]; links=[]; seen=set()
  for r in rs:
   u=clean(r.get('original_link') or r.get('url') or r.get('link')); dom=source_domain(u)
   if dom and dom not in domains: domains.append(dom)
   if u and u not in seen: seen.add(u); links.append(u)
  confidence='high' if len(domains)>=3 else 'moderate' if len(domains)>=2 else 'low'
  events.append({'id':hashlib.sha1((lead.lower()+c['kind']).encode()).hexdigest()[:16],'title':lead,'category':c['kind'],'confidence':confidence,'reportCount':len(rs),'sourceCount':len(domains),'sources':domains[:8],'firstSeen':min([str(x.get('publishedAt') or x.get('published_date') or '') for x in rs if x.get('publishedAt') or x.get('published_date')] or ['']),'lastSeen':max([str(x.get('publishedAt') or x.get('published_date') or '') for x in rs if x.get('publishedAt') or x.get('published_date')] or ['']),'urls':links[:8],'reports':rs[:8]})
 events.sort(key=lambda e:(e['reportCount'],e['sourceCount'],e['lastSeen']),reverse=True)
 payload={'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'window':'recent public reporting','method':'title-token clustering with category agreement; not a claim that reports describe identical facts','events':events[:80]}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'LIVE EVENTS: {len(payload["events"])} clusters from {len(reports)} unique reports')
if __name__=='__main__': main()
