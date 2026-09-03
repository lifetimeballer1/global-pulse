#!/usr/bin/env python3
"""Replace failed news feeds with public no-key fallback feeds.

Google News RSS is used only as a resilience layer. It is not treated as a
primary source and each story retains its publisher/source metadata when
available. Failed feeds are never allowed to make the whole snapshot empty.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
SOURCES = DATA / "sources.json"
UA = "Mozilla/5.0 (compatible; GlobalPulse/3.0)"

FALLBACKS = {
    "GDELT Climate & Disaster Watch": "climate disaster flood wildfire drought famine epidemic",
    "GDELT Climate Security Watch": "climate security migration food water disease crisis",
    "GDELT Live — U.S. Politics": "US politics Congress White House election Senate",
    "CNN Politics — GDELT Mirror": "CNN politics Trump Congress Senate White House",
    "Axios Politics — GDELT Mirror": "Axios politics Trump Congress Senate White House",
    "Morse Report — GDELT Mirror": "Morse Report politics Congress Senate White House",
    "GDELT Live — Global Economics": "global economy markets oil inflation trade central bank",
    "GDELT Live — World Politics": "world politics diplomacy sanctions election conflict",
    "GDELT Live — Global": "world conflict war military crisis sanctions",
    "GDELT Live — Africa": "Africa conflict war military Sudan Congo Sahel Nigeria Somalia",
    "GDELT Live — Americas": "South America conflict Colombia Venezuela Brazil Ecuador Peru Haiti Mexico",
    "GDELT Live — Middle East": "Middle East conflict Iran Israel Gaza Yemen Syria Iraq",
    "FAO GIEWS": "FAO food security famine drought crop harvest Africa",
    "ReliefWeb": "humanitarian crisis conflict disaster Africa Asia Middle East",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def fetch(query):
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml"})
    with urlopen(req, timeout=15) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        pub = clean(item.findtext("pubDate"))
        source_el = item.find("source")
        source = clean(source_el.text if source_el is not None else "Google News")
        if not title or not link:
            continue
        out.append({"title": title, "url": link, "source": source, "published_date": pub})
    return out[:30]


def main():
    data = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
    sources = json.loads(SOURCES.read_text(encoding="utf-8")) if SOURCES.exists() else {}
    failed = set()
    for e in sources.get("errors", []):
        failed.add(str(e).split(":", 1)[0].strip())
    stories = list(data.get("stories", []))
    existing = {str(x.get("url") or x.get("title")) for x in stories}
    replacements = []
    for name, query in FALLBACKS.items():
        if not any(name == f.get("name") for f in sources.get("feeds", [])) and name not in failed:
            continue
        try:
            rows = fetch(query)
            added = 0
            for row in rows:
                key = row["url"]
                if key in existing:
                    continue
                stories.append({
                    "title": row["title"],
                    "url": row["url"],
                    "published_date": row["published_date"],
                    "summary_snippet": "Fallback discovery via Google News RSS; publisher: " + row["source"],
                    "source": row["source"],
                    "sourceType": "fallback-news",
                    "fallbackFor": name,
                    "credit_metadata": "Google News RSS fallback",
                })
                existing.add(key)
                added += 1
            replacements.append({"failedSource": name, "fallback": "Google News RSS", "query": query, "storiesAdded": added, "checkedAt": now()})
        except Exception as exc:
            replacements.append({"failedSource": name, "fallback": "Google News RSS", "query": query, "storiesAdded": 0, "error": f"{type(exc).__name__}: {exc}"[:160], "checkedAt": now()})

    data["stories"] = stories[:1000]
    data["sourceFailover"] = {"updatedAt": now(), "replacements": replacements}
    data["updatedAt"] = now()
    SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SOURCE FAILOVER:", json.dumps(replacements, ensure_ascii=False))


if __name__ == "__main__":
    main()
