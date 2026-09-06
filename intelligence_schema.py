"""Canonical intelligence data model for Global Pulse.

This module defines the shared schema used between ingestion, intelligence
processing, graph generation, validation, and the presentation layer.
It intentionally contains no hard-coded intelligence facts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "2.0"

ENTITY_TYPES = {
    "country",
    "government",
    "government_agency",
    "military",
    "intelligence",
    "political_party",
    "person",
    "company",
    "financial_institution",
    "international_organization",
    "armed_group",
    "region",
    "location",
    "conflict",
    "infrastructure",
    "technology",
    "other",
}

EVENT_TYPES = {
    "military_action",
    "diplomatic_action",
    "economic_action",
    "political_action",
    "trade_action",
    "sanction",
    "cyber_activity",
    "technology_action",
    "energy_action",
    "conflict_event",
    "protest",
    "election",
    "disaster",
    "other",
}

RELATIONSHIP_TYPES = {
    "allied_with",
    "opposes",
    "cooperates_with",
    "negotiates_with",
    "trades_with",
    "sanctions",
    "sanctioned_by",
    "military_action_against",
    "deploys_to",
    "supplies",
    "targets",
    "controls",
    "located_in",
    "member_of",
    "owns",
    "invests_in",
    "depends_on",
    "affects",
    "participates_in",
    "associated_with",
    "mentioned_with",
    "other",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Evidence:
    id: str
    title: str
    source: str
    url: str = ""
    published_at: str = ""
    reliability: float = 0.5
    excerpt: str = ""


@dataclass
class Entity:
    id: str
    canonical_name: str
    entity_type: str
    aliases: List[str] = field(default_factory=list)
    country: Optional[str] = None
    region: Optional[str] = None
    importance: float = 0.0
    mention_count: int = 0
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Event:
    id: str
    event_type: str
    title: str
    timestamp: str = ""
    location: Optional[str] = None
    severity: float = 0.0
    confidence: float = 0.0
    entity_ids: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    source_entity_id: str
    relationship_type: str
    target_entity_id: str
    confidence: float = 0.0
    weight: float = 0.0
    first_seen: str = ""
    last_seen: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    event_ids: List[str] = field(default_factory=list)


@dataclass
class Signal:
    id: str
    signal_type: str
    severity: float
    confidence: float
    entity_ids: List[str] = field(default_factory=list)
    event_ids: List[str] = field(default_factory=list)
    impact: str = ""
    evidence_ids: List[str] = field(default_factory=list)


def validate_document(document: Dict[str, Any]) -> List[str]:
    """Return validation errors without mutating the supplied document."""
    errors: List[str] = []
    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    entities = document.get("entities", [])
    events = document.get("events", [])
    relationships = document.get("relationships", [])
    evidence = document.get("evidence", [])
    signals = document.get("signals", [])

    entity_ids = {x.get("id") for x in entities}
    event_ids = {x.get("id") for x in events}
    evidence_ids = {x.get("id") for x in evidence}

    for entity in entities:
        if not entity.get("id") or not entity.get("canonical_name"):
            errors.append("entity missing id or canonical_name")
        if entity.get("entity_type") not in ENTITY_TYPES:
            errors.append(f"invalid entity_type: {entity.get('entity_type')}")
        missing = set(entity.get("evidence_ids", [])) - evidence_ids
        if missing:
            errors.append(f"entity {entity.get('id')} references missing evidence: {sorted(missing)}")

    for event in events:
        if not event.get("id") or not event.get("event_type"):
            errors.append("event missing id or event_type")
        if event.get("event_type") not in EVENT_TYPES:
            errors.append(f"invalid event_type: {event.get('event_type')}")
        missing_entities = set(event.get("entity_ids", [])) - entity_ids
        if missing_entities:
            errors.append(f"event {event.get('id')} references missing entities: {sorted(missing_entities)}")
        missing_evidence = set(event.get("evidence_ids", [])) - evidence_ids
        if missing_evidence:
            errors.append(f"event {event.get('id')} references missing evidence: {sorted(missing_evidence)}")

    for relationship in relationships:
        if relationship.get("source_entity_id") not in entity_ids:
            errors.append("relationship references missing source entity")
        if relationship.get("target_entity_id") not in entity_ids:
            errors.append("relationship references missing target entity")
        if relationship.get("relationship_type") not in RELATIONSHIP_TYPES:
            errors.append(f"invalid relationship_type: {relationship.get('relationship_type')}")
        missing_events = set(relationship.get("event_ids", [])) - event_ids
        if missing_events:
            errors.append("relationship references missing event")
        missing_evidence = set(relationship.get("evidence_ids", [])) - evidence_ids
        if missing_evidence:
            errors.append("relationship references missing evidence")

    for signal in signals:
        if not signal.get("id") or not signal.get("signal_type"):
            errors.append("signal missing id or signal_type")
        if not set(signal.get("entity_ids", [])) <= entity_ids:
            errors.append(f"signal {signal.get('id')} references missing entity")
        if not set(signal.get("event_ids", [])) <= event_ids:
            errors.append(f"signal {signal.get('id')} references missing event")

    return errors


def empty_document() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "entities": [],
        "events": [],
        "relationships": [],
        "evidence": [],
        "signals": [],
        "metadata": {
            "model": "canonical-intelligence",
            "source_backed_only": True,
        },
    }


def dataclass_to_dict(value: Any) -> Dict[str, Any]:
    """Convert one of the schema dataclasses to a JSON-ready dictionary."""
    return asdict(value)
