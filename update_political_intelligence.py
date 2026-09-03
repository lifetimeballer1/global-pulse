#!/usr/bin/env python3
"""Build an automatic, provenance-first political intelligence layer.

This is intentionally deterministic and conservative. It does not decide what is
true from outlet reputation alone. It clusters similar reports, counts independent
source domains, extracts issue/entity signals, and labels a story corroborated only
when independent domains report a sufficiently similar event in a limited time
window. Otherwise it remains single-source/developing.
"""
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"

ENTITY_PATTERNS = {
    "Donald Trump": r"\btrump|donald trump|president trump\b",
    "White House": r"\bwhite house\b",
    "Congress": r"\bcongress|house of representatives\b",
    "U.S. Senate": r"\bsenate|senator\b",
    "Supreme Court": r"\bsupreme court|scotus\b",
    "Democrats": r"\bdemocrat|democratic party|democrats\b",
    "Republicans": r"\brepublican|gop|republicans\b",
    "Federal Reserve": r"\bfederal reserve|fed\b",
    "Department of Justice": r"\bdepartment of justice|doj\b",
    "China": r"\bchina|chinese|beijing\b",
    "Russia": r"\brussia|russian|moscow|putin\b",
    "Ukraine": r"\bukraine|ukrainian|kyiv|zelensky\b",
    "Iran": r"\biran|iranian|tehran\b",
    "Israel": r"\bisrael|israeli|tel aviv\b",
    "NATO": r"\bnato\b",
    "European Union": r"\beuropean union|eu\b",
}

TOPICS = {
    "Elections": r"\belection|midterm|primary|ballot|voting|voter|polling|redistrict|campaign\b",
    "Congress": r"\bcongress|senate|house of representatives|bill|legislation|filibuster|committee\b",
    "Executive": r"\bexecutive order|white house|president|administration|cabinet|agency\b",
    "Courts": r"\bsupreme court|federal court|judge|lawsuit|ruling|appeal|injunction\b",
    "Immigration": r"\bimmigration|deport|border|asylum|visa|migrant\b",
    "Trade": r"\btariff|trade|export|import|customs\b",
    "Foreign Policy": r"\bdiplomacy|diplomatic|summit|treaty|alliance|sanction|foreign policy|envoy\b",
    "Defense": r"\bdefense|military|pentagon|troops|missile|drone|airstrike|navy\b",
    "Economy": r"\binflation|jobs|employment|gdp|interest rate|central bank|economy|market|stocks|bond|oil\b",
    "Public Opinion": r"\bpoll|approval|favorability|survey|voters|opinion\b",
}

EVENT_WORDS = set(re.findall(r"[a-z]{4,}", "".join(TOPICS.values()).lower()))
STOP = set("the and that with from for this have has were will into about after before while says said their they them president latest report reports politics political news according amid over under into its are was been being would could should where which what when how more than also very against between through during there here").split())

def clean_text(story):
    return re.sub(r"\s+", " ", f"{story.get('title','')} {story.get('summary','')}").strip().lower()

def tokens(story):
    words = re.findall(r"[a-z0-9]{4,}", clean_text(story))
    return {w for w in words if w not in STOP}

def entities(story):
    text = clean_text(story)
    return [name for name, pat in ENTITY_PATTERNS.items() if re.search(pat, text, re.I)]

def topics(story):
    text = clean_text(story)
    return [name for name, pat in TOPICS.items() if re.search(pat, text, re.I)]

def domain(story):
    url = str(story.get("source") or story.get("url") or "")
    host = urlparse(url).netloc.lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    if host.endswith("gdeltproject.org"):
        # GDELT is an aggregator, not an independent outlet for corroboration.
        label = str(story.get("sourceLabel") or "").lower()
        for known in ("cnn", "axios", "morsereport"):
            if known in label:
                return known
        return "gdelt-aggregate"
    return host or str(story.get("sourceLabel") or "unknown").lower()

def parse_time(story):
    value = story.get("time") or story.get("published") or story.get("updatedAt")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

def similarity(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))

def event_match(a, b):
    ea, eb = set(entities(a)), set(entities(b))
    ta, tb = set(topics(a)), set(topics(b))
    shared_entities = len(ea & eb)
    shared_topics = len(ta & tb)
    sim = similarity(a, b)
    if shared_entities >= 2 and shared_topics >= 1 and sim >= 0.18:
        return True
    if shared_entities >= 1 and shared_topics >= 1 and sim >= 0.32:
        return True
    return False

def main():
    data = json.loads(SNAP.read_text(encoding="utf-8"))
    stories = data.get("stories", [])
    political = [s for s in stories if s.get("intelligenceLayer") in ("us-politics", "world-politics")]

    for s in political:
        s["politicalEntities"] = entities(s)
        s["politicalTopics"] = topics(s)
        s["sourceDomain"] = domain(s)
        s["evidenceLevel"] = "SINGLE-SOURCE"
        s["corroboratingSources"] = []

    # Candidate reports are restricted to the same layer and a 24-hour window.
    for i, story in enumerate(political):
        t = parse_time(story)
        matches = []
        for j, other in enumerate(political):
            if i == j:
                continue
            if story["sourceDomain"] == other["sourceDomain"]:
                continue
            ot = parse_time(other)
            if t and ot and abs((t - ot).total_seconds()) > 24 * 3600:
                continue
            if event_match(story, other):
                matches.append(other)
        domains = sorted({m["sourceDomain"] for m in matches if m.get("sourceDomain") not in ("", "unknown", "gdelt-aggregate")})
        if domains:
            story["evidenceLevel"] = "CORROBORATED"
            story["corroboratingSources"] = domains[:8]

    # Rank for the dashboard without pretending the rank is factual truth.
    now = datetime.now(timezone.utc)
    for s in political:
        age = 48.0
        t = parse_time(s)
        if t:
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            age = max(0.0, (now - t).total_seconds() / 3600)
        recency = max(0, 48 - age) / 48 * 45
        corroboration = min(30, 15 * len(s.get("corroboratingSources", [])))
        breaking = 15 if s.get("breaking") else 0
        topic_bonus = min(10, 2 * len(s.get("politicalTopics", [])))
        s["politicalSignalScore"] = round(recency + corroboration + breaking + topic_bonus, 1)

    political.sort(key=lambda s: (s.get("politicalSignalScore", 0), s.get("time", "")), reverse=True)
    us = [s for s in political if s.get("intelligenceLayer") == "us-politics"]
    world = [s for s in political if s.get("intelligenceLayer") == "world-politics"]
    corroborated = [s for s in political if s.get("evidenceLevel") == "CORROBORATED"]
    source_counts = defaultdict(int)
    for s in political:
        source_counts[s.get("sourceDomain") or "unknown"] += 1

    data["politicalIntelligence"] = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "method": "Deterministic event clustering using entity/topic overlap, time proximity, and independent source domains.",
        "caveat": "Corroboration means independent public reports describe a sufficiently similar event; it is not proof that every claim in those reports is true.",
        "totalSignals": len(political),
        "usPoliticsSignals": len(us),
        "worldPoliticsSignals": len(world),
        "corroboratedSignals": len(corroborated),
        "singleSourceSignals": len(political) - len(corroborated),
        "sourceCounts": dict(sorted(source_counts.items(), key=lambda x: (-x[1], x[0]))),
        "topSignals": political[:60],
    }
    data["usPolitics"] = us
    data["worldPolitics"] = world
    SNAP.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("POLITICAL INTELLIGENCE:", len(political), "signals;", len(corroborated), "corroborated")

if __name__ == "__main__":
    main()
