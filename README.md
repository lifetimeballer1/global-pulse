# Global Pulse

**Global Pulse — Global Conflict & Intelligence Monitor**

A no-API-key global intelligence dashboard built for GitHub Pages. It combines public news/RSS, conflict tracking, open-source map signals, strategic reference points, and live public hazard data into one mobile-friendly command-center interface.

## Automatic refresh

GitHub Actions refreshes the public data pipeline every 30 minutes and on main-branch changes. The production validation step checks the generated snapshot, maps, intelligence graph, JavaScript, branding, and required data layers before deployment.

The dashboard also checks the published snapshot in the browser every 60 seconds and reloads when a newer snapshot is available.

## Data philosophy

Global Pulse separates reported signals from confirmed facts. News and open-source map signals can be incomplete, delayed, duplicated, or wrong. Conflict scores are analytical indicators of reporting activity, not measurements of battlefield truth or predictions of war.

## Project

- `index.html` — dashboard UI
- `data/snapshot.json` — generated public intelligence snapshot
- `data/history.json` — tension history
- `data/sources.json` — feed health and source registry
- `update_snapshot.py` — RSS/open-data aggregation
- `update_feed_expansion.py` — U.S. politics, world politics, and economics feed expansion
- `update_osint.py` — open-source map layers
- `update_cfr.py` — Council on Foreign Relations conflict layer
- `update8_global_layers.py` — strategic reference and USGS hazard layers
- `update_intelligence_web.py` — evidence-linked relationship graph
- `global_map_ui.py` — canonical interactive map UI
- `global_pulse_graph.js` — intelligence web visualization
- `global_pulse_enhancements.js` — production UI/status enhancements

**Made by J.S.**