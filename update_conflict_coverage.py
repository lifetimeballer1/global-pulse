#!/usr/bin/env python3
"""Build evidence-driven conflict coverage and geolocated public OSINT map signals.

All imported points retain provenance. Country/theater points are only created when
current reporting matches the theater. Event-area points are created only when a
current story contains a known place name; they are explicitly labelled as reported
area, not exact geolocation. External feeds are optional and failures are non-fatal.
"""
import json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"
USER_AGENT = "GlobalPulse/1.1 (+https://github.com/lifetimeballer1/global-pulse)"

WATCHES = [
    ("haiti-criminal-violence", "Haiti Criminal Violence", "Americas", "CRIME/SECURITY", (18.5944,-72.3074), ["haiti","port-au-prince","gangs","g9","viv ansanm"]),
    ("mexico-cartel-violence", "Mexico Cartel Violence", "Americas", "ORGANIZED CRIME", (23.6345,-102.5528), ["mexico","mexican cartel","sinaloa cartel","cjng","jalisco new generation","cartel violence"]),
    ("ecuador-security", "Ecuador Security Crisis", "Americas", "ORGANIZED CRIME", (-1.8312,-78.1834), ["ecuador","ecuadorian","guayaquil","los choneros","los lobos","drug gang"]),
    ("colombia-armed-groups", "Colombia Armed Groups", "Americas", "INSURGENCY/CRIME", (4.5709,-74.2973), ["colombia","colombian","eln","farc dissident","clan del golfo","armed groups"]),
    ("venezuela-security", "Venezuela Security / Political Crisis", "Americas", "POLITICAL/SECURITY", (8.0,-66.0), ["venezuela","venezuelan","caracas","maduro","tren de aragua"]),
    ("central-america-security", "Central America Security", "Americas", "SECURITY", (14.1,-88.9), ["guatemala","honduras","el salvador","central america","maras","ms-13"]),
    ("car-central-africa", "Central African Republic Conflict", "Africa", "CONFLICT", (6.6,20.9), ["central african republic","bangui","rebel groups","militia"]),
    ("nigeria-northwest", "Nigeria Insurgency / Banditry", "Africa", "INSURGENCY", (10.0,8.0), ["nigeria","nigerian","boko haram","iswap","bandit","banditry"]),
    ("mozambique-cabo-delgado", "Mozambique Cabo Delgado", "Africa", "INSURGENCY", (-12.5,40.0), ["mozambique","cabo delgado","mocimboa","insurgents","islamic state mozambique"]),
    ("cameroon-anglophone", "Cameroon Anglophone Conflict", "Africa", "INSURGENCY", (5.96,10.15), ["cameroon","ambazonia","anglophone","separatist"]),
    ("libya-militia", "Libya Militia / Political Security", "Africa", "SECURITY", (27.0,17.0), ["libya","tripoli","benghazi","libyan militia","haftar"]),
    ("ethiopia-regional", "Ethiopia Regional Conflict Risk", "Africa", "CONFLICT", (9.145,40.4897), ["ethiopia","amhara","oromia","tigray","fano"]),
]

# Known places in conflict/security theaters. These are used only when the place
# name appears in current reporting; the point means "reported area", not exact event.
PLACE_POINTS = {
    "Port-au-Prince": (18.5944,-72.3074), "Cap-Haitien": (19.7595,-72.1983),
    "Culiacan": (24.8091,-107.3940), "Tijuana": (32.5149,-117.0382), "Ciudad Juarez": (31.6904,-106.4245),
    "Reynosa": (26.0927,-98.2773), "Acapulco": (16.8531,-99.8237), "Guadalajara": (20.6597,-103.3496),
    "Guayaquil": (-2.1709,-79.9224), "Quito": (-0.1807,-78.4678), "Esmeraldas": (0.9682,-79.6517),
    "Cauca": (2.5359,-76.8258), "Cali": (3.4516,-76.5320), "Arauca": (7.0903,-70.7617), "Catatumbo": (8.2,-72.5),
    "Caracas": (10.4806,-66.9036), "Maracaibo": (10.6545,-71.6299),
    "Guatemala City": (14.6349,-90.5069), "Tegucigalpa": (14.0723,-87.1921), "San Salvador": (13.6929,-89.2182),
    "Bangui": (4.3947,18.5582), "Bambari": (5.7623,20.6672),
    "Maiduguri": (11.8333,13.1500), "Borno": (11.5,13.0), "Kaduna": (10.5105,7.4165), "Zamfara": (12.1844,6.2376),
    "Mocimboa da Praia": (-11.3467,40.3500), "Palma": (-10.7736,40.5260), "Pemba": (-12.9739,40.5178),
    "Bamenda": (5.9631,10.1591), "Buea": (4.1550,9.2310), "Kumba": (4.6363,9.4469),
    "Tripoli": (32.8872,13.1913), "Benghazi": (32.1194,20.0868), "Misrata": (32.3754,15.0925),
    "Addis Ababa": (9.0320,38.7469), "Amhara": (11.7,37.9), "Oromia": (7.9,39.1), "Tigray": (14.1,39.5),
    "Khartoum": (15.5007,32.5599), "Darfur": (13.0,25.0), "El Fasher": (13.6279,25.3494),
    "Goma": (-1.6771,29.2285), "Beni": (0.4917,29.4733), "Bukavu": (-2.5083,28.8608),
    "Mogadishu": (2.0469,45.3182), "Kismayo": (-0.3582,42.5454), "Baidoa": (3.1167,43.6500),
    "Kabul": (34.5553,69.2075), "Kandahar": (31.6289,65.7372),
    "Damascus": (33.5138,36.2765), "Aleppo": (36.2021,37.1343), "Idlib": (35.9306,36.6339),
    "Sana'a": (15.3694,44.1910), "Hodeidah": (14.7978,42.9545), "Taiz": (13.5795,44.0209),
}

STRONG = re.compile(r"\b(airstrike|air strike|bombing|missile|rocket|killed|dead|attack|clash|fighting|offensive|ambush|massacre|kidnap|kidnapping|gang|cartel|militia|insurgent|terrorist|raid|shooting|violence|battle|siege|explosion|drone|war|shelling|artillery)\b", re.I)
NEGATE = re.compile(r"\b(historical|history of|anniversary|documentary|book review|explainer|what is|how to|vacation|travel|recipe|sport|movie|music)\b", re.I)
LIVEUAMAP_FEEDS = ["https://liveuamap.com/rss","https://sudan.liveuamap.com/rss","https://iran.liveuamap.com/rss","https://caucasus.liveuamap.com/rss"]


def text_of(a):
    return " ".join(str(a.get(k) or "") for k in ("title","summary","summary_snippet","description","text","detail"))


def domain(a):
    try: return (urlparse(str(a.get("url") or "")).hostname or "").lower().removeprefix("www.")
    except Exception: return ""


def fetch_bytes(url, timeout=15):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, application/json, text/xml, */*"})
    with urlopen(req, timeout=timeout) as r: return r.read()


def fetch_gdelt_points():
    queries = ["conflict OR attack OR fighting OR airstrike OR bombing", "missile OR rocket OR explosion OR shooting OR clash"]
    points=[]
    for q in queries:
        url = "https://api.gdeltproject.org/api/v2/geo/geo?query=" + quote(q) + "&mode=PointData&format=GeoJSON&timespan=1d&maxrecords=250"
        try:
            obj=json.loads(fetch_bytes(url,timeout=20).decode("utf-8",errors="replace"))
            for f in obj.get("features",[]):
                coords=(f.get("geometry") or {}).get("coordinates") or []
                if len(coords)<2: continue
                try: lng,lat=float(coords[0]),float(coords[1])
                except (TypeError,ValueError): continue
                if not (-90<=lat<=90 and -180<=lng<=180): continue
                p=f.get("properties") or {}
                points.append({"lat":lat,"lng":lng,"title":str(p.get("name") or p.get("html") or p.get("description") or "GDELT geolocated signal")[:180],"url":str(p.get("url") or ""),"source":"GDELT GEO","sourceDomain":"gdeltproject.org","eventType":"OSINT/GEO","observedAt":datetime.now(timezone.utc).isoformat()})
        except Exception as exc: print(f"GDELT GEO unavailable for query {q!r}: {exc}")
    out=[]; seen=set()
    for p in points:
        key=(round(p["lat"],3),round(p["lng"],3),p["url"])
        if key in seen: continue
        seen.add(key); out.append(p)
    return out[:350]


def fetch_liveuamap_rss():
    out=[]
    for feed in LIVEUAMAP_FEEDS:
        try:
            root=ET.fromstring(fetch_bytes(feed,timeout=12))
            for item in root.findall(".//item")[:100]:
                title=(item.findtext("title") or "").strip(); link=(item.findtext("link") or "").strip(); pub=(item.findtext("pubDate") or "").strip()
                if title and link: out.append({"title":title,"url":link,"published":pub,"source":"Liveuamap","sourceDomain":urlparse(feed).hostname or "liveuamap.com"})
        except Exception as exc: print(f"Liveuamap feed unavailable: {feed}: {exc}")
    return out


def story_place_points(stories):
    """Create reported-area points from current stories containing known place names."""
    out=[]; seen=set()
    ordered=sorted(stories,key=lambda x:str(x.get("published_date") or x.get("published") or x.get("time") or ""),reverse=True)
    for a in ordered:
        txt=text_of(a)
        if NEGATE.search(txt) or not STRONG.search(txt): continue
        lower=txt.lower()
        for place,(lat,lng) in PLACE_POINTS.items():
            if place.lower() not in lower: continue
            url=str(a.get("url") or "")
            key=(place.lower(),url or str(a.get("title") or ""))
            if key in seen: continue
            seen.add(key)
            out.append({"lat":lat,"lng":lng,"title":f"Reported activity — {place}","detail":str(a.get("title") or "Current public report")[:220],"url":url,"sourceUrl":url,"source":str(a.get("source") or "Global Pulse news pipeline"),"eventType":"REPORTED AREA","layer":"osint-reported","confidence":"OSINT","observedAt":a.get("published_date") or a.get("published") or a.get("time")})
            if len(out)>=250: return out
    return out


def main():
    snap=json.loads(SNAP.read_text(encoding="utf-8"))
    stories=list(snap.get("stories") or [])+list((snap.get("liveArticles") or {}).get("articles") or [])
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
        status="NO CURRENT SIGNAL" if not unique else ("CORROBORATED" if len(domains)>=3 else ("MULTI-SOURCE" if len(domains)>=2 else "SINGLE-SOURCE"))
        confidence=min(1.0,(len(domains)/3)*0.7+min(len(unique),5)/5*0.3) if unique else 0
        out.append({"id":wid,"title":title,"region":region,"type":kind,"lat":lat,"lng":lng,"status":status,"confidence":round(confidence,2),"articleCount":len(unique),"sourceDomains":sorted(domains),"evidence":unique[:5],"note":"Evidence-driven monitoring coverage; this is not a claim that every matched report describes a new incident."})

    gdelt=fetch_gdelt_points(); liveuamap=fetch_liveuamap_rss(); reported=story_place_points(stories + liveuamap)
    snap["osintMaps"]={"version":2,"updatedAt":datetime.now(timezone.utc).isoformat(),"sources":[
        {"name":"GDELT GEO","status":"online" if gdelt else "unavailable","points":len(gdelt),"cadence":"near-real-time","url":"https://www.gdeltproject.org/"},
        {"name":"Liveuamap RSS","status":"online" if liveuamap else "unavailable","stories":len(liveuamap),"cadence":"near-real-time when feed is reachable","url":"https://liveuamap.com/"},
        {"name":"Global Pulse reported-area extraction","status":"online" if reported else "no-current-place-matches","points":len(reported),"cadence":"every refresh","url":"https://github.com/lifetimeballer1/global-pulse"},
        {"name":"GeoConfirmed","status":"reference-only","reason":"No documented public machine-readable export/API located; automated access to the public map is blocked. No scraping bypass used.","cadence":"manual/reference"}
    ],"gdeltPoints":gdelt,"liveuamapStories":liveuamap[:300],"reportedAreaPoints":reported}

    base=[m for m in (snap.get("markers") or []) if m.get("layer") not in ("conflict-coverage","osint-gdelt","osint-reported")]
    for x in out:
        if x["articleCount"]<1: continue
        base.append({"lat":x["lat"],"lng":x["lng"],"type":"conflict-coverage","layer":"conflict-coverage","importance":2 if x["status"] in ("CORROBORATED","MULTI-SOURCE") else 1,"title":x["title"],"detail":f"{x['status']} | {x['articleCount']} current reports | {len(x['sourceDomains'])} independent domains | Evidence-linked monitoring","url":x["evidence"][0].get("url") if x["evidence"] else "","sourceUrl":x["evidence"][0].get("url") if x["evidence"] else "","source":"Global Pulse evidence-driven coverage","eventType":x["type"],"confidence":x["status"]})
    for p in gdelt:
        base.append({"lat":p["lat"],"lng":p["lng"],"type":"osint-gdelt","layer":"osint-gdelt","importance":1,"title":p["title"],"detail":"GDELT GEO geolocated news/event signal; approximate geography","url":p["url"],"sourceUrl":p["url"],"source":"GDELT GEO","eventType":"OSINT/GEO","confidence":"OSINT"})
    for p in reported:
        base.append(p)
    snap["markers"]=base
    snap["conflictCoverage"]={"version":3,"updatedAt":datetime.now(timezone.utc).isoformat(),"method":"Current snapshot reporting + independent source-domain corroboration + public OSINT map enrichment + reported-area place extraction.","watchlist":out}
    changes=snap.get("changes") or []
    changes.insert(0,{"kind":"system","title":"OSINT map enrichment refreshed","detail":f"GDELT GEO: {len(gdelt)} points; Liveuamap: {len(liveuamap)} stories; reported-area extraction: {len(reported)} points; GeoConfirmed remains reference-only until a permitted public data export is available."})
    snap["changes"]=changes[:8]
    SNAP.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Conflict coverage: {sum(1 for x in out if x['articleCount'])}/{len(out)} theaters have current evidence")
    print(f"OSINT enrichment: {len(gdelt)} GDELT points, {len(liveuamap)} Liveuamap stories, {len(reported)} reported-area points")

if __name__=="__main__": main()
