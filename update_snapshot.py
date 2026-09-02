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

DEFAULT_CONFLICTS = [
  {"id":"ukraine","name":"Ukraine–Russia War","region":"Europe","status":"Active high-intensity","actors":"Ukraine, Russia, NATO support states","recent":"Continued deep strikes and front-line pressure.","escalation":"HIGH","facts":"Full-scale conflict ongoing since 2022.","analysis":"Attrition and long-range strike capacity dominate.","confidence":"CONFIRMED"},
  {"id":"hormuz","name":"Iran / Hormuz Theater","region":"Middle East","status":"Elevated kinetic risk","actors":"Iran, US, Israel, Gulf states","recent":"Strikes, tanker incidents, Hormuz risk.","escalation":"HIGH","facts":"Critical oil chokepoint.","analysis":"Energy markets price escalation quickly.","confidence":"LIKELY"},
  {"id":"taiwan","name":"Taiwan Strait Pressure","region":"Indo-Pacific","status":"Sustained military pressure","actors":"PRC, Taiwan, US and partners","recent":"Elevated PLA air and naval activity.","escalation":"MODERATE","facts":"Semiconductor and deterrence node.","analysis":"Pressure below kinetic threshold.","confidence":"LIKELY"},
  {"id":"israel-iran","name":"Israel–Iran Axis Front","region":"Middle East","status":"Multi-front residual risk","actors":"Israel, Iran, regional proxies","recent":"Intermittent exchanges and proxy activity.","escalation":"MODERATE–HIGH","facts":"Cascading regional exchanges since 2023–26.","analysis":"Energy and nuclear dossiers can widen risk.","confidence":"LIKELY"},
  {"id":"sudan","name":"Sudan Civil War","region":"Africa","status":"Active civil war","actors":"SAF, RSF","recent":"Fighting with severe civilian impact.","escalation":"MODERATE","facts":"Major humanitarian crisis.","analysis":"Limited mediation leverage.","confidence":"CONFIRMED"},
  {"id":"yemen","name":"Yemen / Red Sea","region":"Middle East / Maritime","status":"Residual interdiction risk","actors":"Houthis, shipping","recent":"Residual Red Sea shipping risk.","escalation":"MODERATE","facts":"Secondary chokepoint.","analysis":"Insurance and routing sensitive.","confidence":"LIKELY"},
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
                    "confidence": "LIKELY",
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
    conflicts = old.get("conflicts") or DEFAULT_CONFLICTS
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
        "conflicts": conflicts,
        "markers": old.get("markers", []),
        "social": old.get("social", []),
        "stories": stories,
    }

    SNAP.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))

    history = load_json(HIST, [])
    should_append = True
    if history and str(history[-1].get("updatedAt", ""))[:16] == now[:16]:
        should_append = False
    if should_append:
        history.append({"updatedAt": now, "tension": snapshot["tension"]})
    history = history[-240:]
    HIST.write_text(json.dumps(history, ensure_ascii=False, indent=2))

    print(snapshot["sourceStatus"], "conflicts", len(conflicts))
    if errors:
        print("errors:", "; ".join(errors))

if __name__ == "__main__":
    main()
