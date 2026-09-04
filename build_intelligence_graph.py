#!/usr/bin/env python3
"""Publish a compact Intelligence Web payload.

The public snapshot is intentionally large. The 3D graph should not download the
entire dashboard snapshot just to render a small network, especially on mobile.
This step copies only the evidence graph into a small dedicated JSON payload.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"
OUT = ROOT / "data" / "intelligence_graph.json"


def main():
    data = json.loads(SNAP.read_text(encoding="utf-8"))
    graph = data.get("intelligenceGraph")
    if not isinstance(graph, dict):
        raise SystemExit("snapshot has no intelligenceGraph object")

    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    edges = graph.get("edges") if isinstance(graph.get("edges"), list) else []

    # Keep the public evidence records needed by the graph detail panel, while
    # dropping unrelated dashboard payloads such as thousands of news stories.
    compact_nodes = []
    for n in nodes[:80]:
        if not isinstance(n, dict) or not n.get("id"):
            continue
        compact_nodes.append({
            "id": str(n.get("id")),
            "label": str(n.get("label") or n.get("name") or n.get("id")),
            "kind": str(n.get("kind") or "actor"),
            "mentions": int(n.get("mentions") or 0),
            "evidence": [e for e in (n.get("evidence") or [])[:8] if isinstance(e, dict)],
        })

    valid = {n["id"] for n in compact_nodes}
    compact_edges = []
    for e in edges[:500]:
        if not isinstance(e, dict):
            continue
        source, target = str(e.get("source") or ""), str(e.get("target") or "")
        evidence = [x for x in (e.get("evidence") or [])[:8] if isinstance(x, dict)]
        if source not in valid or target not in valid or source == target or not evidence:
            continue
        compact_edges.append({
            "source": source,
            "target": target,
            "weight": max(1, int(e.get("weight") or 1)),
            "types": list(e.get("types") or []),
            "relationship": str(e.get("relationship") or "Both entities are referenced in the same public evidence record."),
            "evidence": evidence,
            "evidenceCount": len(evidence),
        })

    if len(compact_nodes) < 10 or len(compact_edges) < 10:
        raise SystemExit(f"intelligence graph too small: {len(compact_nodes)} nodes / {len(compact_edges)} edges")

    payload = {
        "updatedAt": graph.get("updatedAt") or data.get("updatedAt") or "",
        "method": graph.get("method") or "evidence-backed public reporting graph",
        "caution": graph.get("caution") or "A connection means the entities share a public evidence record; it does not independently prove causation, coordination, alliance, or responsibility.",
        "nodes": compact_nodes,
        "edges": compact_edges,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Compact Intelligence Web payload: {len(compact_nodes)} nodes / {len(compact_edges)} edges / {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
