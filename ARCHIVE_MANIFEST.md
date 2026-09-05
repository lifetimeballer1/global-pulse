# Global Pulse maintenance archive manifest

The canonical runtime is now `global_pulse_core.js`, `global_pulse_event_pipeline.js`, `global_pulse_tokens.css`, `global_map_ui.py`, and `refresh_pipeline.py`.

## Superseded V2.2–V2.7 renderers

`global_pulse_v22.js`, `global_pulse_v23.js`, `global_pulse_v24.js`, `global_pulse_v25.js`, `global_pulse_v26.js`, `global_pulse_v27.js`, and `global_pulse_v27_quality.js` were reviewed for unique behavior before consolidation. Their durable behavior is represented by the canonical core: trend/history, source health, conflict modal behavior, climate/humanitarian context, climate-to-conflict evidence pathways, market health, duplicate map hygiene, Morse/source visibility, and evidence-quality indicators.

They are no longer required by the canonical refresh pipeline and are safe to archive/delete after a successful production deployment of the canonical core.

## One-time install/migration scripts

The following 12 `install_*.py` files are migration/installers rather than runtime services:

- `install_breaking_alerts.py`
- `install_claim_intelligence.py`
- `install_commander_center.py`
- `install_event_intelligence.py`
- `install_health_finalizer.py`
- `install_intelligence_assessment.py`
- `install_intelligence_web.py`
- `install_live_events.py`
- `install_map_age_filter.py`
- `install_map_clustering.py`
- `install_map_v3.py`
- `install_v27.py`

The canonical pipeline no longer invokes these installers. They remain in the repository temporarily so deployment can be verified before deletion/archival. `global_map_ui.py` and `clean_index.py` now own the canonical map/index installation behavior.

## Event build consolidation

`build_event_history.py`, `build_event_intelligence.py`, `build_event_consistency.py`, `build_event_resolution.py`, and `build_event_market_impact.py` are orchestrated by `build_event_pipeline.py`. Their generated artifacts remain separate because downstream evidence consumers use those stable artifact names. `global_pulse_event_pipeline.js` is the canonical UI surface for the five outputs.

The old event renderers are no longer required by the canonical UI after `clean_index.py` runs.
