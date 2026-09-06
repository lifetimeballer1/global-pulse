#!/usr/bin/env python3
"""Strict Phase 1 validator for the canonical Intelligence Brain artifact."""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PATH = DATA / "intelligence_brain.json"
ALLOWED_KINDS = {"country", "cartel", "economic", "conflict", "chokepoint"}
MAX_NODES = 35
MAX_EVIDENCE_PER_ITEM = 100


def fail(message: str) -> None:
    raise RuntimeError(f"INTELLIGENCE BRAIN VALIDATION FAILED: {message}")


def parse_time(value: object) -> datetime:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception as exc:
        fail(f"invalid updatedAt: {value!r}")
        raise exc
    if dt.tzinfo is None:
        fail("updatedAt must include timezone information")
    return dt.astimezone(timezone.utc)


def evidence_key(item: object) -> tuple[str, str, str, str]:
    if not isinstance(item, dict):
        fail("evidence entry is not an object")
    title = str(item.get("title") or "").strip()
    url = str(item.get("url") or "").strip()
    source = str(item.get("source") or "").strip()
    time = str(item.get("time") or "").strip()
    if not (url or source):
        fail("evidence entry has neither url nor source")
    return title, url, source, time


def validate() -> dict:
    if not PATH.is_file() or PATH.stat().st_size == 0:
        fail("artifact missing or empty")
    try:
        brain = json.loads(PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON: {exc}")
    if not isinstance(brain, dict):
        fail("root must be an object")

    required = ("version", "updatedAt", "complete", "sourceBackedOnly", "consolidated", "maxNodes", "nodes", "edges", "stats")
    missing = [key for key in required if key not in brain]
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if brain["complete"] is not True or brain["sourceBackedOnly"] is not True or brain["consolidated"] is not True:
        fail("completeness/sourceBackedOnly/consolidated flags are not all true")
    if int(brain["maxNodes"]) != MAX_NODES:
        fail(f"maxNodes must be {MAX_NODES}")
    updated = parse_time(brain["updatedAt"])
    age = (datetime.now(timezone.utc) - updated).total_seconds()
    if age < -120:
        fail(f"updatedAt is too far in the future: {age:.0f}s")
    if age > 3600:
        fail(f"artifact is stale: {age:.0f}s old")

    nodes = brain["nodes"]
    edges = brain["edges"]
    stats = brain["stats"]
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(stats, dict):
        fail("nodes, edges, and stats must have the correct container types")
    if not (10 <= len(nodes) <= MAX_NODES):
        fail(f"node count {len(nodes)} outside 10..{MAX_NODES}")
    if len(edges) < 5:
        fail(f"too few relationships: {len(edges)}")

    node_ids: set[str] = set()
    kind_counts = {kind: 0 for kind in ALLOWED_KINDS}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            fail(f"node[{index}] is not an object")
        node_id = str(node.get("id") or "").strip()
        label = str(node.get("label") or "").strip()
        kind = str(node.get("kind") or "").strip()
        if not node_id or not label:
            fail(f"node[{index}] missing id or label")
        if node_id in node_ids:
            fail(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
        if kind not in ALLOWED_KINDS:
            fail(f"node {label!r} has invalid kind {kind!r}")
        if node.get("canonical") is not True:
            fail(f"node {label!r} is not canonical")
        try:
            score = float(node.get("score"))
            mentions = int(node.get("mentions"))
        except (TypeError, ValueError):
            fail(f"node {label!r} has invalid score/mentions")
        if not math.isfinite(score) or score < 0 or mentions < 1:
            fail(f"node {label!r} has invalid score/mentions values")
        evidence = node.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            fail(f"node {label!r} has no evidence")
        if len(evidence) > MAX_EVIDENCE_PER_ITEM:
            fail(f"node {label!r} has excessive evidence: {len(evidence)}")
        seen_evidence = set()
        for item in evidence:
            key = evidence_key(item)
            if key in seen_evidence:
                fail(f"node {label!r} contains duplicate evidence")
            seen_evidence.add(key)
        if kind in ("country", "cartel"):
            for field in ("lat", "lng"):
                try:
                    value = float(node.get(field))
                except (TypeError, ValueError):
                    fail(f"node {label!r} missing numeric {field}")
                if not math.isfinite(value):
                    fail(f"node {label!r} has non-finite {field}")
            if not (-90 <= float(node["lat"]) <= 90 and -180 <= float(node["lng"]) <= 180):
                fail(f"node {label!r} has invalid coordinates")
        kind_counts[kind] += 1

    edge_keys: set[tuple[str, str]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            fail(f"edge[{index}] is not an object")
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if not source or not target or source == target:
            fail(f"edge[{index}] has invalid endpoints")
        if source not in node_ids or target not in node_ids:
            fail(f"edge[{index}] references a missing node")
        key = tuple(sorted((source, target)))
        if key in edge_keys:
            fail(f"duplicate relationship: {source} <-> {target}")
        edge_keys.add(key)
        try:
            weight = int(edge.get("weight"))
            evidence_count = int(edge.get("evidenceCount"))
        except (TypeError, ValueError):
            fail(f"edge[{index}] has invalid weight/evidenceCount")
        if weight < 1 or evidence_count < 1:
            fail(f"edge[{index}] has non-positive weight/evidenceCount")
        types = edge.get("types")
        if not isinstance(types, list) or not types or any(not str(x).strip() for x in types):
            fail(f"edge[{index}] has invalid types")
        evidence = edge.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            fail(f"edge[{index}] has no evidence")
        if evidence_count != len(evidence):
            fail(f"edge[{index}] evidenceCount mismatch")
        if len(evidence) > MAX_EVIDENCE_PER_ITEM:
            fail(f"edge[{index}] has excessive evidence: {len(evidence)}")
        seen_evidence = set()
        for item in evidence:
            key = evidence_key(item)
            if key in seen_evidence:
                fail(f"edge[{index}] contains duplicate evidence")
            seen_evidence.add(key)

    if kind_counts["cartel"] < 1 or kind_counts["country"] < 1 or kind_counts["economic"] < 1:
        fail(f"required groups missing: {kind_counts}")
    if int(stats.get("nodes", -1)) != len(nodes) or int(stats.get("edges", -1)) != len(edges):
        fail("stats node/edge counts do not match artifact")
    for kind, count in kind_counts.items():
        stat_key = f"{kind}Nodes"
        if int(stats.get(stat_key, -1)) != count:
            fail(f"stats mismatch for {stat_key}: expected {count}, got {stats.get(stat_key)}")

    print(
        "PASS: Intelligence Brain Phase 1 validation "
        f"nodes={len(nodes)} edges={len(edges)} kinds={kind_counts} age={age:.0f}s"
    )
    return brain


if __name__ == "__main__":
    validate()
    # A successful validation is the safe point to generate next-cycle feed
    # expansion hints. If feedback generation fails, validation still remains
    # authoritative and the pipeline surfaces the feedback failure explicitly.
    import subprocess, sys
    subprocess.run([sys.executable, str(ROOT / "update_brain_feedback.py")], cwd=ROOT, check=True)
