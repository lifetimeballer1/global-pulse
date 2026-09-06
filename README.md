# Global Pulse (Clean Rebuild)

**Real-time global conflict, geopolitical risk & open-source intelligence**

This is a complete clean-architecture rebuild of the original Global Pulse project, produced according to the `global-intelligence-web` skill.

## What was fixed

- Removed the explosion of one-off `build_*` / `install_*` / `update_*` scripts.
- Single modular frontend (clear separation of core / modules).
- Proper loading / empty / error / offline states.
- Resilient fetch layer with localStorage cache fallback.
- Consistent confidence labeling and source attribution.
- Mobile-first bottom navigation + sticky header.
- Dark intelligence-terminal design system.
- Clear DELAYED labeling on markets.
- Fail-safe data loading (never crashes the UI).

## Required sections (skill compliance)

1. Global Situation Overview — ✓
2. Interactive World Map — ✓ (Leaflet + layers)
3. War / Conflict Tracker — ✓
4. Economic / Market context — ✓ (labeled DELAYED)
5. Breaking News Engine — ✓
6. Intelligence Web (relationships) — ✓ (list + graph data)
7. System & Source Status — ✓

## Running locally

```bash
cd global-pulse-clean
python -m http.server 8000
```

Open http://localhost:8000

The UI will load the JSON artifacts in `/data`. If a file is missing it degrades gracefully and shows clear empty/error states.

## Data pipeline (next steps)

A single clean orchestrator should replace the previous dozens of scripts:

```
pipeline/
  build_snapshot.py   # one entry point
  sources/            # modular adapters (RSS, GDACS, USGS, Yahoo delayed, etc.)
  normalize/
  enrich/
  validate.py
```

GitHub Actions should call only `build_snapshot.py` + validation, then commit the generated `/data` artifacts.

## Design principles (enforced)

- Never invent events or numbers.
- Always show LAST UPDATED + source + confidence.
- Separate FACTS / ANALYSIS / PREDICTIONS.
- Primary → secondary → cache → “data unavailable”.
- Mobile-first, accessible, fast.

## License

Same as original project. Public open-source intelligence only.
