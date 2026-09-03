#!/usr/bin/env python3
"""Collect near-real-time market indicators without requiring user API keys.

Yahoo Finance's public chart endpoint is the primary provider. Optional provider
secrets can be added by a deployment environment later, but the site never
requires the user to obtain one. Failed quotes retain the last known value and
are explicitly marked stale/closed; prices are never invented.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"
UA = "Mozilla/5.0 (compatible; GlobalPulse/4.0; +https://github.com/lifetimeballer1/global-pulse)"

WATCH = [
    ("S&P 500", "^GSPC", "index", "USD", 2), ("Dow Jones", "^DJI", "index", "USD", 2),
    ("Nasdaq Composite", "^IXIC", "index", "USD", 2), ("Nasdaq 100", "^NDX", "index", "USD", 2),
    ("Russell 2000", "^RUT", "index", "USD", 2), ("VIX", "^VIX", "volatility", "USD", 2),
    ("WTI Crude", "CL=F", "commodity", "USD", 2), ("Gold", "GC=F", "commodity", "USD", 2),
    ("Bitcoin", "BTC-USD", "crypto", "USD", 0), ("EUR / USD", "EURUSD=X", "fx", "USD", 4),
    ("USD / JPY", "JPY=X", "fx", "JPY", 2), ("U.S. 10Y Yield", "^TNX", "rates", "%", 2),
    ("FTSE 100", "^FTSE", "index", "GBP", 2), ("DAX", "^GDAXI", "index", "EUR", 2),
    ("Nikkei 225", "^N225", "index", "JPY", 2), ("Shanghai Composite", "000001.SS", "index", "CNY", 2),
    ("Hang Seng", "^HSI", "index", "HKD", 2), ("Nifty 50", "^NSEI", "index", "INR", 2),
    ("Sensex", "^BSESN", "index", "INR", 2), ("Apple", "AAPL", "equity", "USD", 2),
    ("Microsoft", "MSFT", "equity", "USD", 2), ("NVIDIA", "NVDA", "equity", "USD", 2),
    ("Amazon", "AMZN", "equity", "USD", 2), ("Alphabet", "GOOGL", "equity", "USD", 2),
    ("Meta", "META", "equity", "USD", 2), ("Tesla", "TSLA", "equity", "USD", 2),
]

def now():
    return datetime.now(timezone.utc).isoformat()

def fetch_quote(symbol):
    encoded = quote(symbol, safe="")
    last_error = None
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        url = f"https://{host}/v8/finance/chart/{encoded}?range=1d&interval=1m&includePrePost=false&events=history"
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urlopen(req, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = (payload.get("chart") or {}).get("result") or []
            if not result: raise RuntimeError("no chart result")
            meta = result[0].get("meta") or {}
            price = meta.get("regularMarketPrice")
            previous = meta.get("chartPreviousClose") or meta.get("previousClose")
            if price is None:
                closes = (((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or [])
                closes = [float(x) for x in closes if x is not None]
                price = closes[-1] if closes else None
            if price is None: raise RuntimeError("no current price")
            price = float(price); previous = float(previous) if previous is not None else price
            change = price - previous
            pct = change / previous * 100.0 if previous else 0.0
            market_time = meta.get("regularMarketTime")
            timestamp = datetime.fromtimestamp(float(market_time), tz=timezone.utc).isoformat() if market_time else now()
            state = str(meta.get("marketState") or "").upper()
            return {"price": price, "previousClose": previous, "change": change, "changePercent": pct,
                    "marketTime": timestamp, "marketState": state, "currency": meta.get("currency"),
                    "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
                    "endpoint": host, "interval": "1m", "provider": "Yahoo Finance"}
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error) if last_error else "all public market endpoints failed")

def collect_one(item):
    try: return item, fetch_quote(item[1]), None
    except Exception as exc: return item, None, f"{type(exc).__name__}: {exc}"[:180]

def main():
    data = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
    previous = data.get("marketData") if isinstance(data.get("marketData"), dict) else {}
    old_values = previous.get("indicators", []) if isinstance(previous, dict) else []
    old_by_symbol = {x.get("symbol"): x for x in old_values if isinstance(x, dict)}
    values_by_symbol, errors = {}, []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(collect_one, item) for item in WATCH]
        for future in as_completed(futures):
            item, quote_data, error = future.result()
            name, symbol, kind, unit, decimals = item
            if quote_data:
                state = quote_data.get("marketState", "")
                status = "live" if state in {"REGULAR", "PRE", "POST"} else "closed"
                quote_data.update({"name": name, "symbol": symbol, "type": kind, "unit": unit,
                                   "decimals": decimals, "status": status,
                                   "source": "Yahoo Finance public chart (1m)", "checkedAt": now()})
                values_by_symbol[symbol] = quote_data
            else:
                old = old_by_symbol.get(symbol)
                if old:
                    old = dict(old); old["status"] = "stale"; old["checkedAt"] = now(); values_by_symbol[symbol] = old
                errors.append({"symbol": symbol, "error": error})
    values = [values_by_symbol[symbol] for _, symbol, *_ in WATCH if symbol in values_by_symbol]
    market = {"updatedAt": now(), "source": "Yahoo Finance public chart (1m)", "provider": "Yahoo Finance",
              "noApiKey": True, "quoteInterval": "1m", "refreshMinutes": 5, "indicators": values,
              "errors": errors, "liveCount": sum(x.get("status") == "live" for x in values),
              "closedCount": sum(x.get("status") == "closed" for x in values),
              "staleCount": sum(x.get("status") == "stale" for x in values)}
    data["marketData"] = market
    SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MARKET DATA: live={market['liveCount']} closed={market['closedCount']} stale={market['staleCount']} errors={len(errors)}")

if __name__ == "__main__": main()
