# Global Pulse v2
No-key news dashboard package.

## Structure
- `index.html` — front-end dashboard (Leaflet map, tension score, stories)
- `update_snapshot.py` — refreshes public RSS feeds into `data/snapshot.json`
- `data/snapshot.json` — current state served by the page
- `data/history.json` — tension history for the trend chart
- `.github/workflows/refresh.yml` — GitHub Action that runs the updater every 30 minutes

## Install
1. Copy these files into a GitHub repository (or replace an existing one).
2. Push to GitHub.
3. Enable GitHub Actions if prompted. The workflow refreshes public feeds every 30 minutes and commits updated snapshot/history.
4. For a live site, enable GitHub Pages (serve from root or `/docs` as preferred).

## Local refresh
```bash
python3 update_snapshot.py
```

## Notes
- Headlines come from public RSS feeds (BBC, Guardian, NPR).
- This version intentionally does not invent random market or news data.
- Tension scoring and breakdown are still illustrative until you define a transparent scoring pipeline.
- Map markers and social links are optional fields in the snapshot; they are preserved across refreshes if present.
- Direct X/Twitter live ingestion is not included because reliable live access generally requires platform access; optional public links can be stored in `social`.
