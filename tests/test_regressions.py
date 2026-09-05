from pathlib import Path
import json
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def test_map_conflict_filter_has_canonical_classifier_and_rerender():
    text = (ROOT / "global_map_ui.py").read_text(encoding="utf-8")
    assert 'data-f="conflict"' in text
    assert 'if(filter!=="all"&&k!==filter)return false' in text
    assert 'cfr|conflict|military|war|attack|strike' in text
    assert 'window.renderMap' in text


def test_live_news_feed_schema_normalizes_to_browser_story_shape():
    import merge_live_news as merger
    item = {
        "url": "https://example.test/story",
        "title": "Test conflict report",
        "published_date": "2026-09-05T12:00:00+00:00",
        "summary_snippet": "A test report.",
        "source_name": "Example News",
        "source_type": "news",
    }
    story = merger.normalize_article(item)
    assert story["url"] == item["url"]
    assert story["source"] == "Example News"
    assert story["sourceLabel"] == "Example News"
    assert story["sourceType"] == "news"
    assert story["published_date"] == item["published_date"]
    assert story["time"] == item["published_date"]
    assert story["title"] == item["title"]


def test_rss_parser_accepts_normal_feed_shape():
    import news_feed_db
    payload = b'''<?xml version="1.0"?><rss><channel><item><title>Fresh report</title><link>https://example.test/a</link><pubDate>Sat, 05 Sep 2026 12:00:00 GMT</pubDate><description>Summary</description></item></channel></rss>'''
    rows = news_feed_db.parse_feed(payload, "test", {"name": "Example", "type": "news", "category": "test", "url": "https://example.test/rss"})
    assert len(rows) == 1
    assert rows[0]["url"] == "https://example.test/a"
    assert rows[0]["title"] == "Fresh report"
    assert rows[0]["source_name"] == "Example"
