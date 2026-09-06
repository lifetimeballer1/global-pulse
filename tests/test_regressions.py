from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_map_conflict_filter_has_canonical_classifier_and_rerender():
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


def test_map_renders_only_geographic_brain_relationships_and_can_toggle_them():
    text = (ROOT / 'js/modules/map.js').read_text(encoding='utf-8')
    assert 'renderBrainLinks' in text
    assert 'L.polyline' in text
    assert 'byId.get(String(e.source))' in text
    assert 'byId.get(String(e.target))' in text
    assert "String(e.source)===String(e.target)" in text
    assert 'gpMapBrainLinks' in text
    assert 'gp.mapBrainLinks' in text
    assert "if(!a||!b" in text


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


def test_phase5_failover_preserves_existing_story_records():
    import source_failover
    existing = [
        {'url': 'https://example.test/old', 'title': 'Existing story', 'published_date': '2026-09-06T01:00:00Z'},
        {'url': 'https://example.test/keep', 'title': 'Another story', 'published_date': '2026-09-06T02:00:00Z'},
    ]
    additions = [
        {'url': 'https://example.test/new', 'title': 'Fallback story', 'published_date': '2026-09-06T03:00:00Z'},
        {'url': 'https://example.test/old', 'title': 'Duplicate existing', 'published_date': '2026-09-06T04:00:00Z'},
    ]
    merged = source_failover.merge_stories(existing, additions)
    assert len(merged) == 3
    assert [x['url'] for x in merged] == [
        'https://example.test/old',
        'https://example.test/keep',
        'https://example.test/new',
    ]


def test_phase5_resilience_validator_is_wired_into_refresh_and_workflows():
    pipeline = (ROOT / 'refresh_pipeline.py').read_text(encoding='utf-8')
    workflow = (ROOT / '.github/workflows/update-snapshot.yml').read_text(encoding='utf-8')
    diagnostics = (ROOT / '.github/workflows/data-resilience.yml').read_text(encoding='utf-8')
    assert 'validate_data_resilience.py' in pipeline
    assert 'validate_data_resilience.py' in workflow
    assert 'python validate_data_resilience.py' in diagnostics
    assert 'uses: actions/deploy-pages@v4' in workflow
    assert 'uses: actions/deploy-pages@v4' not in diagnostics
