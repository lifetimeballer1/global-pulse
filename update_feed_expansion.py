#!/usr/bin/env python3
"""Ensure high-value U.S. politics, world politics and economics feeds exist."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=ROOT/'update_snapshot.py'
s=p.read_text(encoding='utf-8')
anchor='FEEDS = ['
feeds='''    ("GDELT Live — U.S. Politics", "https://api.gdeltproject.org/api/v2/doc/doc?query=(Trump%20OR%20Congress%20OR%20Senate%20OR%20House%20OR%20Supreme%20Court%20OR%20election%20OR%20midterms%20OR%20White%20House)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "us-politics"),
    ("GDELT Live — World Politics", "https://api.gdeltproject.org/api/v2/doc/doc?query=(election%20OR%20president%20OR%20parliament%20OR%20prime%20minister%20OR%20diplomacy%20OR%20summit%20OR%20sanctions%20OR%20alliance)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "world-politics"),
    ("GDELT Live — Global Economics", "https://api.gdeltproject.org/api/v2/doc/doc?query=(oil%20OR%20inflation%20OR%20tariff%20OR%20trade%20OR%20interest%20rate%20OR%20central%20bank%20OR%20stocks%20OR%20bonds%20OR%20currency)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "economics"),
    ("NPR Politics", "https://feeds.npr.org/1014/rss.xml", "us-politics"),
    ("Fox News Politics", "https://moxie.foxnews.com/google-publisher/politics.xml", "us-politics"),
    ("CNN Politics — GDELT Mirror", "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Acnn.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20Senate%20OR%20election%20OR%20White%20House)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "us-politics"),
    ("Axios Politics — GDELT Mirror", "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Aaxios.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20Senate%20OR%20election%20OR%20White%20House%20OR%20midterms)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "us-politics"),
    ("Morse Report — GDELT Mirror", "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Amorsereport.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20Senate%20OR%20election%20OR%20White%20House)&mode=ArtList&format=rss&maxrecords=100&timespan=24h", "us-politics"),
'''
if '"Fox News Politics"' not in s:
    i=s.index(anchor)+len(anchor)
    s=s[:i]+'\n'+feeds+s[i:]
p.write_text(s,encoding='utf-8')
print('Feed expansion applied.')
