# Global Pulse

### Real-time global conflict, geopolitical risk & open-source intelligence

**Global Pulse** is a mobile-first intelligence dashboard that turns public, open-source information into a continuously refreshed view of global events, conflicts, strategic locations, markets, hazards, and evidence-backed relationships.

> **Mission:** make fast-moving global information easier to monitor, understand, verify, and connect — without requiring an API key or a proprietary intelligence platform.

---

## Overview

Global Pulse is designed as a public-facing **global intelligence command center**. It combines multiple open data streams and analytical layers rather than treating a single news article as the complete picture.

The platform brings together:

- 🌐 **Live & breaking intelligence** — rapidly surfaced reports and newly detected activity
- 🧠 **Intelligence Web** — relationships between countries, organizations, conflicts, resources, and strategic entities
- ⚔️ **Conflict monitoring** — conflict and military-activity indicators
- 🗺️ **Global intelligence map** — geographic events, strategic locations, hazards, and open-source signals
- 📈 **Risk indicators** — explainable analytical scores based on observed signals
- 💹 **Market context** — public market information used as contextual evidence, not proof of causation
- 📰 **Source intelligence** — source attribution, freshness, corroboration, and evidence links
- ⚠️ **Conflict detection** — identification of reports that disagree or remain unconfirmed
- 🔎 **Why This Matters** — contextual assessment of potential immediate, regional, and global implications

---

## Intelligence pipeline

Global Pulse is built around a simple principle: **raw information should become structured intelligence only after it has been processed and contextualized.**

```text
REAL WORLD EVENTS
       ↓
PUBLIC / OPEN SOURCES
       ↓
LIVE INGESTION
       ↓
FRESHNESS & SOURCE VALIDATION
       ↓
EVENT DETECTION
       ↓
EVENT CLUSTERING
       ↓
CORROBORATION & CONFLICT CHECKS
       ↓
RELATIONSHIP / EVIDENCE ENGINE
       ↓
RISK & IMPACT ANALYSIS
       ↓
MARKET + MAP CONTEXT
       ↓
BREAKING INTELLIGENCE
```

This architecture is intended to prevent the dashboard from simply becoming a collection of unrelated headlines.

---

## Core principles

### Evidence first

Relationships and analytical indicators should be traceable to public evidence whenever possible. A connection is not treated as a fact merely because two entities appear on the same page.

### Fresh information gets priority

New events should be surfaced quickly while older information can remain visible when it continues to provide useful context.

### Correlation is not causation

Market movements, geographic proximity, and simultaneous reporting can provide context, but Global Pulse does not treat correlation as proof that one event caused another.

### Uncertainty is part of the intelligence

Reports can be incomplete, duplicated, delayed, disputed, or wrong. The system is designed to preserve that uncertainty rather than hide it behind overly confident language.

### Open-source by design

Global Pulse is designed around publicly accessible information and does not require a paid intelligence feed or user-supplied API key for its core public-data pipeline.

---

## Intelligence Web

The Intelligence Web is the relationship-analysis layer of Global Pulse.

Nodes represent entities such as countries, organizations, conflicts, strategic locations, economic interests, and resources. Connections are intended to represent relationships supported by available evidence.

Connection categories can include:

| Signal | Meaning |
|---|---|
| 🔴 Conflict | Conflict, attack, or military confrontation |
| 🟠 Energy / Oil | Energy, petroleum, infrastructure, or supply exposure |
| 🟡 Economic | Trade, sanctions, markets, financial, or economic pressure |
| 🔵 Strategic | Strategic, security, geographic, or alliance relationship |
| 🟣 Political | Political, diplomatic, or governmental relationship |
| 🟢 Resource | Resource or supply-chain relationship |

Selecting a node is intended to show **why it is connected**, the supporting evidence, related entities, and original source links.

---

## Risk & impact analysis

Global Pulse uses explainable indicators rather than presenting its calculations as predictions.

A risk indicator can incorporate signals such as:

- recent conflict activity
- military activity
- breaking-event activity
- economic or energy exposure
- diplomatic/de-escalation signals
- evidence-backed network exposure
- source and evidence volume

Example concept:

```text
RUSSIA RISK — 78 / 100  ↑  +12

CONTRIBUTING SIGNALS
+ Conflict activity
+ NATO-related tension
+ Military activity
+ Energy exposure
- Diplomatic de-escalation
```

The purpose is to explain **what changed and why**, not to claim certainty about what will happen next.

---

## Live events & breaking intelligence

Global Pulse separates an individual report from the broader event it may describe.

For example, several independent reports about the same developing incident can be grouped into a single event record:

```text
BREAKING
Missile strike reported near NATO territory

First detected: 6 min ago
Last updated: 48 sec ago
Reports: 11
Independent sources: 6
Confidence: HIGH

Potential impact:
NATO · Russia · Energy · Markets
```

The event layer is designed to reduce duplicate reporting and give the user a clearer picture of how much independent evidence exists.

---

## Source reliability & uncertainty

Source information is treated as a first-class part of the intelligence model.

The system can distinguish between:

- established news organizations
- official/government sources
- specialist open-source reporting
- public datasets
- social or user-generated reports
- unverified claims

A source or event may be represented with confidence such as:

- 🟢 **High**
- 🟡 **Moderate**
- 🟠 **Limited**
- 🔴 **Unverified**

Confidence describes the available evidence — **not absolute truth**.

When credible sources disagree, Global Pulse should preserve the disagreement and label the assessment accordingly rather than silently selecting one version.

---

## Data sources

The project is designed to aggregate public/open information including, where available:

- RSS and public news feeds
- public political and economic reporting
- conflict-monitoring datasets
- open-source map intelligence
- public hazard/event data
- public market data
- strategic reference data
- other openly accessible datasets incorporated by the update pipeline

Source availability can change over time. A feed being listed in the project does not guarantee that the upstream provider is currently available or publishing without delay.

---

## Automatic updates

The production pipeline is automated through **GitHub Actions**.

The update process is responsible for rebuilding public intelligence artifacts and validating the deployment before publication.

The browser also checks for newer generated data so the interface can update without requiring a full manual rebuild.

The exact refresh interval is controlled by the repository's workflow configuration and may change as the project evolves.

---

## Reliability & validation

Global Pulse uses automated validation to reduce the chance of deploying a partially generated dashboard.

Validation can check for:

- valid Python syntax
- valid JavaScript syntax
- required generated data files
- usable intelligence graph data
- evidence-backed connections
- source URLs and timestamps
- market data availability
- breaking intelligence artifacts
- event-clustering output
- risk/impact output
- required UI components
- successful production build/deployment conditions

If a required intelligence layer fails, the goal is to **fail safely instead of silently publishing incomplete intelligence**.

---

## Project structure

| File / directory | Purpose |
|---|---|
| `index.html` | Main Global Pulse dashboard |
| `data/snapshot.json` | Generated public intelligence snapshot |
| `data/history.json` | Historical tension/activity data |
| `data/sources.json` | Source registry and feed health |
| `data/live_articles.json` | Rapid/live article intelligence |
| `data/intelligence_graph.json` | Evidence-linked relationship graph |
| `data/` | Generated intelligence artifacts |
| `update_snapshot.py` | Core public-data aggregation |
| `update_feed_expansion.py` | News/politics/economics feed expansion |
| `update_osint.py` | Open-source geographic intelligence |
| `update_cfr.py` | Conflict reference layer |
| `update8_global_layers.py` | Strategic and hazard layers |
| `update_intelligence_web.py` | Evidence-linked relationship graph generation |
| `global_map_ui.py` | Interactive map UI |
| `global_pulse_graph.js` | Intelligence Web visualization |
| `global_pulse_enhancements.js` | Dashboard enhancements and status UI |
| `.github/workflows/` | Automated refresh, validation, and deployment workflows |

> Generated data files may be updated automatically and should not be edited manually unless the project specifically requires it.

---

## Running locally

Global Pulse is primarily designed for static hosting, but the generated files can be inspected locally with any simple HTTP server.

For example:

```bash
python -m http.server 8000
```

Then open the local dashboard at:

```text
http://localhost:8000/
```

Some browser features may require HTTP rather than opening `index.html` directly from the filesystem.

---

## No API key required

The core public-data experience is designed to work without asking the user to enter an API key.

External data providers may impose their own availability, rate limits, licensing requirements, or terms of use. Global Pulse does not guarantee uninterrupted access to any individual upstream source.

---

## Limitations

Global Pulse is an **open-source intelligence monitoring and analysis project**, not a government intelligence system and not a guaranteed real-time source of truth.

Important limitations include:

- some public sources publish with delays
- feeds can fail or disappear
- breaking events may initially be based on limited information
- duplicate reporting can occur
- geolocation can be imperfect
- markets may be delayed depending on the public data source
- analytical scores are indicators, not predictions
- source confidence does not equal factual certainty

For consequential decisions, users should verify important information against primary and authoritative sources.

---

## Roadmap

The long-term direction is to strengthen the complete intelligence loop:

- [x] Public-data aggregation
- [x] Conflict and geopolitical monitoring
- [x] Open-source geographic layers
- [x] Evidence-linked Intelligence Web
- [x] Live/breaking intelligence foundation
- [x] Event clustering foundation
- [x] Explainable risk/impact foundation
- [ ] Full multi-source corroboration engine
- [ ] Automated conflicting-report detection across major events
- [ ] Deeper event → relationship propagation
- [ ] Event → market impact attribution
- [ ] Event → map impact propagation
- [ ] Expanded historical event intelligence
- [ ] More comprehensive reliability testing

---

## Disclaimer

Global Pulse provides informational and analytical content derived from publicly available sources. It does not provide military, financial, legal, medical, or other professional advice.

**Do not interpret a Global Pulse score, alert, map marker, or relationship as a guarantee that an event occurred, will occur, or will produce a specific outcome. Always review the underlying sources for important claims.**

---

## License & attribution

See the repository's license and individual source/provider terms for applicable permissions, attribution requirements, and restrictions.

---

<div align="center">

**GLOBAL PULSE**  
*Real-time global intelligence from open sources.*

</div>
