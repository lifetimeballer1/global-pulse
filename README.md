# Global Pulse

**Evidence-backed global intelligence dashboard for conflict, geopolitical risk, public-source reporting, disasters, organized crime, strategic nodes, markets, and cross-domain intelligence relationships.**

Global Pulse is a public-source intelligence monitor. It does not claim classified access and it does not intentionally collect visitor identities or precise visitor locations.

## System overview

Global Pulse continuously turns public data into validated intelligence artifacts and user-facing views:

```text
Public sources
  ↓
Ingestion / source health
  ↓
Normalization + timestamp normalization
  ↓
Failover / preservation
  ↓
Conflict, OSINT, hazard, market and macro enrichment
  ↓
Event history + event intelligence + consistency + resolution
  ↓
Evidence-linked Intelligence Web
  ↓
Cross-domain Intelligence Brain
  ↓
Canonical JSON artifacts + refresh manifest
  ↓
GitHub Pages
  ↓
Pulse dashboard / map / markets / Intelligence Web / Brain
```

The production refresh entry point is `refresh_pipeline.py`. It is the canonical orchestrator used by the scheduled GitHub Actions refresh.

## Intelligence Web

The Intelligence Web is the evidence-linked relationship graph. It is built from the current intelligence snapshot rather than from a manually maintained second database.

The browser presentation is now a **WebGL-based 3D force-directed knowledge graph** using the canonical `data/intelligence_graph.json` artifact. It is designed as a living intelligence brain rather than a decorative network: related records attract, unrelated records repel, highly connected records become hubs, and the layout stabilizes instead of being continuously rebuilt.

The renderer supports:

- thousands of validated nodes/relationships with a bounded rendering cap for pathological datasets
- organic force-directed clustering and spatial hubs
- 3D rotation, pan, zoom, drag and smooth camera focus
- evidence-backed node selection and an intelligence inspector
- hover labels without permanently labeling the entire graph
- domain-aware node colors and importance/connectivity-based node sizing
- relationship color, opacity and width based on relationship semantics and weight
- recency-based visual emphasis
- search, domain filters and time-window filters
- relationship visibility, directional activity particles and auto-orbit controls
- preservation of approximate node positions across refreshes
- mobile touch interaction and a compact mobile inspector
- fail-safe loading/error behavior without fabricated intelligence

Graph data is normalized before rendering. Duplicate IDs, invalid endpoints, self-links, empty-evidence records, and malformed optional fields are ignored so one bad record cannot crash the visualization. The renderer never creates fake nodes or fake relationships to fill empty space.

Every published relationship is required to retain evidence. A relationship means that available public evidence connects the records; it is **not** presented as proof of causation, coordination, intent, or responsibility.

## Intelligence Brain

`data/intelligence_brain.json` is the compact cross-domain graph used for the main Brain experience.

The Brain is rebuilt on every canonical refresh from source-backed artifacts including live news, conflict corroboration, OSINT/map signals, event intelligence, claims, assessments, market indicators, macro context, and the evidence-linked Intelligence Web.

The human-facing Brain is intentionally capped at 35 major nodes. Raw records remain upstream. Nodes and relationships without source evidence are rejected by validation.

Market relationships are contextual relevance mappings and are never represented as causal claims.

## Major data sources and layers

### News

- Live RSS/Atom publisher feeds
- Global War News / OSINT reporting layers
- geopolitical and security reporting
- optional GDELT domain failover for eligible publisher feeds
- public X/RSS proxy sources where available

The live collector uses a persistent SQLite database with a seven-day retention window. Current source health, failures, fallbacks, and freshness are published in `data/live_status.json`.

### Conflict

- UCDP Candidate Events for conflict corroboration
- CFR conflict coverage
- Global War News conflict/map reporting
- event history, intelligence, consistency, and resolution artifacts

### Disasters and hazards

- GDACS alerts
- USGS earthquake data
- hazard/event geographic layers

### Organized crime / cartel intelligence

- dedicated Western Hemisphere / SOUTHCOM and counter-cartel feeds
- cartel/enforcer map data
- source-backed organized-crime map and relationship layers

### Strategic layer

Strategic nodes and chokepoints are generated into the canonical snapshot and can participate in map and Brain relationships.

### Markets

The market layer uses public Yahoo Finance chart data without a user API key. The current watchlist includes major indexes, volatility, commodities, FX, rates, and major equities. Market status distinguishes live, stale, and closed conditions using exchange-local session logic and recent intraday candles.

### Macro context

World Bank public macro observations are incorporated as contextual economic data.

## Canonical generated artifacts

The refresh pipeline validates and publishes these core artifacts:

- `data/snapshot.json` — primary dashboard snapshot
- `data/history.json` — historical state
- `data/sources.json` — source registry
- `data/live_articles.json` — persistent live-news export
- `data/live_status.json` — current source health and collector telemetry
- `data/intelligence_graph.json` — canonical evidence-linked Intelligence Web graph
- `data/intelligence_brain.json` — compact cross-domain Brain
- `data/map_points.json` — validated browser map marker feed
- `data/refresh_manifest.json` — SHA-256 hashes and generation metadata

Additional event, assessment, claim, regional, market-impact, trend, and intelligence artifacts are generated as part of the pipeline.

## Refresh and deployment

The canonical workflow is `.github/workflows/update-snapshot.yml`.

It runs:

- every 10 minutes
- on manual dispatch
- when core pipeline/validation/frontend files change

The workflow restores the persistent news database cache, runs `refresh_pipeline.py`, rebuilds browser map points, repairs/finalizes the map UI and cache busting, runs regression/performance/operational/security/repository/artifact checks, verifies hashes and critical browser inputs, commits generated changes, verifies the generated commit is on `main`, and deploys that exact site to GitHub Pages.

## Validation gates

The production path is deliberately fail-closed for internal pipeline failures. Important gates include:

- source health
- data resilience/failover
- map coordinate validation
- market freshness and positive-price checks
- event pipeline validation
- Intelligence Web evidence validation
- Intelligence Brain completeness and source-backed checks
- repository integrity
- browser security/privacy checks
- mobile/performance invariants
- operational health
- refresh manifest/hash verification

A successful process exit is not considered sufficient by itself; generated records, timestamps, counts, coordinates, evidence, and browser integration are checked before deployment.

## Map

The canonical map is implemented in `js/modules/map.js` and uses Leaflet with OpenStreetMap tiles.

The map supports conflict/military signals, hazards/disasters, strategic sites, cartel/organized crime, OSINT/reporting, Brain relationship lines, clustering, search, layer toggles, fit/reset controls, marker detail panels, source links, and Brain-node selection.

Map data is normalized and filtered to valid latitude/longitude ranges before rendering.

## Browser architecture

The main application is a mobile-first static site using modular JavaScript under `js/` plus focused browser modules.

Important browser layers include:

- `js/core/` — application state/config/utilities
- `js/modules/` — map and feature modules
- `global_pulse_core.js` — core dashboard integration
- `global_pulse_event_pipeline.js` — event UI/data integration
- `global_pulse_brain_ui.js` — Brain presentation
- `global_pulse_performance.js` — deferred loading and mobile performance behavior
- `global_pulse_qa.js` — browser QA/failure-state hardening
- `intelligence_brain_web.js` — canonical 3D Intelligence Web renderer, normalization, force layout, interaction and inspector
- `intelligence_web_controls_fix.js` — Intelligence Web filter-panel behavior

The Intelligence Web renderer is a presentation layer over the canonical generated graph. It does not replace the ingestion, evidence, relationship, refresh, map, or market systems.

## Intelligence Web architecture

```text
data/intelligence_graph.json
        ↓
validation + normalization
        ↓
node/relationship importance + recency scoring
        ↓
3D force-directed layout
        ↓
WebGL renderer
        ↓
hover / selection / filters / camera
        ↓
intelligence inspector + evidence sources
```

The graph uses evidence-backed records from the production intelligence pipeline. Node size combines connectivity with available mentions, importance/significance and confidence. Recency controls opacity/emphasis. Colors are centralized in `INTELLIGENCE_NODE_COLORS` so intelligence domains remain consistent and maintainable.

The renderer is intentionally dark and atmospheric. Minor records remain visually subordinate to major hubs, and labels are generated on demand rather than rendered as thousands of permanent DOM labels. Force simulation is warmed, cooled and reheated only when graph data or filters materially change. Approximate positions are retained by node ID where possible so refreshes evolve the graph instead of resetting it unnecessarily.

At present the canonical web surface is 3D/2.5D through `3d-force-graph`/Three.js/WebGL. The browser remains functional without a custom SVG graph implementation, avoiding a large DOM/SVG element count for dense datasets. If the external WebGL renderer cannot load, the page exposes a clear failure state rather than inventing a replacement graph.

## Time and freshness rules

Canonical generated timestamps are UTC ISO-8601 values.

The live news collector converts RSS/Atom publication timestamps to UTC before persistence. The refresh pipeline validates artifact freshness, and the live-site monitor rejects a published snapshot that is missing a timestamp or is materially stale.

The product distinguishes publication/event time from ingestion/refresh time where the underlying artifact provides both. It does not intentionally convert old reporting into a new publication time.

## Failure recovery

External sources are expected to fail occasionally.

Global Pulse therefore uses:

```text
primary source
  ↓
source-specific fallback where available
  ↓
last-known-good/preserved records
  ↓
explicit degraded/source-health state
```

A failed optional source must not erase the last known-good intelligence set. A failed internal processing stage is different: it should stop publication rather than silently publish a partially processed intelligence graph. The browser similarly displays a data-unavailable state rather than fabricating graph content.

## Security and privacy

The repository runs automated browser security/privacy checks before publication.

Current protections include:

- no client-side API keys or secrets
- no advertising identifiers
- no first-party analytics requirement
- no fingerprinting
- CSP coverage on browser surfaces
- external source text escaped before DOM insertion
- no `pull_request_target` workflows
- least-privilege workflow permissions appropriate to the deployment model
- local-only watchlist behavior

Third-party GitHub Actions are currently version-pinned by major release tags; immutable SHA pinning remains a security-hardening opportunity for the workflow fleet.

See `SECURITY.md` and `PRIVACY.md` for the project policies.

## Performance and mobile design

Global Pulse is designed for mobile-first use and large datasets.

The browser performance layer lazy-loads the Intelligence Web iframe, defers below-fold rendering work, uses `IntersectionObserver`/idle scheduling where supported, respects `prefers-reduced-motion`, uses marker clustering and chunked marker loading, and avoids unnecessary eager iframe loading.

The Intelligence Web itself uses WebGL/Three.js through `3d-force-graph`, bounded graph normalization, force-simulation cooling, persistent node positions during refreshes, low-opacity relationship rendering, on-demand labels, and compact mobile inspector behavior. Touch gestures are delegated to the 3D graph controls so the same canvas supports mobile rotation, pan and pinch zoom.

CI performance checks validate implementation invariants without pretending that a GitHub-hosted runner can reproduce every real-device performance metric.

## Running locally

Use a local static HTTP server so browser module and JSON loading behave like production:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

To run the canonical refresh locally:

```bash
python refresh_pipeline.py
```

The refresh requires network access to the public data sources used by the repository and may require the same Python runtime available in CI (currently Python 3.12).

Regression tests:

```bash
python -m pytest -q tests/test_regressions.py
```

Important validation commands include:

```bash
python validate_data_resilience.py
python validate_performance.py
python validate_operational_health.py
python validate_security.py
python validate_repository.py
```

## Production limitations

Global Pulse depends on public third-party sources. Availability, rate limits, feed changes, publisher timestamp quality, and public API behavior can change without notice.

The market layer is public-data context, not a trading feed or execution service. Some market instruments may legitimately be closed or stale outside their trading sessions.

The Intelligence Web and Brain are evidence-linking systems. They should be interpreted as structured public-source context, not as proof of hidden relationships or causation.

## Repository maintenance

`README.md`, `INTELLIGENCE_ARCHITECTURE.md`, and `SERVICE_ARCHITECTURE.md` are production documentation and must remain aligned with the implementation.

Do not add another versioned renderer or rescue layer when the canonical module can be extended safely. Deprecated code should be removed only after confirming it is no longer referenced by workflows or the live site.
