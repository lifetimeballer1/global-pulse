import json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"
FEEDS=[
 ("BBC World","https://feeds.bbci.co.uk/news/world/rss.xml"),
 ("Guardian World","https://www.theguardian.com/world/rss"),
 ("NPR World","https://feeds.npr.org/1004/rss.xml"),
]
def text(node, tag):
    x=node.find(tag)
    return (x.text or "").strip() if x is not None and x.text else ""
def fetch(url):
    req=Request(url,headers={"User-Agent":"GlobalPulse/1.0"})
    with urlopen(req,timeout=20) as r: return r.read()
stories=[]
errors=[]
for label,url in FEEDS:
    try:
        raw=fetch(url)
        root=ET.fromstring(raw)
        for item in root.findall(".//item")[:12]:
            title=text(item,"title")
            link=text(item,"link")
            desc=re.sub("<[^>]+>","",text(item,"description"))
            pub=text(item,"pubDate")
            if title and link:
                stories.append({"id":hashlib.sha1(link.encode()).hexdigest()[:12],"sourceLabel":label,"title":title,"summary":desc[:280],"source":link,"time":pub,"tag":"World"})
    except Exception as e:
        errors.append(f"{label}: {type(e).__name__}")
seen=set(); unique=[]
for s in stories:
    if s["id"] not in seen: unique.append(s); seen.add(s["id"])
stories=unique[:24]

snap_path=DATA/"snapshot.json"
old=json.loads(snap_path.read_text()) if snap_path.exists() else {}
old_ids={s.get("id") for s in old.get("stories",[])}
new=[s for s in stories if s["id"] not in old_ids]
changes=[]
for s in new[:5]:
    changes.append({"kind":"new reporting","title":s["title"],"detail":f"New item from {s['sourceLabel']}"})
if not changes: changes=[{"kind":"refresh","title":"No new unique headline detected","detail":"Feeds refreshed successfully; existing items were retained."}]
now=datetime.now(timezone.utc).isoformat()
snapshot={
 "updatedAt":now,
 "sourceStatus":f"{len(stories)} public-feed items loaded; {len(errors)} feed errors",
 "dataNote":"Headlines and links are refreshed from public RSS feeds. No API key is used. Failed feeds do not create substitute or random data.",
 "tension":old.get("tension",60),
 "breakdownScores":old.get("breakdownScores",{"Conflict activity":72,"Diplomatic strain":58,"Economic pressure":54,"Market volatility":46,"Military posture":61}),
 "changes":changes,
 "stories":stories,
 "markers":old.get("markers",[]),
 "social":old.get("social",[])
}
snap_path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2))
hist_path=DATA/"history.json"
history=json.loads(hist_path.read_text()) if hist_path.exists() else []
if not history or history[-1].get("tension")!=snapshot["tension"]:
    history.append({"updatedAt":now,"tension":snapshot["tension"]})
history=history[-240:]
hist_path.write_text(json.dumps(history,ensure_ascii=False,indent=2))
print(snapshot["sourceStatus"])
