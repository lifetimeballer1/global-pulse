#!/usr/bin/env python3
"""Add a public UCDP conflict corroboration layer without API credentials.

The UCDP download center publishes candidate-event CSV releases without an API
key. This updater discovers the current global CSV link from the official page,
then converts recent geocoded events into bounded map corroboration records.
"""
from __future__ import annotations
import csv, io, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';SNAP=DATA/'snapshot.json'
INDEX_URL='https://ucdp.uu.se/downloads/'
UA='GlobalPulse/20.0 (+https://github.com/lifetimeballer1/global-pulse)'

def fetch(url,timeout=45):
    with urlopen(Request(url,headers={'User-Agent':UA}),timeout=timeout) as r:return r.read()

def discover_csv():
    html=fetch(INDEX_URL).decode('utf-8','ignore')
    links=re.findall(r'href=[\'\"]([^\'\"]+\.csv(?:\?[^\'\"]*)?)[\'\"]',html,re.I)
    preferred=[x for x in links if 'candidate' in x.lower() and ('global' in x.lower() or '26.0.7' in x)]
    if not preferred:preferred=[x for x in links if 'candidate' in x.lower()]
    if not preferred:raise RuntimeError('UCDP candidate CSV link not found on download center')
    return urljoin(INDEX_URL,preferred[0])

def rows_from_csv(blob):
    text=blob.decode('utf-8-sig','replace');sample=text[:4096];dialect=csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
    reader=csv.DictReader(io.StringIO(text),dialect=dialect);return list(reader)

def num(row,*keys):
    for k in keys:
        try:return float(str(row.get(k,'')).strip())
        except (TypeError,ValueError):pass
    return None

def main():
    snap=json.loads(SNAP.read_text(encoding='utf-8')) if SNAP.exists() else {};url=discover_csv();rows=rows_from_csv(fetch(url));markers=[];recent=[]
    for row in rows:
        year=str(row.get('year') or row.get('date_start') or '')
        lat=num(row,'latitude','lat');lng=num(row,'longitude','lon','lng')
        if lat is None or lng is None or abs(lat)>90 or abs(lng)>180:continue
        deaths=num(row,'best','deaths_best','fatalities') or 0
        country=row.get('country') or row.get('location') or 'Unknown'
        conflict=row.get('conflict_name') or row.get('conflict') or row.get('side_a') or 'Organized violence event'
        event_id=row.get('id') or row.get('event_id') or ''
        markers.append({'lat':round(lat,5),'lng':round(lng,5),'type':'conflict-dataset','layer':'conflict','importance':2 if deaths>=10 else 1,'title':f'UCDP corroboration — {conflict}','detail':f'Public UCDP candidate event in {country}; fatalities field: {deaths:g}. Dataset event date/year: {year}.','source':'UCDP Candidate Events','sourceUrl':'https://ucdp.uu.se/downloads/','url':'https://ucdp.uu.se/downloads/','eventType':'Conflict Dataset','confidence':'DATASET CORROBORATION','datasetEventId':event_id,'time':row.get('date_start') or year,'timestamp':row.get('date_start') or year});recent.append(row)
        if len(markers)>=2500:break
    snap['conflictDataset']={'provider':'UCDP Candidate Events','version':'26.0.7-or-current-public-release','url':'https://ucdp.uu.se/downloads/','updatedAt':datetime.now(timezone.utc).isoformat(),'rowsRead':len(rows),'mappedEvents':len(markers),'note':'Dataset corroboration is independent of news reporting; absence does not prove an event did not occur.'}
    existing=[m for m in snap.get('markers',[]) if m.get('source')!='UCDP Candidate Events'];snap['markers']=existing+markers;snap['updatedAt']=datetime.now(timezone.utc).isoformat();SNAP.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'UCDP: rows={len(rows)} mapped={len(markers)} source={url}')
if __name__=='__main__':main()
