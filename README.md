# Global Pulse

**World Economics & Conflict Dashboard** — a single-page “situation room” view combining:

- **Global Tension Index** (illustrative 0–100% composite)
- Interactive country relationship map (D3 force-directed)
- Hourly-style news digest (sample stories)
- Economic pulse panel (oil, VIX, indices, yields)

## Live page

Once GitHub Pages is enabled:

**https://lifetimeballer1.github.io/global-pulse/**

### Enable Pages
1. Go to the repository **Settings → Pages**
2. Under **Source**, select **Deploy from a branch**
3. Branch: `main` / folder: `/ (root)`
4. Save — the site usually appears within a minute or two

## Notes

- This is a **static demo**. The Tension Index and stories are sample data shaped around the September 2026 picture (Iran/Hormuz risk, Russia–Ukraine, China–Taiwan pressure, China–Russia alignment, elevated oil).
- The Index is explicitly labeled as an **illustrative model**, not a forecast or prediction.
- Framing is slightly more attentive to revisionist pressure, energy leverage, and deterrence costs while staying within mainstream reporting.
- For a production version you would add a scheduled backend (Vercel Cron / Netlify function) pulling GDELT, market APIs, etc., and overwrite a JSON snapshot the frontend loads.

## License

Demo / illustrative use. Source links in a live system should point to original reporting.
