#!/usr/bin/env python3
"""Keyless watcher for The Enforcer's public YouTube feed.

Reads the channel's public RSS feed (no YouTube API key) and extracts Google
My Maps links from video descriptions. Links are stored as source references;
they are NOT treated as independently verified intelligence.
"""
import json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "enforcer_maps.json"
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=UCM-eRxEc_TutiPIbOS1YYbw"
NS = {"a": "http://www.w3.org/2005/Atom", "m": "http://search.yahoo.com/mrss/"}
MAP_RE = re.compile(r"https?://(?:www\.)?google\.com/maps/d/(?:edit|viewer)\?[^\s<>'\"]+", re.I)

def clean_url(u):
    return u.rstrip(".,;:)]}")

def main():
    req = Request(FEED, headers={"User-Agent": "GlobalPulse/1.0"})
    xml = urlopen(req, timeout=25).read()
    root = ET.fromstring(xml)
    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"source":"The Enforcer","channel":"@enforcerofficial","maps":[]}
    by_url = {x.get("url"): x for x in existing.get("maps", []) if x.get("url")}
    videos = []
    for entry in root.findall("a:entry", NS):
        vid = entry.findtext("a:id", "", NS).split(":")[-1]
        title = entry.findtext("a:title", "", NS)
        published = entry.findtext("a:published", "", NS)
        link = "https://www.youtube.com/watch?v=" + vid if vid else ""
        desc = ""
        group = entry.find("m:group", NS)
        if group is not None:
            desc = group.findtext("m:description", "", NS) or ""
        found = []
        for u in MAP_RE.findall(desc):
            u = clean_url(u)
            if u not in found: found.append(u)
            by_url.setdefault(u, {"url":u,"title":title,"videoUrl":link,"published":published,"source":"The Enforcer YouTube description","confidence":"SOURCE LINK / UNVERIFIED"})
        videos.append({"videoId":vid,"title":title,"published":published,"videoUrl":link,"mapCount":len(found)})
    maps = sorted(by_url.values(), key=lambda x: x.get("published", ""), reverse=True)[:100]
    existing.update({"updatedAt":datetime.now(timezone.utc).isoformat(),"feedUrl":FEED,"maps":maps,"recentVideos":videos[:20],"note":"Public YouTube RSS only; map links are extracted from descriptions and remain source references."})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Enforcer watcher: {len(videos)} feed videos, {len(maps)} unique map links")

if __name__ == "__main__": main()
