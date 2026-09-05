# Global Pulse — Intelligence Service Architecture

Global Pulse is a public-source intelligence service, not a private intelligence collection system.

## Core pipeline

`source -> report -> normalized claim -> evidence lineage -> corroboration/contradiction -> event -> entity -> relationship -> assessment -> user-facing brief`

The production implementation is orchestrated by `refresh_pipeline.py`. It runs keyless public-data ingestion, market and macro context, conflict/hazard corroboration, event processing, evidence-linked graph generation, assessments, claims, historical trends, index cleanup, browser hardening, and final validation before the GitHub Pages deployment gate.

## Product surfaces

- **Pulse:** what changed recently, prioritized by recency, significance and evidence quality.
- **Investigate:** claim/event evidence, source lineage, contradictions and confidence factors.
- **World:** map and event context.
- **Intelligence Web:** time-aware entity and relationship context.
- **Watchlist:** locally stored topics/entities chosen by the visitor; no server-side visitor profile.
- **Brief:** concise global/regional intelligence summaries.
- **Data Health:** freshness, source availability, feed failover and pipeline status.

## Evidence rules

1. A different URL is not automatically an independent source.
2. Syndicated, mirrored or copied reporting should inherit the origin when detectable.
3. Source diversity increases confidence only when the underlying reporting is materially independent.
4. Official statements are evidence, not automatic truth.
5. Contradictory credible reporting must remain visible and is explicitly flagged in the browser where detected.
6. Confidence describes the evidence available at the time, not absolute truth.
7. Every high-impact assessment should retain a path back to source material.
8. Market relationships are contextual relevance, not causal attribution.

## Generated-data contract

The canonical refresh verifies and publishes `data/snapshot.json`, `data/history.json`, `data/sources.json`, `data/live_articles.json`, and `data/intelligence_graph.json`. `data/refresh_manifest.json` records hashes and generation timestamps for these critical artifacts. Stale or missing required artifacts fail the pipeline rather than silently disappearing from the product.

Market data is accepted only when fresh and populated with real positive prices. Live news must contain recent articles and a healthy feed count. Feed failover state is surfaced to the browser, and the last successful refresh timestamp is retained in the snapshot.

## Privacy model

- No advertising identifiers.
- No first-party analytics requirement.
- No fingerprinting.
- Watchlists are stored locally in the browser only.
- Do not ingest visitor data into intelligence datasets.
- Never put secrets, API keys, credentials or private identifiers into client-side assets or generated public data.
- Do not claim that GitHub Pages makes the project operator anonymous; hosting infrastructure can retain security logs.

## Safety model

Global Pulse should describe public events and evidence without providing operational instructions for wrongdoing. Sensitive information should be presented at a level appropriate for public-source analysis. Avoid exposing private personal information, precise sensitive locations, or actionable targeting information when it is not necessary to understand the event.

## Reliability targets

- Every pipeline has a validation gate.
- Stale datasets must be labeled as stale rather than presented as live.
- Failed sources should not erase the last known good dataset.
- UI rendering must tolerate malformed or missing records.
- Automated updates must be idempotent.
- Changes should be small, testable and reversible.
- Scheduled live-site monitoring validates the published HTML and critical JSON artifacts independently of the build workflow.
