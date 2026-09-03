#!/usr/bin/env python3
"""Reliable regional OSINT collector for Global Pulse.

Collects fresh geolocated signals from GDELT GEO and supplements them with
current story URLs already present in the snapshot. GDELT is queried with ISO
country codes (the API's locationcc filter expects country codes), which fixes
the previous country-name query problem. No API key is required.
"""
import json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
SNAP=ROOT/"data"/"snapshot.json"
UA="GlobalPulse/2.0 (+https://github.com/lifetimeballer1/global-pulse)"

REGIONS={
 "Africa": ["SD","SS","CD","NG","SO","ET","KE","MZ","CM","CF","LY","ML","BF","NE","TD","TZ","UG","ZA","AO","SN","GH","GN","SL","CI","ER","DJ","RW","BI","ZW","ZM"],
 "South America": ["BR","CO","VE","EC","PE","BO","PY","UY","AR","CL","GY","SR"],
 "South Asia": ["IN","PK","BD","AF","LK","NP","BT","MV","MM"]
}
QUERIES={
 "Africa":"(conflict OR attack OR fighting OR bombing OR shooting OR insurgent OR militia OR jihadist OR violence OR clash OR kidnapping OR military OR coup OR protest)",
 "South America":"(conflict OR attack OR fighting OR bombing OR shooting OR cartel OR gang OR guerrilla OR insurgent OR violence OR clash OR kidnapping OR military OR protest)",
 "South Asia":"(conflict OR attack OR fighting OR bombing OR shooting OR insurgent OR militant OR terrorism OR violence OR clash OR kidnapping OR military OR border OR protest)"
}
COUNTRY_NAMES={
"SD":"Sudan","SS":"South Sudan","CD":"DR Congo","NG":"Nigeria","SO":"Somalia","ET":"Ethiopia","KE":"Kenya","MZ":"Mozambique","CM":"Cameroon","CF":"Central African Republic","LY":"Libya","ML":"Mali","BF":"Burkina Faso","NE":"Niger","TD":"Chad","TZ":"Tanzania","UG":"Uganda","ZA":"South Africa","AO":"Angola","SN":"Senegal","GH":"Ghana","GN":"Guinea","SL":"Sierra Leone","CI":"Cote d'Ivoire","ER":"Eritrea","DJ":"Djibouti","RW":"Rwanda","BI":"Burundi","ZW":"Zimbabwe","ZM":"Zambia",
"BR":"Brazil","CO":"Colombia","VE":"Venezuela","EC":"Ecuador","PE":"Peru","BO":"Bolivia","PY":"Paraguay","UY":"Uruguay","AR":"Argentina","CL":"Chile","GY":"Guyana","SR":"Suriname",
"IN":"India","PK":"Pakistan","BD":"Bangladesh","AF":"Afghanistan","LK":"Sri Lanka","NP":"Nepal","BT":"Bhutan","MV":"Maldives","MM":"Myanmar"}

def get(url):
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/json,*/*"})
    with urlopen(req,timeout=20) as r: return r.read().decode("utf-8",errors="replace")

def parse_time(p):
    for k in ("seendate","published","published_date","time","date"):
        v=str(p.get(k) or "").strip()
        if v: return v
    return datetime.now(timezone.utc).isoformat()

def gdelt(region,cc):
    q=quote(f"locationcc:{cc} {QUERIES[region]}",safe="")
    url=f"https://api.gdeltproject.org/api/v2/geo/geo?query={q}&mode=PointData&format=GeoJSON&timespan=24h&maxrecords=80"
    try:
        raw=get(url); obj=json.loads(raw); out=[]
        for f in obj.get("features",[]):
            geom=f.get("geometry") or {}; c=geom.get("coordinates") or []
            if len(c)<2: continue
            try: lng=float(c[0]); lat=float(c[1])
            except (TypeError,ValueError): continue
            if not (-90<=lat<=90 and -180<=lng<=180): continue
            p=f.get("properties") or {}
            u=str(p.get("url") or p.get("sourceurl") or "").strip()
            name=str(p.get("name") or COUNTRY_NAMES.get(cc,cc))[:180]
            out.append({"id":f"gdelt-{cc}-{lat:.4f}-{lng:.4f}-{abs(hash(u or name))}","lat":lat,"lng":lng,"title":name,"detail":str(p.get("description") or p.get("html") or "Fresh GDELT GEO signal")[:320],"url":u,"sourceUrl":u,"source":"GDELT GEO","sourceDomain":(urlparse(u).hostname or "").lower().removeprefix("www."),"eventType":"OSINT/GEO","layer":"osint-regional","region":region,"country":COUNTRY_NAMES.get(cc,cc),"countryCode":cc,"confidence":"DISCOVERY SIGNAL","observedAt":parse_time(p)})
        return out, None
    except Exception as e:
        return [], str(e)

def story_points(snap):
    places={
      "Mogadishu":(2.0469,45.3182),"Maiduguri":(11.8333,13.1500),"Khartoum":(15.5007,32.5599),"Goma":(-1.6771,29.2285),"Juba":(4.8594,31.5713),"Tripoli":(32.8872,13.1913),"Bamako":(12.6392,-8.0029),"Niamey":(13.5127,2.1126),"Nairobi":(-1.2864,36.8172),"Maputo":(-25.9692,32.5732),"Lagos":(6.5244,3.3792),
      "Bogota":(4.7110,-74.0721),"Medellin":(6.2442,-75.5812),"Cali":(3.4516,-76.5320),"Caracas":(10.4806,-66.9036),"Maracaibo":(10.6545,-71.6299),"Quito":(-0.1807,-78.4678),"Guayaquil":(-2.1709,-79.9224),"Lima":(-12.0464,-77.0428),"Sao Paulo":(-23.5505,-46.6333),"Rio de Janeiro":(-22.9068,-43.1729),"Buenos Aires":(-34.6037,-58.3816),"Santiago":(-33.4489,-70.6693),
      "Kabul":(34.5553,69.2075),"Kandahar":(31.6289,65.7372),"Peshawar":(34.0151,71.5249),"Quetta":(30.1798,66.9750),"Karachi":(24.8607,67.0011),"Srinagar":(34.0837,74.7973),"Imphal":(24.8170,93.9368),"Dhaka":(23.8103,90.4125),"Chittagong":(22.3569,91.7832),"Yangon":(16.8409,96.1735),"Mandalay":(21.9588,96.0891)
    }
    strong=re.compile(r"\b(attack|killed|dead|fighting|bomb|missile|rocket|clash|militia|insurgent|militant|terror|cartel|gang|kidnap|shooting|violence|battle|drone|shelling|artillery|protest|unrest|coup)\b",re.I)
    neg=re.compile(r"\b(historical|history of|anniversary|documentary|recipe|sport|movie|music|travel)\b",re.I)
    articles=list(snap.get("stories") or [])+list((snap.get("liveArticles") or {}).get("articles") or [])
    out=[]; seen=set()
    for a in articles:
        text=" ".join(str(a.get(k) or "") for k in ("title","summary","description","text","detail"))
        if neg.search(text) or not strong.search(text): continue
        low=text.lower(); url=str(a.get("url") or a.get("link") or a.get("sourceUrl") or "").strip()
        for place,(lat,lng) in places.items():
            if place.lower() not in low: continue
            key=(place,url or str(a.get("title") or ""))
            if key in seen: continue
            seen.add(key)
            out.append({"id":f"report-{place}-{abs(hash(url or text))}","lat":lat,"lng":lng,"title":f"Reported activity — {place}","detail":str(a.get("title") or "Current public report")[:260],"url":url,"sourceUrl":url,"source":str(a.get("source") or "Global Pulse news pipeline"),"sourceDomain":(urlparse(url).hostname or "").lower().removeprefix("www."),"eventType":"REPORTED AREA","layer":"osint-regional","confidence":"OSINT REPORT","observedAt":parse_time(a)})
            if len(out)>=300: return out
    return out

def main():
    snap=json.loads(SNAP.read_text(encoding="utf-8"))
    base=[m for m in snap.get("markers",[]) if m.get("layer")!="osint-regional"]
    points=[]; failures=[]; counts={r:0 for r in REGIONS}
    for region,codes in REGIONS.items():
        for cc in codes:
            pts,err=gdelt(region,cc); points.extend(pts); counts[region]+=len(pts)
            if err: failures.append({"region":region,"country":COUNTRY_NAMES[cc],"error":err[:180]})
            time.sleep(.08)
    seen=set(); clean=[]
    for p in points:
        key=(round(p["lat"],3),round(p["lng"],3),p.get("url") or p.get("title"))
        if key not in seen: seen.add(key); clean.append(p)
    reports=story_points(snap)
    snap["markers"]=base+clean[:1200]+reports
    snap["regionalOsint"]={"version":2,"updatedAt":datetime.now(timezone.utc).isoformat(),"totalPoints":len(clean),"reportedAreaPoints":len(reports),"regions":{r:{"points":counts[r]} for r in REGIONS},"failures":failures[:50],"sourceHealth":{"GDELT GEO":{"attempted":sum(map(len,REGIONS.values())),"successful":sum(map(len,REGIONS.values()))-len(failures)}}}
    SNAP.write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Regional OSINT: {len(clean)} GDELT points + {len(reports)} reported-area points; failures={len(failures)}; counts={counts}")
    if not clean and not reports: raise SystemExit("Regional OSINT produced zero points; refusing to publish an empty expansion")

if __name__=="__main__": main()
