from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_map_conflict_filter_has_canonical_classifier_and_rerender():
    text = (ROOT / 'global_map_ui.py').read_text(encoding='utf-8')
    assert 'data-f="conflict"' in text
    assert re.search(r'filter\s*!==\s*["\']all["\']\s*&&\s*k\s*!==\s*filter', text)
    assert re.search(r'cfr\|conflict\|military\|war\|attack\|strike', text)
    assert 'window.renderMap' in text


def test_live_news_feed_schema_normalizes_to_browser_story_shape():
    import merge_live_news as merger
    item = {
        'url': 'https://example.test/story',
        'title': 'Test conflict report',
        'published_date': '2026-09-05T12:00:00+00:00',
        'summary_snippet': 'A test report.',
        'source_name': 'Example News',
        'source_type': 'news',
    }
    story = merger.normalize_article(item)
    assert story['url'] == item['url']
    assert story['source'] == item['url']
    assert story['sourceLabel'] == 'Example News'
    assert story['sourceName'] == 'Example News'
    assert story['sourceType'] == 'news'
    assert story['published_date'] == item['published_date']
    assert story['time'] == item['published_date']
    assert story['title'] == item['title']


def test_rss_parser_accepts_normal_feed_shape():
    import news_feed_db
    payload = b'''<?xml version="1.0"?><rss><channel><item><title>Fresh report</title><link>https://example.test/a</link><pubDate>Sat, 05 Sep 2026 12:00:00 GMT</pubDate><description>Summary</description></item></channel></rss>'''
    rows = news_feed_db.parse_feed(payload, 'test', {'name': 'Example', 'type': 'news', 'category': 'test', 'url': 'https://example.test/rss'})
    assert len(rows) == 1
    assert rows[0]['url'] == 'https://example.test/a'
    assert rows[0]['title'] == 'Fresh report'
    assert rows[0]['source_name'] == 'Example'


def test_browser_qa_layer_is_installed_and_distinguishes_fetch_failure():
    text = (ROOT / 'global_pulse_qa.js').read_text(encoding='utf-8')
    assert 'LIVE DATA UNAVAILABLE' in text
    assert 'gp.howToRead.v1' in text
    assert 'gp-qa-contradiction' in text
    assert 'aria-label' in text


def test_refresh_pipeline_requires_real_market_prices_and_manifest():
    text = (ROOT / 'refresh_pipeline.py').read_text(encoding='utf-8')
    assert 'market data contains no positive real prices' in text
    assert 'refresh_manifest.json' in text
    assert 'build_what_changed.py' in text
