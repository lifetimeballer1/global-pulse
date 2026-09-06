# Global Pulse

**Evidence-backed global intelligence dashboard for conflict, geopolitical risk, public-source reporting, disasters, organized crime, strategic nodes, markets, and cross-domain intelligence relationships.**

Global Pulse is a public-source intelligence monitor. It does not claim classified access and it does not intentionally collect visitor identities or precise visitor locations.

## System overview

Global Pulse continuously turns public data into a set of validated intelligence artifacts and user-facing views:

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

The graph can represent:

- entities and actors
- countries
- conflicts and events
- strategic nodes and chokepoints
- organized-crime/cartel entities
- economic factors
- evidence/source relationships
- contextual relationships between major intelligence entities

Every published relationship is required to retain evidence. A relationship means that the available public evidence connects the records; it is **not** presented as proof of causation, coordination, intent, or responsibility.

The browser also exposes relationship context from the Intelligence Brain, allowing a map signal or Brain node to be traced into connected intelligence and source evidence.

## Intelligence Brain

`data/intelligence_brain.json` is the compact cross-domain graph used for the main Brain experience.

The Brain is rebuilt on every canonical refresh from source-backed artifacts including:

- live news and source records
- conflict corroboration
- OSINT/map signals
- event intelligence and historical event data
- claims and assessments
- market indicators and market-impact context
- macro context
- the evidence-linked Intelligence Web

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
- `data/intelligence_graph.json` — Intelligence Web graph
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

The workflow:

1. restores the persistent news database cache
2. runs `refresh_pipeline.py`
3. rebuilds browser map points
4. repairs/finalizes the map UI and cache busting
5. runs regression tests
6. runs performance, operational-health, resilience, security, repository, and artifact checks
7. verifies hashes and critical browser inputs
8. commits generated data/UI changes
9. verifies the generated commit is on `main`
10. uploads the exact generated working tree to GitHub Pages
11. deploys that exact site

The repository also contains separate diagnostics/recovery workflows. Writer workflows are serialized with the canonical refresh concurrency group so they do not race with the production refresh when they commit generated artifacts.

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

The map supports:

- conflict/military signals
- hazards/disasters
- strategic sites
- cartel/organized crime
- OSINT/reporting
- Brain relationship lines
- clustering
- search
- layer toggles
- fit/reset controls
- marker detail panels
- source links
- Brain-node selection

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
- `intelligence_brain_web.js` — Intelligence Web interface
- `intelligence_web_controls_fix.js` — Intelligence Web controls

The browser is designed to tolerate missing optional records and to expose data-unavailable states instead of fabricating values.

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

A failed optional source must not erase the last known-good intelligence set. A failed internal processing stage is different: it should stop publication rather than silently publish a partially processed intelligence graph.

## Security and privacy

The repository runs automated browser security/privacy checks before publication.

Current protections include:

- no client-side API keys or secrets
- no advertising identifiers
- no first-party analytics requirement
- no fingerprinting
- CSP coverage on the browser surfaces
- external source text escaped before DOM insertion
- no `pull_request_target` workflows
- least-privilege workflow permissions appropriate to the deployment model
- local-only watchlist behavior

Third-party GitHub Actions are currently version-pinned by major release tags; immutable SHA pinning remains a security-hardening opportunity for the workflow fleet.

See `SECURITY.md` and `PRIVACY.md` for the project policies.

## Performance and mobile design

Global Pulse is designed for mobile-first use and large map datasets.

The browser performance layer:

- lazy-loads the Intelligence Web iframe
- defers below-fold rendering work
- uses `IntersectionObserver`/idle scheduling where supported
- respects `prefers-reduced-motion`
- uses marker clustering and chunked marker loading
- avoids unnecessary eager iframe loading
- protects against horizontal-overflow regressions

The CI performance gate validates these implementation invariants without pretending that a GitHub-hosted runner can reproduce every real-device performance metric.

## Running locally

Use a local static HTTP server so browser module and JSON loading behave like production:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

To run the canonical refresh locally, use:

```bash
python refresh_pipeline.py
```

The refresh requires network access to the public data sources used by the repository. It may also require the same Python runtime available in CI (currently Python 3.12).

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
