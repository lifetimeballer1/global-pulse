#!/usr/bin/env python3
"""Build a relationship graph from the existing public Global Pulse snapshot.

The graph is deliberately evidence-based: nodes come from stories/conflicts and
edges are created only when two entities co-occur in the same source story or
conflict record. It does not claim that co-occurrence proves causation.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"

# Broad political/economic/strategic entities that make useful graph nodes.
ENTITIES = {
    "United States": ["united states", "u.s.", "us government", "washington", "white house", "trump", "congress"],
    "China": ["china", "chinese", "beijing", "pla"],
    "Russia": ["russia", "russian", "moscow", "kremlin", "putin"],
    "Ukraine": ["ukraine", "ukrainian", "kyiv", "zelensky"],
    "Iran": ["iran", "iranian", "tehran"],
    "Israel": ["israel", "israeli", "tel aviv", "jerusalem"],
    "Palestinians": ["palestinian", "gaza", "west bank", "hamas"],
    "Saudi Arabia": ["saudi arabia", "saudi", "riyadh"],
    "Turkey": ["turkey", "turkish", "ankara", "erdogan"],
    "India": ["india", "indian", "new delhi"],
    "Pakistan": ["pakistan", "pakistani", "islamabad"],
    "Taiwan": ["taiwan", "taiwanese", "taipei"],
    "North Korea": ["north korea", "dprk", "pyongyang"],
    "South Korea": ["south korea", "seoul"],
    "Japan": ["japan", "japanese", "tokyo"],
    "European Union": ["european union", "eu", "brussels"],
    "United Kingdom": ["united kingdom", "britain", "british", "london"],
    "NATO": ["nato", "north atlantic treaty organization"],
    "Mexico": ["mexico", "mexican", "mexico city"],
    "Canada": ["canada", "canadian", "ottawa"],
    "Brazil": ["brazil", "brazilian", "brasilia"],
    "Venezuela": ["venezuela", "venezuelan", "caracas"],
    "Colombia": ["colombia", "colombian", "bogota"],
    "Haiti": ["haiti", "haitian", "port-au-prince"],
    "Sudan": ["sudan", "sudanese", "khartoum", "darfur"],
    "Democratic Republic of Congo": ["democratic republic of congo", "drc", "eastern congo", "goma", "m23"],
    "Somalia": ["somalia", "somali", "mogadishu", "al-shabaab"],
    "Nigeria": ["nigeria", "nigerian", "abuja", "boko haram"],
    "Sahel": ["sahel", "mali", "burkina faso", "niger", "jnim"],
    "Yemen": ["yemen", "yemeni", "houthi", "red sea"],
    "Syria": ["syria", "syrian", "damascus"],
    "Iraq": ["iraq", "iraqi", "baghdad"],
    "Lebanon": ["lebanon", "lebanese", "beirut", "hezbollah"],
    "Egypt": ["egypt", "egyptian", "cairo"],
    "Strait of Hormuz": ["strait of hormuz", "hormuz", "persian gulf"],
    "Oil Markets": ["oil", "crude", "brent", "wti", "opec", "oil prices"],
    "Global Trade": ["tariff", "trade", "shipping", "freight", "export", "import", "supply chain"],
    "Global Economy": ["inflation", "interest rate", "central bank", "recession", "economy", "gdp", "markets"],
    "U.S. Politics": ["congress", "senate", "house republicans", "house democrats", "white house", "supreme court", "election", "midterms", "president"],
}

def norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower())

def matches(blob, aliases):
    return [a for a in aliases if re.search(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])", blob)]

def main():
    data = json.loads(SNAP.read_text(encoding="utf-8"))
    stories = data.get("stories", [])
    conflicts = data.get("conflicts", [])
    nodes = {}
    edges = {}

    def add_node(name, kind="actor"):
        if name not in nodes:
            nodes[name] = {"id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), "label": name, "kind": kind, "mentions": 0}
        nodes[name]["mentions"] += 1

    def add_edge(a, b, evidence, source="story"):
        if a == b: return
        key = "|".join(sorted((a, b)))
        e = edges.setdefault(key, {"source": a, "target": b, "weight": 0, "evidence": [], "types": set()})
        e["weight"] += 1
        e["types"].add(source)
        if evidence and len(e["evidence"]) < 4: e["evidence"].append(evidence[:240])

    for story in stories:
        blob = norm((story.get("title") or "") + " " + (story.get("summary") or ""))
        found = []
        for name, aliases in ENTITIES.items():
            hit = matches(blob, aliases)
            if hit:
                add_node(name, "economic" if name in {"Oil Markets", "Global Trade", "Global Economy"} else "political" if name in {"U.S. Politics", "NATO", "European Union"} else "actor")
                found.append(name)
        for i, a in enumerate(found):
            for b in found[i + 1:]: add_edge(a, b, story.get("title", ""), "story")

    for c in conflicts:
        blob = norm((c.get("name") or "") + " " + (c.get("region") or "") + " " + (c.get("category") or ""))
        found = []
        for name, aliases in ENTITIES.items():
            if matches(blob, aliases):
                add_node(name, "actor")
                found.append(name)
        for i, a in enumerate(found):
            for b in found[i + 1:]: add_edge(a, b, c.get("name", ""), "conflict")

    # Keep meaningful links, but preserve a useful hub around U.S. politics/world politics.
    edge_list = []
    for e in edges.values():
        e["types"] = sorted(e["types"])
        if e["weight"] >= 2:
            edge_list.append(e)
    edge_list.sort(key=lambda e: e["weight"], reverse=True)
    edge_list = edge_list[:220]

    keep = {e["source"] for e in edge_list} | {e["target"] for e in edge_list}
    node_list = [n for n in nodes.values() if n["label"] in keep]
    node_list.sort(key=lambda n: n["mentions"], reverse=True)

    data["intelligenceGraph"] = {
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "method": "co-occurrence graph from public stories and conflict records",
        "caution": "Connections indicate shared reporting/evidence, not proof of causation or alliance.",
        "nodes": node_list,
        "edges": edge_list,
    }
    SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Intelligence graph: {len(node_list)} nodes / {len(edge_list)} edges")

if __name__ == "__main__": main()
