#!/usr/bin/env python3
"""Build the public Global Pulse snapshot from no-key RSS sources.

The site is intentionally keyless: GitHub Actions fetches public RSS feeds,
deduplicates stories, derives transparent analytical scores, and writes a
static snapshot consumed by index.html. Scores are analytical indicators, not
claims of ground truth.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
HIST = DATA / "history.json"
SOURCES = DATA / "sources.json"

FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", "international"),
    ("BBC Middle East", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "regional"),
    ("BBC Africa", "https://feeds.bbci.co.uk/news/world/africa/rss.xml", "regional"),
    ("BBC Asia", "https://feeds.bbci.co.uk/news/world/asia/rss.xml", "regional"),
    ("BBC Europe", "https://feeds.bbci.co.uk/news/world/europe/rss.xml", "regional"),
    ("BBC Americas", "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml", "regional"),
    ("Guardian World", "https://www.theguardian.com/world/rss", "international"),
    ("Guardian US", "https://www.theguardian.com/us-news/rss", "regional"),
    ("NPR World", "https://feeds.npr.org/1004/rss.xml", "international"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "international"),
    ("DW World", "https://rss.dw.com/rdf/rss-en-world", "international"),
    ("France 24", "https://www.france24.com/en/rss", "international"),
    ("Crisis Group", "https://www.crisisgroup.org/rss.xml", "analysis"),
    ("ReliefWeb", "https://reliefweb.int/updates/rss.xml", "humanitarian"),
]

CONFLICTS = [
    ("ukraine", "Ukraine–Russia War", "Europe", "WAR", "HIGH", "Ukraine Russia Kyiv Donetsk Crimea Kharkiv missile drone strike offensive ceasefire"),
    ("gaza", "Gaza / Israel–Hamas", "Middle East", "WAR", "HIGH", "Gaza Hamas Israel Rafah Gaza Strip hostage ceasefire strike"),
    ("israel-iran", "Israel–Iran Regional Front", "Middle East", "WAR", "HIGH", "Israel Iran Tehran missile strike nuclear Hezbollah proxy"),
    ("hormuz", "Iran / Strait of Hormuz", "Middle East", "FLASHPOINT", "HIGH", "Hormuz tanker Gulf Iran blockade shipping oil"),
    ("yemen", "Yemen / Red Sea", "Middle East", "CONFLICT", "HIGH", "Yemen Houthi Red Sea ship Bab el-Mandeb missile"),
    ("syria", "Syria Conflict / Residual Fronts", "Middle East", "CONFLICT", "MODERATE", "Syria Damascus Idlib Kurdish clashes militia"),
    ("iraq", "Iraq Militia / Security Risk", "Middle East", "CONFLICT", "MODERATE", "Iraq militia rocket Islamic State ISIS Baghdad"),
    ("sudan", "Sudan Civil War", "Africa", "WAR", "CRITICAL", "Sudan SAF RSF Khartoum Darfur Kordofan famine"),
    ("south-sudan", "South Sudan Instability", "Africa", "CONFLICT", "HIGH", "South Sudan Juba militia clashes"),
    ("drc", "Eastern DRC Conflict", "Africa", "CONFLICT", "HIGH", "DRC Congo M23 Goma Rwanda militia"),
    ("somalia", "Somalia / al-Shabaab", "Africa", "INSURGENCY", "HIGH", "Somalia al-Shabaab Mogadishu militant attack"),
    ("ethiopia", "Ethiopia Internal Conflict Risk", "Africa", "CONFLICT", "MODERATE", "Ethiopia Amhara Tigray Oromia clashes"),
    ("nigeria", "Nigeria Insurgency / Banditry", "Africa", "INSURGENCY", "HIGH", "Nigeria Boko Haram ISWAP bandit kidnapping attack"),
    ("sahel-mali", "Mali / Sahel Insurgency", "Africa", "INSURGENCY", "HIGH", "Mali JNIM Islamic State insurgency attack"),
    ("sahel-burkina", "Burkina Faso Insurgency", "Africa", "INSURGENCY", "HIGH", "Burkina Faso JNIM militant attack"),
    ("sahel-niger", "Niger Insurgency / Coup Fallout", "Africa", "INSURGENCY", "HIGH", "Niger JNIM Islamic State insurgency coup"),
    ("cameroon", "Cameroon Separatist Conflict", "Africa", "INSURGENCY", "MODERATE", "Cameroon Anglophone separatist attack"),
    ("chad", "Chad Security / Sahel Spillover", "Africa", "FLASHPOINT", "MODERATE", "Chad Sudan border rebels attack"),
    ("libya", "Libya Political / Militia Risk", "Africa", "CONFLICT", "MODERATE", "Libya militia Tripoli Benghazi clashes"),
    ("mozambique", "Mozambique Cabo Delgado", "Africa", "INSURGENCY", "MODERATE", "Mozambique Cabo Delgado insurgency Islamic State"),
    ("myanmar", "Myanmar Civil War", "Asia", "WAR", "HIGH", "Myanmar junta resistance civil war Mandalay Rakhine"),
    ("afghanistan", "Afghanistan Security Risk", "Asia", "INSURGENCY", "MODERATE", "Afghanistan Taliban ISIS-K attack Kabul"),
    ("pakistan", "Pakistan Militancy / Border Risk", "Asia", "INSURGENCY", "HIGH", "Pakistan TTP Balochistan militant attack"),
    ("taiwan", "Taiwan Strait Pressure", "Indo-Pacific", "FLASHPOINT", "HIGH", "Taiwan China PLA blockade military drills"),
    ("korea", "Korean Peninsula", "Indo-Pacific", "FLASHPOINT", "HIGH", "North Korea missile South Korea artillery nuclear"),
    ("south-china-sea", "South China Sea Flashpoint", "Indo-Pacific", "FLASHPOINT", "MODERATE", "South China Sea Philippines China collision"),
    ("haiti", "Haiti Gang Conflict", "Caribbean", "CRIMINAL CONFLICT", "CRITICAL", "Haiti gangs Port-au-Prince police kidnapping"),
    ("mexico", "Mexico Cartel Conflict", "Latin America", "CRIMINAL CONFLICT", "HIGH", "Mexico cartel CJNG Sinaloa cartel attack drone explosive kidnapping"),
    ("ecuador", "Ecuador Organized Crime Conflict", "Latin America", "CRIMINAL CONFLICT", "HIGH", "Ecuador gangs prison violence cartel attack"),
    ("colombia", "Colombia Armed Groups", "Latin America", "INSURGENCY", "MODERATE", "Colombia ELN FARC dissidents armed group attack"),
]

BREAKING_RE = re.compile(r"strike|attack|killed|drone|missile|blockade|escalat|invasion|ceasefire|bomb|shell|offensive|mobiliz|sanction|hostage|explosion|raid|coup|clash|shooting", re.I)
CONFLICT_RE = re.compile(r"war|conflict|military|troops|forces|attack|strike|missile|drone|airstrike|shelling|insurgent|militant|clash|ceasefire|coup|cartel|gang|kidnap", re.I)
ECON_RE = re.compile(r"oil|gas|inflation|tariff|trade|market|stocks|bond|currency|dollar|euro|yuan|yen|interest rate|central bank|economy|sanction|shipping|freight|commodity", re.I)
DIPLO_RE = re.compile(r"talks|summit|negotiat|diplomat|ceasefire|peace|agreement|treaty|alliance|sanction|tariff|embassy|envoy", re.I)
MIL_RE = re.compile(r"missile|drone|troops|military|army|navy|air force|fighter|carrier|exercise|mobiliz|weapons|defense", re.I)


def fetch(url):
    req = Request(url, headers={"User-Agent": "GlobalPulse/3.0 (+https://github.com/lifetimeballer1/global-pulse)"})
    with urlopen(req, timeout=25) as r:
        return r.read()


def clean(value):
    return re.sub(r"<[^>]+>", " ", value or "").replace("&nbsp;", " ").strip()


def text(node, tag):
    x = node.find(tag)
    return (x.text or "").strip() if x is not None and x.text else ""


def is_breaking(title, summary, pub):
    return bool(BREAKING_RE.search(f"{title} {summary}")) or bool(re.search(r"\bSep(?:tember)?\s*0?[1-3]\b", pub or "", re.I))


def score_dimension(texts, regex, base=50):
    hits = sum(1 for t in texts if regex.search(t))
    return max(0, min(100, base + hits * 4))


def make_conflicts(stories):
    corpus = [f"{s['title']} {s['summary']}" for s in stories]
    result = []
    for cid, name, region, kind, baseline, keywords in CONFLICTS:
        terms = re.compile(keywords, re.I)
        matches = [s for s in stories if terms.search(f"{s['title']} {s['summary']}")]
        activity = min(100, 42 + len(matches) * 11)
        if baseline == "CRITICAL": activity = max(activity, 72)
        elif baseline == "HIGH": activity = max(activity, 58)
        escalation = "CRITICAL" if activity >= 82 else "HIGH" if activity >= 68 else "MODERATE" if activity >= 52 else "LOW"
        confidence = "CORROBORATED" if len({s['sourceLabel'] for s in matches}) >= 2 else "DEVELOPING" if matches else "MONITORING"
        recent = matches[0]['title'] if matches else "No matching headline in the latest public feed window."
        result.append({
            "id": cid, "name": name, "region": region, "category": kind,
            "status": "Active monitoring", "actors": "See latest reporting and source links.",
            "recent": recent[:180], "escalation": escalation,
            "activityScore": activity,
            "facts": f"Monitored theater; {len(matches)} matching items in the current public feed window.",
            "analysis": "Activity score is derived from current source coverage and keyword/event signals; it is not a casualty count or ground-truth battlefield assessment.",
            "confidence": confidence,
            "sourceCount": len({s['sourceLabel'] for s in matches}),
            "lastSignal": matches[0]['time'] if matches else None,
        })
    return result


def main():
    DATA.mkdir(exist_ok=True)
    old = load_json(SNAP, {})
    stories, errors = [], []
    for label, url, kind in FEEDS:
        try:
            root = ET.fromstring(fetch(url))
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for item in items[:18]:
                title = clean(text(item, "title") or text(item, "{http://www.w3.org/2005/Atom}title"))
                link = text(item, "link")
                if not link:
                    link_node = item.find("{http://www.w3.org/2005/Atom}link")
                    link = link_node.attrib.get("href", "") if link_node is not None else ""
                summary = clean(text(item, "description") or text(item, "{http://www.w3.org/2005/Atom}summary"))
                pub = text(item, "pubDate") or text(item, "{http://www.w3.org/2005/Atom}updated")
                if not title or not link: continue
                stories.append({
                    "id": hashlib.sha1(link.encode()).hexdigest()[:12],
                    "sourceLabel": label, "sourceType": kind,
                    "title": title[:240], "summary": summary[:320], "source": link,
                    "time": pub, "tag": "Breaking" if is_breaking(title, summary, pub) else "World",
                    "confidence": "DEVELOPING", "breaking": is_breaking(title, summary, pub),
                })
        except Exception as exc:
            errors.append(f"{label}: {type(exc).__name__}")

    unique, seen = [], set()
    for s in stories:
        if s["id"] not in seen:
            seen.add(s["id"]); unique.append(s)
    unique.sort(key=lambda s: (not s["breaking"], s["sourceLabel"], s["title"]))
    stories = unique[:80]
    old_ids = {s.get("id") for s in old.get("stories", [])}
    new_items = [s for s in stories if s["id"] not in old_ids]

    texts = [f"{s['title']} {s['summary']}" for s in stories]
    breakdown = {
        "Conflict activity": score_dimension(texts, CONFLICT_RE, 45),
        "Diplomatic strain": score_dimension(texts, DIPLO_RE, 40),
        "Economic pressure": score_dimension(texts, ECON_RE, 40),
        "Market volatility": score_dimension(texts, re.compile(r"market|stocks|bond|currency|oil|gas|VIX|volatil", re.I), 38),
        "Military posture": score_dimension(texts, MIL_RE, 42),
    }
    tension = round(sum(breakdown.values()) / len(breakdown))
    old_tension = old.get("tension")
    delta = tension - old_tension if isinstance(old_tension, (int, float)) else 0

    changes = [{"kind": "breaking" if s["breaking"] else "new reporting", "title": s["title"][:140], "detail": f"{s['sourceLabel']} · {s['sourceType']} · {s['confidence']}"} for s in new_items[:8]]
    if not changes:
        changes = [{"kind": "refresh", "title": "Public sources checked — no new unique headlines", "detail": f"{len(FEEDS)} feeds checked; {len(stories)} current stories retained."}]

    conflicts = make_conflicts(stories)
    now = datetime.now(timezone.utc).isoformat()
    snapshot = {
        "updatedAt": now,
        "sourceStatus": f"{len(stories)} stories · {len(new_items)} new · {len(FEEDS)-len(errors)}/{len(FEEDS)} feeds healthy",
        "dataNote": "Public RSS aggregation. Scores are transparent analytical indicators derived from source coverage and event-language signals; they are not official conflict severity measurements.",
        "tension": tension, "tensionDelta": delta, "breakdownScores": breakdown,
        "changes": changes, "conflicts": conflicts,
        "markers": old.get("markers", []), "social": old.get("social", []), "stories": stories,
        "sourceHealth": [{"name": label, "type": kind, "status": "error" if any(e.startswith(label + ":") for e in errors) else "ok"} for label, _, kind in FEEDS],
    }
    SNAP.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    history = load_json(HIST, [])
    history.append({"updatedAt": now, "tension": tension, "delta": delta})
    HIST.write_text(json.dumps(history[-240:], ensure_ascii=False, indent=2) + "\n")
    SOURCES.write_text(json.dumps({"updatedAt": now, "feeds": [{"name": a, "url": b, "type": c, "domain": urlparse(b).netloc} for a,b,c in FEEDS], "errors": errors}, indent=2) + "\n")
    print(snapshot["sourceStatus"], "tension", tension, "conflicts", len(conflicts))
    if errors: print("errors:", "; ".join(errors))


def load_json(path, default):
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except Exception:
        return default


if __name__ == "__main__":
    main()
