#!/usr/bin/env python3
"""Build source-diversity evidence metrics from current public reporting.
No API key required. Counts unique domains and reporting-chain diversity; it does not
assume that different domains are independent when they may share a wire report.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'

def load(name, default):
    try: return json.loads((DATA/name).read_text(encoding='utf-8'))
    except Exception: return default

def domain(url):
    try: return urlparse(str(url or '')).netloc.lower().removeprefix('www.')
    except Exception: return ''

def text(r):
    return ' '.join(str(r.get(k) or '') for k in ('title','name','summary','description')).strip()

def main():
    snap=load('snapshot.json',{})
    breaking=load('breaking_news.json',{})
    events=load('live_events.json',{})
    reports=[x for x in (snap.get('stories') or snap.get('articles') or []) if isinstance(x,dict)]
    reports += [x for x in (breaking.get('articles') or []) if isinstance(x,dict)]
    unique={}
    for r in reports:
        u=str(r.get('original_link') or r.get('url') or r.get('link') or '').strip()
        key=u or hashlib.sha1(text(r).lower().encode()).hexdigest()
        unique[key]=r
    reports=list(unique.values())
    counts=Counter(); by_domain=defaultdict(list)
    for r in reports:
        d=domain(r.get('original_link') or r.get('url') or r.get('link'))
        if d:
            counts[d]+=1; by_domain[d].append(r)
    top=[{'domain':d,'reportCount':n} for d,n in counts.most_common(40)]
    event_metrics=[]
    for e in (events.get('events') or [])[:80]:
        ds=[]
        for r in e.get('reports') or []:
            d=domain(r.get('original_link') or r.get('url') or r.get('link'))
            if d and d not in ds: ds.append(d)
        n=len(ds)
        independence='high' if n>=4 else 'moderate' if n>=2 else 'low'
        event_metrics.append({'eventId':e.get('id'),'title':e.get('title'),'uniqueDomains':n,'domains':ds[:10],'independence':independence,'note':'Domain diversity is a proxy, not proof of independent reporting.'})
    out={'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'method':'Unique-domain diversity proxy across current reports and clustered live events. Shared wire stories may still create apparent diversity.','uniqueReportCount':len(reports),'uniqueSourceDomains':len(counts),'topSources':top,'eventSourceEvidence':event_metrics}
    (DATA/'source_evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'SOURCE EVIDENCE: {len(reports)} reports / {len(counts)} unique domains')

if __name__=='__main__': main()
