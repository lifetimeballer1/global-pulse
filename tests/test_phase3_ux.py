from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'index.html').read_text(encoding='utf-8')
installer=(ROOT/'install_event_intelligence.py').read_text(encoding='utf-8')
css=(ROOT/'global_pulse_phase3.css').read_text(encoding='utf-8')
js=(ROOT/'global_pulse_ux_hardening.js').read_text(encoding='utf-8')
density=(ROOT/'global_pulse_list_density.js').read_text(encoding='utf-8')

def test_phase3_assets_exist():
    assert '<link rel="stylesheet" href="global_pulse_phase3.css?v=1">' in installer
    assert '<script src="global_pulse_ux_hardening.js?v=1"></script>' in installer
    assert 'gp-dialog-open' in css and 'overscroll-behavior:contain' in css
    assert 'focusDialog' in js and 'lastFocus' in js

def test_compact_lists_remain_guarded():
    assert 'const LIMIT=5' in density
    assert 'See more (' in density
    assert 'MutationObserver' in density

def test_event_dialog_has_single_modal_contract():
    assert "getElementById('gp-event-modal')" in js
    assert "document.addEventListener('keydown'" in js

def test_mobile_containment_contract():
    assert 'max-height:calc(100dvh - 20px)' in css
    assert 'touch-action:none' in css
    assert 'touch-action:auto' in css
