#!/usr/bin/env python3
"""Build canonical intelligence using the shared entity extraction layer."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from intelligence_entity_extractor import extract_entities
from intelligence_schema import SCHEMA_VERSION, empty_document, validate_document

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INPUT = DATA / "live_articles.json"
OUTPUT = DATA / "canonical_intelligence.json"
EVENT_PATTERNS = (
    ("sanction", r"\b(sanction|sanctions|sanctioned|sanctioning)\b"),
    ("military_action", r"\b(strike|strikes|airstrike|airstrikes|missile|bombing|deployment|deploys|military operation|troops|forces)\b"),
    ("diplomatic_action", r"\b(meet|meets|meeting|talks|negotiat|diplomatic|envoy|summit|ceasefire)\b"),
    ("economic_action", r"\b(stimulus|interest rate|rate cut|tariff|tariffs|tax|capital|investment|economic policy)\b"),
    ("trade_action", r"\b(trade|export|exports|import|imports|supply chain|customs)\b"),
    ("technology_action", r"\b(chip|chips|semiconductor|semiconductors|artificial intelligence|technology|tech)\b"),
    ("energy_action", r"\b(oil|gas|lng|energy|electricity|power grid|nuclear|uranium)\b"),
    ("cyber_activity", r"\b(cyber|cyberattack|cyberattacks|hacking|malware|ransomware)\b"),
    ("political_action", r"\b(election|elections|vote|voting|parliament|congress|president|government)\b"),
)
RELATIONSHIP_PATTERNS = (
    ("sanctions", r"(?:imposed|announced|issued|expanded|tightened)\s+(?:new\s+)?sanctions?\s+(?:on|against)"),
    ("trades_with", r"(?:trade|trades|trading|exports?|imports?)\s+(?:with|between)"),
    ("negotiates_with", r"(?:negotiat(?:e|es|ed|ing)|talks?|meet(?:s|ing)?|summit)\s+(?:with|between)"),
    ("cooperates_with", r"(?:cooperat(?:e|es|ed|ing)|cooperation|joint|agreement)\s+(?:with|between)"),
    ("military_action_against", r"(?:strike|strikes|airstrike|airstrikes|bomb(?:ed|ing)?|attack(?:ed|s|ing)?|military operation)\s+(?:on|against|targeting)"),
    ("deploys_to", r"(?:deploy(?:ed|s|ing)?|troops|forces)\s+(?:to|into)"),
    ("supplies", r"(?:suppl(?:y|ies|ied|ying)|provide(?:s|d)?|arms?)\s+(?:to|for)"),
    ("invests_in", r"(?:invest(?:s|ed|ing)?|investment)\s+(?:in|into)"),
)

def stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}-{hashlib.sha256('|'.join(parts).encode('utf-8', 'ignore')).hexdigest()[:16]}"

def article_text(article: dict[str, Any]) -> str:
    return " ".join(str(article.get(k) or "") for k in ("title", "summary_snippet", "summary", "description", "content")).strip()

def relation_type(text: str) -> str:
    for kind, pattern in RELATIONSHIP_PATTERNS:
        if re.search(pattern, text, re.I):
            return kind
    return "mentioned_with"

def confidence(kind: str, event_types: list[str]) -> float:
    base = {"mentioned_with": .45, "sanctions": .76, "military_action_against": .78, "negotiates_with": .70, "cooperates_with": .70}.get(kind, .68)
    if kind == "sanctions" and "sanction" in event_types: base += .08
    if kind == "military_action_against" and "military_action" in event_types: base += .08
    return min(.95, base)

def main() -> int:
    if not INPUT.exists():
        print(f"ERROR: missing input {INPUT}"); return 2
    try:
        raw = json.loads(INPUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid input JSON: {exc}"); return 2
    document = empty_document()
    document["metadata"].update({"input": str(INPUT.relative_to(ROOT)), "method": "shared-entity-extractor-v3", "source_backed_only": True})
    entities: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    events: dict[str, dict[str, Any]] = {}
    relationships: dict[str, dict[str, Any]] = {}
    articles = raw.get("articles", []) if isinstance(raw, dict) else []
    for article in articles:
        if not isinstance(article, dict): continue
        title, url = str(article.get("title") or "").strip(), str(article.get("url") or "").strip()
        if not title or not url: continue
        published = str(article.get("published_date") or "")
        ev_id = stable_id("evd", url, title)
        evidence[ev_id] = {"id": ev_id, "title": title, "source": str(article.get("source") or "Unknown public source"), "url": url, "published_at": published, "reliability": 0.5, "excerpt": str(article.get("summary_snippet") or "")[:500]}
        text = article_text(article)
        found = extract_entities(text)
        matched: list[str] = []
        names: dict[str, str] = {}
        for found_entity in found:
            entity_id = str(found_entity["id"])
            name = str(found_entity["canonical_name"])
            entity_type = str(found_entity["entity_type"])
            entity = entities.setdefault(entity_id, {"id": entity_id, "canonical_name": name, "entity_type": entity_type, "aliases": list(found_entity.get("aliases", [])), "country": name if entity_type == "country" else None, "region": None, "importance": 0.0, "mention_count": 0, "evidence_ids": []})
            entity["mention_count"] += 1
            entity["importance"] = min(1.0, entity["importance"] + (0.02 if not found_entity.get("discovered", False) else 0.01))
            if ev_id not in entity["evidence_ids"]: entity["evidence_ids"].append(ev_id)
            if entity_id not in matched: matched.append(entity_id)
            names[entity_id] = name
        lowered = text.lower()
        event_types = [kind for kind, pattern in EVENT_PATTERNS if re.search(pattern, lowered, re.I)]
        for event_type in event_types[:3]:
            event_id = stable_id("evt", ev_id, event_type)
            events[event_id] = {"id": event_id, "event_type": event_type, "title": title, "timestamp": published, "location": None, "severity": 0.0, "confidence": 0.5, "entity_ids": matched, "evidence_ids": [ev_id]}
        kind = relation_type(lowered)
        positions = []
        for entity_id in matched:
            match = re.search(r"(?<![a-z])" + re.escape(names[entity_id]) + r"(?![a-z])", text, re.I)
            if match: positions.append((match.start(), entity_id))
        positions.sort()
        if kind != "mentioned_with" and len(positions) >= 2:
            source_id, target_id = positions[0][1], positions[1][1]
            key = f"{source_id}|{kind}|{target_id}"
            rel = relationships.setdefault(key, {"source_entity_id": source_id, "relationship_type": kind, "target_entity_id": target_id, "confidence": confidence(kind, event_types), "weight": 0.0, "first_seen": published, "last_seen": published, "evidence_ids": [], "event_ids": []})
            rel["weight"] += 1.0; rel["last_seen"] = published or rel["last_seen"]
            if ev_id not in rel["evidence_ids"]: rel["evidence_ids"].append(ev_id)
            for event_id, event in events.items():
                if event["evidence_ids"] == [ev_id] and event_id not in rel["event_ids"]: rel["event_ids"].append(event_id)
        for i, source_id in enumerate(matched):
            for target_id in matched[i + 1:]:
                if source_id == target_id: continue
                pair = sorted((source_id, target_id))
                key = f"{pair[0]}|mentioned_with|{pair[1]}"
                semantic_a = f"{source_id}|{kind}|{target_id}"; semantic_b = f"{target_id}|{kind}|{source_id}"
                if kind != "mentioned_with" and (key.replace("mentioned_with", kind) in relationships or semantic_a in relationships or semantic_b in relationships): continue
                rel = relationships.setdefault(key, {"source_entity_id": pair[0], "relationship_type": "mentioned_with", "target_entity_id": pair[1], "confidence": .45, "weight": 0.0, "first_seen": published, "last_seen": published, "evidence_ids": [], "event_ids": []})
                rel["weight"] += 1.0
                if ev_id not in rel["evidence_ids"]: rel["evidence_ids"].append(ev_id)
    document["entities"] = list(entities.values()); document["events"] = list(events.values()); document["relationships"] = list(relationships.values()); document["evidence"] = list(evidence.values()); document["signals"] = []
    document["metadata"].update({"article_count": len(articles), "entity_count": len(entities), "event_count": len(events), "relationship_count": len(relationships), "semantic_relationship_count": sum(r["relationship_type"] != "mentioned_with" for r in relationships.values()), "discovered_entity_count": sum(not any(e["canonical_name"] == n for e in []) for n in [])})
    errors = validate_document(document)
    if errors:
        print(f"FAIL: canonical build produced {len(errors)} validation errors"); [print(f" - {e}") for e in errors[:25]]; return 1
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: canonical v3 entities={len(entities)} events={len(events)} relationships={len(relationships)} evidence={len(evidence)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
