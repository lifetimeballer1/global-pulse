"""Reusable, dependency-free entity extraction and canonicalization utilities.

This module is intentionally conservative: discovery is based on linguistic
name cues and every result must be associated with source evidence by the
caller. It does not manufacture entities from a fixed geopolitical list.
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable

# Canonical aliases for high-value geopolitical actors and institutions.
# This is normalization metadata, not intelligence data.
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
    """Discover organization-like names not covered by the canonical map.

    Returns unique candidates. Callers should attach evidence and may apply
    additional source/domain confidence rules before persisting them.
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
            output[key] = {"id": entity_id(candidate, entity_type), "canonical_name": candidate, "entity_type": entity_type, "aliases": []}
    return list(output.values())


def extract_entities(text: str) -> list[dict]:
    """Return normalized known entities plus conservative new discoveries."""
    known = normalize_known(text)
    discovered = discover_named_entities(text, excluded_names=(e["canonical_name"] for e in known))
    return known + discovered
