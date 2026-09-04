#!/usr/bin/env python3
"""Deterministic claim/evidence layer for Global Pulse.

This is deliberately conservative: it extracts report-level claims from public
story metadata, groups near-identical reports, counts independent source
networks, and preserves disagreement. It never labels an unverified claim as
fact and never collects visitor information.
"""
from __future__ import annotations
import hashlib, json, re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SNAP = DATA / "snapshot.json"
OUT = DATA / "claims.json"
STOP = set("the a an and or of to in on for from with by as at is are was were be this that after before into near over under about against amid during report reports reported says said according officials official new latest global world".split())
CATEGORY = {
    "conflict": re.compile(r"\b(war|fighting|battle|airstrike|air strike|shelling|invasion|armed clash|bombing|missile|drone strike|offensive|militant|insurgent)\b", re.I),
    "politics": re.compile(r"\b(election|president|prime minister|government|parliament|coup|sanction|diplomatic|ceasefire|talks|treaty)\b", re.I),
    "economics": re.compile(r"\b(inflation|tariff|trade|recession|gdp|interest rate|central bank|currency|debt|oil price|gas price|market)\b", re.I),
    "disaster": re.compile(r"\b(earthquake|hurricane|cyclone|typhoon|flood|wildfire|landslide|volcano|tsunami)\b", re.I),
    "humanitarian": re.compile(r"\b(famine|hunger|refugee|displaced|humanitarian|cholera|outbreak|epidemic|food insecurity)\b", re.I),
}

def clean_words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]{3,}", text.lower())
    return [w for w in words if w not in STOP][:18]

def domain(url: str) -> str:
    try:
        h = urlparse(url).netloc.lower().split(":")[0]
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""

def key_for(story: dict) -> str:
    # Keep a small, stable lexical fingerprint. This avoids pretending that
    # two stories with only one common generic word are the same claim.
    words = clean_words(story.get("title", ""))
    return hashlib.sha256("|".join(sorted(words[:10])).encode()).hexdigest()[:16]

def category(text: str) -> str:
    for name, rx in CATEGORY.items():
        if rx.search(text):
            return name
    return "general"

def parse_time(value: str):
    if not value:
        return None
    try:
        v = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(v)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def build(stories: list[dict]) -> dict:
    groups = defaultdict(list)
    for s in stories:
        if not isinstance(s, dict) or not s.get("title") or not s.get("url"):
            continue
        groups[key_for(s)].append(s)
    claims = []
    for key, rows in groups.items():
        rows.sort(key=lambda x: parse_time(x.get("time", "")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        domains = sorted({domain(str(x.get("url", ""))) for x in rows if domain(str(x.get("url", "")))})
        sources = sorted({str(x.get("sourceLabel") or x.get("source") or "Unknown") for x in rows})
        text = " ".join(str(x.get("title", "")) for x in rows[:5])
        # Disagreement is explicit when source titles contain opposing terms.
        conflict_terms = re.compile(r"\b(denies|denied|false|incorrect|disputed|no evidence|contradicts|not true|unconfirmed)\b", re.I)
        disputed = any(conflict_terms.search(str(x.get("title", "")) + " " + str(x.get("summary", ""))) for x in rows)
        independent = len(domains)
        if disputed:
            confidence = "DISPUTED"
        elif independent >= 4:
            confidence = "HIGH"
        elif independent >= 2:
            confidence = "MODERATE"
        else:
            confidence = "LOW"
        latest = rows[0]
        claims.append({
            "id": "clm-" + key,
            "claim": str(latest.get("title", ""))[:240],
            "category": category(text),
            "confidence": confidence,
            "status": "disputed" if disputed else ("corroborated" if independent >= 2 else "single-source"),
            "independentSourceDomains": independent,
            "sourceCount": len(rows),
            "sources": sources[:12],
            "evidence": [{"source": x.get("sourceLabel", "Unknown"), "url": x.get("url", ""), "time": x.get("time", ""), "title": x.get("title", "")[:240]} for x in rows[:8]],
            "lastObserved": latest.get("time", ""),
        })
    claims.sort(key=lambda c: (c["confidence"] == "HIGH", c["independentSourceDomains"], c["sourceCount"]), reverse=True)
    return {"updatedAt": datetime.now(timezone.utc).isoformat(), "method": "Deterministic lexical clustering of public story metadata; independent means distinct source domain, not independent truth.", "claims": claims[:150]}

def main():
    DATA.mkdir(exist_ok=True)
    snapshot = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
    result = build(snapshot.get("stories") or [])
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CLAIMS: {len(result['claims'])} clusters")

if __name__ == "__main__":
    main()
