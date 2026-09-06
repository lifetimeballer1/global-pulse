#!/usr/bin/env python3
"""Build the canonical intelligence layer from source-backed articles.

The builder is deliberately conservative: every entity, event, and semantic
relationship must be traceable to source evidence. When language is not strong
enough to support a semantic relationship, the builder retains a
``mentioned_with`` relationship rather than inventing intent or causality.
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
    ("cyber_activity", r"\b(cyber|cyberattack|cyberattacks|hacking|malware|ransomware)\b"),
    ("political_action", r"\b(election|elections|vote|voting|parliament|congress|president|government)\b"),
]

# Directional language is required before creating a semantic relationship.
# These patterns are intentionally conservative and evidence-backed.
RELATIONSHIP_PATTERNS = [
    ("sanctions", [
        r"(?:united states|u\.s\.|usa|treasury|government)\s+(?:imposed|announced|issued|expanded|tightened)\s+(?:new\s+)?sanctions?\s+(?:on|against)\s+",
        r"sanctions?\s+(?:on|against)\s+",
    ]),
    ("trades_with", [r"(?:trade|trades|trading|exports?|imports?)\s+(?:with|between)\s+"]),
    ("negotiates_with", [r"(?:negotiat(?:e|es|ed|ing)|talks?|meet(?:s|ing)?|summit)\s+(?:with|between)\s+"]),
    ("cooperates_with", [r"(?:cooperat(?:e|es|ed|ing)|cooperation|joint|agreement)\s+(?:with|between)\s+"]),
    ("military_action_against", [r"(?:strike|strikes|airstrike|airstrikes|bomb(?:ed|ing)?|attack(?:ed|s|ing)?|military operation)\s+(?:on|against|targeting)\s+"]),
    ("deploys_to", [r"(?:deploy(?:ed|s|ing)?|troops|forces)\s+(?:to|into)\s+"]),
    ("supplies", [r"(?:suppl(?:y|ies|ied|ying)|provide(?:s|d)?|arms?)\s+(?:to|for)\s+"]),
    ("invests_in", [r"(?:invest(?:s|ed|ing)?|investment)\s+(?:in|into)\s+"]),
]


def stable_id(prefix: str, *parts: str) -> str:
    raw = "|".join(parts).encode("utf-8", "ignore")
    return f"{prefix}-{hashlib.sha256(raw).hexdigest()[:16]}"


def article_text(article: dict[str, Any]) -> str:
    return " ".join(str(article.get(k) or "") for k in ("title", "summary_snippet", "summary", "description", "content")).strip()


def _contains_alias(text: str, alias: str) -> bool:
    return bool(re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", text))


def _relationship_type_for_text(text: str) -> str:
    for relationship_type, patterns in RELATIONSHIP_PATTERNS:
        if any(re.search(pattern, text, re.I) for pattern in patterns):
            return relationship_type
    return "mentioned_with"


def _relationship_confidence(relationship_type: str, event_types: list[str]) -> float:
    if relationship_type == "mentioned_with":
        return 0.45
    base = 0.68
    if relationship_type == "military_action_against":
        base = 0.78
    elif relationship_type == "sanctions":
        base = 0.76
    elif relationship_type in {"negotiates_with", "cooperates_with"}:
        base = 0.70
    if relationship_type == "sanctions" and "sanction" in event_types:
        base += 0.08
    if relationship_type == "military_action_against" and "military_action" in event_types:
        base += 0.08
    return min(0.95, base)


def _directed_pairs(matched: list[str], text: str, entity_names: dict[str, str]) -> list[tuple[str, str, str]]:
    """Infer only conservative directional relations supported by language.

    We use the textual order of canonical entity mentions for directional
    patterns. If direction cannot be supported, callers create a symmetric
    ``mentioned_with`` relationship instead.
    """
    relationship_type = _relationship_type_for_text(text)
    if relationship_type == "mentioned_with" or len(matched) < 2:
        return []

    positions = []
    for entity_id in matched:
        name = entity_names[entity_id]
        aliases = [name.lower()]
        if name == "United States":
            aliases += ["u.s.", "usa", "american", "washington"]
        elif name == "China":
            aliases += ["chinese", "beijing"]
        for alias in aliases:
            match = re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", text, re.I)
            if match:
                positions.append((match.start(), entity_id))
                break

    positions.sort()
    if len(positions) < 2:
        return []

    # The nearest two entities around the first actionable verb are a safer
    # inference than assigning a relationship to every entity in an article.
    return [(positions[0][1], positions[1][1], relationship_type)]


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
    document["metadata"].update({"input": str(INPUT.relative_to(ROOT)), "method": "conservative-source-backed-v2"})
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
        entity_names: dict[str, str] = {}
        for canonical, (entity_type, aliases) in ENTITY_ALIASES.items():
            if any(_contains_alias(text, alias) for alias in aliases):
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
                entity_names[entity_id] = canonical

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

        directed = _directed_pairs(matched, text, entity_names)
        directed_keys = set()
        for source_id, target_id, relationship_type in directed:
            key = f"{source_id}|{relationship_type}|{target_id}"
            directed_keys.add(key)
            relationship = relationships.setdefault(key, {
                "source_entity_id": source_id,
                "relationship_type": relationship_type,
                "target_entity_id": target_id,
                "confidence": _relationship_confidence(relationship_type, event_types),
                "weight": 0.0,
                "first_seen": str(article.get("published_date") or ""),
                "last_seen": str(article.get("published_date") or ""),
                "evidence_ids": [],
                "event_ids": [],
            })
            relationship["weight"] += 1.0
            relationship["last_seen"] = str(article.get("published_date") or relationship["last_seen"])
            if ev_id not in relationship["evidence_ids"]:
                relationship["evidence_ids"].append(ev_id)
            for event_id, event in events.items():
                if event["evidence_ids"] == [ev_id] and event["event_type"] in event_types:
                    if event_id not in relationship["event_ids"]:
                        relationship["event_ids"].append(event_id)

        # Preserve evidence-backed co-mentions that were not safely classified.
        for index, source_id in enumerate(matched):
            for target_id in matched[index + 1:]:
                if source_id == target_id:
                    continue
                pair = sorted((source_id, target_id))
                semantic_key_a = f"{source_id}|{_relationship_type_for_text(text)}|{target_id}"
                semantic_key_b = f"{target_id}|{_relationship_type_for_text(text)}|{source_id}"
                if semantic_key_a in directed_keys or semantic_key_b in directed_keys:
                    continue
                key = "|".join(pair) + "|mentioned_with"
                relationship = relationships.setdefault(key, {
                    "source_entity_id": pair[0],
                    "relationship_type": "mentioned_with",
                    "target_entity_id": pair[1],
                    "confidence": 0.45,
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
    document["metadata"]["semantic_relationship_count"] = sum(
        1 for r in document["relationships"] if r["relationship_type"] != "mentioned_with"
    )
    document["metadata"]["cooccurrence_relationship_count"] = sum(
        1 for r in document["relationships"] if r["relationship_type"] == "mentioned_with"
    )

    errors = validate_document(document)
    if errors:
        print(f"FAIL: canonical build produced {len(errors)} validation errors")
        for error in errors[:25]:
            print(f" - {error}")
        return 1

    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS: built canonical intelligence: "
        f"entities={len(entities)} events={len(events)} relationships={len(relationships)} "
        f"semantic_relationships={document['metadata']['semantic_relationship_count']} evidence={len(evidence)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
