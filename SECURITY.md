# Global Pulse Security

## Security model

Global Pulse is a public, read-mostly intelligence dashboard. The safest architecture is to keep visitor interaction separate from ingestion credentials and automation.

### Rules

1. Never put API keys, tokens, passwords, webhook secrets, or private credentials in frontend JavaScript, HTML, JSON data, or Git history.
2. Prefer keyless public sources for the public pipeline.
3. Automated source fetching runs in GitHub Actions; browsers should only read published artifacts.
4. Do not collect visitor identifiers, precise location, fingerprinting data, or behavioral profiles.
5. Treat third-party source content as untrusted input. Escape it before inserting into HTML and never execute source-provided scripts.
6. External links opened from the dashboard use `noopener noreferrer`.
7. Intelligence scores are analytical indicators, not claims of certainty or predictions.
8. Preserve source attribution and evidence so users can independently inspect important claims.

## Operational privacy

The repository owner should use a dedicated project identity if separation from a personal identity is important. GitHub commit history, repository ownership, domain registration, hosting providers, and ordinary network logs can still establish associations. Application code alone cannot guarantee anonymity.

## Reporting a vulnerability

Do not publish credentials, personal information, or an exploitable vulnerability in a public issue. Use GitHub's private vulnerability-reporting mechanism if it is enabled for this repository, or contact the repository maintainer through a private channel.
