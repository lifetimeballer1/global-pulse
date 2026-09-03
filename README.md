# Global Pulse

**Global Pulse — Global Conflict & Intelligence Monitor**

A no-API-key global intelligence dashboard built for GitHub Pages. It combines public news/RSS, conflict tracking, open-source map signals, strategic reference points, and live public hazard data into one mobile-friendly command-center interface.

## What it does

- **Global news:** public RSS/open feeds with regional and global coverage.
- **Conflict monitor:** activity signals, escalation/status labels, facts, and analysis.
- **CFR layer:** Council on Foreign Relations Global Conflict Tracker data.
- **Global map:** conflict, OSINT, organized-crime, strategic-reference, and hazard layers.
- **Hazards:** public USGS earthquake data where available.
- **Watchlist:** save theaters locally on your device for quick access.
- **Automatic refresh:** the backend refreshes every 30 minutes; an open page checks for a newer snapshot and reloads automatically.
- **No API keys required:** the refresh pipeline uses public sources that do not require private credentials.

## Project structure

- `index.html` — dashboard UI and client-side interaction.
- `update_snapshot.py` — news/RSS collection and snapshot generation.
- `update_osint.py` — public map/OSINT synchronization.
- `update_cfr.py` — CFR conflict synchronization.
- `update8_global_layers.py` — strategic and hazard layers plus map installation.
- `update7_live_branding.py` — final deterministic UI cleanup and live-refresh logic.
- `global_map_ui.py` — canonical Leaflet map renderer.
- `apply_ui_patch.py` — stable intelligence brief/watchlist/modal behavior.
- `patch_index_ui.py` — small compatibility hardening step.
- `data/snapshot.json` — current published intelligence snapshot.
- `data/history.json` — tension/activity history.
- `data/sources.json` — source metadata.
- `.github/workflows/update-snapshot.yml` — refreshes, validates, commits, and deploys the site every 30 minutes.

## Automatic updates

The GitHub Actions workflow runs every 30 minutes and can also be started manually from the **Actions** tab. It validates the generated data and UI before deployment.

GitHub Pages is deployed from the same workflow that refreshes the data. This is intentional: commits made with the GitHub Actions token do not themselves start a second Pages workflow, so deployment happens directly after the refreshed site is built.

## Local development

```bash
python3 update_snapshot.py
```

Then open `index.html` in a browser or serve the folder with a local HTTP server.

## Data philosophy

Global Pulse separates **reported signals** from confirmed battlefield truth. Map points may be source-map reports or reference nodes and should not automatically be interpreted as verified incidents. Activity scores are signals derived from the available public data, not authoritative casualty or military assessments.

Direct X/Twitter ingestion is not included because reliable unauthenticated live access is not guaranteed. Public links can still be preserved when supplied by source data.

## Credits

Made by J.S.
