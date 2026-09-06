from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_map_conflict_filter_has_canonical_classifier_and_rerender():
    # The canonical map renderer now lives in js/modules/map.js.  The legacy
    # global_map_ui.py installer intentionally removes obsolete map fragments,
    # so testing that installer for runtime UI strings is incorrect.
    text = (ROOT / 'js/modules/map.js').read_text(encoding='utf-8')
    assert "filter='all'" in text
    assert "filter!=='all'" in text
    assert "filter==='conflict'&&k==='conflicts'" in text
    assert re.search(r'cartel|organized.?crime|narco', text)
    assert re.search(r'cfr|conflict|military|war|attack|strike', text, re.I)
    assert 'renderMap' in text
    assert 'window.renderMap' not in text


def test_map_and_brain_share_canonical_artifact_and_node_identity():
    map_text = (ROOT / 'js/modules/map.js').read_text(encoding='utf-8')
    config_text = (ROOT / 'js/core/config.js').read_text(encoding='utf-8')
    brain = (ROOT / 'data/intelligence_brain.json').read_text(encoding='utf-8')
    assert 'intelligenceBrain' in config_text
    assert "'intelligenceBrain'" in map_text
    assert 'mapData?.brain' in map_text
    assert 'sourceBackedOnly===true' in map_text
    assert 'nodeId:String(n.id)' in map_text
    assert 'brainEdgesFor' in map_text
    assert '"complete":true' in brain
    assert '"sourceBackedOnly":true' in brain
    assert '"consolidated":true' in brain


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
