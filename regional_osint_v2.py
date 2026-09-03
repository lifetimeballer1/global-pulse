#!/usr/bin/env python3
"""Fast regional OSINT collector with multi-source failover."""
import json,re,time,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent; SNAP=ROOT/'data'/'snapshot.json'; UA='GlobalPulse/4.0'
REGIONS={'Africa':['SD','SS','CD','NG','SO','ET','KE','MZ','CM','CF','LY','ML','BF','NE','TD','TZ','UG','ZA','AO','SN','GH','GN','SL','CI','ER','DJ','RW','BI','ZW','ZM'],'South America':['BR','CO','VE','EC','PE','BO','PY','UY','AR','CL','GY','SR'],'South Asia':['IN','PK','BD','AF','LK','NP','BT','MV','MM']}
NAMES={'SD':'Sudan','SS':'South Sudan','CD':'DR Congo','NG':'Nigeria','SO':'Somalia','ET':'Ethiopia','KE':'Kenya','MZ':'Mozambique','CM':'Cameroon','CF':'Central African Republic','LY':'Libya','ML':'Mali','BF':'Burkina Faso','NE':'Niger','TD':'Chad','TZ':'Tanzania','UG':'Uganda','ZA':'South Africa','AO':'Angola','SN':'Senegal','GH':'Ghana','GN':'Guinea','SL':'Sierra Leone','CI':"Cote d'Ivoire",'ER':'Eritrea','DJ':'Djibouti','RW':'Rwanda','BI':'Burundi','ZW':'Zimbabwe','ZM':'Zambia','BR':'Brazil','CO':'Colombia','VE':'Venezuela','EC':'Ecuador','PE':'Peru','BO':'Bolivia','PY':'Paraguay','UY':'Uruguay','AR':'Argentina','CL':'Chile','GY':'Guyana','SR':'Suriname','IN':'India','PK':'Pakistan','BD':'Bangladesh','AF':'Afghanistan','LK':'Sri Lanka','NP':'Nepal','BT':'Bhutan','MV':'Maldives','MM':'Myanmar'}
CENTERS={'SD':(15.5,32.56),'SS':(4.85,31.58),'CD':(-2.88,23.66),'NG':(9.08,7.4),'SO':(5.15,46.2),'ET':(9.15,40.49),'KE':(.02,37.91),'MZ':(-18.67,35.53),'CM':(5.96,10.15),'CF':(6.61,20.94),'LY':(26.34,17.23),'ML':(17.57,-4),'BF':(12.24,-1.56),'NE':(17.61,8.08),'TD':(15.45,18.73),'TZ':(-6.37,34.89),'UG':(1.37,32.29),'ZA':(-30.56,22.94),'AO':(-11.2,17.87),'SN':(14.5,-14.45),'GH':(7.95,-1.02),'GN':(9.95,-9.7),'SL':(8.46,-11.78),'CI':(7.54,-5.55),'ER':(15.18,39.78),'DJ':(11.83,42.59),'RW':(-1.94,29.87),'BI':(-3.37,29.92),'ZW':(-19.02,29.15),'ZM':(-13.13,27.85),'BR':(-14.24,-51.93),'CO':(4.57,-74.3),'VE':(6.42,-66.59),'EC':(-1.83,-78.18),'PE':(-9.19,-75.02),'BO':(-16.29,-63.59),'PY':(-23.44,-58.44),'UY':(-32.52,-55.77),'AR':(-38.42,-63.62),'CL':(-35.68,-71.54),'GY':(4.86,-58.93),'SR':(3.92,-56.03),'IN':(22.35,78.67),'PK':(30.38,69.35),'BD':(23.68,90.36),'AF':(33.94,67.71),'LK':(7.87,80.77),'NP':(28.39,84.12),'BT':(27.51,90.43),'MV':(3.2,73.22),'MM':(21.92,95.96)}

def fetch(url,timeout=8):
 r=urllib.request.Request(url,headers={'User-Agent':UA});
 with urllib.request.urlopen(r,timeout=timeout) as x:return x.read()
def gdelt(region,cc):
 q=urllib.parse.quote(f'locationcc:{cc} (conflict OR attack OR fighting OR bombing OR shooting OR insurgent OR militant OR violence OR clash OR kidnapping OR military OR protest)',safe='')
 try:
  obj=json.loads(fetch(f'https://api.gdeltproject.org/api/v2/geo/geo?query={q}&mode=PointData&format=GeoJSON&timespan=24h&maxrecords=80').decode('utf-8','replace')); out=[]
  for f in obj.get('features',[]):
   c=(f.get('geometry') or {}).get('coordinates') or []
   if len(c)<2:continue
   lng,lat=float(c[0]),float(c[1]); p=f.get('properties') or {}; u=str(p.get('url') or p.get('sourceurl') or '').strip()
   if -90<=lat<=90 and -180<=lng<=180:out.append({'id':f'gdelt-{cc}-{lat:.4f}-{lng:.4f}-{abs(hash(u))}','lat':lat,'lng':lng,'title':str(p.get('name') or NAMES[cc])[:180],'detail':'Fresh GDELT GEO signal','url':u,'sourceUrl':u,'source':'GDELT GEO','sourceDomain':(urlparse(u).hostname or '').lower().removeprefix('www.'),'eventType':'OSINT/GEO','layer':'osint-regional','region':region,'country':NAMES[cc],'countryCode':cc,'confidence':'DISCOVERY SIGNAL','observedAt':p.get('seendate') or datetime.now(timezone.utc).isoformat()})
  return out,None
 except Exception as e:return [],str(e)
def rss(region,cc):
 name=NAMES[cc]; q=urllib.parse.quote(f'{name} conflict OR fighting OR attack OR military when:1d')
 try:
  root=ET.fromstring(fetch(f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'));out=[];lat,lng=CENTERS[cc]
  for it in root.findall('./channel/item')[:8]:
   title=(it.findtext('title') or '').strip();u=(it.findtext('link') or '').strip()
   if u:out.append({'id':f'rss-{cc}-{abs(hash(u))}','lat':lat,'lng':lng,'title':title,'detail':'Current regional report; location is approximate country center','url':u,'sourceUrl':u,'source':'Google News RSS','layer':'osint-regional','type':'reported-area','eventType':'REPORTED AREA','region':region,'country':name,'countryCode':cc,'confidence':'OSINT REPORT','observedAt':it.findtext('pubDate') or datetime.now(timezone.utc).isoformat()})
  return out,None
 except Exception as e:return [],str(e)
def main():
 snap=json.loads(SNAP.read_text(encoding='utf-8'));base=[m for m in snap.get('markers',[]) if m.get('layer')!='osint-regional'];points=[];fails=[];counts={r:0 for r in REGIONS}
 jobs={}
 with ThreadPoolExecutor(max_workers=20) as ex:
  for r,codes in REGIONS.items():
   for cc in codes:jobs[(r,cc)]=ex.submit(gdelt,r,cc)
  for (r,cc),f in jobs.items():
   pts,e=f.result()
   if pts:points+=pts;counts[r]+=len(pts)
   else:fails.append((r,cc,e or 'no results'))
  fb={(r,cc):ex.submit(rss,r,cc) for r,cc,_ in fails}
  remaining=[]
  for (r,cc),f in fb.items():
   pts,e=f.result()
   if pts:points+=pts;counts[r]+=len(pts)
   else:remaining.append({'region':r,'country':NAMES[cc],'error':str(e or 'no results')[:180]})
 seen=set();clean=[]
 for p in points:
  k=(round(p['lat'],3),round(p['lng'],3),p.get('url') or p.get('title'))
  if k not in seen:seen.add(k);clean.append(p)
 snap['markers']=base+clean[:2000];o=snap.setdefault('osintMaps',{});o['version']=3;o['regionalPoints']=clean;o['regionalCounts']=counts;o['regionalFailures']=remaining;o['regionalUpdatedAt']=datetime.now(timezone.utc).isoformat();o['regionalSourcePolicy']='GDELT GEO -> Google News RSS; fallback country-center points are approximate and labeled.'
 SNAP.write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf-8');print(f'Regional OSINT: {len(clean)} points; failures after fallback={len(remaining)}; counts={counts}')
 if not clean:raise SystemExit('No fresh regional OSINT points from GDELT or Google News RSS')
if __name__=='__main__':main()
