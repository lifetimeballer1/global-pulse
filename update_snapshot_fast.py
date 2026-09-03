#!/usr/bin/env python3
"""Parallel snapshot builder using the existing Global Pulse source catalog."""
from __future__ import annotations

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import update_snapshot as base

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
HIST = DATA / "history.json"
SOURCES = DATA / "sources.json"
MAX_WORKERS = 10
SCORE_VERSION = 3

CLIMATE_RE = re.compile(r"\b(drought|water shortage|water stress|water scarcity|reservoir|water supply|flood|flooding|cyclone|hurricane|typhoon|storm surge|landslide|heatwave|heat wave|extreme heat|wildfire|forest fire|bushfire|extreme cold|food insecurity|food crisis|famine|acute hunger|hunger|crop failure|harvest failure|epidemic|outbreak|cholera|malaria|avian flu|pandemic|disease outbreak)\b", re.I)
MARKET_RE = re.compile(r"\b(stock market|stocks|shares|bond yields?|treasury yields?|currency|forex|exchange rate|dollar|euro|yen|yuan|oil prices?|crude prices?|natural gas prices?|market volatility|market selloff|market rally|volatility index)\b", re.I)


def parse_feed(label, url, kind):
    rows, error = [], None
    try:
        root = ET.fromstring(base.fetch(url))
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for item in items[:18]:
            title = base.clean(base.text(item, "title") or base.text(item, "{http://www.w3.org/2005/Atom}title"))
            link = base.text(item, "link")
            if not link:
                node = item.find("{http://www.w3.org/2005/Atom}link")
                link = node.attrib.get("href", "") if node is not None else ""
            summary = base.clean(base.text(item, "description") or base.text(item, "{http://www.w3.org/2005/Atom}summary"))
            pub = base.text(item, "pubDate") or base.text(item, "updated") or base.text(item, "{http://www.w3.org/2005/Atom}updated")
            if not title or not link:
                continue
            breaking = base.is_breaking(title, summary)
            rows.append({"id": hashlib.sha1(link.encode()).hexdigest()[:12], "sourceLabel": label, "sourceType": kind, "title": title[:240], "summary": summary[:420], "source": link, "url": link, "time": pub, "tag": "Breaking" if breaking else "World", "confidence": "DEVELOPING", "breaking": breaking})
    except Exception as exc:
        error = f"{label}: {type(exc).__name__}"
    return rows, error


def weighted_total(stories):
    return sum(max(0.05, base.recency_weight(s.get("time"))) for s in stories)


def normalized_score(stories, regex, base_score=40, eligible=None, boost_terms=()):
    """Calibrate a driver against its relevant reporting pool, not raw headline count.

    Adding a new politics, climate, or disaster feed must not automatically raise
    every tension driver. Each driver therefore uses only an appropriate source
    pool and measures the weighted share of that pool carrying the signal.
    """
    pool = [s for s in stories if eligible is None or s.get("sourceType") in eligible]
    if not pool:
        return int(base_score)
    total = weighted_total(pool)
    if total <= 0:
        return int(base_score)
    matched = 0.0
    for story in pool:
        text = f"{story.get('title', '')} {story.get('summary', '')}"
        weight = max(0.05, base.recency_weight(story.get("time")))
        if regex.search(text):
            matched += weight
            if boost_terms and any(re.search(term, text, re.I) for term in boost_terms):
                matched += weight * 0.35
    share = min(1.0, matched / total)
    # 35-100 is the intended monitoring range for an active driver; baselines
    # remain stable when feeds are unavailable rather than falling to zero.
    signal = min(65.0, 65.0 * share)
    return int(round(max(0.0, min(100.0, base_score + signal))))


def climate_metrics(stories):
    groups = {
        "Drought & water": re.compile(r"\b(drought|water shortage|water stress|water scarcity|reservoir|water supply)\b", re.I),
        "Floods & storms": re.compile(r"\b(flood|flooding|cyclone|hurricane|typhoon|storm surge|landslide|glacier)\b", re.I),
        "Heat & fire": re.compile(r"\b(heatwave|heat wave|extreme heat|wildfire|forest fire|bushfire|extreme cold)\b", re.I),
        "Food security": re.compile(r"\b(famine|food insecurity|food crisis|acute hunger|hunger|crop failure|harvest failure|food shortage)\b", re.I),
        "Health outbreaks": re.compile(r"\b(epidemic|outbreak|cholera|malaria|avian flu|pandemic|disease outbreak)\b", re.I),
    }
    climate_pool = {"climate-hazard", "food-security", "humanitarian", "international", "regional", "live"}
    return {name: normalized_score(stories, rx, 25, climate_pool) for name, rx in groups.items()}


def build_early_warning(tension, breakdown, history):
    """Compare only snapshots produced by the current scoring model."""
    points = [p for p in history if isinstance(p, dict) and p.get("scoreVersion") == SCORE_VERSION and isinstance(p.get("tension"), (int, float))]
    recent = [float(p["tension"]) for p in points[-12:]]
    prior = [float(p["tension"]) for p in points[-36:-12]]
    recent_avg = sum(recent) / len(recent) if recent else float(tension)
    prior_avg = sum(prior) / len(prior) if prior else recent_avg
    momentum = round(recent_avg - prior_avg, 1)
    strongest_name, strongest_value = max(breakdown.items(), key=lambda item: item[1]) if breakdown else ("Overall tension", tension)
    if tension >= 75 or momentum >= 10:
        level = "HIGH"
    elif tension >= 55 or momentum >= 5:
        level = "ELEVATED"
    else:
        level = "WATCH"
    return {"level": level, "score": int(round(tension)), "momentum": momentum, "direction": "rising" if momentum >= 2 else "falling" if momentum <= -2 else "stable", "strongestDriver": strongest_name, "strongestDriverScore": int(strongest_value), "method": "Recent 12 snapshots versus the preceding 24 snapshots from the current scoring model only."}


def main():
    DATA.mkdir(exist_ok=True)
    old = base.load_json(SNAP, {})
    history = base.load_json(HIST, [])
    stories, errors = [], []
    feeds = list(dict.fromkeys(base.FEEDS))
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(parse_feed, *feed) for feed in feeds]
        for future in as_completed(futures):
            rows, error = future.result()
            stories.extend(rows)
            if error:
                errors.append(error)

    unique, seen = [], set()
    for story in stories:
        if story["id"] not in seen:
            seen.add(story["id"])
            unique.append(story)
    unique.sort(key=lambda s: base.parse_time(s["time"]) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    stories = unique[:300]
    old_ids = {s.get("id") for s in old.get("stories", [])}
    new_items = [s for s in stories if s["id"] not in old_ids]

    all_sources = None
    politics_pool = {"us-politics", "world-politics", "analysis"}
    economics_pool = {"economics", "international", "regional", "live"}
    conflict_pool = {"live", "international", "regional", "middle-east", "africa", "americas", "analysis"}
    military_boost = (r"airstrike", r"missile", r"drone", r"troops", r"offensive", r"shelling", r"invasion")
    breakdown = {
        "Conflict activity": normalized_score(stories, re.compile(r"\b(war|armed conflict|fighting|battle|offensive|airstrike|shelling|invasion|insurgent|insurgency|militant attack|clash|bombing|hostage crisis)\b", re.I), 35, conflict_pool, military_boost),
        "Diplomatic strain": normalized_score(stories, base.DIPLO_RE, 32, politics_pool, (r"sanction", r"expulsion", r"ultimatum", r"diplomatic crisis")),
        "Economic pressure": normalized_score(stories, base.ECON_RE, 32, economics_pool, (r"tariff", r"sanction", r"supply disruption", r"recession")),
        "Market volatility": normalized_score(stories, MARKET_RE, 30, {"economics", "international", "regional", "live"}, (r"selloff", r"plunge", r"surge", r"volatility")),
        "Military posture": normalized_score(stories, base.MIL_RE, 34, conflict_pool, military_boost),
        "Climate & humanitarian pressure": normalized_score(stories, CLIMATE_RE, 25, {"climate-hazard", "food-security", "humanitarian", "international", "regional", "live"}),
    }
    climate = climate_metrics(stories)
    weights = {
        "Conflict activity": 0.22,
        "Diplomatic strain": 0.15,
        "Economic pressure": 0.16,
        "Market volatility": 0.10,
        "Military posture": 0.25,
        "Climate & humanitarian pressure": 0.12,
    }
    tension = round(sum(breakdown[k] * weights[k] for k in weights))
    old_tension = old.get("tension")
    delta = tension - old_tension if isinstance(old_tension, (int, float)) and old.get("scoreVersion") == SCORE_VERSION else 0
    changes = [{"kind": "breaking" if s["breaking"] else "new reporting", "title": s["title"][:150], "detail": f"{s['sourceLabel']} · {s['sourceType']} · {s['confidence']}"} for s in new_items[:10]]
    if not changes:
        changes = [{"kind": "refresh", "title": "Public sources checked — no new unique headlines", "detail": f"{len(feeds)} feeds checked; {len(stories)} current stories retained."}]
    conflicts = base.make_conflicts(stories, old)
    now = datetime.now(timezone.utc).isoformat()
    history_points = [p for p in history if isinstance(p, dict) and p.get("scoreVersion") == SCORE_VERSION]
    history_with_current = history_points + [{"updatedAt": now, "tension": tension, "delta": delta, "scoreVersion": SCORE_VERSION}]
    early_warning = build_early_warning(tension, breakdown, history_with_current)
    snapshot = {
        "updatedAt": now,
        "scoreVersion": SCORE_VERSION,
        "sourceStatus": f"{len(stories)} stories · {len(new_items)} new · {len(feeds)-len(errors)}/{len(feeds)} feeds healthy",
        "dataNote": "Public RSS aggregation plus keyless disaster/humanitarian feeds. Driver scores are calibrated by relevant reporting pools; adding sources does not itself raise tension.",
        "tension": tension,
        "tensionDelta": delta,
        "breakdownScores": breakdown,
        "climatePressure": climate,
        "earlyWarning": early_warning,
        "changes": changes,
        "conflicts": conflicts,
        "markers": old.get("markers", []),
        "social": old.get("social", []),
        "stories": stories,
        "sourceHealth": [{"name": label, "type": kind, "status": "error" if any(e.startswith(label + ":") for e in errors) else "ok"} for label, _, kind in feeds],
    }
    SNAP.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HIST.write_text(json.dumps(history_with_current[-288:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SOURCES.write_text(json.dumps({"updatedAt": now, "feeds": [{"name": a, "url": b, "type": c, "domain": urlparse(b).netloc} for a, b, c in feeds], "errors": errors}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(snapshot["sourceStatus"], "tension", tension, "early warning", early_warning["level"], "climate", breakdown["Climate & humanitarian pressure"], "conflicts", len(conflicts))
    if errors:
        print("errors:", "; ".join(errors))


if __name__ == "__main__":
    main()
