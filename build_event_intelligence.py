#!/usr/bin/env python3
"""Build a transparent event-intelligence layer from live events and snapshot reports.
No API key required. Produces evidence counts, entity candidates, timeline points,
regional spillover hints, and explicit confidence limitations.
"""
from __future__ import annotations
import json,re,hashlib
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'
EVENTS=DATA/'live_events.json'; SNAP=DATA/'snapshot.json'; OUT=DATA/'event_intelligence.json'
STOP=set('the a an and or of to in on for from with by as at is are was were has have had this that report reports reported says said after before over into near amid during its their his her'.split())
COUNTRIES={'afghanistan','algeria','angola','argentina','armenia','australia','azerbaijan','belarus','belgium','benin','bolivia','brazil','burkina faso','burundi','cameroon','canada','chad','chile','china','colombia','croatia','cuba','cyprus','denmark','drc','egypt','eritrea','estonia','ethiopia','finland','france','georgia','germany','ghana','greece','guatemala','guinea','haiti','honduras','hungary','india','indonesia','iran','iraq','ireland','israel','italy','japan','jordan','kazakhstan','kenya','kosovo','lebanon','libya','lithuania','malaysia','mali','mexico','moldova','mongolia','morocco','mozambique','myanmar','nato','nepal','netherlands','niger','nigeria','north korea','norway','pakistan','peru','philippines','poland','portugal','qatar','romania','russia','rwanda','saudi arabia','senegal','serbia','somalia','south africa','south korea','south sudan','spain','sri lanka','sudan','sweden','switzerland','syria','taiwan','tajikistan','tanzania','thailand','tunisia','turkey','turkmenistan','uganda','ukraine','united arab emirates','united kingdom','united states','uzbekistan','venezuela','vietnam','yemen','zambia','zimbabwe'}
REGIONS={'sahel':{'mali','burkina faso','niger','chad'},'horn of africa':{'somalia','ethiopia','eritrea','djibouti','sudan','south sudan'},'great lakes':{'drc','rwanda','burundi','uganda'},'middle east':{'iran','iraq','israel','syria','lebanon','yemen','jordan','saudi arabia','qatar','united arab emirates'},'europe':{'ukraine','russia','belarus','poland','germany','france','united kingdom'},'east asia':{'china','taiwan','japan','south korea','north korea'},'latin america':{'mexico','brazil','colombia','venezuela','peru','argentina','chile'}}

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def tokens(s): return {x for x in re.findall(r'[a-z0-9]{4,}',clean(s).lower()) if x not in STOP}
def domain(url):
 try:return urlparse(url).netloc.lower().removeprefix('www.')
 except:return ''
def candidates(text):
 low=clean(text).lower(); found=[]
 for c in sorted(COUNTRIES,key=len,reverse=True):
  if re.search(r'(?<![a-z])'+re.escape(c)+r'(?![a-z])',low): found.append(c)
 return found[:8]
def region_hits(entities):
 out=[]
 for region,members in REGIONS.items():
  hits=sorted(set(entities)&members)
  if hits: out.append({'region':region,'entities':hits})
 return out

def main():
 ev=json.loads(EVENTS.read_text(encoding='utf-8')) if EVENTS.exists() else {'events':[]}
 snap=json.loads(SNAP.read_text(encoding='utf-8')) if SNAP.exists() else {'stories':[]}
 story_by_url={}
 for r in snap.get('stories',[]):
  if isinstance(r,dict):
   u=clean(r.get('original_link') or r.get('url') or r.get('link'))
   if u: story_by_url[u]=r
 output=[]
 for e in ev.get('events',[]):
  if not isinstance(e,dict): continue
  reports=[r for r in e.get('reports',[]) if isinstance(r,dict)]
  text=' '.join([clean(e.get('title'))]+[clean(r.get('title') or r.get('name')) for r in reports])
  entities=candidates(text)
  domains=[]; times=[]; urls=[]
  for r in reports:
   u=clean(r.get('original_link') or r.get('url') or r.get('link'))
   d=domain(u)
   if d: domains.append(d)
   if u: urls.append(u)
   t=clean(r.get('publishedAt') or r.get('published_date') or r.get('time'))
   if t: times.append(t)
  counts=Counter(domains)
  unique_domains=sorted(counts)
  concentration=max(counts.values(),default=0)/max(1,len(domains))
  source_independence='stronger' if len(unique_domains)>=4 and concentration<=.5 else 'mixed' if len(unique_domains)>=2 else 'limited'
  regions=region_hits(entities)
  spill=[]
  for rg in regions:
   for member in rg['entities']:
    spill.extend(sorted(REGIONS[rg['region']]-{member}))
  spill=list(dict.fromkeys(spill))[:8]
  timeline=sorted([{'time':t,'type':'report'} for t in times],key=lambda x:x['time'])[-8:]
  confidence=e.get('confidence','low')
  caveats=[]
  if len(unique_domains)<3: caveats.append('Limited source diversity')
  if concentration>.5: caveats.append('One domain supplies most observed reports')
  caveats.append('Entity and spillover links are rule-based candidates, not verified causal relationships')
  output.append({'eventId':e.get('id'),'title':e.get('title'),'category':e.get('category'),'confidence':confidence,'reportCount':len(reports),'uniqueSourceDomains':len(unique_domains),'sourceIndependence':source_independence,'sourceDomains':unique_domains[:8],'entityCandidates':entities,'regionalContext':regions,'spilloverCandidates':spill,'timeline':timeline,'sourceBreakdown':dict(counts.most_common(8)),'evidenceUrls':urls[:8],'caveats':caveats})
 output.sort(key=lambda x:(x['reportCount'],x['uniqueSourceDomains']),reverse=True)
 payload={'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'method':'rule-based event enrichment from existing public-report artifacts','disclaimer':'Candidates and relationships require human/source verification; source-domain diversity is not proof of independence.','events':output[:80]}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'EVENT INTELLIGENCE: {len(payload["events"])} events enriched')
if __name__=='__main__': main()
