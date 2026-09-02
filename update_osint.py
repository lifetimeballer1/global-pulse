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
MAP_URL = f"https://www.google.com/maps/d/viewer?mid={MID}"
NS = {"k": "http://www.opengis.net/kml/2.2"}
MAX_POINTS = 250
SOURCE = "Global War News Map"

# Lightweight theater matching lets the dashboard connect a map point directly
# to the corresponding conflict drawer without requiring another API.
THEATERS = [
    ("ukraine", "Ukraine–Russia War", "Europe", ["ukraine", "russia", "kyiv", "donetsk", "crimea", "kharkiv", "zaporizhzhia"]),
    ("gaza", "Gaza / Israel–Hamas", "Middle East", ["gaza", "hamas", "gaza strip", "rafah", "west bank", "palestinian"]),
    ("israel-iran", "Israel–Iran Regional Front", "Middle East", ["israel iran", "iran israel", "tehran", "iranian missile", "iranian nuclear"]),
    ("hormuz", "Iran / Strait of Hormuz", "Middle East", ["strait of hormuz", "hormuz", "persian gulf", "gulf tanker"]),
    ("yemen", "Yemen / Red Sea", "Middle East", ["yemen", "houthi", "red sea", "bab el-mandeb", "aden"]),
    ("syria", "Syria Conflict / Residual Fronts", "Middle East", ["syria", "syrian", "damascus", "idlib"]),
    ("iraq", "Iraq Militia / Security Risk", "Middle East", ["iraq", "iraqi", "baghdad", "kurdistan iraq"]),
    ("sudan", "Sudan Civil War", "Africa", ["sudan", "sudanese", "khartoum", "darfur", "kordofan", "rsf"]),
    ("south-sudan", "South Sudan Instability", "Africa", ["south sudan", "juba", "south sudanese"]),
    ("drc", "Eastern DRC Conflict", "Africa", ["democratic republic of congo", "eastern congo", "goma", "m23", "north kivu", "south kivu"]),
    ("somalia", "Somalia / al-Shabaab", "Africa", ["somalia", "somali", "al-shabaab", "mogadishu"]),
    ("ethiopia", "Ethiopia Internal Conflict Risk", "Africa", ["ethiopia", "ethiopian", "amhara", "tigray", "oromia"]),
    ("nigeria", "Nigeria Insurgency / Banditry", "Africa", ["nigeria", "nigerian", "boko haram", "iswap", "banditry"]),
    ("sahel-mali", "Mali / Sahel Insurgency", "Africa", ["mali", "malian", "jnim", "bamako"]),
    ("sahel-burkina", "Burkina Faso Insurgency", "Africa", ["burkina faso", "burkinabe", "ouagadougou"]),
    ("sahel-niger", "Niger Insurgency / Coup Fallout", "Africa", ["niger", "nigerien", "niamey", "islamic state sahel"]),
    ("cameroon", "Cameroon Separatist Conflict", "Africa", ["cameroon", "cameroonian", "ambazonia"]),
    ("chad", "Chad Security / Sahel Spillover", "Africa", ["chad", "chadian", "n'djamena", "lake chad"]),
    ("libya", "Libya Political / Militia Risk", "Africa", ["libya", "libyan", "tripoli libya", "benghazi libya"]),
    ("mozambique", "Mozambique Cabo Delgado", "Africa", ["mozambique", "mozambican", "cabo delgado", "mocimboa"]),
    ("myanmar", "Myanmar Civil War", "Asia", ["myanmar", "burma", "junta", "rakhine", "mandalay", "naypyidaw"]),
    ("afghanistan", "Afghanistan Security Risk", "Asia", ["afghanistan", "afghan", "taliban", "isis-k", "kabul"]),
    ("pakistan", "Pakistan Militancy / Border Risk", "Asia", ["pakistan", "pakistani", "ttp", "balochistan", "islamabad"]),
    ("taiwan", "Taiwan Strait Pressure", "Indo-Pacific", ["taiwan", "taiwan strait", "pla", "beijing", "cross-strait"]),
    ("korea", "Korean Peninsula", "Indo-Pacific", ["north korea", "south korea", "dprk", "pyongyang", "korean peninsula"]),
    ("south-china-sea", "South China Sea Flashpoint", "Indo-Pacific", ["south china sea", "philippines china", "spratly", "second thomas shoal"]),
    ("haiti", "Haiti Gang Conflict", "Caribbean", ["haiti", "haitian", "port-au-prince", "gang violence"]),
    ("mexico", "Mexico Cartel Conflict", "Latin America", ["mexico", "mexican", "cjng", "sinaloa cartel", "cartel violence"]),
    ("ecuador", "Ecuador Organized Crime Conflict", "Latin America", ["ecuador", "ecuadorian", "guayaquil", "los choneros", "prison violence"]),
    ("colombia", "Colombia Armed Groups", "Latin America", ["colombia", "colombian", "eln", "farc dissidents", "catatumbo"]),
]


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
        raw_description = pm.findtext("k:description", default="", namespaces=NS) or ""
        description = clean_html(raw_description)
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

        urls = re.findall(r"https?://[^\s<>\"']+", raw_description + " " + description, re.I)
        cleaned_urls = []
        for candidate in urls:
            candidate = candidate.rstrip(".,;:)]}")[:500]
            if candidate not in cleaned_urls:
                cleaned_urls.append(candidate)
        social_url = next((u for u in cleaned_urls if re.search(r"(?:x\.com|twitter\.com)/", u, re.I)), "")
        url = social_url or (cleaned_urls[0] if cleaned_urls else "")

        title = name[:150] if name else "Global War News Map report"
        detail = description[:360] if description else "Imported point from Global War News Map"

        # Match the point to a known theater. Exact-word matching prevents
        # false positives such as Niger matching Nigeria.
        conflict_id = ""
        conflict_name = ""
        region = ""
        for cid, cname, cregion, aliases in THEATERS:
            if any(re.search(r"(?<![a-z0-9])" + re.escape(a.lower()) + r"(?![a-z0-9])", blob) for a in aliases):
                conflict_id, conflict_name, region = cid, cname, cregion
                break

        out.append({
            "lat": round(lat, 5),
            "lng": round(lng, 5),
            "type": marker_type,
            "layer": layer,
            "importance": importance,
            "title": title,
            "detail": detail,
            "url": url,
            "sourceUrl": url or MAP_URL,
            "sourceMapUrl": MAP_URL,
            "confidence": "SOURCE MAP REPORT / UNVERIFIED",
            "source": SOURCE,
            "conflictId": conflict_id,
            "conflictName": conflict_name,
            "region": region,
        })
        if len(out) >= MAX_POINTS:
            break
    return out


def main():
    DATA.mkdir(exist_ok=True)
    snap = json.loads(SNAP.read_text()) if SNAP.exists() else {}

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
