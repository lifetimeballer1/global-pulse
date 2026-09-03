#!/usr/bin/env python3
"""Add evidence-driven coverage for underrepresented conflict/crime theaters.

No API key required. Uses the already-collected snapshot stories and only promotes
a theater when current reporting contains geographically specific evidence.
This intentionally adds a separate conflictCoverage layer instead of inventing
active incidents or inflating the existing conflict count.
"""
import json, re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"

WATCHES = [
    ("haiti-criminal-violence", "Haiti Criminal Violence", "Americas", "CRIME/SECURITY", (18.5944,-72.3074), ["haiti","port-au-prince","gangs","g9","viv ansanm"]),
    ("mexico-cartel-violence", "Mexico Cartel Violence", "Americas", "ORGANIZED CRIME", (23.6345,-102.5528), ["mexico","mexican cartel","sinaloa cartel","cjng","jalisco new generation","cartel violence"]),
    ("ecuador-security", "Ecuador Security Crisis", "Americas", "ORGANIZED CRIME", (-1.8312,-78.1834), ["ecuador","ecuadorian","guayaquil","los choneros","los lobos","drug gang"]),
    ("colombia-armed-groups", "Colombia Armed Groups", "Americas", "INSURGENCY/CRIME", (4.5709,-74.2973), ["colombia","colombian","eln","farc dissident","clan del golfo","armed groups"]),
    ("venezuela-security", "Venezuela Security / Political Crisis", "Americas", "POLITICAL/SECURITY", (8.0,-66.0), ["venezuela","venezuelan","caracas","maduro","tren de aragua"]),
    ("central-america-security", "Central America Security", "Americas", "SECURITY", (14.1,-88.9), ["guatemala","honduras","el salvador","central america","maras","ms-13"]),
    ("car-central-africa", "Central African Republic Conflict", "Africa", "CONFLICT", (6.6,20.9), ["central african republic","car","bangui","rebel groups","militia"]),
    ("nigeria-northwest", "Nigeria Insurgency / Banditry", "Africa", "INSURGENCY", (10.0,8.0), ["nigeria","nigerian","boko haram","iswap","bandit","banditry"]),
    ("mozambique-cabo-delgado", "Mozambique Cabo Delgado", "Africa", "INSURGENCY", (-12.5,40.0), ["mozambique","cabo delgado","mocimboa","insurgents","islamic state mozambique"]),
    ("cameroon-anglophone", "Cameroon Anglophone Conflict", "Africa", "INSURGENCY", (5.96,10.15), ["cameroon","ambazonia","anglophone","separatist"]),
    ("libya-militia", "Libya Militia / Political Security", "Africa", "SECURITY", (27.0,17.0), ["libya","tripoli","benghazi","libyan militia","haftar"]),
    ("ethiopia-regional", "Ethiopia Regional Conflict Risk", "Africa", "CONFLICT", (9.145,40.4897), ["ethiopia","amhara","oromia","tigray","fano"]),
]

STRONG = re.compile(r"\b(airstrike|air strike|bombing|missile|rocket|killed|dead|attack|clash|fighting|offensive|ambush|massacre|kidnap|kidnapping|gang|cartel|militia|insurgent|terrorist|raid|shooting|violence|battle|siege)\b", re.I)
NEGATE = re.compile(r"\b(historical|history of|anniversary|documentary|book review|explainer|what is|how to|vacation|travel|recipe|sport|movie|music)\b", re.I)

def text_of(a):
    return " ".join(str(a.get(k) or "") for k in ("title","summary","summary_snippet","description","text","detail"))

def domain(a):
    try: return (urlparse(str(a.get("url") or "")).hostname or "").lower().removeprefix("www.")
    except Exception: return ""

def main():
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    stories = list(snap.get("stories") or []) + list((snap.get("liveArticles") or {}).get("articles") or [])
    out=[]
    for wid,title,region,kind,(lat,lng),terms in WATCHES:
        hits=[]; domains=set()
        for a in stories:
            txt=text_of(a).lower()
            if NEGATE.search(txt): continue
            matched=[t for t in terms if t.lower() in txt]
            if not matched: continue
            if not STRONG.search(txt): continue
            hits.append({"title":a.get("title"),"source":a.get("source") or a.get("credit_metadata") or "Unknown","url":a.get("url"),"time":a.get("published_date") or a.get("published") or a.get("time"),"matchedTerms":matched[:4]})
            d=domain(a)
            if d: domains.add(d)
        # One strong current report is enough for monitoring; 2+ domains becomes corroborated.
        unique=[]; seen=set()
        for h in sorted(hits,key=lambda x:str(x.get("time") or ""),reverse=True):
            k=str(h.get("url") or h.get("title"))
            if k in seen: continue
            seen.add(k); unique.append(h)
        unique=unique[:8]
        if not unique: status="NO CURRENT SIGNAL"
        elif len(domains)>=3: status="CORROBORATED"
        elif len(domains)>=2: status="MULTI-SOURCE"
        else: status="SINGLE-SOURCE"
        confidence=min(1.0, (len(domains)/3)*0.7 + min(len(unique),5)/5*0.3) if unique else 0
        out.append({"id":wid,"title":title,"region":region,"type":kind,"lat":lat,"lng":lng,"status":status,"confidence":round(confidence,2),"articleCount":len(unique),"sourceDomains":sorted(domains),"evidence":unique[:5],"note":"Evidence-driven monitoring coverage; this is not a claim that every matched report describes a new incident."})
    snap["conflictCoverage"]={"version":1,"updatedAt":datetime.now(timezone.utc).isoformat(),"method":"Current snapshot reporting + independent source-domain corroboration; no API key required.","watchlist":out}
    # Only add map markers when there is current evidence. Never create static active dots.
    base=[m for m in (snap.get("markers") or []) if m.get("layer")!="conflict-coverage"]
    for x in out:
        if x["articleCount"]<1: continue
        base.append({"lat":x["lat"],"lng":x["lng"],"type":"conflict-coverage","layer":"conflict-coverage","importance":2 if x["status"] in ("CORROBORATED","MULTI-SOURCE") else 1,"title":x["title"],"detail":f"{x['status']} | {x['articleCount']} current reports | {len(x['sourceDomains'])} independent domains | Evidence-linked monitoring","url":(x["evidence"][0].get("url") if x["evidence"] else ""),"sourceUrl":(x["evidence"][0].get("url") if x["evidence"] else ""),"source":"Global Pulse evidence-driven coverage","eventType":x["type"],"confidence":x["status"]})
    snap["markers"]=base
    changes=snap.get("changes") or []
    changes.insert(0,{"kind":"system","title":"Evidence-driven conflict coverage refreshed","detail":f"Monitored {len(out)} underrepresented Africa/Americas theaters; only theaters with current reporting receive map markers."})
    snap["changes"]=changes[:8]
    SNAP.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    active=sum(1 for x in out if x["articleCount"])
    print(f"Conflict coverage: {active}/{len(out)} theaters have current evidence")

if __name__=="__main__": main()
