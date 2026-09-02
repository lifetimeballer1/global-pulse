#!/usr/bin/env python3
"""Refresh War OSINT markers from the public Global War News Map KML.
Preserves strategic markers, stories, conflicts, and social list structure.
Labels all imported points as SOCIAL MEDIA REPORT / UNVERIFIED.
"""
import json, re, zipfile, io
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
MID = "1LCWz0ynlXTMgdJYgKS89O_T5u_yh2QY"
KML_URL = f"https://www.google.com/maps/d/u/0/kml?mid={MID}"
NS = {"k": "http://www.opengis.net/kml/2.2"}
MAX_OSINT = 50

def fetch_kml():
    req = Request(KML_URL, headers={"User-Agent": "GlobalPulse/1.0"})
    raw = urlopen(req, timeout=30).read()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            name = next(n for n in zf.namelist() if n.endswith(".kml"))
            return zf.read(name)
    return raw

def parse_points(kml_bytes):
    root = ET.fromstring(kml_bytes)
    seen, out = set(), []
    for pm in root.findall(".//k:Placemark", NS):
        n = (pm.findtext("k:name", default="", namespaces=NS) or "").strip()
        if not n:
            continue
        key = n.lower()[:80]
        if key in seen:
            continue
        d = pm.findtext("k:description", default="", namespaces=NS) or ""
        d = re.sub("<[^>]+>", " ", d)
        d = re.sub(r"\s+", " ", d).strip()
        point = pm.find(".//k:Point/k:coordinates", NS)
        if point is None:
            continue
        coords = (point.text or "").strip().split(",")
        if len(coords) < 2:
            continue
        try:
            lng, lat = float(coords[0]), float(coords[1])
        except ValueError:
            continue
        m = re.search(r"https?://(?:x\.com|twitter\.com)/[^\s\)\"\']+", d)
        if not m:
            continue
        url = m.group(0).rstrip(").,;")[:120]
        seen.add(key)
        blob = (n + " " + d).lower()
        imp = 3
        if any(k in blob for k in ("strike", "hit", "drone", "missile", "bomb", "attack", "losses")):
            imp = 2
        if any(k in blob for k in ("nato", "nuclear", "patriot", "blockade", "hormuz", "critical")):
            imp = 1
        out.append({
            "lat": round(lat, 5),
            "lng": round(lng, 5),
            "type": "conflict",
            "layer": "osint",
            "importance": imp,
            "title": n[:110],
            "detail": (d[:150] if d else "OSINT map report"),
            "url": url,
            "confidence": "SOCIAL MEDIA REPORT",
        })
        if len(out) >= MAX_OSINT:
            break
    return out

def main():
    DATA.mkdir(exist_ok=True)
    snap = json.loads(SNAP.read_text()) if SNAP.exists() else {}
    base = [m for m in snap.get("markers", []) if m.get("layer") != "osint"]
    try:
        kml = fetch_kml()
        osint = parse_points(kml)
        status = f"OSINT refreshed: {len(osint)} points"
        err = None
    except Exception as e:
        osint = [m for m in snap.get("markers", []) if m.get("layer") == "osint"]
        status = f"OSINT refresh failed ({type(e).__name__}); kept previous points"
        err = str(e)

    snap["markers"] = base + osint
    snap["updatedAt"] = datetime.now(timezone.utc).isoformat()
    snap["sourceStatus"] = status if not snap.get("sourceStatus") else f"{snap.get('sourceStatus', '')}; {status}"
    note = snap.get("dataNote") or ""
    if "War OSINT" not in note:
        snap["dataNote"] = (note + " War OSINT from Global War News Map = SOCIAL MEDIA REPORT / UNVERIFIED.").strip()
    changes = snap.get("changes") or []
    changes.insert(0, {
        "kind": "osint",
        "title": "War OSINT layer refresh",
        "detail": status + (f" — {err}" if err else ""),
    })
    snap["changes"] = changes[:8]
    social = []
    for p in osint[:10]:
        if p.get("url"):
            social.append({
                "label": p["title"][:100],
                "note": "SOCIAL MEDIA REPORT / UNVERIFIED — Global War News Map",
                "url": p["url"],
            })
    if social:
        snap["social"] = social
    SNAP.write_text(json.dumps(snap, ensure_ascii=False, indent=2))
    print(status)

if __name__ == "__main__":
    main()
