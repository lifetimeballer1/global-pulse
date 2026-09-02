#!/usr/bin/env python3
"""Refresh public RSS headlines into data/snapshot.json while preserving
Conflict Tracker, rich map markers, and intelligence metadata.
"""
import json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
HIST = DATA / "history.json"

FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Middle East", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"),
    ("Guardian World", "https://www.theguardian.com/world/rss"),
    ("NPR World", "https://feeds.npr.org/1004/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
]

BREAKING_RE = re.compile(
    r"strike|attack|killed|drone|missile|blockade|escalat|invasion|ceasefire|"
    r"bomb|shell|offensive|mobiliz|sanction|hostage|explosion|raid",
    re.I,
)

def text(node, tag):
    x = node.find(tag)
    return (x.text or "").strip() if x is not None and x.text else ""

def fetch(url):
    req = Request(url, headers={"User-Agent": "GlobalPulse/2.0 (+github.com/lifetimeballer1/global-pulse)"})
    with urlopen(req, timeout=25) as r:
        return r.read()

def confidence_for(title, source_label):
    return "LIKELY"

def is_breaking(title, pub):
    if BREAKING_RE.search(title or ""):
        return True
    if re.search(r"\b0?[0-3]\s+Sep\b|\bSep(?:tember)?\s*0?[0-3]\b", pub or "", re.I):
        return True
    return False

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default

def main():
    DATA.mkdir(exist_ok=True)
    old = load_json(SNAP, {})

    stories = []
    errors = []
    for label, url in FEEDS:
        try:
            root = ET.fromstring(fetch(url))
            for item in root.findall(".//item")[:15]:
                title = text(item, "title")
                link = text(item, "link")
                desc = re.sub("<[^>]+>", "", text(item, "description"))
                pub = text(item, "pubDate")
                if not title or not link:
                    continue
                stories.append({
                    "id": hashlib.sha1(link.encode()).hexdigest()[:12],
                    "sourceLabel": label,
                    "title": title,
                    "summary": desc[:280],
                    "source": link,
                    "time": pub,
                    "tag": "World",
                    "confidence": confidence_for(title, label),
                    "breaking": is_breaking(title, pub),
                })
        except Exception as e:
            errors.append(f"{label}: {type(e).__name__}")

    seen, unique = set(), []
    for s in stories:
        if s["id"] not in seen:
            unique.append(s)
            seen.add(s["id"])

    unique = sorted(unique, key=lambda s: 0 if s.get("breaking") else 1)
    stories = unique[:24]

    old_ids = {s.get("id") for s in old.get("stories", [])}
    new_items = [s for s in stories if s["id"] not in old_ids]

    changes = []
    for s in new_items[:6]:
        kind = "breaking" if s.get("breaking") else "new reporting"
        changes.append({
            "kind": kind,
            "title": s["title"][:140],
            "detail": f"New item from {s['sourceLabel']}",
        })
    if not changes:
        changes = [{
            "kind": "refresh",
            "title": "Feeds checked — no new unique headlines",
            "detail": "Public RSS refreshed; existing items retained.",
        }]

    now = datetime.now(timezone.utc).isoformat()
    err_note = f"; {len(errors)} feed errors" if errors else ""
    snapshot = {
        "updatedAt": now,
        "sourceStatus": f"{len(stories)} feed items · {len(new_items)} new{err_note}",
        "dataNote": (
            "Headlines refreshed from public RSS (BBC, Guardian, NPR, Al Jazeera). "
            "Story confidence = LIKELY. War OSINT markers = SOCIAL MEDIA REPORT / UNVERIFIED. "
            "Conflict Tracker and map briefs preserved across refreshes. Tension illustrative only."
        ),
        "tension": old.get("tension", 60),
        "breakdownScores": old.get("breakdownScores", {
            "Conflict activity": 72,
            "Diplomatic strain": 58,
            "Economic pressure": 54,
            "Market volatility": 46,
            "Military posture": 61,
        }),
        "changes": changes,
        "conflicts": old.get("conflicts", []),
        "markers": old.get("markers", []),
        "social": old.get("social", []),
        "stories": stories,
    }

    SNAP.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))

    history = load_json(HIST, [])
    should_append = True
    if history:
        last = history[-1]
        if str(last.get("updatedAt", ""))[:16] == now[:16]:
            should_append = False
    if should_append:
        history.append({"updatedAt": now, "tension": snapshot["tension"]})
    history = history[-240:]
    HIST.write_text(json.dumps(history, ensure_ascii=False, indent=2))

    print(snapshot["sourceStatus"])
    if errors:
        print("errors:", "; ".join(errors))

if __name__ == "__main__":
    main()
