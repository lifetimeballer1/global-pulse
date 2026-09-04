#!/usr/bin/env python3
"""Link geospatial markers to likely live-event clusters without inventing locations."""
from __future__ import annotations
import json,re
from pathlib import Path
DATA=Path(__file__).resolve().parent/'data'
STOP=set('the a an and or of to in on for from with by as at is are was were has have had this that report reports reported says said after before over into near amid during its their his her'.split())

def tokens(s):return {x for x in re.findall(r'[a-z0-9]{4,}',str(s or '').lower()) if x not in STOP}
def score(a,b):
 aa=tokens(a);bb=tokens(b)
 return len(aa&bb)/max(1,len(aa|bb))

def main():
 snap=json.loads((DATA/'snapshot.json').read_text(encoding='utf-8'));events=json.loads((DATA/'live_events.json').read_text(encoding='utf-8'))
 es=[e for e in events.get('events',[]) if isinstance(e,dict)];linked=0;review=0
 for m in snap.get('markers',[]):
  if not isinstance(m,dict):continue
  text=' '.join(str(m.get(k) or '') for k in ('title','detail','description','conflictName'))
  best=None;best_score=0
  for e in es:
   s=score(text,e.get('title'))
   if s>best_score:best,best_score=e,s
  if best and best_score>=.32:
   m['eventId']=best.get('id');m['eventTitle']=best.get('title');m['eventLinkConfidence']='candidate' if best_score<.5 else 'strong-candidate';m['eventMatchScore']=round(best_score,3);linked+=1
   if best_score<.5:review+=1
  else:
   for k in ('eventId','eventTitle','eventLinkConfidence','eventMatchScore'):m.pop(k,None)
 snap['mapEventLinking']={'linkedMarkers':linked,'reviewCandidates':review,'method':'token-overlap candidate linking between marker text and live-event titles; no coordinates are moved or invented.'}
 (DATA/'snapshot.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('MAP EVENT LINKS:',linked,'linked /',review,'review candidates')
if __name__=='__main__':main()
