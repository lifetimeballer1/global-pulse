#!/usr/bin/env python3
"""Publish the compact Intelligence Web artifact from the authoritative snapshot."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; SNAP=ROOT/'data'/'snapshot.json'; OUT=ROOT/'data'/'intelligence_graph.json'

def _recency_score(node):
    dates=[e.get('time') for e in (node.get('evidence') or []) if isinstance(e,dict) and e.get('time')]
    raw=node.get('updatedAt') or node.get('time') or (max(dates) if dates else '')
    if not raw: return 0
    try:
        dt=datetime.fromisoformat(str(raw).replace('Z','+00:00'))
        age=max(0,(datetime.now(timezone.utc)-dt).total_seconds()/86400)
        return 30 if age<=1 else 20 if age<=3 else 10 if age<=7 else 0
    except Exception: return 0

def node_rank(n):
    evidence=n.get('evidence') or []
    text=' '.join(str(x.get(k,'')).lower() for x in evidence if isinstance(x,dict) for k in ('title','source'))
    breaking=12 if any(k in text for k in ('breaking','urgent','attack','strike','invasion','ceasefire','sanction')) else 0
    return (int(n.get('mentions') or 0)*2 + math.log1p(len(evidence))*8 + _recency_score(n) + breaking)

def main():
 data=json.loads(SNAP.read_text(encoding='utf-8')); graph=data.get('intelligenceGraph') or {}
 raw_nodes=[n for n in graph.get('nodes',[]) if isinstance(n,dict) and n.get('id')]
 nodes=[{'id':str(n.get('id')),'label':str(n.get('label') or n.get('name') or n.get('id')),'kind':str(n.get('kind') or 'actor'),'mentions':int(n.get('mentions') or 0),'evidence':[e for e in (n.get('evidence') or [])[:12] if isinstance(e,dict)]} for n in raw_nodes]
 valid={n['id'] for n in nodes}; label_to_id={n['label'].strip().lower():n['id'] for n in nodes}; id_to_id={str(n['id']):str(n['id']) for n in nodes}
 def resolve(value):
  v=str(value or '').strip()
  return id_to_id.get(v) or label_to_id.get(v.lower()) or label_to_id.get(v.replace('_',' ').lower())
 edges=[]
 for e in graph.get('edges',[]):
  if not isinstance(e,dict): continue
  s=resolve(e.get('source') or e.get('sid')); t=resolve(e.get('target') or e.get('tid')); ev=[x for x in (e.get('evidence') or [])[:12] if isinstance(x,dict) and (x.get('title') or x.get('url') or x.get('link'))]
  if s in valid and t in valid and s!=t and ev:
   edges.append({'source':s,'target':t,'weight':max(1,int(e.get('weight') or 1)),'types':list(e.get('types') or []),'relationship':str(e.get('relationship') or 'Both entities are referenced in the same public evidence record.'),'evidence':ev,'evidenceCount':len(ev)})
 node_by_id={n['id']:n for n in nodes}
 degree={n['id']:0 for n in nodes}
 for e in edges:
  degree[e['source']]+=1; degree[e['target']]+=1
 for n in nodes:
  n['importance']=round(node_rank(n)+degree[n['id']]*5,3)
  n['_degree']=degree[n['id']]
 nodes.sort(key=lambda n:(n['importance'],n['mentions'],n['label']),reverse=True)
 edges.sort(key=lambda e:(e['weight'],e['evidenceCount']),reverse=True)
 payload={'updatedAt':graph.get('updatedAt') or data.get('updatedAt') or '','method':graph.get('method') or 'Evidence-backed public reporting graph','caution':graph.get('caution') or 'A connection means the entities share a public evidence record; it does not independently prove causation, coordination, alliance, or responsibility.','nodes':nodes[:100],'edges':edges[:500]}
 for n in payload['nodes']: n.pop('_degree',None)
 if len(payload['nodes'])<10: raise SystemExit(f'RENDER BLOCKED: graph has only {len(payload["nodes"])} nodes')
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8'); print(f'Published Intelligence Web artifact: {len(payload["nodes"])} ranked nodes / {len(payload["edges"])} evidence-backed edges')
if __name__=='__main__': main()
