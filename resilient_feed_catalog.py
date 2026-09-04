#!/usr/bin/env python3
"""Canonical no-key feed catalog for Global Pulse.

The old catalog contained duplicate entries and several GDELT RSS queries that
were returning HTTP errors.  This catalog deliberately favors direct publisher
RSS feeds and Google News RSS search feeds as a no-key resilience layer.
"""
from urllib.parse import quote_plus


def google(query: str) -> str:
    q = quote_plus(f"{query} when:1d")
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


FEEDS = [
    ("GDACS Global Disaster Alerts", "https://www.gdacs.org/xml/rss.xml", "climate-hazard"),
    ("NPR Politics", "https://feeds.npr.org/1014/rss.xml", "us-politics"),
    ("Fox News Politics", "https://moxie.foxnews.com/google-publisher/politics.xml", "us-politics"),
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", "international"),
    ("BBC Middle East", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "regional"),
    ("BBC Africa", "https://feeds.bbci.co.uk/news/world/africa/rss.xml", "regional"),
    ("BBC Asia", "https://feeds.bbci.co.uk/news/world/asia/rss.xml", "regional"),
    ("BBC Europe", "https://feeds.bbci.co.uk/news/world/europe/rss.xml", "regional"),
    ("Guardian World", "https://www.theguardian.com/world/rss", "international"),
    ("Guardian US", "https://www.theguardian.com/us-news/rss", "regional"),
    ("NPR World", "https://feeds.npr.org/1004/rss.xml", "international"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "international"),
    ("DW World", "https://rss.dw.com/rdf/rss-en-world", "international"),
    ("France 24", "https://www.france24.com/en/rss", "international"),
    ("Crisis Group", "https://www.crisisgroup.org/rss.xml", "analysis"),
    ("ReliefWeb", "https://reliefweb.int/updates/rss.xml", "humanitarian"),

    ("Google News — Climate & Disaster", google("drought flood wildfire cyclone hurricane famine epidemic"), "climate-hazard"),
    ("Google News — Climate Security", google("climate security migration food water disease crisis"), "climate-hazard"),
    ("Google News — U.S. Politics", google("US politics Congress Senate White House election"), "us-politics"),
    ("Google News — CNN Politics", google("site:cnn.com politics Trump Congress Senate White House"), "us-politics"),
    ("Google News — Axios Politics", google("site:axios.com politics Trump Congress Senate White House"), "us-politics"),
    ("Google News — Morse Report", google("site:morsereport.com politics Congress Senate White House"), "us-politics"),
    ("Google News — World Politics", google("election president parliament diplomacy sanctions alliance"), "world-politics"),
    ("Google News — Global Economics", google("oil inflation tariff trade interest rate central bank stocks bonds currency"), "economics"),
    ("Google News — Global Conflict", google("war conflict military sanctions crisis attack airstrike missile drone"), "live"),
    ("Google News — Africa Security", google("Africa Sudan Congo Sahel Nigeria Somalia conflict military attack"), "africa"),
    ("Google News — South America Security", google("South America Colombia Venezuela Brazil Ecuador Peru conflict crime military"), "americas"),
    ("Google News — Middle East Security", google("Gaza Iran Israel Yemen Syria Iraq conflict missile drone"), "middle-east"),
    ("Google News — South Asia Security", google("India Pakistan Afghanistan Bangladesh Nepal Sri Lanka conflict security"), "south-asia"),
]

# Stable unique catalog; URL duplication must never create duplicate health rows.
FEEDS = list(dict.fromkeys(FEEDS))
