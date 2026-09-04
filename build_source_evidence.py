#!/usr/bin/env python3
"""Build transparent corroboration metrics from current public reporting.
No API key required. Domain diversity is preferred; source IDs are used only
when a report does not expose a URL, and shared-wire duplication is discounted.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'

def load(name, default):
    try:return json.loads((DATA/name).read_text(encoding='utf-8'))
    except Exception:return default

def domain(url):
    try:return urlparse(str(url or '')).netloc.lower().removeprefix('www.')
    except Exception:return ''

def source_id(r):
    credit=r.get('credit') or {}
    if isinstance(credit,str):
        try:credit=json.loads(credit)
        except Exception:credit={}
    return str(credit.get('sourceId') or r.get('sourceLabel') or r.get('source_name') or r.get('source') or '')

def report_url(r):
    credit=r.get('credit') or {}
    if isinstance(credit,str):
        try:credit=json.loads(credit)
        except Exception:credit={}
    return str(r.get('original_link') or r.get('url') or r.get('link') or credit.get('url') or credit.get('sourceUrl') or '')

def identity(r):
    d=domain(report_url(r))
    return ('domain:'+d) if d else ('source:'+source_id(r))

def title_key(r):
    t=re.sub(r'[^a-z0-9 ]+',' ',str(r.get('title') or r.get('name') or '').lower())
    return re.sub(r'\s+',' ',t).strip()

def text(r):return ' '.join(str(r.get(k) or '') for k in ('title','name','summary','description')).strip()

def independent_groups(reports):
    """Cluster near-identical headlines so copies do not count as separate corroboration."""
    groups=[]
    for r in reports:
        tokens=set(re.findall(r'[a-z0-9]{4,}',title_key(r)))
        if not tokens:continue
        placed=False
        for g in groups:
            gt=g['tokens']; j=len(tokens & gt)/max(1,len(tokens | gt))
            if j>=.82:
                g['reports'].append(r);g['tokens']|=tokens;placed=True;break
        if not placed:groups.append({'tokens':tokens,'reports':[r]})
    return groups

def main():
    snap=load('snapshot.json',{});breaking=load('breaking_news.json',{});events=load('live_events.json',{})
    reports=[x for x in (snap.get('stories') or snap.get('articles') or []) if isinstance(x,dict)]
    reports += [x for x in (breaking.get('articles') or []) if isinstance(x,dict)]
    unique={}
    for r in reports:
        u=report_url(r);key=u or hashlib.sha1(text(r).lower().encode()).hexdigest();unique[key]=r
    reports=list(unique.values());counts=Counter();by_identity=defaultdict(list)
    for r in reports:
        ident=identity(r)
        if ident:counts[ident]+=1;by_identity[ident].append(r)
    top=[{'source':d,'reportCount':n} for d,n in counts.most_common(40)]
    event_metrics=[]
    for e in (events.get('events') or [])[:80]:
        rs=[r for r in e.get('reports') or [] if isinstance(r,dict)]
        ids=[]
        for r in rs:
            ident=identity(r)
            if ident and ident not in ids:ids.append(ident)
        groups=independent_groups(rs)
        independent=len(groups)
        unique_domains=sorted({i.removeprefix('domain:') for i in ids if i.startswith('domain:')})
        domain_count=len(unique_domains)
        if domain_count>=4 and independent>=3:independence='high'
        elif domain_count>=2 or independent>=2:independence='moderate'
        else:independence='low'
        event_metrics.append({'eventId':e.get('id'),'title':e.get('title'),'reportCount':len(rs),'uniqueDomains':domain_count,'sourceIdentities':ids[:10],'independentReportingGroups':independent,'domains':unique_domains[:10],'independence':independence,'note':'Near-identical headlines are grouped; domain diversity is a proxy, not proof of independent reporting.'})
    out={'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'method':'URL/domain diversity with source-ID fallback and near-identical headline grouping. Shared wire stories are discounted as one reporting group.','uniqueReportCount':len(reports),'uniqueSourceDomains':len({x.removeprefix('domain:') for x in counts if x.startswith('domain:')}),'topSources':top,'eventSourceEvidence':event_metrics}
    (DATA/'source_evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'SOURCE EVIDENCE: {len(reports)} reports / {out["uniqueSourceDomains"]} domains / corroboration groups calculated')

if __name__=='__main__':main()
