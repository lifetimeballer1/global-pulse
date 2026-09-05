#!/usr/bin/env python3
"""Ensure high-value politics, economics, climate, humanitarian and Western Hemisphere security feeds exist."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=ROOT/'update_snapshot.py'
s=p.read_text(encoding='utf-8')
anchor='FEEDS = ['
feeds='''    ("GDACS Global Disaster Alerts", "https://www.gdacs.org/xml/rss.xml", "climate-hazard"),
    ("GDELT Climate & Disaster Watch", "https://api.gdeltproject.org/api/v2/doc/doc?query=(drought%20OR%20flood%20OR%20wildfire%20OR%20cyclone%20OR%20hurricane%20OR%20heatwave%20OR%20famine%20OR%20food%20insecurity%20OR%20epidemic%20OR%20outbreak)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "climate-hazard"),
    ("GDELT Climate Security Watch", "https://api.gdeltproject.org/api/v2/doc/doc?query=(drought%20OR%20flood%20OR%20famine%20OR%20water%20shortage%20OR%20food%20crisis%20OR%20disease%20OR%20epidemic)%20AND%20(country%20OR%20government%20OR%20security%20OR%20migration)&mode=ArtList&format=rss&maxrecords=150&timespan=1h", "climate-hazard"),
    ("FAO GIEWS", "https://www.fao.org/giews/english/ew/ewr.xml", "food-security"),
    ("NPR Politics", "https://feeds.npr.org/1014/rss.xml", "us-politics"),
    ("Fox News Politics", "https://moxie.foxnews.com/google-publisher/politics.xml", "us-politics"),
    ("CNN Politics — GDELT Mirror", "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Acnn.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20Senate%20OR%20election%20OR%20White%20House)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "us-politics"),
    ("Axios Politics — GDELT Mirror", "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Aaxios.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20Senate%20OR%20election%20OR%20White%20House%20OR%20midterms)&mode=ArtList&format=rss&maxrecords=200&timespan=15m", "us-politics"),
    ("Morse Report — GDELT Mirror", "https://api.gdeltproject.org/api/v2/doc/doc?query=domain%3Amorsereport.com%20AND%20(politics%20OR%20Trump%20OR%20Congress%20OR%20Senate%20OR%20election%20OR%20White%20House)&mode=ArtList&format=rss&maxrecords=100&timespan=24h", "us-politics"),
    ("SOUTHCOM Official RSS", "https://www.southcom.mil/RSS/", "southcom"),
    ("Google News — SOUTHCOM", "https://news.google.com/rss/search?q=SOUTHCOM+US+Southern+Command+military+when%3A1d&hl=en-US&gl=US&ceid=US:en", "southcom-news"),
    ("Google News — Operation Southern Spear", "https://news.google.com/rss/search?q=%22Operation+Southern+Spear%22+cartel+narco-terrorism+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — Joint Task Force Western Hemisphere", "https://news.google.com/rss/search?q=%22Joint+Task+Force+Western+Hemisphere%22+cartel+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — Americas Counter Cartel Coalition", "https://news.google.com/rss/search?q=%22Americas+Counter+Cartel+Coalition%22+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — U.S. Counter-Cartel Operations", "https://news.google.com/rss/search?q=US+military+cartels+narco-terrorism+Ecuador+Mexico+Caribbean+Eastern+Pacific+when%3A1d&hl=en-US&gl=US&ceid=US:en", "counter-cartel"),
    ("Google News — Los Choneros", "https://news.google.com/rss/search?q=%22Los+Choneros%22+Ecuador+US+military+when%3A1d&hl=en-US&gl=US&ceid=US:en", "cartel"),
    ("Google News — Sinaloa Cartel / CJNG", "https://news.google.com/rss/search?q=Sinaloa+Cartel+CJNG+US+military+Mexico+when%3A1d&hl=en-US&gl=US&ceid=US:en", "cartel"),
'''
if '"SOUTHCOM Official RSS"' not in s:
    i=s.index(anchor)+len(anchor)
    s=s[:i]+'\n'+feeds+s[i:]
p.write_text(s,encoding='utf-8')
print('Politics + climate/humanitarian + SOUTHCOM/counter-cartel feed expansion applied.')
