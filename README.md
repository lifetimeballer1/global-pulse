# Global Pulse

**Global Pulse — Global Conflict & Intelligence Monitor**

A no-API-key global intelligence dashboard built for GitHub Pages. It combines public news/RSS, conflict tracking, open-source map signals, strategic reference points, and live public hazard data into one mobile-friendly command-center interface.

## What it does

- **Global news:** public RSS/open feeds with global and regional coverage.
- **Conflict monitor:** theater activity signals, escalation/status labels, facts, and analysis.
- **CFR layer:** Council on Foreign Relations Global Conflict Tracker reference data.
- **Global map:** conflict, OSINT, organized-crime, strategic-reference, and hazard layers.
- **Hazards:** public USGS earthquake data where available.
- **Watchlist:** save theaters locally on the device for quick access.
- **Automatic refresh:** backend data refreshes every 30 minutes; an open page checks for a newer snapshot and reloads automatically.
- **No API keys required:** the pipeline uses public sources that do not require private credentials.

## Project structure

- `index.html` — dashboard UI and client-side interaction.
- `update_snapshot.py` — news/RSS collection and snapshot generation.
- `update_osint.py` — public map/OSINT synchronization.
- `update_cfr.py` — CFR conflict synchronization.
- `update8_global_layers.py` — strategic and hazard layers plus map installation.
- `update7_live_branding.py` — deterministic branding/layout cleanup and live-refresh logic.
- `global_map_ui.py` — canonical Leaflet map renderer.
- `data/snapshot.json` — current published intelligence snapshot.
- `data/history.json` — tension/activity history.
- `data/sources.json` — source metadata.
- `.github/workflows/update-snapshot.yml` — scheduled/manual refresh, validation, and direct Pages deployment.

## Automatic updates

The GitHub Actions workflow runs every 30 minutes and can also be started manually from the **Actions** tab. It validates the generated data and UI before deployment.

The refresh workflow deploys the refreshed artifact directly. It intentionally does not run on ordinary pushes because GitHub Pages already handles source-change deployments; this avoids duplicate deployments while preserving scheduled data publishing. GitHub notes that commits made with `GITHUB_TOKEN` do not themselves trigger another workflow or Pages build. citeturn0search1turn0search4

## Local development

```bash
python3 update_snapshot.py
```

Then serve the folder with a local HTTP server rather than opening the HTML file directly:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000` in a browser.

## Data philosophy

Global Pulse separates **reported signals** from confirmed battlefield truth. Map points may be source-map reports or reference nodes and should not automatically be interpreted as verified incidents. Activity scores are analytical signals derived from available public data, not authoritative casualty or military assessments.

Direct X/Twitter ingestion is not included because reliable unauthenticated live access is not guaranteed. Public links can still be preserved when supplied by source data.

## Credits

Made by J.S.
