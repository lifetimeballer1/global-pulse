#!/usr/bin/env python3
"""Build the canonical intelligence layer from existing source-backed articles.

This is deliberately conservative: it creates entities/events only when there
is source evidence. The 35-node presentation limit remains in the legacy Brain
builder and is not applied here.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from intelligence_schema import SCHEMA_VERSION, empty_document, validate_document

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INPUT = DATA / "live_articles.json"
OUTPUT = DATA / "canonical_intelligence.json"

ENTITY_ALIASES = {
    "United States": ("country", ["united states", "u.s.", "u.s", "usa", "american", "washington"]),
    "China": ("country", ["china", "chinese", "beijing"]),
    "Russia": ("country", ["russia", "russian", "moscow", "putin"]),
    "Ukraine": ("country", ["ukraine", "ukrainian", "kyiv", "zelensky"]),
    "Taiwan": ("country", ["taiwan", "taiwanese", "taipei"]),
    "Iran": ("country", ["iran", "iranian", "tehran"]),
    "Israel": ("country", ["israel", "israeli", "jerusalem"]),
    "NATO": ("international_organization", ["nato"]),
    "European Union": ("international_organization", ["european union", "eu"]),
    "United Nations": ("international_organization", ["united nations", "u.n.", "un"]),
    "People's Liberation Army": ("military", ["people's liberation army", "pla"]),
    "U.S. Department of Defense": ("government_agency", ["department of defense", "defense department", "pentagon"]),
    "U.S. Department of State": ("government_agency", ["department of state", "state department"]),
    "U.S. Treasury": ("government_agency", ["u.s. treasury", "treasury department"]),
    "Federal Reserve": ("financial_institution", ["federal reserve", "fed"]),
}

EVENT_PATTERNS = [
    ("sanction", r"\b(sanction|sanctions|sanctioned|sanctioning)\b"),
    ("military_action", r"\b(strike|strikes|airstrike|airstrikes|missile|bombing|deployment|deploys|military operation|troops)\b"),
    ("diplomatic_action", r"\b(meet|meets|meeting|talks|negotiat|diplomatic|envoy|summit|ceasefire)\b"),
    ("economic_action", r"\b(stimulus|interest rate|rate cut|tariff|tariffs|tax|capital|investment|economic policy)\b"),
    ("trade_action", r"\b(trade|export|exports|import|imports|supply chain|customs)\b"),
    ("technology_action", r"\b(chip|chips|semiconductor|semiconductors|artificial intelligence|ai|technology|tech)\b"),
    ("energy_action", r"\b(oil|gas|lng|energy|electricity|power grid|nuclear|uranium)\b"),
    ("cyber_activity", r"\b(cyber|cyberattack|cyberattack|hacking|malware|ransomware)\b"),
    ("political_action", r"\b(election|elections|vote|voting|parliament|congress|president|government)\b"),
]


def stable_id(prefix: str, *parts: str) -> str:
    raw = "|".join(parts).encode("utf-8", "ignore")
    return f"{prefix}-{hashlib.sha256(raw).hexdigest()[:16]}"


def article_text(article: dict[str, Any]) -> str:
    return " ".join(str(article.get(k) or "") for k in ("title", "summary_snippet", "summary", "description", "content")).strip()


def main() -> int:
    if not INPUT.exists():
        print(f"ERROR: missing input {INPUT}")
        return 2
    try:
        raw = json.loads(INPUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid input JSON: {exc}")
        return 2

    document = empty_document()
    document["schema_version"] = SCHEMA_VERSION
    document["metadata"].update({"input": str(INPUT.relative_to(ROOT)), "method": "conservative-source-backed-v1"})
    entities: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    events: dict[str, dict[str, Any]] = {}
    relationships: dict[str, dict[str, Any]] = {}

    articles = raw.get("articles", []) if isinstance(raw, dict) else []
    for article in articles:
        if not isinstance(article, dict):
            continue
        title = str(article.get("title") or "").strip()
        url = str(article.get("url") or "").strip()
        source = str(article.get("source") or "").strip()
        if not title or not url:
            continue
        ev_id = stable_id("evd", url, title)
        evidence[ev_id] = {
            "id": ev_id,
            "title": title,
            "source": source or "Unknown public source",
            "url": url,
            "published_at": str(article.get("published_date") or ""),
            "reliability": 0.5,
            "excerpt": str(article.get("summary_snippet") or "")[:500],
        }
        text = article_text(article).lower()
        matched: list[str] = []
        for canonical, (entity_type, aliases) in ENTITY_ALIASES.items():
            if any(re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", text) for alias in aliases):
                entity_id = stable_id("ent", canonical)
                entity = entities.setdefault(entity_id, {
                    "id": entity_id,
                    "canonical_name": canonical,
                    "entity_type": entity_type,
                    "aliases": aliases,
                    "country": canonical if entity_type == "country" else None,
                    "region": None,
                    "importance": 0.0,
                    "mention_count": 0,
                    "evidence_ids": [],
                })
                entity["mention_count"] += 1
                entity["importance"] = min(1.0, entity["importance"] + 0.02)
                if ev_id not in entity["evidence_ids"]:
                    entity["evidence_ids"].append(ev_id)
                matched.append(entity_id)

        event_types = [kind for kind, pattern in EVENT_PATTERNS if re.search(pattern, text, re.I)]
        for event_type in event_types[:3]:
            event_id = stable_id("evt", ev_id, event_type)
            events[event_id] = {
                "id": event_id,
                "event_type": event_type,
                "title": title,
                "timestamp": str(article.get("published_date") or ""),
                "location": None,
                "severity": 0.0,
                "confidence": 0.5,
                "entity_ids": matched,
                "evidence_ids": [ev_id],
            }

        for index, source_id in enumerate(matched):
            for target_id in matched[index + 1:]:
                if source_id == target_id:
                    continue
                pair = sorted((source_id, target_id))
                key = "|".join(pair)
                relationship = relationships.setdefault(key, {
                    "source_entity_id": pair[0],
                    "relationship_type": "mentioned_with",
                    "target_entity_id": pair[1],
                    "confidence": 0.5,
                    "weight": 0.0,
                    "first_seen": str(article.get("published_date") or ""),
                    "last_seen": str(article.get("published_date") or ""),
                    "evidence_ids": [],
                    "event_ids": [],
                })
                relationship["weight"] += 1.0
                if ev_id not in relationship["evidence_ids"]:
                    relationship["evidence_ids"].append(ev_id)

    document["entities"] = list(entities.values())
    document["events"] = list(events.values())
    document["relationships"] = list(relationships.values())
    document["evidence"] = list(evidence.values())
    document["signals"] = []
    document["metadata"]["article_count"] = len(articles)

    errors = validate_document(document)
    if errors:
        print(f"FAIL: canonical build produced {len(errors)} validation errors")
        for error in errors[:25]:
            print(f" - {error}")
        return 1

    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: built canonical intelligence: entities={len(entities)} events={len(events)} relationships={len(relationships)} evidence={len(evidence)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
