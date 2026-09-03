#!/usr/bin/env python3
"""Parallel snapshot builder using the existing Global Pulse scoring engine."""
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

CLIMATE_RE = re.compile(r"drought|flood|flooding|wildfire|forest fire|cyclone|hurricane|typhoon|heatwave|heat wave|extreme heat|extreme cold|storm|landslide|glacier|sea level|water shortage|water stress|food insecurity|food crisis|famine|hunger|crop failure|harvest failure|epidemic|outbreak|disease|cholera|malaria|avian flu|pandemic", re.I)


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
            pub = base.text(item, "pubDate") or base.text(item, "{http://www.w3.org/2005/Atom}updated")
            if not title or not link:
                continue
            breaking = base.is_breaking(title, summary)
            rows.append({"id": hashlib.sha1(link.encode()).hexdigest()[:12], "sourceLabel": label, "sourceType": kind, "title": title[:240], "summary": summary[:420], "source": link, "url": link, "time": pub, "tag": "Breaking" if breaking else "World", "confidence": "DEVELOPING", "breaking": breaking})
    except Exception as exc:
        error = f"{label}: {type(exc).__name__}"
    return rows, error


def climate_metrics(stories):
    """Transparent climate/humanitarian signal components from current public reporting."""
    groups = {
        "Drought & water": re.compile(r"drought|water shortage|water stress|reservoir|water supply", re.I),
        "Floods & storms": re.compile(r"flood|flooding|cyclone|hurricane|typhoon|storm|landslide|glacier", re.I),
        "Heat & fire": re.compile(r"heatwave|heat wave|extreme heat|wildfire|forest fire|extreme cold", re.I),
        "Food security": re.compile(r"famine|food insecurity|food crisis|hunger|crop failure|harvest failure", re.I),
        "Health outbreaks": re.compile(r"epidemic|outbreak|disease|cholera|malaria|avian flu|pandemic", re.I),
    }
    out = {}
    for name, rx in groups.items():
        out[name] = min(100, base.score_dimension(stories, rx, 34))
    return out


def build_early_warning(tension, breakdown, history):
    """Turn recent tension history into a transparent early-warning signal."""
    points = [p for p in history if isinstance(p, dict) and isinstance(p.get("tension"), (int, float))]
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
    return {"level": level, "score": int(round(tension)), "momentum": momentum, "direction": "rising" if momentum >= 2 else "falling" if momentum <= -2 else "stable", "strongestDriver": strongest_name, "strongestDriverScore": int(strongest_value), "method": "Recent 12 snapshots versus the preceding 24 snapshots, plus current tension level."}


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
    breakdown = {
        "Conflict activity": base.score_dimension(stories, base.CONFLICT_RE, 35),
        "Diplomatic strain": base.score_dimension(stories, base.DIPLO_RE, 32),
        "Economic pressure": base.score_dimension(stories, base.ECON_RE, 32),
        "Market volatility": base.score_dimension(stories, re.compile(r"market|stocks|bond|currency|oil|gas|volatil", re.I), 30),
        "Military posture": base.score_dimension(stories, base.MIL_RE, 34),
        "Climate & humanitarian pressure": base.score_dimension(stories, CLIMATE_RE, 34),
    }
    climate = climate_metrics(stories)
    tension = round(sum(breakdown.values()) / len(breakdown))
    old_tension = old.get("tension")
    delta = tension - old_tension if isinstance(old_tension, (int, float)) else 0
    changes = [{"kind": "breaking" if s["breaking"] else "new reporting", "title": s["title"][:150], "detail": f"{s['sourceLabel']} · {s['sourceType']} · {s['confidence']}"} for s in new_items[:10]]
    if not changes:
        changes = [{"kind": "refresh", "title": "Public sources checked — no new unique headlines", "detail": f"{len(feeds)} feeds checked; {len(stories)} current stories retained."}]
    conflicts = base.make_conflicts(stories, old)
    now = datetime.now(timezone.utc).isoformat()
    history_with_current = history + [{"updatedAt": now, "tension": tension, "delta": delta}]
    early_warning = build_early_warning(tension, breakdown, history_with_current)
    snapshot = {"updatedAt": now, "sourceStatus": f"{len(stories)} stories · {len(new_items)} new · {len(feeds)-len(errors)}/{len(feeds)} feeds healthy", "dataNote": "Public RSS aggregation plus keyless disaster/humanitarian feeds. Climate & humanitarian pressure is a monitoring signal derived from current reporting and disaster alerts; it is not a climate model or official hazard index.", "tension": tension, "tensionDelta": delta, "breakdownScores": breakdown, "climatePressure": climate, "earlyWarning": early_warning, "changes": changes, "conflicts": conflicts, "markers": old.get("markers", []), "social": old.get("social", []), "stories": stories, "sourceHealth": [{"name": label, "type": kind, "status": "error" if any(e.startswith(label + ":") for e in errors) else "ok"} for label, _, kind in feeds]}
    SNAP.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HIST.write_text(json.dumps(history_with_current[-288:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SOURCES.write_text(json.dumps({"updatedAt": now, "feeds": [{"name": a, "url": b, "type": c, "domain": urlparse(b).netloc} for a, b, c in feeds], "errors": errors}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(snapshot["sourceStatus"], "tension", tension, "early warning", early_warning["level"], "climate", breakdown["Climate & humanitarian pressure"], "conflicts", len(conflicts))
    if errors:
        print("errors:", "; ".join(errors))


if __name__ == "__main__":
    main()
