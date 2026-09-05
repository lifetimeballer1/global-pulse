#!/usr/bin/env python3
"""Keyless watcher for The Enforcer's public YouTube feed.

Primary path uses yt-dlp against the public channel page (no API key), which
also exposes current video descriptions. RSS remains a lightweight fallback.
Google My Maps links are stored only as source references and are not treated
as independently verified intelligence.
"""
import json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "enforcer_maps.json"
CHANNEL = "https://www.youtube.com/@enforcerofficial/videos"
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=UCM-eRxEc_TutiPIbOS1YYbw"
NS = {"a": "http://www.w3.org/2005/Atom", "m": "http://search.yahoo.com/mrss/"}
MAP_RE = re.compile(r"https?://(?:www\.)?google\.com/maps/d/(?:[^\s<>'\"]*?/)?(?:edit|viewer)(?:\?[^\s<>'\"]+)?", re.I)
UA = "GlobalPulse/1.3 (+https://github.com/lifetimeballer1/global-pulse)"

def clean_url(u):
    return u.rstrip(".,;:)]}")

def collect_with_ytdlp():
    try:
        import yt_dlp
    except ImportError:
        return None
    opts={"quiet":True,"no_warnings":True,"skip_download":True,"extract_flat":False,"playlistend":20,"socket_timeout":25}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info=ydl.extract_info(CHANNEL,download=False)
    entries=[e for e in (info.get("entries") or []) if e]
    videos=[]
    for e in entries:
        vid=str(e.get("id") or "")
        title=str(e.get("title") or "")
        published=e.get("upload_date") or e.get("timestamp") or ""
        if isinstance(published,int):
            published=datetime.fromtimestamp(published,timezone.utc).isoformat()
        elif re.fullmatch(r"\d{8}",str(published)):
            published=f"{published[:4]}-{published[4:6]}-{published[6:8]}T00:00:00+00:00"
        video_url="https://www.youtube.com/watch?v="+vid if vid else str(e.get("webpage_url") or "")
        desc=str(e.get("description") or "")
        found=[]
        for u in MAP_RE.findall(desc):
            u=clean_url(u)
            if u not in found: found.append(u)
        videos.append({"videoId":vid,"title":title,"published":published,"videoUrl":video_url,"mapCount":len(found),"mapUrls":found})
    return videos

def collect_with_rss():
    req=Request(FEED,headers={"User-Agent":UA,"Accept":"application/atom+xml,application/xml,text/xml,*/*"})
    with urlopen(req,timeout=25) as r: xml=r.read()
    root=ET.fromstring(xml)
    videos=[]
    for entry in root.findall("a:entry",NS):
        vid=entry.findtext("a:id","",NS).split(":")[-1]
        title=entry.findtext("a:title","",NS)
        published=entry.findtext("a:published","",NS)
        link="https://www.youtube.com/watch?v="+vid if vid else ""
        desc=""
        group=entry.find("m:group",NS)
        if group is not None: desc=group.findtext("m:description","",NS) or ""
        found=[]
        for u in MAP_RE.findall(desc):
            u=clean_url(u)
            if u not in found: found.append(u)
        videos.append({"videoId":vid,"title":title,"published":published,"videoUrl":link,"mapCount":len(found),"mapUrls":found})
    return videos

def main():
    videos=None; source="yt-dlp public channel"
    try:
        videos=collect_with_ytdlp()
    except Exception as e:
        print(f"yt-dlp channel check unavailable: {e}")
    if videos is None:
        try:
            videos=collect_with_rss(); source="YouTube public RSS fallback"
        except (HTTPError,URLError,ET.ParseError) as e:
            raise RuntimeError(f"YouTube channel and RSS checks both failed: {e}") from e
    existing=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"source":"The Enforcer","channel":"@enforcerofficial","maps":[]}
    by_url={x.get("url"):x for x in existing.get("maps",[]) if x.get("url")}
    new_links=0
    for video in videos:
        for u in video.get("mapUrls",[]):
            if u not in by_url:
                new_links+=1
                by_url[u]={"url":u,"title":video.get("title",""),"videoUrl":video.get("videoUrl",""),"published":video.get("published",""),"source":"The Enforcer YouTube description","confidence":"SOURCE LINK / UNVERIFIED"}
            else:
                by_url[u].update({"title":video.get("title",""),"videoUrl":video.get("videoUrl",""),"published":video.get("published","")})
    maps=sorted(by_url.values(),key=lambda x:x.get("published","") or "",reverse=True)[:100]
    existing.update({"updatedAt":datetime.now(timezone.utc).isoformat(),"feedUrl":FEED,"channelUrl":CHANNEL,"maps":maps,"recentVideos":videos[:20],"newMapLinks":new_links,"collectionMethod":source,"note":"Public YouTube channel data only; map links are extracted from descriptions and remain source references."})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Enforcer watcher: {len(videos)} public videos checked, {len(maps)} unique map links, {new_links} new links via {source}")

if __name__=="__main__": main()
