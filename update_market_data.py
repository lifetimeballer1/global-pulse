#!/usr/bin/env python3
"""Collect a small set of live market indicators without an API key.

Uses Yahoo Finance's public chart endpoint server-side. The collector tries
both public Yahoo hosts and retries transient failures. If a quote cannot be
retrieved, the previous good value is retained and marked stale instead of
inventing a number.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"
UA = "Mozilla/5.0 (compatible; GlobalPulse/2.7; +https://github.com/lifetimeballer1/global-pulse)"

WATCH = [
    ("S&P 500", "^GSPC", "index", "USD", 2),
    ("Dow Jones", "^DJI", "index", "USD", 2),
    ("Nasdaq Composite", "^IXIC", "index", "USD", 2),
    ("VIX", "^VIX", "volatility", "USD", 2),
    ("WTI Crude", "CL=F", "commodity", "USD", 2),
    ("Gold", "GC=F", "commodity", "USD", 2),
    ("Bitcoin", "BTC-USD", "crypto", "USD", 0),
    ("EUR / USD", "EURUSD=X", "fx", "USD", 4),
    ("USD / JPY", "JPY=X", "fx", "JPY", 2),
    ("U.S. 10Y Yield", "^TNX", "rates", "%", 2),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_quote(symbol: str) -> dict:
    encoded = quote(symbol, safe="")
    last_error = None
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        url = f"https://{host}/v8/finance/chart/{encoded}?range=5d&interval=1d&events=history"
        for attempt in range(2):
            try:
                req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
                with urlopen(req, timeout=12) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                result = (payload.get("chart") or {}).get("result") or []
                if not result:
                    raise RuntimeError("no chart result")
                meta = result[0].get("meta") or {}
                price = meta.get("regularMarketPrice")
                previous = meta.get("previousClose")
                if price is None:
                    closes = (((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or [])
                    closes = [float(x) for x in closes if x is not None]
                    price = closes[-1] if closes else None
                if price is None:
                    raise RuntimeError("no current price")
                if previous is None:
                    previous = price
                price = float(price)
                previous = float(previous)
                change = price - previous
                pct = (change / previous * 100.0) if previous else 0.0
                market_time = meta.get("regularMarketTime")
                timestamp = datetime.fromtimestamp(float(market_time), tz=timezone.utc).isoformat() if market_time else now()
                return {"price": price, "previousClose": previous, "change": change, "changePercent": pct, "marketTime": timestamp, "currency": meta.get("currency"), "endpoint": host}
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.5)
    raise RuntimeError(str(last_error) if last_error else "all public market endpoints failed")


def main() -> None:
    data = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
    previous = data.get("marketData") if isinstance(data.get("marketData"), dict) else {}
    values = []
    errors = []
    for name, symbol, kind, unit, decimals in WATCH:
        try:
            q = fetch_quote(symbol)
            q.update({"name": name, "symbol": symbol, "type": kind, "unit": unit, "decimals": decimals, "status": "live", "source": "Yahoo Finance public chart", "checkedAt": now()})
            values.append(q)
        except Exception as exc:
            old = next((x for x in (previous.get("indicators", []) if isinstance(previous, dict) else []) if x.get("symbol") == symbol), None)
            if old:
                old = dict(old); old["status"] = "stale"; old["checkedAt"] = now(); values.append(old)
            errors.append({"symbol": symbol, "error": f"{type(exc).__name__}: {exc}"[:180]})
        time.sleep(0.15)
    if not values and previous:
        market = previous
    else:
        market = {"updatedAt": now(), "source": "Yahoo Finance public chart", "noApiKey": True, "indicators": values, "errors": errors, "liveCount": sum(1 for x in values if x.get("status") == "live"), "staleCount": sum(1 for x in values if x.get("status") == "stale")}
    data["marketData"] = market
    data["marketData"]["updatedAt"] = now()
    data["marketData"]["errors"] = errors
    data["marketData"]["liveCount"] = sum(1 for x in values if x.get("status") == "live")
    data["marketData"]["staleCount"] = sum(1 for x in values if x.get("status") == "stale")
    data["marketData"]["noApiKey"] = True
    SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MARKET DATA: live={data['marketData']['liveCount']} stale={data['marketData']['staleCount']} errors={len(errors)}")


if __name__ == "__main__":
    main()
