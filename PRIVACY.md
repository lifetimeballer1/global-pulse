# Global Pulse Privacy

Global Pulse is designed to be a public, privacy-respecting intelligence dashboard.

## What the site intentionally does not collect

- No account is required for the public dashboard.
- No first-party analytics or advertising tracker is included.
- No first-party cookies are used for identity tracking.
- No IP address, precise location, contacts, camera, microphone, or device identifier is intentionally collected by Global Pulse application code.
- No visitor data is written into the public intelligence datasets.

## What the site does

The browser downloads public data and public-source links. Some third-party services used by the site (for example map tiles or linked source websites) may receive normal web requests from your browser and may have their own logs and privacy policies. Global Pulse does not control those services.

Automated data collection happens in GitHub Actions on the server side, not from a visitor's browser. The public pipeline fetches open sources and publishes derived, non-personal intelligence artifacts.

## Important limitation

No public website can honestly guarantee that a visitor is anonymous. GitHub Pages, DNS providers, browsers, networks, map/CDN providers, and linked websites can keep ordinary infrastructure logs. Global Pulse therefore makes a narrower promise: its own application code is designed not to identify, profile, or intentionally track visitors.

Do not submit personal, confidential, operationally sensitive, or identifying information through public issues, pull requests, URLs, or other project surfaces.
