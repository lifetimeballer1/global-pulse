#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
INDEX=ROOT/'index.html'; SNAP=ROOT/'data'/'snapshot.json'; LIVE=ROOT/'data'/'live_articles.json'; DB=ROOT/'news_feed.db'

class MorseParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.href=''; self.parts=[]; self.in_a=False
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='a': self.in_a=True; self.href=dict(attrs).get('href',''); self.parts=[]
    def handle_data(self,data):
        if self.in_a:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=='a' and self.in_a:
            text=' '.join(''.join(self.parts).split()); href=self.href
            if href and text:self.links.append((href,text))
            self.in_a=False; self.href=''; self.parts=[]

def fetch(url):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 (GlobalPulse/2.6)','Accept':'text/html,application/rss+xml,application/atom+xml,application/xml;q=0.9,*/*;q=0.8'})
    with urlopen(req,timeout=15) as r:return r.read()

def rss_rows(payload):
    try:
        from xml.etree import ElementTree as ET
        root=ET.fromstring(payload); rows=[]
        for item in root.findall('.//item')[:30]:
            title=' '.join((item.findtext('title') or '').split()); link=(item.findtext('link') or '').strip(); desc=' '.join((item.findtext('description') or '').split()); pub=(item.findtext('pubDate') or '').strip()
            if title and link:rows.append((link,title,desc,pub))
        return rows
    except Exception:return []

def direct_morse_rows():
    for u in ('https://morsereport.com/blogs/news/rss','https://morsereport.com/blogs/news.atom','https://morsereport.com/rss','https://morsereport.com/feed'):
        try:
            rows=rss_rows(fetch(u))
            if rows:return rows
        except Exception:pass
    try:
        p=MorseParser();p.feed(fetch('https://morsereport.com/').decode('utf-8','ignore')); rows=[];seen=set()
        for href,text in p.links:
            url=urljoin('https://morsereport.com/',href)
            if '/a/news/' not in url or url in seen or len(text)<12:continue
            if re.search(r'^(read more|listen|share|login|subscribe|menu|home)$',text,re.I):continue
            seen.add(url);rows.append((url,text,'',''))
            if len(rows)>=20:break
        return rows
    except Exception:return []

def add_morse_to_db():
    if not DB.exists():return 0
    rows=direct_morse_rows()
    if not rows:return 0
    now=datetime.now(timezone.utc).isoformat(); conn=sqlite3.connect(DB); added=0
    try:
        for url,title,summary,pub in rows:
            published=now
            try:
                from email.utils import parsedate_to_datetime
                if pub:published=parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
            except Exception:pass
            cur=conn.execute('INSERT OR IGNORE INTO articles (url,title,published_date,summary_snippet,source_name,source_type,category,author,username,credit_metadata,fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',(url,title,published,summary,'Morse Report','news-mirror','us-politics','','','{"sourceUrl":"https://morsereport.com/","collector":"direct-public-site"}',now))
            if cur.rowcount:added+=1
        conn.commit()
        rowsdb=conn.execute('SELECT url,title,published_date,summary_snippet,source_name,source_type,category,author,username,credit_metadata FROM articles ORDER BY datetime(published_date) DESC LIMIT 500').fetchall(); arts=[]
        for r in rowsdb:
            try:credit=json.loads(r[9] or '{}')
            except Exception:credit={}
            arts.append({'url':r[0],'title':r[1],'published_date':r[2],'summary_snippet':r[3],'source':r[4],'sourceType':r[5],'category':r[6],'author':r[7],'username':r[8],'credit':credit})
        LIVE.write_text(json.dumps({'updatedAt':now,'retentionDays':7,'count':len(arts),'articles':arts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    finally:conn.close()
    return added

def dedupe_earthquakes():
    if not SNAP.exists():return 0
    d=json.loads(SNAP.read_text(encoding='utf-8')); out=[];seen=set();removed=0
    for m in d.get('markers',[]):
        if m.get('source')=='USGS Earthquakes':
            key=str(m.get('url') or f"{m.get('title','')}|{m.get('lat')}|{m.get('lng')}")
            if key in seen:removed+=1;continue
            seen.add(key)
        out.append(m)
    d['markers']=out;SNAP.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return removed

def install_ui():
    s=INDEX.read_text(encoding='utf-8')
    for asset in ('global_pulse_v22.js','global_pulse_source_health.js','global_pulse_v26.js'):
        ap=Path(asset); digest=hashlib.sha256(ap.read_bytes()).hexdigest()[:12]
        pattern=rf'<script src="{re.escape(asset)}(?:\?[^" ]*)?" defer></script>'
        s=re.sub(pattern,f'<script src="{asset}?v={digest}" defer></script>',s)
    s=re.sub(r'<script src="global_pulse_source_health\.js(?:\?[^" ]*)?" defer></script>','',s)
    s=re.sub(r'<script src="global_pulse_v26\.js(?:\?[^" ]*)?" defer></script>','',s)
    if '</body>' not in s:raise SystemExit('index.html has no </body>')
    d=hashlib.sha256(Path('global_pulse_source_health.js').read_bytes()).hexdigest()[:12]; v=hashlib.sha256(Path('global_pulse_v26.js').read_bytes()).hexdigest()[:12]
    s=s.replace('</body>',f'<script src="global_pulse_source_health.js?v={d}" defer></script><script src="global_pulse_v26.js?v={v}" defer></script></body>',1)
    INDEX.write_text(s,encoding='utf-8')

def main():
    morse=add_morse_to_db(); quake=dedupe_earthquakes(); install_ui()
    print(f'V2.6 repairs: Morse rows added={morse}; duplicate USGS earthquake markers removed={quake}; single conflict dialog and visible V5 trend installed.')

if __name__=='__main__':main()
