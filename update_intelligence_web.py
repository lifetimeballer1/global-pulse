#!/usr/bin/env python3
"""Build a resilient, evidence-first relationship web from the public snapshot.

Every rendered relationship must carry a reason and public evidence record. Seeded
entities may remain visible without links. The entity catalog intentionally covers
major-power issues plus smaller conflicts and transnational security problems so
important regional activity is not hidden behind the headline conflicts.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SNAP=ROOT/'data'/'snapshot.json'

ENTITIES={
"United States":("actor",["united states","u.s.","u.s","us government","washington","white house","trump"]),
"U.S. Politics":("political",["u.s. politics","congress","senate","white house","supreme court","election"]),
"China":("actor",["china","chinese","beijing","pla"]),"Russia":("actor",["russia","russian","moscow","kremlin","putin"]),
"Ukraine":("actor",["ukraine","ukrainian","kyiv","zelensky"]),"Iran":("actor",["iran","iranian","tehran"]),
"Israel":("actor",["israel","israeli","tel aviv","jerusalem"]),"Palestinians":("actor",["palestinian","gaza","west bank","hamas"]),
"Saudi Arabia":("actor",["saudi arabia","saudi","riyadh"]),"Turkey":("actor",["turkey","turkish","ankara","erdogan"]),
"India":("actor",["india","indian","new delhi"]),"Pakistan":("actor",["pakistan","pakistani","islamabad"]),
"Taiwan":("actor",["taiwan","taiwanese","taipei"]),"North Korea":("actor",["north korea","dprk","pyongyang"]),
"South Korea":("actor",["south korea","seoul"]),"Japan":("actor",["japan","japanese","tokyo"]),
"European Union":("political",["european union","eu","brussels"]),"United Kingdom":("actor",["united kingdom","britain","british","london"]),
"NATO":("political",["nato","north atlantic treaty organization"]),"Mexico":("actor",["mexico","mexican","mexico city"]),
"Canada":("actor",["canada","canadian","ottawa"]),"Brazil":("actor",["brazil","brazilian","brasilia"]),
"Venezuela":("actor",["venezuela","venezuelan","caracas"]),"Colombia":("actor",["colombia","colombian","bogota"]),
"Haiti":("actor",["haiti","haitian","port-au-prince"]),"Sudan":("actor",["sudan","sudanese","khartoum","darfur"]),
"Democratic Republic of Congo":("actor",["democratic republic of congo","drc","eastern congo","goma","m23"]),
"Somalia":("actor",["somalia","somali","mogadishu","al-shabaab"]),"Nigeria":("actor",["nigeria","nigerian","abuja","boko haram"]),
"Sahel":("actor",["sahel","mali","burkina faso","niger","jnim"]),"Yemen":("actor",["yemen","yemeni","houthi","red sea"]),
"Syria":("actor",["syria","syrian","damascus"]),"Iraq":("actor",["iraq","iraqi","baghdad"]),
"Lebanon":("actor",["lebanon","lebanese","beirut","hezbollah"]),"Egypt":("actor",["egypt","egyptian","cairo"]),
"Ethiopia":("actor",["ethiopia","ethiopian","tigray","amhara","addis ababa"]),
"South Sudan":("actor",["south sudan","south sudanese","juba"]),"Libya":("actor",["libya","libyan","tripoli","benghazi"]),
"Cameroon":("actor",["cameroon","cameroonian","yaounde","far north cameroon"]),
"Mozambique":("actor",["mozambique","mozambican","cabo delgado","palma"]),
"Central African Republic":("actor",["central african republic","car","bangui"]),
"Kenya":("actor",["kenya","kenyan","nairobi","mombasa"]),
"Mali":("actor",["mali","malian","bamako"]),"Burkina Faso":("actor",["burkina faso","burkinabe","ouagadougou"]),
"Niger":("actor",["niger","niamey"]),"Chad":("actor",["chad","chadian","ndjamena"]),
"Sinaloa Cartel":("military",["sinaloa cartel","cartel de sinaloa","sinaloa"]),
"CJNG":("military",["cjng","jalisco new generation cartel","cartel jalisco nueva generacion"]),
"Mexican Cartel Conflict":("military",["cartel war","cartel conflict","drug cartel","drug war","organized crime","narco","cartels"]),
"Strait of Hormuz":("strategic",["strait of hormuz","hormuz","persian gulf"]),
"Oil Markets":("economic",["oil","crude","brent","wti","opec","oil prices"]),
"Global Trade":("economic",["tariff","trade","shipping","freight","export","import","supply chain"]),
"Global Economy":("economic",["inflation","interest rate","central bank","recession","economy","gdp","markets"]),
}

def norm(value): return re.sub(r"\s+"," ",str(value or "").lower()).strip()
def has_alias(blob,alias): return re.search(r"(?<![a-z0-9])"+re.escape(alias)+r"(?![a-z0-9])",blob) is not None
def record_text(record):
    keys=("title","summary","description","content","text","name","region","country","location","category","type","tags","keywords")
    parts=[]
    for key in keys:
        value=record.get(key,"") if isinstance(record,dict) else ""
        parts.append(" ".join(map(str,value)) if isinstance(value,list) else str(value or ""))
    return norm(" ".join(parts))
def slug(name): return re.sub(r"[^a-z0-9]+","-",name.lower()).strip("-")
def evidence_from(record):
    if not isinstance(record,dict): return None
    title=str(record.get("title") or record.get("name") or "Public intelligence record").strip()
    url=str(record.get("url") or record.get("sourceUrl") or record.get("link") or "").strip()
    source=str(record.get("sourceLabel") or record.get("source") or record.get("publisher") or "Public source").strip()
    time=str(record.get("time") or record.get("publishedAt") or record.get("published_date") or record.get("updatedAt") or "").strip()
    summary=str(record.get("summary") or record.get("description") or record.get("summary_snippet") or "").strip()
    if not title and not url and source=="Public source": return None
    return {"title":title or "Public intelligence record","url":url,"source":source or "Public source","time":time,"summary":summary[:420]}

def main():
    data=json.loads(SNAP.read_text(encoding="utf-8"));nodes={};edges={}
    def add_node(name,kind,mentions=1):
        node=nodes.setdefault(name,{"id":slug(name),"label":name,"kind":kind,"mentions":0,"evidence":[]});node["mentions"]+=max(0,int(mentions));return node
    def add_edge(a,b,evidence,source_type):
        if not a or not b or a==b or not evidence:return
        key="|".join(sorted((a,b)));edge=edges.setdefault(key,{"source":a,"target":b,"weight":0,"types":set(),"evidence":[],"relationship":""});edge["weight"]+=1;edge["types"].add(source_type)
        edge["relationship"]={"conflict":"Both entities are referenced in the same conflict record.","graph":"Relationship retained from an evidence-backed graph record."}.get(source_type,"Both entities are referenced in the same public reporting record.")
        title=evidence.get("title","")
        if title and not any(x.get("title")==title for x in edge["evidence"]) and len(edge["evidence"])<8:edge["evidence"].append(evidence)
    stories=data.get("stories",[]) if isinstance(data.get("stories",[]),list) else []
    conflicts=data.get("conflicts",[]) if isinstance(data.get("conflicts",[]),list) else []
    for name,(kind,_) in ENTITIES.items():add_node(name,kind,0)
    for record,source_type in [(x,"story") for x in stories[:1200]]+[(x,"conflict") for x in conflicts]:
        blob=record_text(record);found=[];ev=evidence_from(record)
        for name,(kind,aliases) in ENTITIES.items():
            if any(has_alias(blob,alias) for alias in aliases):
                node=add_node(name,kind);found.append(name)
                if ev and len(node["evidence"])<8 and not any(x.get("title")==ev["title"] for x in node["evidence"]):node["evidence"].append(ev)
        if ev:
            for i,a in enumerate(found):
                for b in found[i+1:]:add_edge(a,b,ev,source_type)
    old_graph=data.get("intelligenceGraph",{}) if isinstance(data.get("intelligenceGraph",{}),dict) else {}
    old_nodes={str(n.get("id")):n for n in old_graph.get("nodes",[]) if isinstance(n,dict)};by_id={n["id"]:n for n in nodes.values()}
    for node in nodes.values():
        old=old_nodes.get(node["id"])
        if old:node["mentions"]=max(node["mentions"],int(old.get("mentions") or 0))
    for old in old_graph.get("edges",[]) if isinstance(old_graph.get("edges",[]),list) else []:
        if not isinstance(old,dict):continue
        source,target=str(old.get("source","")),str(old.get("target",""));evs=old.get("evidence") if isinstance(old.get("evidence"),list) else []
        if source in by_id and target in by_id:
            a,b=by_id[source]["label"],by_id[target]["label"]
            for ev in evs[:8]:
                if isinstance(ev,dict) and (ev.get("title") or ev.get("url")):add_edge(a,b,ev,"graph")
    edge_list=[]
    for edge in edges.values():
        edge["types"]=sorted(edge["types"]);edge["evidence"].sort(key=lambda x:x.get("time",""),reverse=True);edge["evidenceCount"]=len(edge["evidence"])
        if edge["evidenceCount"]:edge_list.append(edge)
    edge_list.sort(key=lambda e:(e["evidenceCount"],e["weight"]),reverse=True);edge_list=edge_list[:500]
    degree={name:0 for name in nodes}
    for edge in edge_list:
        degree[edge["source"]]=degree.get(edge["source"],0)+edge["weight"];degree[edge["target"]]=degree.get(edge["target"],0)+edge["weight"]
    node_list=sorted(nodes.values(),key=lambda n:(degree.get(n["label"],0),n["mentions"],n["label"]),reverse=True)[:100]
    data["intelligenceGraph"]={"updatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"method":"evidence-backed co-occurrence graph from current public stories and conflict records","caution":"A connection means the entities share a public evidence record; it does not independently prove causation, coordination, alliance, or responsibility.","nodes":node_list,"edges":edge_list}
    SNAP.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Intelligence graph: {len(node_list)} nodes / {len(edge_list)} evidence-backed edges")
if __name__=="__main__":main()
