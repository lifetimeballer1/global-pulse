#!/usr/bin/env python3
"""Publish the compact Intelligence Web artifact from the authoritative snapshot."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; SNAP=ROOT/'data'/'snapshot.json'; OUT=ROOT/'data'/'intelligence_graph.json'
def main():
 data=json.loads(SNAP.read_text(encoding='utf-8')); graph=data.get('intelligenceGraph') or {}
 nodes=[{'id':str(n.get('id')),'label':str(n.get('label') or n.get('name') or n.get('id')),'kind':str(n.get('kind') or 'actor'),'mentions':int(n.get('mentions') or 0),'evidence':[e for e in (n.get('evidence') or [])[:8] if isinstance(e,dict)]} for n in graph.get('nodes',[]) if isinstance(n,dict) and n.get('id')]
 valid={n['id'] for n in nodes}; edges=[]
 for e in graph.get('edges',[]):
  if not isinstance(e,dict): continue
  s,t=str(e.get('source') or e.get('sid') or ''),str(e.get('target') or e.get('tid') or ''); ev=[x for x in (e.get('evidence') or [])[:8] if isinstance(x,dict)]
  if s in valid and t in valid and s!=t and ev: edges.append({'source':s,'target':t,'weight':max(1,int(e.get('weight') or 1)),'types':list(e.get('types') or []),'relationship':str(e.get('relationship') or 'Both entities are referenced in the same public evidence record.'),'evidence':ev,'evidenceCount':len(ev)})
 payload={'updatedAt':graph.get('updatedAt') or data.get('updatedAt') or '','method':graph.get('method') or 'Evidence-backed public reporting graph','caution':graph.get('caution') or 'A connection means the entities share a public evidence record; it does not independently prove causation, coordination, alliance, or responsibility.','nodes':nodes[:100],'edges':edges[:500]}
 if len(payload['nodes'])<10 or len(payload['edges'])<10: raise SystemExit(f'RENDER BLOCKED: graph has only {len(payload["nodes"])} nodes / {len(payload["edges"])} evidence-backed edges')
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8'); print(f'Published Intelligence Web artifact: {len(nodes)} nodes / {len(edges)} evidence-backed edges')
if __name__=='__main__': main()
