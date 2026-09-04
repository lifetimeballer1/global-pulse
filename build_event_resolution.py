#!/usr/bin/env python3
"""Resolve near-duplicate live reports into stronger event clusters.

This is deterministic, explainable clustering: normalized title tokens, entity/location
signals, and publication-time proximity are combined. It never claims two reports are
independent merely because they have different URLs.
"""
import json, re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVENTS = ROOT / "data/live_events.json"
OUT = ROOT / "data/event_resolution.json"

STOP = {"the","a","an","and","or","of","to","in","on","for","with","from","after","before","as","is","are","at","by","new","latest","report","reports"}

def tokens(text):
    return {x for x in re.findall(r"[a-z0-9]{3,}", (text or "").lower()) if x not in STOP}

def dt(v):
    if not v: return None
    try: return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception: return None

def similarity(a,b):
    ta,tb=tokens(a.get("title")),tokens(b.get("title"))
    if not ta or not tb: return 0.0
    j=len(ta&tb)/len(ta|tb)
    ea=set(a.get("entities") or []) & set(b.get("entities") or [])
    la=set(a.get("locations") or []) & set(b.get("locations") or [])
    # Entity/location agreement can rescue differently worded headlines.
    bonus=min(0.35, .12*len(ea)+.15*len(la))
    da,db=dt(a.get("published_at")),dt(b.get("published_at"))
    time_bonus=0
    if da and db:
        minutes=abs((da-db).total_seconds())/60
        if minutes <= 90: time_bonus=.12
        elif minutes <= 240: time_bonus=.06
    return min(1.0,j*.65+bonus+time_bonus)

def main():
    data=json.loads(EVENTS.read_text()) if EVENTS.exists() else {"events":[]}
    events=data.get("events", data if isinstance(data,list) else [])
    resolved=[]; used=set()
    for i,e in enumerate(events):
        if i in used: continue
        cluster=[i]; used.add(i)
        for j in range(i+1,len(events)):
            if j in used: continue
            score=similarity(e, events[j])
            if score >= .62:
                cluster.append(j); used.add(j)
        members=[events[k] for k in cluster]
        domains=[]
        for m in members:
            d=(m.get("source_domain") or m.get("domain") or "").lower()
            if d: domains.append(d)
        resolved.append({
            "resolution_id": f"ER-{len(resolved)+1:04d}",
            "event_ids": [m.get("id") or m.get("event_id") for m in members],
            "report_count": len(members),
            "unique_domains": sorted(set(domains)),
            "merge_reason": "shared title/entity/location/time signals" if len(members)>1 else "single event candidate",
            "confidence": "high" if len(members)>=3 else "moderate" if len(members)==2 else "low",
        })
    out={"generated_at":datetime.now(timezone.utc).isoformat(),"method":"explainable similarity clustering","events":resolved}
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(f"resolved {len(resolved)} event groups")

if __name__ == "__main__": main()
