#!/usr/bin/env python3
"""Build a resilient, evidence-first relationship web from the public snapshot."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; SNAP=ROOT/'data'/'snapshot.json'
# Entity catalog is kept in the existing production source.
ENTITIES={
"United States":("actor",["united states","u.s.","u.s","us government","washington","white house","trump"]),"U.S. Politics":("political",["u.s. politics","congress","senate","white house","supreme court","election"]),"China":("actor",["china","chinese","beijing","pla"]),"Russia":("actor",["russia","russian","moscow","kremlin","putin"]),"Ukraine":("actor",["ukraine","ukrainian","kyiv","zelensky"]),"Iran":("actor",["iran","iranian","tehran"]),"Israel":("actor",["israel","israeli","tel aviv","jerusalem"]),"Palestinians":("actor",["palestinian","gaza","west bank","hamas"]),"Saudi Arabia":("actor",["saudi arabia","saudi","riyadh"]),"Turkey":("actor",["turkey","turkish","ankara","erdogan"]),"India":("actor",["india","indian","new delhi"]),"Pakistan":("actor",["pakistan","pakistani","islamabad"]),"Taiwan":("actor",["taiwan","taiwanese","taipei"]),"North Korea":("actor",["north korea","dprk","pyongyang"]),"South Korea":("actor",["south korea","seoul"]),"Japan":("actor",["japan","japanese","tokyo"]),"European Union":("political",["european union","eu","brussels"]),"United Kingdom":("actor",["united kingdom","britain","british","london"]),"NATO":("political",["nato","north atlantic treaty organization"]),"Mexico":("actor",["mexico","mexican","mexico city"]),"Canada":("actor",["canada","canadian","ottawa"]),"Brazil":("actor",["brazil","brazilian","brasilia"]),"Venezuela":("actor",["venezuela","venezuelan","caracas"]),"Colombia":("actor",["colombia","colombian","bogota"]),"Haiti":("actor",["haiti","haitian","port-au-prince"]),"Sudan":("actor",["sudan","sudanese","khartoum","darfur"]),"Democratic Republic of Congo":("actor",["democratic republic of congo","drc","eastern congo","goma","m23"]),"Somalia":("actor",["somalia","somali","mogadishu","al-shabaab"]),"Nigeria":("actor",["nigeria","nigerian","abuja","boko haram"]),"Sahel":("actor",["sahel","mali","burkina faso","niger","jnim"]),"Yemen":("actor",["yemen","yemeni","houthi","red sea"]),"Syria":("actor",["syria","syrian","damascus"]),"Iraq":("actor",["iraq","iraqi","baghdad"]),"Lebanon":("actor",["lebanon","lebanese","beirut","hezbollah"]),"Egypt":("actor",["egypt","egyptian","cairo"]),"Ethiopia":("actor",["ethiopia","ethiopian","tigray","amhara","addis ababa"]),"South Sudan":("actor",["south sudan","south sudanese","juba"]),"Libya":("actor",["libya","libyan","tripoli","benghazi"]),"Cameroon":("actor",["cameroon","cameroonian","yaounde","far north cameroon"]),"Mozambique":("actor",["mozambique","mozambican","cabo delgado","palma"]),"Central African Republic":("actor",["central african republic","car","bangui"]),"Kenya":("actor",["kenya","kenyan","nairobi","mombasa"]),"Mali":("actor",["mali","malian","bamako"]),"Burkina Faso":("actor",["burkina faso","burkinabe","ouagadougou"]),"Niger":("actor",["niger","niamey"]),"Chad":("actor",["chad","chadian","ndjamena"]),"Sinaloa Cartel":("military",["sinaloa cartel","cartel de sinaloa","sinaloa"]),"CJNG":("military",["cjng","jalisco new generation cartel","cartel jalisco nueva generacion"]),"Mexican Cartel Conflict":("military",["cartel war","cartel conflict","drug cartel","drug war","organized crime","narco","cartels"]),"Strait of Hormuz":("strategic",["strait of hormuz","hormuz","persian gulf"]),"Oil Markets":("economic",["oil","crude","brent","wti","opec","oil prices"]),"Global Trade":("economic",["tariff","trade","shipping","freight","export","import","supply chain"]),"Global Economy":("economic",["inflation","interest rate","central bank","recession","economy","gdp","markets"])}
def norm(v):return re.sub(r"\s+"," ",str(v or "").lower()).strip()
def has_alias(blob,a):return re.search(r"(?<![a-z0-9])"+re.escape(a)+r"(?![a-z0-9])",blob)!=None
def record_text(r):
    keys=("title","summary","description","content","text","name","region","country","location","category","type","tags","keywords");parts=[]
    for k in keys:
        v=r.get(k,"") if isinstance(r,dict) else "";parts.append(" ".join(map(str,v)) if isinstance(v,list) else str(v or ""))
    return norm(" ".join(parts))
def slug(n):return re.sub(r"[^a-z0-9]+","-",n.lower()).strip("-")
def evidence_from(r):
    if not isinstance(r,dict):return None
    title=str(r.get("title") or r.get("name") or "Public intelligence record").strip()
    # Preserve every known source-link field. original_link is the canonical article URL used by the live reporter.
    url=str(r.get("original_link") or r.get("url") or r.get("sourceUrl") or r.get("source_url") or r.get("link") or ((r.get("credit") or {}).get("source_url") if isinstance(r.get("credit"),dict) else "") or "").strip()
    source=str(r.get("sourceLabel") or r.get("source") or r.get("publisher") or "Public source").strip()
    time=str(r.get("time") or r.get("publishedAt") or r.get("published_date") or r.get("updatedAt") or "").strip()
    summary=str(r.get("summary") or r.get("description") or r.get("summary_snippet") or "").strip()
    if not title and not url and source=="Public source":return None
    return {"title":title or "Public intelligence record","url":url,"source":source or "Public source","time":time,"summary":summary[:420]}
def main():
    data=json.loads(SNAP.read_text(encoding="utf-8"));nodes={};edges={}
    def add_node(name,kind,mentions=1):
        n=nodes.setdefault(name,{"id":slug(name),"label":name,"kind":kind,"mentions":0,"evidence":[]});n["mentions"]+=max(0,int(mentions));return n
    def add_edge(a,b,ev,source_type):
        if not a or not b or a==b or not ev:return
        key="|".join(sorted((a,b)));e=edges.setdefault(key,{"source":a,"target":b,"weight":0,"types":set(),"evidence":[],"relationship":""});e["weight"]+=1;e["types"].add(source_type);e["relationship"]={"conflict":"Both entities are referenced in the same conflict record.","graph":"Relationship retained from an evidence-backed graph record."}.get(source_type,"Both entities are referenced in the same public reporting record.")
        if ev.get("title") and not any(x.get("title")==ev["title"] for x in e["evidence"]) and len(e["evidence"])<8:e["evidence"].append(ev)
    stories=data.get("stories",[]) if isinstance(data.get("stories",[]),list) else [];conflicts=data.get("conflicts",[]) if isinstance(data.get("conflicts",[]),list) else []
    for n,(k,_) in ENTITIES.items():add_node(n,k,0)
    for record,stype in [(x,"story") for x in stories[:1200]]+[(x,"conflict") for x in conflicts]:
        blob=record_text(record);found=[];ev=evidence_from(record)
        for n,(k,aliases) in ENTITIES.items():
            if any(has_alias(blob,a) for a in aliases):
                node=add_node(n,k);found.append(n)
                if ev and len(node["evidence"])<8 and not any(x.get("title")==ev["title"] for x in node["evidence"]):node["evidence"].append(ev)
        if ev:
            for i,a in enumerate(found):
                for b in found[i+1:]:add_edge(a,b,ev,stype)
    old=data.get("intelligenceGraph",{}) if isinstance(data.get("intelligenceGraph"),dict) else {};old_nodes={str(n.get("id")):n for n in old.get("nodes",[]) if isinstance(n,dict)};by_id={n["id"]:n for n in nodes.values()}
    for n in nodes.values():
        o=old_nodes.get(n["id"])
        if o:n["mentions"]=max(n["mentions"],int(o.get("mentions") or 0))
    for olde in old.get("edges",[]) if isinstance(old.get("edges",[]),list) else []:
        if not isinstance(olde,dict):continue
        s,t=str(olde.get("source","")),str(olde.get("target",""));evs=olde.get("evidence") if isinstance(olde.get("evidence"),list) else []
        if s in by_id and t in by_id:
            a,b=by_id[s]["label"],by_id[t]["label"]
            for ev in evs[:8]:
                if isinstance(ev,dict) and (ev.get("title") or ev.get("url") or ev.get("original_link")):
                    if not ev.get("url") and ev.get("original_link"):ev={**ev,"url":ev.get("original_link")}
                    add_edge(a,b,ev,"graph")
    el=[]
    for e in edges.values():
        e["types"]=sorted(e["types"]);e["evidence"].sort(key=lambda x:x.get("time",""),reverse=True);e["evidenceCount"]=len(e["evidence"])
        if e["evidenceCount"]:el.append(e)
    el.sort(key=lambda e:(e["evidenceCount"],e["weight"]),reverse=True);el=el[:500];degree={n:0 for n in nodes}
    for e in el:degree[e["source"]]=degree.get(e["source"],0)+e["weight"];degree[e["target"]]=degree.get(e["target"],0)+e["weight"]
    nl=sorted(nodes.values(),key=lambda n:(degree.get(n["label"],0),n["mentions"],n["label"]),reverse=True)[:100]
    data["intelligenceGraph"]={"updatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"method":"evidence-backed co-occurrence graph from current public stories and conflict records","caution":"A connection means the entities share a public evidence record; it does not independently prove causation, coordination, alliance, or responsibility.","nodes":nl,"edges":el}
    SNAP.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(f"Intelligence graph: {len(nl)} nodes / {len(el)} evidence-backed edges")
if __name__=="__main__":main()
