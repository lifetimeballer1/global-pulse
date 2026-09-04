#!/usr/bin/env python3
"""Build transparent event intelligence from live events and public reports.
No API key required. Corroboration discounts near-identical headlines and
separates raw report count from distinct reporting groups.
"""
from __future__ import annotations
import json,re,hashlib
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; EVENTS=DATA/'live_events.json'; SNAP=DATA/'snapshot.json'; OUT=DATA/'event_intelligence.json'
STOP=set('the a an and or of to in on for from with by as at is are was were has have had this that report reports reported says said after before over into near amid during its their his her'.split())
COUNTRIES={'afghanistan','algeria','angola','argentina','armenia','australia','azerbaijan','belarus','belgium','benin','bolivia','brazil','burkina faso','burundi','cameroon','canada','chad','chile','china','colombia','croatia','cuba','cyprus','denmark','egypt','eritrea','estonia','ethiopia','finland','france','georgia','germany','ghana','greece','guatemala','guinea','haiti','honduras','hungary','india','indonesia','iran','iraq','ireland','israel','italy','japan','jordan','kazakhstan','kenya','kosovo','lebanon','libya','lithuania','malaysia','mali','mexico','moldova','mongolia','morocco','mozambique','myanmar','nato','nepal','netherlands','niger','nigeria','north korea','norway','pakistan','peru','philippines','poland','portugal','qatar','romania','russia','rwanda','saudi arabia','senegal','serbia','somalia','south africa','south sudan','spain','sri lanka','sudan','sweden','switzerland','syria','taiwan','tajikistan','tanzania','thailand','tunisia','turkey','turkmenistan','uganda','ukraine','united arab emirates','united kingdom','united states','uzbekistan','venezuela','vietnam','yemen','zambia','zimbabwe'}
REGIONS={'sahel':{'mali','burkina faso','niger','chad'},'horn of africa':{'somalia','ethiopia','eritrea','djibouti','sudan','south sudan'},'great lakes':{'drc','rwanda','burundi','uganda'},'middle east':{'iran','iraq','israel','syria','lebanon','yemen','jordan','saudi arabia','qatar','united arab emirates'},'europe':{'ukraine','russia','belarus','poland','germany','france','united kingdom'},'east asia':{'china','taiwan','japan','south korea','north korea'},'latin america':{'mexico','brazil','colombia','venezuela','peru','argentina','chile'}}

def clean(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def tokens(s):return {x for x in re.findall(r'[a-z0-9]{4,}',clean(s).lower()) if x not in STOP}
def domain(url):
 try:return urlparse(str(url or '')).netloc.lower().removeprefix('www.')
 except:return ''
def report_url(r):
 credit=r.get('credit') or {}
 if isinstance(credit,str):
  try:credit=json.loads(credit)
  except Exception:credit={}
 return str(r.get('original_link') or r.get('url') or r.get('link') or credit.get('url') or credit.get('sourceUrl') or '')
def source_identity(r):
 d=domain(report_url(r))
 if d:return 'domain:'+d
 credit=r.get('credit') or {}
 if isinstance(credit,str):
  try:credit=json.loads(credit)
  except Exception:credit={}
 return 'source:'+str(credit.get('sourceId') or r.get('sourceLabel') or r.get('source_name') or '')
def candidates(text):
 low=clean(text).lower();found=[]
 for c in sorted(COUNTRIES,key=len,reverse=True):
  if re.search(r'(?<![a-z])'+re.escape(c)+r'(?![a-z])',low):found.append(c)
 return found[:8]
def region_hits(entities):
 out=[]
 for region,members in REGIONS.items():
  hits=sorted(set(entities)&members)
  if hits:out.append({'region':region,'entities':hits})
 return out
def reporting_groups(reports):
 groups=[]
 for r in reports:
  ts=tokens(r.get('title') or r.get('name'))
  if not ts:continue
  placed=False
  for g in groups:
   if len(ts&g['tokens'])/max(1,len(ts|g['tokens']))>=.82:
    g['reports'].append(r);g['tokens']|=ts;placed=True;break
  if not placed:groups.append({'tokens':ts,'reports':[r]})
 return groups

def main():
 ev=json.loads(EVENTS.read_text(encoding='utf-8')) if EVENTS.exists() else {'events':[]}; snap=json.loads(SNAP.read_text(encoding='utf-8')) if SNAP.exists() else {'stories':[]}; output=[]
 for e in ev.get('events',[]):
  if not isinstance(e,dict):continue
  reports=[r for r in e.get('reports',[]) if isinstance(r,dict)]
  text=' '.join([clean(e.get('title'))]+[clean(r.get('title') or r.get('name')) for r in reports]);entities=candidates(text)
  domains=[];times=[];urls=[]
  for r in reports:
   u=report_url(r);d=domain(u)
   if d:domains.append(d)
   if u:urls.append(u)
   t=clean(r.get('publishedAt') or r.get('published_date') or r.get('time'))
   if t:times.append(t)
  counts=Counter(domains);unique_domains=sorted(counts);groups=reporting_groups(reports);group_count=len(groups);concentration=max(counts.values(),default=0)/max(1,len(domains));
  if len(unique_domains)>=4 and group_count>=3 and concentration<=.6:source_independence='stronger'
  elif len(unique_domains)>=2 or group_count>=2:source_independence='mixed'
  else:source_independence='limited'
  corroboration_score=min(100,round(35+15*min(len(unique_domains),4)+12*min(group_count,4)+10*min(len(reports),6)-20*max(0,concentration-.5)))
  regions=region_hits(entities);spill=[]
  for rg in regions:
   for member in rg['entities']:spill.extend(sorted(REGIONS[rg['region']]-{member}))
  spill=list(dict.fromkeys(spill))[:8];timeline=sorted([{'time':t,'type':'report'} for t in times],key=lambda x:x['time'])[-8:];confidence=e.get('confidence','low');caveats=[]
  if len(unique_domains)<3:caveats.append('Limited source diversity')
  if concentration>.5:caveats.append('One domain supplies most observed reports')
  if group_count<2 and len(reports)>1:caveats.append('Multiple reports may not represent independent reporting')
  caveats.append('Entity and spillover links are rule-based candidates, not verified causal relationships')
  output.append({'eventId':e.get('id'),'title':e.get('title'),'category':e.get('category'),'confidence':confidence,'reportCount':len(reports),'uniqueSourceDomains':len(unique_domains),'independentReportingGroups':group_count,'corroborationScore':corroboration_score,'sourceIndependence':source_independence,'sourceDomains':unique_domains[:8],'entityCandidates':entities,'regionalContext':regions,'spilloverCandidates':spill,'timeline':timeline,'sourceBreakdown':dict(counts.most_common(8)),'evidenceUrls':urls[:8],'caveats':caveats})
 output.sort(key=lambda x:(x['corroborationScore'],x['reportCount']),reverse=True);payload={'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'method':'rule-based event enrichment with source-domain diversity, near-identical headline grouping, and corroboration scoring','disclaimer':'Corroboration scores are monitoring aids, not truth probabilities. Domain diversity is not proof of independence.','events':output[:80]};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'EVENT INTELLIGENCE: {len(payload["events"])} events enriched')
if __name__=='__main__':main()
