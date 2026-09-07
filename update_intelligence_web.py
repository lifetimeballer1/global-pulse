#!/usr/bin/env python3
"""Build a resilient, evidence-first relationship web from the public snapshot.

The Intelligence Web consumes the shared canonical entity extractor so the
browser graph and intelligence pipeline use one entity identity model.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from intelligence_entity_extractor import extract_entities, entity_id

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"

def norm(v):
    return re.sub(r"\s+", " ", str(v or "").lower()).strip()

def record_text(r):
    keys = ("title", "summary", "description", "content", "text", "name", "region", "country", "location", "category", "type", "tags", "keywords")
    parts = []
    for k in keys:
        v = r.get(k, "") if isinstance(r, dict) else ""
        parts.append(" ".join(map(str, v)) if isinstance(v, list) else str(v or ""))
    return norm(" ".join(parts))

def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")

def evidence_from(r):
    if not isinstance(r, dict):
        return None
    title = str(r.get("title") or r.get("name") or "Public intelligence record").strip()
    url = str(r.get("original_link") or r.get("url") or r.get("sourceUrl") or r.get("source_url") or r.get("link") or ((r.get("credit") or {}).get("source_url") if isinstance(r.get("credit"), dict) else "") or "").strip()
    source = str(r.get("sourceLabel") or r.get("source") or r.get("publisher") or "Public source").strip()
    time = str(r.get("time") or r.get("publishedAt") or r.get("published_date") or r.get("updatedAt") or "").strip()
    summary = str(r.get("summary") or r.get("description") or r.get("summary_snippet") or "").strip()
    if not title and not url and source == "Public source":
        return None
    return {"title": title or "Public intelligence record", "url": url, "source": source or "Public source", "time": time, "summary": summary[:420]}

def main():
    data = json.loads(SNAP.read_text(encoding="utf-8"))
    nodes = {}
    edges = {}

    def add_node(entity, mentions=1):
        name = entity["canonical_name"]
        kind = entity["entity_type"]
        n = nodes.setdefault(name, {"id": entity["id"], "label": name, "kind": kind, "mentions": 0, "evidence": []})
        n["mentions"] += max(0, int(mentions))
        return n

    def add_edge(a, b, ev, source_type):
        if not a or not b or a == b or not ev:
            return
        key = "|".join(sorted((a, b)))
        e = edges.setdefault(key, {"source": a, "target": b, "weight": 0, "types": set(), "evidence": [], "relationship": ""})
        e["weight"] += 1
        e["types"].add(source_type)
        e["relationship"] = {
            "conflict": "Both entities are referenced in the same conflict record.",
            "graph": "Relationship retained from an evidence-backed graph record.",
        }.get(source_type, "Both entities are referenced in the same public reporting record.")
        if ev.get("title") and not any(x.get("title") == ev["title"] for x in e["evidence"]) and len(e["evidence"]) < 8:
            e["evidence"].append(ev)

    stories = data.get("stories", []) if isinstance(data.get("stories", []), list) else []
    conflicts = data.get("conflicts", []) if isinstance(data.get("conflicts", []), list) else []

    for record, source_type in [(x, "story") for x in stories[:1200]] + [(x, "conflict") for x in conflicts]:
        text = record_text(record)
        extracted = extract_entities(text)
        ev = evidence_from(record)
        found = []
        for entity in extracted:
            node = add_node(entity)
            found.append(entity["canonical_name"])
            if ev and len(node["evidence"]) < 8 and not any(x.get("title") == ev["title"] for x in node["evidence"]):
                node["evidence"].append(ev)
        if ev:
            for i, a in enumerate(found):
                for b in found[i + 1:]:
                    add_edge(a, b, ev, source_type)

    # Preserve previously generated graph evidence when both endpoints still
    # resolve to the shared canonical entity IDs. This prevents data loss while
    # migrating from the old embedded catalog.
    old = data.get("intelligenceGraph", {}) if isinstance(data.get("intelligenceGraph"), dict) else {}
    old_nodes = {str(n.get("id")): n for n in old.get("nodes", []) if isinstance(n, dict)}
    by_id = {n["id"]: n for n in nodes.values()}
    for olde in old.get("edges", []) if isinstance(old.get("edges", []), list) else []:
        if not isinstance(olde, dict):
            continue
        s, t = str(olde.get("source", "")), str(olde.get("target", ""))
        evs = olde.get("evidence") if isinstance(olde.get("evidence"), list) else []
        if s in by_id and t in by_id:
            a, b = by_id[s]["label"], by_id[t]["label"]
            for ev in evs[:8]:
                if isinstance(ev, dict) and (ev.get("title") or ev.get("url") or ev.get("original_link")):
                    if not ev.get("url") and ev.get("original_link"):
                        ev = {**ev, "url": ev.get("original_link")}
                    add_edge(a, b, ev, "graph")

    edge_list = []
    for e in edges.values():
        e["types"] = sorted(e["types"])
        e["evidence"].sort(key=lambda x: x.get("time", ""), reverse=True)
        e["evidenceCount"] = len(e["evidence"])
        if e["evidenceCount"]:
            edge_list.append(e)
    edge_list.sort(key=lambda e: (e["evidenceCount"], e["weight"]), reverse=True)
    edge_list = edge_list[:500]

    degree = {n: 0 for n in nodes}
    for e in edge_list:
        degree[e["source"]] = degree.get(e["source"], 0) + e["weight"]
        degree[e["target"]] = degree.get(e["target"], 0) + e["weight"]

    node_list = sorted(nodes.values(), key=lambda n: (degree.get(n["label"], 0), n["mentions"], n["label"]), reverse=True)[:100]
    data["intelligenceGraph"] = {
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "method": "shared canonical entity extraction with evidence-backed co-occurrence graph from current public stories and conflict records",
        "caution": "A connection means the entities share a public evidence record; it does not independently prove causation, coordination, alliance, or responsibility.",
        "nodes": node_list,
        "edges": edge_list,
    }
    SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Intelligence graph: {len(node_list)} nodes / {len(edge_list)} evidence-backed edges")

if __name__ == "__main__":
    main()
