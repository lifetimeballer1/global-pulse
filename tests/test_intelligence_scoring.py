from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from intelligence_scoring import evidence_score, event_score, geopolitical_relevance


def test_low_relevance_evidence_is_retained_but_downweighted():
    evidence = {
        "tier": "a",
        "published_at": "2026-09-06T00:00:00+00:00",
        "quality": 0.9,
        "geopolitical_relevance": 0.0,
    }
    assert evidence_score(evidence) == 0.0


def test_geopolitical_event_retains_signal():
    evidence = [{
        "tier": "a",
        "published_at": "2026-09-06T00:00:00+00:00",
        "quality": 0.9,
        "geopolitical_relevance": 1.0,
    }]
    event = {
        "event_type": "sanctions",
        "severity": 0.72,
        "confidence": 0.9,
        "strategic_relevance": 0.8,
        "timestamp": "2026-09-06T00:00:00+00:00",
        "geopolitical_relevance": 1.0,
    }
    assert event_score(event, evidence) > 0.5


def test_relevance_is_bounded():
    assert 0.0 <= geopolitical_relevance({"geopolitical_relevance": 0.25}) <= 1.0
    assert 0.0 <= geopolitical_relevance({"geopolitical_relevance": 2}) <= 1.0
    assert 0.0 <= geopolitical_relevance({"geopolitical_relevance": -1}) <= 1.0
