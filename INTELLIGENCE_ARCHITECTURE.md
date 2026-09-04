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

## Security model

- Least-privilege GitHub Actions permissions.
- No secrets or API keys in browser code.
- No analytics, advertising trackers, fingerprinting, or intentional visitor IDs.
- No `pull_request_target` workflows.
- Automated privacy/security checks run before deployment.
- Third-party Actions should be reviewed and pinned to immutable commit SHAs where practical.
- GitHub Pages should use HTTPS enforcement; the repository cannot itself control GitHub's HTTP response headers.

## Maintenance rule

Do not add another versioned renderer (`v28`, `v29`, etc.) when an existing canonical module can be extended safely. New features should either extend the canonical implementation or document why a separate module is required. Deprecated installers and renderers should be removed only after confirming they are no longer referenced by workflows or the live site.
