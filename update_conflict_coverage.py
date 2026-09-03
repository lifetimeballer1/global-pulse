#!/usr/bin/env python3
"""Build evidence-driven conflict coverage and enrich the map with public OSINT feeds.

Sources used here are public, machine-readable feeds that do not require a user API key:
- Global Pulse's already-collected news/snapshot
- GDELT GEO 2.0 public endpoint (near-real-time geolocated news/event signals)
- Liveuamap RSS endpoints when publicly reachable

GeoConfirmed is intentionally NOT scraped or bypassed: its public site currently
blocks automated retrieval, and no documented public API/export was found. We keep
it as a manual/reference source until a permitted machine-readable feed is available.

External-source failures are non-fatal so one unavailable OSINT map cannot break the
Global Pulse refresh. Imported points are marked with source provenance and confidence.
"""
import json, re, time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"
USER_AGENT = "GlobalPulse/1.0 (+https://github.com/lifetimeballer1/global-pulse)"

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

STRONG = re.compile(r"\b(airstrike|air strike|bombing|missile|rocket|killed|dead|attack|clash|fighting|offensive|ambush|massacre|kidnap|kidnapping|gang|cartel|militia|insurgent|terrorist|raid|shooting|violence|battle|siege|explosion|drone)\b", re.I)
NEGATE = re.compile(r"\b(historical|history of|anniversary|documentary|book review|explainer|what is|how to|vacation|travel|recipe|sport|movie|music)\b", re.I)

# Public Liveuamap feeds. They are treated as discovery/evidence, not authoritative truth.
LIVEUAMAP_FEEDS = [
    "https://liveuamap.com/rss",
    "https://sudan.liveuamap.com/rss",
    "https://iran.liveuamap.com/rss",
    "https://caucasus.liveuamap.com/rss",
]


def text_of(a):
    return " ".join(str(a.get(k) or "") for k in ("title","summary","summary_snippet","description","text","detail"))


def domain(a):
    try:
        return (urlparse(str(a.get("url") or "")).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def fetch_bytes(url, timeout=15):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, application/json, text/xml, */*"})
    with urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_gdelt_points():
    """Pull public GDELT GEO point signals from the last 24 hours."""
    queries = [
        "conflict OR attack OR fighting OR airstrike OR bombing",
        "missile OR rocket OR explosion OR shooting OR clash",
    ]
    points = []
    for q in queries:
        url = "https://api.gdeltproject.org/api/v2/geo/geo"
        params = "?query=" + __import__('urllib.parse').parse.quote(q) + "&mode=PointData&format=GeoJSON&timespan=1d&maxrecords=250"
        try:
            raw = fetch_bytes(url + params, timeout=20)
            obj = json.loads(raw.decode("utf-8", errors="replace"))
            for f in obj.get("features", []):
                coords = (f.get("geometry") or {}).get("coordinates") or []
                if len(coords) < 2: continue
                try: lng, lat = float(coords[0]), float(coords[1])
                except (TypeError, ValueError): continue
                if not (-90 <= lat <= 90 and -180 <= lng <= 180): continue
                p = f.get("properties") or {}
                title = str(p.get("name") or p.get("html") or p.get("description") or "GDELT geolocated signal")
                href = str(p.get("url") or p.get("shareimage") or "")
                points.append({
                    "lat": lat, "lng": lng, "title": title[:180], "url": href,
                    "source": "GDELT GEO", "sourceDomain": "gdeltproject.org",
                    "eventType": "OSINT/GEO", "observedAt": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as exc:
            print(f"GDELT GEO unavailable for query {q!r}: {exc}")
    # De-duplicate close-ish exact points and URLs; keep the newest/first signal.
    out, seen = [], set()
    for p in points:
        key = (round(p["lat"], 3), round(p["lng"], 3), p["url"])
        if key in seen: continue
        seen.add(key); out.append(p)
    return out[:350]


def fetch_liveuamap_rss():
    """Read public RSS feeds when available; failures are intentionally non-fatal."""
    out = []
    for feed in LIVEUAMAP_FEEDS:
        try:
            root = ET.fromstring(fetch_bytes(feed, timeout=12))
            for item in root.findall(".//item")[:100]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = (item.findtext("pubDate") or "").strip()
                if not title or not link: continue
                out.append({"title": title, "url": link, "published": pub, "source": "Liveuamap", "sourceDomain": urlparse(feed).hostname or "liveuamap.com"})
        except Exception as exc:
            print(f"Liveuamap feed unavailable: {feed}: {exc}")
    return out


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
            if not matched or not STRONG.search(txt): continue
            hits.append({"title":a.get("title"),"source":a.get("source") or a.get("credit_metadata") or "Unknown","url":a.get("url"),"time":a.get("published_date") or a.get("published") or a.get("time"),"matchedTerms":matched[:4]})
            d=domain(a)
            if d: domains.add(d)
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

    # Enrich with public OSINT map feeds.
    gdelt = fetch_gdelt_points()
    liveuamap = fetch_liveuamap_rss()
    osint = {"version":1,"updatedAt":datetime.now(timezone.utc).isoformat(),"sources":[
        {"name":"GDELT GEO","status":"online" if gdelt else "unavailable","points":len(gdelt),"cadence":"near-real-time","url":"https://www.gdeltproject.org/"},
        {"name":"Liveuamap RSS","status":"online" if liveuamap else "unavailable","stories":len(liveuamap),"cadence":"near-real-time when feed is reachable","url":"https://liveuamap.com/"},
        {"name":"GeoConfirmed","status":"reference-only","reason":"No documented public machine-readable export/API located; automated access to the public map is blocked. No scraping bypass used.","cadence":"manual/reference"},
    ],"gdeltPoints":gdelt,"liveuamapStories":liveuamap[:300]}
    snap["osintMaps"]=osint

    base=[m for m in (snap.get("markers") or []) if m.get("layer") not in ("conflict-coverage","osint-gdelt")]
    for x in out:
        if x["articleCount"]<1: continue
        base.append({"lat":x["lat"],"lng":x["lng"],"type":"conflict-coverage","layer":"conflict-coverage","importance":2 if x["status"] in ("CORROBORATED","MULTI-SOURCE") else 1,"title":x["title"],"detail":f"{x['status']} | {x['articleCount']} current reports | {len(x['sourceDomains'])} independent domains | Evidence-linked monitoring","url":(x["evidence"][0].get("url") if x["evidence"] else ""),"sourceUrl":(x["evidence"][0].get("url") if x["evidence"] else ""),"source":"Global Pulse evidence-driven coverage","eventType":x["type"],"confidence":x["status"]})

    # Add bounded GDELT points as a separate, visibly attributable OSINT layer.
    for p in gdelt:
        base.append({"lat":p["lat"],"lng":p["lng"],"type":"osint-gdelt","layer":"osint-gdelt","importance":1,"title":p["title"],"detail":"GDELT GEO geolocated news/event signal; approximate geography","url":p["url"],"sourceUrl":p["url"],"source":"GDELT GEO","eventType":"OSINT/GEO","confidence":"OSINT"})

    snap["markers"]=base
    snap["conflictCoverage"]={"version":2,"updatedAt":datetime.now(timezone.utc).isoformat(),"method":"Current snapshot reporting + independent source-domain corroboration + public OSINT map enrichment.","watchlist":out}
    changes=snap.get("changes") or []
    changes.insert(0,{"kind":"system","title":"OSINT map enrichment refreshed","detail":f"GDELT GEO added {len(gdelt)} geolocated signals; Liveuamap RSS returned {len(liveuamap)} stories; GeoConfirmed remains reference-only until a permitted public data export is available."})
    snap["changes"]=changes[:8]
    SNAP.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    active=sum(1 for x in out if x["articleCount"])
    print(f"Conflict coverage: {active}/{len(out)} theaters have current evidence")
    print(f"OSINT enrichment: {len(gdelt)} GDELT points, {len(liveuamap)} Liveuamap RSS stories")

if __name__=="__main__": main()
