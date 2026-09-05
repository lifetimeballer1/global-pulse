#!/usr/bin/env python3
"""Ensure high-value politics, economics, climate, humanitarian and Western Hemisphere security feeds exist."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=ROOT/'update_snapshot.py'
s=p.read_text(encoding='utf-8')

# Add focused, no-key Western Hemisphere security feeds once.
anchor='FEEDS = ['
feeds='''    ("SOUTHCOM Official Reporting — GDELT Mirror", "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Asouthcom.mil&mode=ArtList&format=rss&maxrecords=100&timespan=24h", "southcom"),
    ("Google News — SOUTHCOM", "https://news.google.com/rss/search?q=SOUTHCOM+US+Southern+Command+military+when%3A1d&hl=en-US&gl=US&ceid=US:en", "southcom-news"),
    ("Google News — Operation Southern Spear", "https://news.google.com/rss/search?q=%22Operation+Southern+Spear%22+cartel+narco-terrorism+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — Joint Task Force Western Hemisphere", "https://news.google.com/rss/search?q=%22Joint+Task+Force+Western+Hemisphere%22+cartel+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — Americas Counter Cartel Coalition", "https://news.google.com/rss/search?q=%22Americas+Counter+Cartel+Coalition%22+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — U.S. Counter-Cartel Operations", "https://news.google.com/rss/search?q=US+military+cartels+narco-terrorism+Ecuador+Mexico+Caribbean+Eastern+Pacific+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — Los Choneros", "https://news.google.com/rss/search?q=%22Los+Choneros%22+Ecuador+US+military+when%3A1d&hl=en-US&gl=US&ceid=US:en", "cartel"),
    ("Google News — Sinaloa Cartel / CJNG", "https://news.google.com/rss/search?q=Sinaloa+Cartel+CJNG+US+military+Mexico+when%3A1d&hl=en-US&gl=US&ceid=US:en", "cartel"),
    ("GDELT — Western Hemisphere Counter-Cartel", "https://api.gdeltproject.org/api/v2/doc/doc?query=(SOUTHCOM%20OR%20%22Southern%20Spear%22%20OR%20%22Joint%20Task%20Force%20Western%20Hemisphere%22%20OR%20cartel%20OR%20narco-terrorism%20OR%20Los%20Choneros%20OR%20CJNG%20OR%20Sinaloa)&mode=ArtList&format=rss&maxrecords=250&timespan=15m", "counter-cartel"),
'''
if '"GDELT — Western Hemisphere Counter-Cartel"' not in s:
    i=s.index(anchor)+len(anchor)
    s=s[:i]+'\n'+feeds+s[i:]

# Add a dedicated umbrella conflict record so the map/intelligence layers can treat
# the campaign as a connected Western Hemisphere security theater, rather than only
# separate Mexico/Ecuador cartel stories.
conflict_anchor='CONFLICTS = ['
conflict='''    ("western-hemisphere-cartel", "Western Hemisphere Counter-Cartel Campaign", "Western Hemisphere", "CRIMINAL CONFLICT", "HIGH", ["socom", "southcom", "southern command", "operation southern spear", "southern spear", "joint task force western hemisphere", "jtf-whem", "americas counter cartel coalition", "counter cartel", "narco-terrorism", "narco terrorist", "narco-terrorist", "cartel", "los choneros", "sinaloa cartel", "cjng"]),
'''
if '"western-hemisphere-cartel"' not in s:
    i=s.index(conflict_anchor)+len(conflict_anchor)
    s=s[:i]+conflict+s[i:]

p.write_text(s,encoding='utf-8')
print('Western Hemisphere SOUTHCOM/counter-cartel feeds and dedicated conflict layer installed.')
