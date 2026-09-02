#!/usr/bin/env python3
"""Refresh the public Global War News Map into Global Pulse markers.

The source is a publicly shared Google My Maps map. Its KML export is fetched
server-side by GitHub Actions so the browser never needs an API key or a
cross-origin request. Imported points are explicitly labeled as source-map
reports; they are not treated as verified facts.
"""
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
MID = "1LCWz0ynlXTMgdJYgKS89O_T5u_yh2QY"
KML_URL = f"https://www.google.com/maps/d/kml?forcekml=1&mid={MID}"
NS = {"k": "http://www.opengis.net/kml/2.2"}
MAX_POINTS = 250
SOURCE = "Global War News Map"


def fetch_kml():
    req = Request(KML_URL, headers={"User-Agent": "GlobalPulse/5.0"})
    raw = urlopen(req, timeout=35).read()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
            if not names:
                raise ValueError("KMZ contained no KML file")
            return zf.read(names[0])
    return raw


def clean_html(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"\s+", " ", value)
    return value.replace("&nbsp;", " ").strip()


def parse_points(kml_bytes):
    root = ET.fromstring(kml_bytes)
    seen = set()
    out = []
    for pm in root.findall(".//k:Placemark", NS):
        name = (pm.findtext("k:name", default="", namespaces=NS) or "").strip()
        description = clean_html(pm.findtext("k:description", default="", namespaces=NS) or "")
        point = pm.find(".//k:Point/k:coordinates", NS)
        if point is None or not (point.text or "").strip():
            continue
        coords = (point.text or "").strip().split(",")
        if len(coords) < 2:
            continue
        try:
            lng, lat = float(coords[0]), float(coords[1])
        except ValueError:
            continue
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue

        # Keep distinct locations even when the map reuses a generic title.
        key = (name.lower()[:120], round(lat, 4), round(lng, 4))
        if key in seen:
            continue
        seen.add(key)

        blob = f"{name} {description}".lower()
        marker_type = "conflict"
        layer = "osint"
        importance = 3
        if any(k in blob for k in ("strike", "hit", "drone", "missile", "bomb", "attack", "losses", "killed", "casualt")):
            importance = 2
        if any(k in blob for k in ("nato", "nuclear", "patriot", "blockade", "hormuz", "critical", "major")):
            importance = 1

        url_match = re.search(r"https?://(?:x\.com|twitter\.com)/[^\s\)\"']+", description, re.I)
        url = url_match.group(0).rstrip(".,;)")[:300] if url_match else ""

        title = name[:150] if name else "Global War News Map report"
        detail = description[:260] if description else "Imported point from Global War News Map"
        out.append({
            "lat": round(lat, 5),
            "lng": round(lng, 5),
            "type": marker_type,
            "layer": layer,
            "importance": importance,
            "title": title,
            "detail": detail,
            "url": url,
            "confidence": "SOURCE MAP REPORT / UNVERIFIED",
            "source": SOURCE,
        })
        if len(out) >= MAX_POINTS:
            break
    return out


def main():
    DATA.mkdir(exist_ok=True)
    snap = json.loads(SNAP.read_text()) if SNAP.exists() else {}

    # Remove only markers previously imported from this map. Strategic,
    # economic, military, and other OSINT markers remain untouched.
    base = [
        m for m in snap.get("markers", [])
        if m.get("source") != SOURCE
        and not (m.get("layer") == "osint" and "Global War News Map" in str(m.get("confidence", "")))
    ]

    try:
        points = parse_points(fetch_kml())
        status = f"Global War News Map synced: {len(points)} points"
        error = None
    except Exception as exc:
        points = [
            m for m in snap.get("markers", [])
            if m.get("source") == SOURCE
            or (m.get("layer") == "osint" and "Global War News Map" in str(m.get("confidence", "")))
        ]
        status = f"Global War News Map sync failed ({type(exc).__name__}); kept previous points"
        error = str(exc)

    snap["markers"] = base + points
    snap["updatedAt"] = datetime.now(timezone.utc).isoformat()

    existing_status = snap.get("sourceStatus", "")
    snap["sourceStatus"] = f"{existing_status}; {status}" if existing_status else status
    note = snap.get("dataNote") or ""
    map_note = "Global War News Map points are source-map reports and unverified until independently corroborated."
    if map_note not in note:
        snap["dataNote"] = (note + " " + map_note).strip()

    changes = snap.get("changes") or []
    changes.insert(0, {
        "kind": "osint",
        "title": "Global War News Map sync",
        "detail": status + (f" — {error}" if error else ""),
    })
    snap["changes"] = changes[:8]

    social = []
    for point in points:
        if point.get("url"):
            social.append({
                "label": point["title"][:100],
                "note": "SOURCE MAP REPORT / UNVERIFIED — Global War News Map",
                "url": point["url"],
            })
        if len(social) >= 10:
            break
    if social:
        snap["social"] = social

    SNAP.write_text(json.dumps(snap, ensure_ascii=False, indent=2))
    print(status)


if __name__ == "__main__":
    main()
