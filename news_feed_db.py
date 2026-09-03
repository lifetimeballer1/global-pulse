#!/usr/bin/env python3
"""Persistent no-key news/X RSS collector for Global Pulse.

Keeps a rolling seven-day SQLite store, deduplicates by URL, and exports a
clean JSON feed for the static frontend. Run without arguments for a
continuous five-minute polling loop; use --once in CI/GitHub Actions.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DB_PATH = ROOT / "news_feed.db"
JSON_PATH = DATA / "live_articles.json"
STATUS_PATH = DATA / "live_status.json"
POLL_SECONDS = 300
RETENTION_DAYS = 7
USER_AGENT = "GlobalPulse/8.0 (+https://github.com/lifetimeballer1/global-pulse)"

SOURCES = {
    "cnn": {"name": "CNN", "url": "https://rss.cnn.com/rss/edition.rss", "type": "news", "category": "international"},
    "fox_politics": {"name": "Fox News Politics", "url": "https://moxie.foxnews.com/google-publisher/politics.xml", "type": "news", "category": "us-politics"},
    "npr_politics": {"name": "NPR Politics", "url": "https://feeds.npr.org/1014/rss.xml", "type": "news", "category": "us-politics"},
    "bbc_world": {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "type": "news", "category": "international"},
    "guardian_world": {"name": "The Guardian World", "url": "https://www.theguardian.com/world/rss", "type": "news", "category": "international"},
    "al_jazeera": {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "type": "news", "category": "international"},
    "axios_politics": {"name": "Axios Politics", "url": "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Aaxios.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20election)&mode=ArtList&format=rss&maxrecords=100&timespan=24h", "type": "news-mirror", "category": "us-politics"},
    "cnn_politics": {"name": "CNN Politics", "url": "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Acnn.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20election)&mode=ArtList&format=rss&maxrecords=100&timespan=24h", "type": "news-mirror", "category": "us-politics"},
    "morse_report": {"name": "Morse Report", "url": "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Amorsereport.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20election)&mode=ArtList&format=rss&maxrecords=100&timespan=24h", "type": "news-mirror", "category": "us-politics"},
}

X_ACCOUNTS = {
    "NASA": "NASA",
    "WhiteHouse": "White House",
    "POTUS": "POTUS",
    "NATO": "NATO",
    "UN": "United Nations",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def clean(value: str | None, limit: int = 700) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script.*?</script>|<style.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def parse_date(value: str | None) -> str:
    if not value:
        return iso_now()
    try:
        dt = parsedate_to_datetime(value)
    except Exception:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return iso_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def node_text(node: ET.Element, *tags: str) -> str:
    for tag in tags:
        try:
            found = node.find(tag)
        except SyntaxError:
            continue
        if found is not None:
            if found.text:
                return found.text.strip()
            if found.attrib.get("href"):
                return found.attrib["href"].strip()
    return ""


def node_link(node: ET.Element) -> str:
    link = node_text(node, "link", "{http://www.w3.org/2005/Atom}link")
    if link:
        return link
    for child in node:
        if child.tag.endswith("link") and child.attrib.get("href"):
            return child.attrib["href"].strip()
    return ""


def parse_feed(payload: bytes, source_id: str, meta: dict) -> list[dict]:
    root = ET.fromstring(payload)
    items = root.findall(".//item")
    atom = False
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        atom = True
    rows = []
    for item in items[:100]:
        title = clean(node_text(item, "title", "{http://www.w3.org/2005/Atom}title"), 300)
        link = node_link(item)
        summary = clean(node_text(item, "description", "summary", "content", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"), 900)
        pub = node_text(item, "pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated")
        author = clean(node_text(item, "author", "{http://purl.org/dc/elements/1.1/}creator", "{http://www.w3.org/2005/Atom}author"), 160)
        if not link:
            continue
        if not title:
            title = f"Update from {meta['name']}"
        rows.append({
            "url": link,
            "title": title,
            "published_date": parse_date(pub),
            "summary_snippet": summary,
            "source_name": meta["name"],
            "source_type": meta["type"],
            "category": meta["category"],
            "author": author,
            "username": "",
            "credit_metadata": json.dumps({"sourceId": source_id, "sourceUrl": meta["url"], "feedFormat": "atom" if atom else "rss"}, ensure_ascii=False),
        })
    return rows


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8"})
    with urlopen(req, timeout=20) as response:
        return response.read()


def x_urls(handle: str) -> list[str]:
    return [f"https://rss.xcancel.com/{handle}/rss", f"https://xcancel.com/{handle}/rss"]


def parse_x_account(handle: str, display_name: str) -> list[dict]:
    last_error = None
    for url in x_urls(handle):
        try:
            payload = fetch(url)
            text_payload = payload.decode("utf-8", errors="ignore")
            if "RSS reader not yet whitelisted" in text_payload or "checking your browser" in text_payload.lower():
                raise RuntimeError("proxy challenge/whitelist response")
            rows = parse_feed(payload, f"x:{handle}", {"name": f"X @{handle}", "type": "social", "category": "osint", "url": url})
            for row in rows:
                row["username"] = handle
                if not row["title"] or row["title"].startswith("Update from"):
                    row["title"] = f"Tweet by @{handle}"
                row["credit_metadata"] = json.dumps({"sourceId": f"x:{handle}", "handle": handle, "displayName": display_name, "proxy": url}, ensure_ascii=False)
            return rows
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error) if last_error else "X proxy unavailable")


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            published_date TEXT NOT NULL,
            summary_snippet TEXT DEFAULT '',
            source_name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            author TEXT DEFAULT '',
            username TEXT DEFAULT '',
            credit_metadata TEXT DEFAULT '{}',
            fetched_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_date DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_name)")
    conn.commit()


def purge_old(conn: sqlite3.Connection) -> int:
    cutoff = (utc_now() - timedelta(days=RETENTION_DAYS)).isoformat()
    cur = conn.execute("DELETE FROM articles WHERE published_date < ?", (cutoff,))
    conn.commit()
    return cur.rowcount


def upsert_articles(conn: sqlite3.Connection, rows: list[dict]) -> int:
    added = 0
    now = iso_now()
    for row in rows:
        try:
            cur = conn.execute("""
                INSERT OR IGNORE INTO articles
                (url,title,published_date,summary_snippet,source_name,source_type,category,author,username,credit_metadata,fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (row["url"], row["title"], row["published_date"], row["summary_snippet"], row["source_name"], row["source_type"], row["category"], row["author"], row["username"], row["credit_metadata"], now))
            added += 1 if cur.rowcount else 0
        except sqlite3.Error:
            continue
    conn.commit()
    return added


def export_json(conn: sqlite3.Connection, limit: int = 500) -> str:
    rows = conn.execute("""
        SELECT url,title,published_date,summary_snippet,source_name,source_type,category,author,username,credit_metadata
        FROM articles
        ORDER BY datetime(published_date) DESC
        LIMIT ?
    """, (limit,)).fetchall()
    articles = []
    for r in rows:
        credit = r[9]
        try:
            credit = json.loads(credit or "{}")
        except Exception:
            credit = {"raw": credit}
        articles.append({
            "url": r[0], "title": r[1], "published_date": r[2], "summary_snippet": r[3],
            "source": r[4], "sourceType": r[5], "category": r[6], "author": r[7],
            "username": r[8], "credit": credit,
        })
    return json.dumps({"updatedAt": iso_now(), "retentionDays": RETENTION_DAYS, "count": len(articles), "articles": articles}, ensure_ascii=False, indent=2) + "\n"


def write_export(conn: sqlite3.Connection) -> None:
    DATA.mkdir(exist_ok=True)
    JSON_PATH.write_text(export_json(conn), encoding="utf-8")


def run_cycle(conn: sqlite3.Connection) -> dict:
    fetched_rows: list[dict] = []
    errors: list[dict] = []
    for source_id, meta in SOURCES.items():
        try:
            fetched_rows.extend(parse_feed(fetch(meta["url"]), source_id, meta))
        except Exception as exc:
            errors.append({"source": meta["name"], "error": f"{type(exc).__name__}: {exc}"[:240]})
    for handle, display_name in X_ACCOUNTS.items():
        try:
            fetched_rows.extend(parse_x_account(handle, display_name))
        except Exception as exc:
            errors.append({"source": f"X @{handle}", "error": f"{type(exc).__name__}: {exc}"[:240]})

    purged = purge_old(conn)
    added = upsert_articles(conn, fetched_rows)
    write_export(conn)
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    status = {
        "updatedAt": iso_now(), "feedsChecked": len(SOURCES) + len(X_ACCOUNTS),
        "rowsFetched": len(fetched_rows), "newArticles": added, "purged": purged,
        "databaseArticles": count, "healthySources": len(SOURCES) + len(X_ACCOUNTS) - len(errors),
        "failedSources": errors, "pollSeconds": POLL_SECONDS, "retentionDays": RETENTION_DAYS,
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="fetch once and exit; intended for GitHub Actions")
    args = parser.parse_args()
    DATA.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        while True:
            try:
                status = run_cycle(conn)
                print(json.dumps(status, ensure_ascii=False))
            except Exception as exc:
                print(f"collector-cycle-error: {type(exc).__name__}: {exc}")
            if args.once:
                break
            time.sleep(POLL_SECONDS)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
