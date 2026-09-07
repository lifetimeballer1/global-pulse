"""Reusable, dependency-free entity extraction and canonicalization utilities.

This module is intentionally conservative: discovery is based on linguistic
name cues and every result must be associated with source evidence by the
caller. It does not manufacture intelligence from a fixed geopolitical list.
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable

# Canonical aliases are normalization metadata, not intelligence data.
CANONICAL_ALIASES = {
    "United States": ("country", {"united states", "u.s.", "u.s", "usa", "american", "washington"}),
    "China": ("country", {"china", "chinese", "beijing"}),
    "Russia": ("country", {"russia", "russian", "moscow"}),
    "Ukraine": ("country", {"ukraine", "ukrainian", "kyiv"}),
    "Taiwan": ("country", {"taiwan", "taiwanese", "taipei"}),
    "Iran": ("country", {"iran", "iranian", "tehran"}),
    "Israel": ("country", {"israel", "israeli", "jerusalem"}),
    "NATO": ("international_organization", {"nato"}),
    "European Union": ("international_organization", {"european union", "eu"}),
    "United Nations": ("international_organization", {"united nations", "u.n."}),
    "People's Liberation Army": ("military", {"people's liberation army", "pla"}),
    "U.S. Department of Defense": ("government_agency", {"department of defense", "defense department", "pentagon"}),
    "U.S. Department of State": ("government_agency", {"department of state", "state department"}),
    "U.S. Treasury": ("government_agency", {"u.s. treasury", "treasury department"}),
    "Federal Reserve": ("financial_institution", {"federal reserve", "fed"}),
}

DISCOVERY_RULES = (
    ("government_agency", re.compile(r"\b(?:Department|Ministry|Agency|Office)\s+(?:of\s+)?(?:[A-Z][\w'’-]+\s*){1,5}")),
    ("military", re.compile(r"\b(?:[A-Z][\w'’-]+\s+){1,5}(?:Army|Navy|Air Force|Armed Forces|Defense Forces|Corps)\b")),
    ("company", re.compile(r"\b(?:[A-Z][\w&'.-]+\s+){1,5}(?:Inc\.?|Corp\.?|Corporation|Ltd\.?|LLC|Holdings|Group)\b")),
    ("financial_institution", re.compile(r"\b(?:[A-Z][\w&'.-]+\s+){1,5}(?:Bank|Fund|Capital|Finance)\b")),
    ("international_organization", re.compile(r"\b(?:[A-Z][\w'’-]+\s+){1,5}(?:Organization|Organisation|Alliance|Union)\b")),
)

# Conservative person/location discovery. These patterns require contextual
# cues so ordinary capitalized words are not promoted to entities.
PERSON_RULE = re.compile(
    r"\b(?:President|Vice President|Prime Minister|Chancellor|Secretary|Minister|Senator|Representative|General|Admiral|Ambassador|Director|Chairman|Chairwoman|CEO|CFO)\s+"
    r"(?:[A-Z][\w'’-]+(?:\s+[A-Z][\w'’-]+){0,3})"
)
LOCATION_RULE = re.compile(
    r"\b(?:in|near|at|from|to|toward|around|across|inside|outside|off)\s+"
    r"([A-Z][\w'’-]+(?:\s+[A-Z][\w'’-]+){0,3})"
)


def entity_id(canonical_name: str, entity_type: str) -> str:
    digest = hashlib.sha256(f"{entity_type}|{canonical_name.lower()}".encode("utf-8")).hexdigest()[:16]
    return f"ent-{digest}"


def normalize_known(text: str) -> list[dict]:
    """Return known canonical entities mentioned in text, without duplicates."""
    lowered = text.lower()
    found = []
    for canonical, (entity_type, aliases) in CANONICAL_ALIASES.items():
        matched_aliases = sorted({alias for alias in aliases if re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", lowered)})
        if matched_aliases:
            found.append({"id": entity_id(canonical, entity_type), "canonical_name": canonical, "entity_type": entity_type, "aliases": matched_aliases})
    return found


def discover_named_entities(text: str, excluded_names: Iterable[str] = ()) -> list[dict]:
    """Discover organization, person and location candidates conservatively.

    Returns candidates only; callers must attach source evidence before
    persistence and can apply additional source/domain confidence rules.
    """
    excluded = {name.casefold() for name in excluded_names}
    known = {name.casefold() for name in CANONICAL_ALIASES}
    output: dict[tuple[str, str], dict] = {}

    for entity_type, rule in DISCOVERY_RULES:
        for match in rule.finditer(text):
            candidate = " ".join(match.group(0).split()).strip(" ,.;:()[]")
            key = (entity_type, candidate.casefold())
            if len(candidate) < 4 or candidate.casefold() in excluded or candidate.casefold() in known:
                continue
            output[key] = {"id": entity_id(candidate, entity_type), "canonical_name": candidate, "entity_type": entity_type, "aliases": [], "discovered": True}

    for match in PERSON_RULE.finditer(text):
        candidate = " ".join(match.group(0).split()).strip(" ,.;:()[]")
        key = ("person", candidate.casefold())
        if len(candidate) >= 6 and candidate.casefold() not in excluded and candidate.casefold() not in known:
            output[key] = {"id": entity_id(candidate, "person"), "canonical_name": candidate, "entity_type": "person", "aliases": [], "discovered": True}

    # Strip the preposition from location candidates and reject obvious
    # sentence-level phrases. This remains intentionally conservative.
    for match in LOCATION_RULE.finditer(text):
        candidate = " ".join(match.group(1).split()).strip(" ,.;:()[]")
        if len(candidate) < 4 or candidate.casefold() in excluded or candidate.casefold() in known:
            continue
        if candidate.casefold() in {"the united states", "the world", "the region", "the country", "the government"}:
            continue
        key = ("location", candidate.casefold())
        output.setdefault(key, {"id": entity_id(candidate, "location"), "canonical_name": candidate, "entity_type": "location", "aliases": [], "discovered": True})

    return list(output.values())


def extract_entities(text: str) -> list[dict]:
    """Return normalized known entities plus conservative new discoveries."""
    known = normalize_known(text)
    discovered = discover_named_entities(text, excluded_names=(e["canonical_name"] for e in known))
    return known + discovered
