#!/usr/bin/env python3
"""Runtime compatibility helpers for the canonical snapshot refresh."""
from __future__ import annotations
import re


def install(base, builder):
    """Patch the legacy builder in-process before it builds snapshot.json."""
    def improved_match_conflict(story, aliases):
        title = str(story.get("title", ""))
        summary = str(story.get("summary", ""))
        source_label = str(story.get("sourceLabel", ""))
        score = 0.0
        matched = []
        for alias in aliases:
            pattern = re.escape(alias.lower())
            if alias.lower() == "cartel":
                pattern = r"cartel(?:s)?"
            elif alias.lower() in {"narco-terrorist", "narco terrorist"}:
                pattern = r"narco[- ]terrorist(?:s)?"
            rx = re.compile(r"(?<![a-z0-9])" + pattern + r"(?![a-z0-9])", re.I)
            if rx.search(title):
                score += 6.0; matched.append(alias)
            elif rx.search(summary):
                score += 2.5; matched.append(alias)
            elif rx.search(source_label):
                score += 4.0; matched.append(alias)
        if not matched:
            return 0.0, []
        blob = f"{title} {summary} {source_label}"
        severity_bonus = max((points for _, rx, points in base.SEVERITY if rx.search(blob)), default=0)
        return min(32.0, score + severity_bonus * base.recency_weight(story.get("time"))), matched

    base.match_conflict = improved_match_conflict
    for driver in ("Conflict activity", "Military posture"):
        regex, eligible = builder.DRIVER_DEFS[driver]
        builder.DRIVER_DEFS[driver] = (
            regex,
            set(eligible) | {"southcom", "southcom-news", "counter-cartel", "cartel"},
        )
