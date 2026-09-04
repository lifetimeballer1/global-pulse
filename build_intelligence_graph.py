#!/usr/bin/env python3
"""Publish the compact Intelligence Web artifact from the authoritative snapshot."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; SNAP=ROOT/'data'/'snapshot.json'; OUT=ROOT/'data'/'intelligence_graph.json'
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
 payload={'updatedAt':graph.get('updatedAt') or data.get('updatedAt') or '','method':graph.get('method') or 'Evidence-backed public reporting graph','caution':graph.get('caution') or 'A connection means the entities share a public evidence record; it does not independently prove causation, coordination, alliance, or responsibility.','nodes':nodes[:100],'edges':edges[:500]}
 if len(payload['nodes'])<10: raise SystemExit(f'RENDER BLOCKED: graph has only {len(payload["nodes"])} nodes')
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8'); print(f'Published Intelligence Web artifact: {len(payload["nodes"])} nodes / {len(payload["edges"])} evidence-backed edges')
if __name__=='__main__': main()
