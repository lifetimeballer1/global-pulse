# Global Pulse Intelligence Architecture

## Mission
Global Pulse is a public, evidence-oriented global intelligence monitor. It is designed to summarize public information, expose uncertainty, preserve source provenance, and help users investigate events. It does not claim access to classified information and it does not identify or track visitors.

## Canonical data flow

`public reports -> normalization -> candidate claims -> evidence linkage -> corroboration/contradiction -> events -> entities/relationships -> assessments -> UI`

### Evidence rules

1. Report count is never treated as truth.
2. A distinct domain is not automatically an independent source.
3. Syndicated, copied, or clearly derivative reports should not increase independent-evidence counts.
4. Contradicting or denying reports remain attached to the claim.
5. Confidence must be explainable from observable factors.
6. Every intelligence relationship should retain evidence/provenance where available.
7. Missing data is represented as missing; the system must not manufacture precision.
8. Public-source collection must not collect visitor identifiers or precise user location.

## Reliability model

The system distinguishes:

- **Source domain** — the web publisher/domain.
- **Source family** — the underlying publisher/network when known.
- **Report** — one published item.
- **Claim** — a normalized proposition suggested by one or more reports.
- **Event** — a time/location/topic cluster of related claims.
- **Entity** — a country, organization, person, place, infrastructure item, or other durable object.
- **Assessment** — an explicitly qualified interpretation based on evidence.

## Current canonical refresh

`refresh_pipeline.py` is the production orchestrator. It refreshes live news, the market layer, political/OSINT/conflict/hazard layers, UCDP corroboration, World Bank macro context, event artifacts, the evidence-linked Intelligence Web, assessments, claims, What Changed, and historical trends. It then cleans the generated index, applies browser security hardening, installs the browser QA layer, validates the repository, and writes `data/refresh_manifest.json` with SHA-256 hashes and freshness timestamps for critical generated artifacts.

Required public artifacts include `snapshot.json`, `history.json`, `sources.json`, `live_articles.json`, and `intelligence_graph.json`. The pipeline treats stale/missing required data as a validation failure rather than manufacturing replacement values.

## Market and external-data model

The market layer uses public Yahoo Finance chart data without a user API key. A refresh is accepted only when the market artifact is fresh, contains at least the expected indicator count, and includes positive real prices. Event-to-market relationships are contextual relevance mappings; they do not claim causation.

Open hazard, conflict-corroboration, and macro layers use keyless public sources such as GDACS/USGS, UCDP Candidate Events, and World Bank data. Source availability is recorded rather than treated as guaranteed.

## Browser resilience

The dashboard labels stale data, surfaces source failover health, shows a distinct snapshot-fetch failure state, and isolates map/graph rendering errors. Map markers expose keyboard/assistive labels, long evidence text is collapsible, and confidence is represented independently from signal color.

The first-use guide explains signal colors and confidence tiers. Event/node cards can be deep-linked with URL hashes. Watchlists remain local to the browser.

## Security model

- Least-privilege GitHub Actions permissions.
- No secrets or API keys in browser code.
- No `pull_request_target` workflows.
- Automated privacy/security checks run before deployment.
- Third-party Actions should be reviewed and pinned to immutable commit SHAs where practical.
- Browser-facing HTML receives a defense-in-depth CSP; GitHub Pages itself controls the final HTTP response headers.
- External source content is escaped before insertion into the DOM.

## Maintenance rule

Do not add another versioned renderer (`v28`, `v29`, etc.) when an existing canonical module can be extended safely. New features should either extend the canonical implementation or document why a separate module is required. Deprecated installers and renderers should be removed only after confirming they are no longer referenced by workflows or the live site.
