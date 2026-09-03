#!/usr/bin/env python3
"""Sync public Council on Foreign Relations Global Conflict Tracker metadata.

CFR is used as an independent conflict-assessment layer. We do not copy CFR
incident records; the script collects public conflict title/type/status/U.S.
impact/update metadata and places one reference point for each tracked conflict.
No API key is required.
"""
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"
BASE = "https://www.cfr.org"
TRACKER = BASE + "/global-conflict-tracker"
UA = "GlobalPulse/9.0 (+https://github.com/lifetimeballer1/global-pulse)"

# Stable geographic reference points for CFR's tracked conflicts.
POINTS = {
    "Criminal Violence in Haiti": (18.5944, -72.3074),
    "Criminal Violence in Mexico": (23.6345, -102.5528),
    "Instability in the Northern Triangle": (14.1, -88.9),
    "Instability in Venezuela": (8.0, -66.0),
    "Civil War in Myanmar": (21.9162, 95.9560),
    "Conflict Between Afghanistan and Pakistan": (33.7, 70.0),
    "Conflict Between India and Pakistan": (34.0, 74.5),
    "Confrontation Over Taiwan": (23.6978, 120.9605),
    "Confrontation With North Korea": (39.0, 127.0),
    "Territorial Disputes in the South China Sea": (12.0, 114.0),
    "Tensions Between Armenia and Azerbaijan": (40.3, 46.0),
    "War in Ukraine": (48.3794, 31.1656),
    "Conflict Between Turkey and Armed Kurdish Groups": (37.5, 42.5),
    "Conflict in Yemen and the Red Sea": (15.5, 44.2),
    "Conflict With Hezbollah in Lebanon": (33.85, 35.85),
    "Conflict With Iran": (32.4279, 53.6880),
    "Instability in Iraq": (33.2232, 43.6793),
    "Instability in Libya": (27.0, 17.0),
    "Instability in Syria": (35.0, 38.0),
    "Israeli-Palestinian Conflict": (31.8, 35.2),
    "Civil War in Sudan": (15.5, 32.5),
    "Conflict in Ethiopia": (9.1, 40.5),
    "Conflict in the Central African Republic": (6.6, 20.9),
    "Conflict in the Democratic Republic of Congo": (-2.9, 23.7),
    "Conflict With Al-Shabaab in Somalia": (2.0, 45.3),
    "Instability in South Sudan": (6.9, 31.3),
    "Violent Extremism in the Sahel": (15.0, 0.0),
}

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag != "a": return
        a = dict(attrs); href = a.get("href")
        if href and "/global-conflict-tracker/conflict/" in href:
            self.links.append(urljoin(BASE, href))

def fetch(url):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def strip_html(raw):
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I|re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I|re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()

def between(text, start, stops):
    m = re.search(re.escape(start) + r"\s*(.*?)\s*(?:" + "|".join(map(re.escape, stops)) + r")", text, re.I)
    return m.group(1).strip() if m else ""

def parse_conflict(url):
    raw = fetch(url); text = strip_html(raw)
    # Prefer the H1 from the HTML source.
    h1 = re.search(r"<h1[^>]*>\s*(.*?)\s*</h1>", raw, re.I|re.S)
    title = strip_html(h1.group(1)) if h1 else ""
    if not title or title.lower() in {"conflict", "global conflict tracker"}:
        for candidate in POINTS:
            if candidate.lower() in text.lower(): title = candidate; break
    if not title: return None
    ctype = between(text, "TYPE", ["IMPACT ON U.S.", "STATUS", "Updated", "Overview"])
    impact = between(text, "IMPACT ON U.S.", ["STATUS", "Updated", "Overview"])
    status = between(text, "STATUS", ["Updated", "Overview"])
    updated = ""
    m = re.search(r"Updated\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", text)
    if m: updated = m.group(1)
    # Collapse common navigation noise while keeping the actual assessment fields.
    ctype = re.sub(r"\s+", " ", ctype).strip()[:120]
    impact = re.sub(r"\s+", " ", impact).strip()[:40]
    status = re.sub(r"\s+", " ", status).strip()[:40]
    lat, lng = POINTS.get(title, (None, None))
    if lat is None:
        return None
    return {
        "title": title,
        "url": url,
        "type": ctype or "Conflict",
        "impactOnUS": impact or "Not specified",
        "status": status or "Not specified",
        "updated": updated or "Not specified",
        "lat": lat,
        "lng": lng,
        "source": "Council on Foreign Relations — Global Conflict Tracker",
    }

def main():
    snap = json.loads(SNAP.read_text()) if SNAP.exists() else {}
    raw = fetch(TRACKER)
    parser = LinkParser(); parser.feed(raw)
    urls = list(dict.fromkeys(parser.links))
    records = []
    for url in urls:
        try:
            item = parse_conflict(url)
            if item: records.append(item)
        except Exception as exc:
            print("CFR skip", url, type(exc).__name__)
    # If CFR changes its page markup, preserve the last successful layer instead of deleting it.
    if not records and snap.get("cfrConflicts"):
        records = snap["cfrConflicts"]
    old_markers = [m for m in snap.get("markers", []) if m.get("source") != "Council on Foreign Relations — Global Conflict Tracker"]
    for item in records:
        old_markers.append({
            "lat": item["lat"], "lng": item["lng"], "type": "strategic", "layer": "cfr", "importance": 3,
            "title": "CFR: " + item["title"],
            "detail": f"CFR status: {item['status']} | U.S. impact: {item['impactOnUS']} | Type: {item['type']} | Updated: {item['updated']}",
            "url": item["url"], "sourceUrl": item["url"],
            "source": item["source"], "eventType": "CONFLICT ASSESSMENT",
            "confidence": "CFR ASSESSMENT / REFERENCE POINT"
        })
    snap["markers"] = old_markers
    snap["cfrConflicts"] = records
    snap["externalLayers"] = snap.get("externalLayers") or {}
    snap["externalLayers"]["cfrGlobalConflictTracker"] = {
        "name": "Council on Foreign Relations — Global Conflict Tracker",
        "url": TRACKER,
        "status": "live public assessment layer",
        "count": len(records),
        "note": "Conflict assessment metadata and reference points are collected from CFR public pages. Points represent tracked conflicts, not individual incidents."
    }
    snap["sourceStatus"] = ((snap.get("sourceStatus", "") + "; ") if snap.get("sourceStatus") else "") + f"CFR Global Conflict Tracker: {len(records)} tracked conflicts"
    note = snap.get("dataNote") or ""
    addition = "CFR Global Conflict Tracker is an independent conflict-assessment layer; its reference points are not incident reports."
    if addition not in note: snap["dataNote"] = (note + " " + addition).strip()
    changes = snap.get("changes") or []
    changes.insert(0, {"kind":"system", "title":"CFR conflict layer refreshed", "detail":f"Synced {len(records)} CFR tracked-conflict assessments and map reference points."})
    snap["changes"] = changes[:8]
    snap["updatedAt"] = datetime.now(timezone.utc).isoformat()
    SNAP.write_text(json.dumps(snap, ensure_ascii=False, indent=2))
    print(f"CFR synced: {len(records)} conflicts")

if __name__ == "__main__": main()
