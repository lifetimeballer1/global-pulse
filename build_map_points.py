#!/usr/bin/env python3
"""Publish a compact, canonical geographic marker feed for the browser."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; SNAP=DATA/'snapshot.json'; OUT=DATA/'map_points.json'

def num(v):
    try:
        n=float(v); return n if n==n else None
    except (TypeError,ValueError): return None

def coord(item):
    if not isinstance(item,dict): return None
    lat=num(item.get('lat',item.get('latitude',item.get('lat_deg')))); lng=num(item.get('lng',item.get('lon',item.get('longitude',item.get('long')))))
    c=item.get('coordinates')
    if (lat is None or lng is None) and isinstance(c,dict):
        lat=num(c.get('lat',c.get('latitude',lat))); lng=num(c.get('lng',c.get('lon',c.get('longitude',lng))))
    elif (lat is None or lng is None) and isinstance(c,list) and len(c)>=2:
        lng=num(c[0]); lat=num(c[1])
    g=item.get('geometry')
    if (lat is None or lng is None) and isinstance(g,dict) and isinstance(g.get('coordinates'),list) and len(g['coordinates'])>=2:
        lng=num(g['coordinates'][0]); lat=num(g['coordinates'][1])
    if lat is None or lng is None or abs(lat)>90 or abs(lng)>180: return None
    return round(lat,5),round(lng,5)

def flatten(value,out=None,seen=None,depth=0):
    out=[] if out is None else out; seen=set() if seen is None else seen
    if depth>8 or not isinstance(value,(dict,list)): return out
    if isinstance(value,list):
        for x in value: flatten(x,out,seen,depth+1)
        return out
    ident=id(value)
    if ident in seen: return out
    seen.add(ident)
    c=coord(value)
    if c:
        x=dict(value); x['lat'],x['lng']=c; out.append(x)
    for child in value.values():
        if isinstance(child,(dict,list)): flatten(child,out,seen,depth+1)
    return out

def marker_key(m):
    return str(m.get('id') or m.get('eventId') or m.get('mapId') or m.get('datasetEventId') or m.get('sourceUrl') or m.get('url') or f"{m.get('lat')}|{m.get('lng')}|{m.get('title') or m.get('name') or m.get('location') or ''}")

def main():
    snap=json.loads(SNAP.read_text(encoding='utf-8'))
    sources=[snap.get('markers'),(snap.get('osintMaps') or {}).get('regionalPoints'),(snap.get('osintMaps') or {}).get('markers'),(snap.get('conflictDataset') or {}).get('markers'),snap.get('mapPoints'),snap.get('map_points')]
    points=[]
    for src in sources:
        if isinstance(src,list): points.extend(flatten(src))
    if len(points)<10: points=flatten(snap)
    out=[];seen=set()
    for p in points:
        k=marker_key(p)
        if k in seen: continue
        seen.add(k); p.pop('geometry',None); p.pop('coordinates',None); out.append(p)
    if not out: raise RuntimeError('map_points.json contains zero valid geographic markers')
    payload={'version':2,'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'count':len(out),'source':'canonical snapshot geographic intelligence layers','markers':out}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(f'MAP POINTS: {len(out)} valid geographic markers')

if __name__=='__main__': raise SystemExit(main())
