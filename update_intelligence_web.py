#!/usr/bin/env python3
"""Build an evidence-linked relationship web from the public snapshot.

Edges represent entities appearing together in a source story or conflict record.
They are reporting relationships, not proof of causation, coordination, or alliance.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"

ENTITIES = {
    "United States": ("actor", ["united states", "u.s.", "us government", "washington", "white house", "trump", "congress"]),
    "U.S. Politics": ("political", ["u.s. politics", "congress", "senate", "house republicans", "house democrats", "white house", "supreme court", "election", "midterms"]),
    "China": ("actor", ["china", "chinese", "beijing", "pla"]), "Russia": ("actor", ["russia", "russian", "moscow", "kremlin", "putin"]),
    "Ukraine": ("actor", ["ukraine", "ukrainian", "kyiv", "zelensky"]), "Iran": ("actor", ["iran", "iranian", "tehran"]),
    "Israel": ("actor", ["israel", "israeli", "tel aviv", "jerusalem"]), "Palestinians": ("actor", ["palestinian", "gaza", "west bank", "hamas"]),
    "Saudi Arabia": ("actor", ["saudi arabia", "saudi", "riyadh"]), "Turkey": ("actor", ["turkey", "turkish", "ankara", "erdogan"]),
    "India": ("actor", ["india", "indian", "new delhi"]), "Pakistan": ("actor", ["pakistan", "pakistani", "islamabad"]),
    "Taiwan": ("actor", ["taiwan", "taiwanese", "taipei"]), "North Korea": ("actor", ["north korea", "dprk", "pyongyang"]),
    "South Korea": ("actor", ["south korea", "seoul"]), "Japan": ("actor", ["japan", "japanese", "tokyo"]),
    "European Union": ("political", ["european union", "eu", "brussels"]), "United Kingdom": ("actor", ["united kingdom", "britain", "british", "london"]),
    "NATO": ("political", ["nato", "north atlantic treaty organization"]), "Mexico": ("actor", ["mexico", "mexican", "mexico city"]),
    "Canada": ("actor", ["canada", "canadian", "ottawa"]), "Brazil": ("actor", ["brazil", "brazilian", "brasilia"]),
    "Venezuela": ("actor", ["venezuela", "venezuelan", "caracas"]), "Colombia": ("actor", ["colombia", "colombian", "bogota"]),
    "Haiti": ("actor", ["haiti", "haitian", "port-au-prince"]), "Sudan": ("actor", ["sudan", "sudanese", "khartoum", "darfur"]),
    "Democratic Republic of Congo": ("actor", ["democratic republic of congo", "drc", "eastern congo", "goma", "m23"]),
    "Somalia": ("actor", ["somalia", "somali", "mogadishu", "al-shabaab"]), "Nigeria": ("actor", ["nigeria", "nigerian", "abuja", "boko haram"]),
    "Sahel": ("actor", ["sahel", "mali", "burkina faso", "niger", "jnim"]), "Yemen": ("actor", ["yemen", "yemeni", "houthi", "red sea"]),
    "Syria": ("actor", ["syria", "syrian", "damascus"]), "Iraq": ("actor", ["iraq", "iraqi", "baghdad"]),
    "Lebanon": ("actor", ["lebanon", "lebanese", "beirut", "hezbollah"]), "Egypt": ("actor", ["egypt", "egyptian", "cairo"]),
    "Strait of Hormuz": ("strategic", ["strait of hormuz", "hormuz", "persian gulf"]),
    "Oil Markets": ("economic", ["oil", "crude", "brent", "wti", "opec", "oil prices"]),
    "Global Trade": ("economic", ["tariff", "trade", "shipping", "freight", "export", "import", "supply chain"]),
    "Global Economy": ("economic", ["inflation", "interest rate", "central bank", "recession", "economy", "gdp", "markets"]),
}

def norm(value):
    return re.sub(r"\s+", " ", str(value or "").lower())

def has_alias(blob, alias):
    return re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", blob) is not None

def matched_aliases(blob, aliases):
    return [a for a in aliases if has_alias(blob, a)]

def add_node(nodes, name, kind):
    node = nodes.setdefault(name, {"id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), "label": name, "kind": kind, "mentions": 0})
    node["mentions"] += 1

def main():
    data = json.loads(SNAP.read_text(encoding="utf-8"))
    nodes, edges = {}, {}

    def add_edge(a, b, evidence, source_type):
        if a == b: return
        key = "|".join(sorted((a, b)))
        edge = edges.setdefault(key, {"source": a, "target": b, "weight": 0, "types": set(), "evidence": []})
        edge["weight"] += 1
        edge["types"].add(source_type)
        if evidence and len(edge["evidence"]) < 6 and not any(x.get("title") == evidence.get("title") for x in edge["evidence"]):
            edge["evidence"].append(evidence)

    for story in data.get("stories", []):
        title = str(story.get("title") or "").strip(); summary = str(story.get("summary") or "").strip(); blob = norm(title + " " + summary)
        found = []
        for name, (kind, aliases) in ENTITIES.items():
            hits = matched_aliases(blob, aliases)
            if name == "U.S. Politics" and not hits: continue
            if hits: add_node(nodes, name, kind); found.append(name)
        evidence = {"title": title, "url": str(story.get("url") or ""), "source": str(story.get("sourceLabel") or story.get("source") or "Public source"), "time": str(story.get("time") or "")}
        for i, a in enumerate(found):
            for b in found[i + 1:]: add_edge(a, b, evidence, "story")

    for conflict in data.get("conflicts", []):
        name_text = str(conflict.get("name") or "").strip(); blob = norm(" ".join(str(conflict.get(k) or "") for k in ("name", "region", "category")))
        found = []
        for name, (kind, aliases) in ENTITIES.items():
            if matched_aliases(blob, aliases): add_node(nodes, name, kind); found.append(name)
        evidence = {"title": name_text, "url": str(conflict.get("sourceUrl") or conflict.get("url") or ""), "source": str(conflict.get("source") or "Conflict record"), "time": str(conflict.get("updatedAt") or conflict.get("time") or "")}
        for i, a in enumerate(found):
            for b in found[i + 1:]: add_edge(a, b, evidence, "conflict")

    # Keep first-order relationships too. The old >=2 filter made the graph look
    # empty when a region/entity only appeared once in the current snapshot.
    edge_list = []
    for edge in edges.values():
        edge["types"] = sorted(edge["types"]); edge["evidence"].sort(key=lambda x: x.get("time", ""), reverse=True)
        if edge["weight"] >= 1: edge_list.append(edge)
    edge_list.sort(key=lambda e: (e["weight"], len(e["evidence"])), reverse=True); edge_list = edge_list[:400]
    keep = {e["source"] for e in edge_list} | {e["target"] for e in edge_list}
    node_list = [n for n in nodes.values() if n["label"] in keep]; node_list.sort(key=lambda n: n["mentions"], reverse=True)

    data["intelligenceGraph"] = {"updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "method": "co-occurrence graph from public stories and conflict records", "caution": "Connections indicate shared reporting/evidence, not proof of causation, coordination, or alliance.", "nodes": node_list, "edges": edge_list}
    SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Intelligence graph: {len(node_list)} nodes / {len(edge_list)} edges")

if __name__ == "__main__": main()
