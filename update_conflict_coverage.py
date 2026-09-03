#!/usr/bin/env python3
"""Validate/normalize conflict and OSINT map records without discarding usable evidence."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
SNAP=ROOT/"data"/"snapshot.json"


def first_url(a):
    for k in ("url","link","sourceUrl","source_url"):
        v=str(a.get(k) or "").strip()
        if v: return v
    return ""


def domain(url):
    try: return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception: return ""


def normalize_point(p, default_layer="osint"):
    try:
        lat=float(p.get("lat")); lng=float(p.get("lng"))
    except (TypeError,ValueError): return None
    if not (-90<=lat<=90 and -180<=lng<=180): return None
    q=dict(p); q["lat"]=lat; q["lng"]=lng
    url=first_url(q)
    if url:
        q["url"]=url; q["sourceUrl"]=url; q["sourceDomain"]=q.get("sourceDomain") or domain(url)
    q["layer"]=q.get("layer") or default_layer
    q["observedAt"]=q.get("observedAt") or datetime.now(timezone.utc).isoformat()
    return q


def main():
    snap=json.loads(SNAP.read_text(encoding="utf-8"))
    osint=snap.get("osintMaps") or {}
    normalized=[]
    for p in osint.get("gdeltPoints") or []:
        q=normalize_point(p,"osint-gdelt")
        if q: q["source"]="GDELT GEO"; normalized.append(q)
    for p in osint.get("reportedAreaPoints") or []:
        q=normalize_point(p,"osint-reported")
        if q and q.get("sourceUrl"): normalized.append(q)
    # De-duplicate map events while preserving provenance.
    seen=set(); dedup=[]
    for p in normalized:
        key=(round(p["lat"],3),round(p["lng"],3),p.get("url") or p.get("title") or "")
        if key in seen: continue
        seen.add(key); dedup.append(p)
    osint["version"]=2
    osint["updatedAt"]=datetime.now(timezone.utc).isoformat()
    osint["normalizedPointCount"]=len(dedup)
    osint["normalization"]={"urlFields":["url","link","sourceUrl","source_url"],"invalidCoordinatesDropped":True,"duplicatePointsDropped":True}
    osint["normalizedPoints"]=dedup
    snap["osintMaps"]=osint
    # Merge normalized OSINT points into the canonical marker collection.
    markers=[m for m in (snap.get("markers") or []) if m.get("layer") not in ("osint-gdelt","osint-reported")]
    markers.extend(dedup)
    snap["markers"]=markers
    SNAP.write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Normalized OSINT points:",len(dedup))

if __name__=="__main__": main()
