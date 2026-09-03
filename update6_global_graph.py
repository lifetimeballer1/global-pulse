#!/usr/bin/env python3
"""Build the Global Pulse relationship graph from the current snapshot."""
from pathlib import Path
import html
import json
import math
import re

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data" / "snapshot.json"
INDEX = ROOT / "index.html"

COUNTRIES = [
("dz","Algeria","Africa",["algeria","algerian","algiers"]),("ao","Angola","Africa",["angola","angolan","luanda"]),("bf","Burkina Faso","Africa",["burkina faso","burkinabe"]),("bi","Burundi","Africa",["burundi","burundian"]),("cm","Cameroon","Africa",["cameroon","cameroonian"]),("cf","Central African Republic","Africa",["central african republic","bangui"]),("td","Chad","Africa",["chad","chadian","n'djamena"]),("ci","Cote d'Ivoire","Africa",["cote d'ivoire","ivory coast","abidjan"]),("cd","DR Congo","Africa",["democratic republic of congo","eastern congo","goma","m23","north kivu","south kivu"]),("eg","Egypt","Africa",["egypt","egyptian","cairo","sinai"]),("er","Eritrea","Africa",["eritrea","eritrean","asmara"]),("et","Ethiopia","Africa",["ethiopia","ethiopian","addis ababa","amhara","oromia","tigray"]),("gh","Ghana","Africa",["ghana","ghanaian","accra"]),("gn","Guinea","Africa",["guinea","guinean","conakry"]),("ke","Kenya","Africa",["kenya","kenyan","nairobi"]),("ly","Libya","Africa",["libya","libyan","tripoli","benghazi"]),("mg","Madagascar","Africa",["madagascar","malagasy"]),("mw","Malawi","Africa",["malawi","malawian"]),("ml","Mali","Africa",["mali","malian","bamako","jnim"]),("mr","Mauritania","Africa",["mauritania","mauritanian"]),("mz","Mozambique","Africa",["mozambique","mozambican","cabo delgado"]),("na","Namibia","Africa",["namibia","namibian"]),("ne","Niger","Africa",["niger","nigerien","niamey","islamic state sahel"]),("ng","Nigeria","Africa",["nigeria","nigerian","abuja","boko haram","iswap"]),("rw","Rwanda","Africa",["rwanda","rwandan","kigali"]),("sn","Senegal","Africa",["senegal","senegalese","dakar"]),("so","Somalia","Africa",["somalia","somali","mogadishu","al-shabaab"]),("za","South Africa","Africa",["south africa","south african","johannesburg","cape town"]),("ss","South Sudan","Africa",["south sudan","south sudanese","juba"]),("sd","Sudan","Africa",["sudan","sudanese","khartoum","darfur","kordofan","rsf"]),("tz","Tanzania","Africa",["tanzania","tanzanian","dar es salaam"]),("ug","Uganda","Africa",["uganda","ugandan","kampala"]),("zm","Zambia","Africa",["zambia","zambian","lusaka"]),("zw","Zimbabwe","Africa",["zimbabwe","zimbabwean","harare"]),
("bz","Belize","Americas",["belize","belizean"]),("bo","Bolivia","Americas",["bolivia","bolivian","la paz"]),("br","Brazil","Americas",["brazil","brazilian","brasil","sao paulo","rio de janeiro"]),("cl","Chile","Americas",["chile","chilean","santiago"]),("co","Colombia","Americas",["colombia","colombian","bogota","eln","farc","catatumbo"]),("cr","Costa Rica","Americas",["costa rica","costa rican"]),("cu","Cuba","Americas",["cuba","cuban","havana"]),("do","Dominican Republic","Americas",["dominican republic","dominican"]),("ec","Ecuador","Americas",["ecuador","ecuadorian","guayaquil","los choneros"]),("sv","El Salvador","Americas",["el salvador","salvadoran"]),("gt","Guatemala","Americas",["guatemala","guatemalan"]),("gy","Guyana","Americas",["guyana","guyanese","georgetown"]),("ht","Haiti","Americas",["haiti","haitian","port-au-prince"]),("hn","Honduras","Americas",["honduras","honduran"]),("jm","Jamaica","Americas",["jamaica","jamaican","kingston"]),("mx","Mexico","Americas",["mexico","mexican","sinaloa cartel","cjng","cartel"]),("ni","Nicaragua","Americas",["nicaragua","nicaraguan","managua"]),("pa","Panama","Americas",["panama","panamanian","panama canal"]),("py","Paraguay","Americas",["paraguay","paraguayan","asuncion"]),("pe","Peru","Americas",["peru","peruvian","lima"]),("sr","Suriname","Americas",["suriname","surinamese"]),("uy","Uruguay","Americas",["uruguay","uruguayan","montevideo"]),("ve","Venezuela","Americas",["venezuela","venezuelan","caracas"]),
("af","Afghanistan","Asia",["afghanistan","afghan","taliban","kabul"]),("in","India","Asia",["india","indian","delhi","mumbai"]),("id","Indonesia","Asia",["indonesia","indonesian","jakarta"]),("jp","Japan","Asia",["japan","japanese","tokyo"]),("kr","South Korea","Asia",["south korea","korean","seoul"]),("mm","Myanmar","Asia",["myanmar","burma","junta","rakhine","mandalay"]),("pk","Pakistan","Asia",["pakistan","pakistani","ttp","balochistan","islamabad"]),("ph","Philippines","Asia",["philippines","philippine","manila","second thomas shoal"]),("tw","Taiwan","Asia",["taiwan","taiwan strait","taipei"]),("cn","China","Asia",["china","chinese","beijing","pla"]),("ru","Russia","Europe",["russia","russian","moscow","putin"]),("ua","Ukraine","Europe",["ukraine","ukrainian","kyiv","donetsk","crimea","kharkiv","zelensky"]),("ir","Iran","Middle East",["iran","iranian","tehran","hormuz"]),("il","Israel","Middle East",["israel","israeli","tel aviv","gaza"]),("ps","Palestine","Middle East",["palestinian","gaza","west bank","rafah"]),("iq","Iraq","Middle East",["iraq","iraqi","baghdad"]),("sy","Syria","Middle East",["syria","syrian","damascus","idlib"]),("ye","Yemen","Middle East",["yemen","yemeni","houthi","aden"]),("sa","Saudi Arabia","Middle East",["saudi arabia","saudi","riyadh"]),("tr","Turkey","Middle East",["turkey","turkish","ankara","istanbul"]),
]

def hit(alias, blob):
    return re.search(r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])", blob.lower()) is not None

def build_graph(data):
    stories = data.get("stories", [])
    nodes=[]; story_hits={}
    for cid,name,region,aliases in COUNTRIES:
        ids=[]
        for s in stories:
            blob=f"{s.get('title','')} {s.get('summary','')}"
            if any(hit(a,blob) for a in aliases): ids.append(s.get('id'))
        story_hits[cid]=set(ids)
        nodes.append({"id":cid,"label":name,"region":region,"type":"country","signalCount":len(ids)})
    for c in data.get("conflicts",[]):
        nodes.append({"id":"conflict:"+str(c.get('id')),"label":c.get('name','Conflict'),"region":c.get('region','Other'),"type":"conflict","signalCount":c.get('signalCount',0)})
    edges=[]
    for i,a in enumerate(COUNTRIES):
        for b in COUNTRIES[i+1:]:
            common=len(story_hits[a[0]] & story_hits[b[0]])
            if common>=2:
                edges.append({"source":a[0],"target":b[0],"weight":min(8,common),"basis":"shared current reporting","confidence":"LOW–MODERATE"})
    for c in data.get("conflicts",[]):
        aliases=[]
        # use conflict signals and its name as a conservative matching basis
        name=str(c.get('name',''))
        for cid,n,region,als in COUNTRIES:
            if str(c.get('region','')) not in (region,'Africa','Americas','Asia','Europe','Middle East','Latin America','Caribbean','Indo-Pacific'): continue
            related=sum(1 for s in stories if any(hit(a,f"{s.get('title','')} {s.get('summary','')}") for a in als) and any(hit(x,f"{s.get('title','')} {s.get('summary','')}") for x in re.findall(r"[A-Za-z][A-Za-z-]{3,}",name)))
            if related>=1:
                edges.append({"source":"conflict:"+str(c.get('id')),"target":cid,"weight":min(6,related),"basis":"shared conflict reporting","confidence":"MODERATE" if related>=2 else "LOW"})
    return {"nodes":nodes,"edges":edges,"method":"Relationships are generated from current public-source co-occurrence and conflict associations. They are analytical signals, not proof of causation."}

CSS='''<style id="gp-graph-css">.gp-graph{margin:22px 0;border:1px solid rgba(148,163,184,.14);border-radius:18px;background:linear-gradient(180deg,rgba(15,23,42,.98),rgba(9,14,26,.98));overflow:hidden}.gp-graph-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;padding:18px 20px;border-bottom:1px solid rgba(148,163,184,.12)}.gp-graph-title{font-size:18px;font-weight:800}.gp-graph-sub{margin-top:5px;color:#94a3b8;font-size:12px;line-height:1.5}.gp-graph-tools{display:flex;gap:6px;flex-wrap:wrap}.gp-graph-tools button{border:1px solid rgba(148,163,184,.18);background:#111827;color:#cbd5e1;border-radius:999px;padding:7px 10px;font-size:11px;cursor:pointer}.gp-graph-tools button.active{background:#1e293b;color:#fff;border-color:rgba(96,165,250,.5)}.gp-graph-body{min-height:460px}.gp-graph svg{width:100%;height:460px;display:block}.gp-edge{stroke:rgba(148,163,184,.22)}.gp-node{cursor:pointer}.gp-node circle{fill:#152235;stroke:rgba(255,255,255,.2);stroke-width:1.2}.gp-node.conflict circle{fill:#3a2025;stroke:#ff6678}.gp-node text{fill:#cbd5e1;font-size:9px;pointer-events:none}.gp-graph-note{padding:11px 20px;color:#64748b;font-size:10px;border-top:1px solid rgba(148,163,184,.1)}@media(max-width:700px){.gp-graph-head{display:block}.gp-graph-tools{margin-top:12px}.gp-graph-body,.gp-graph svg{min-height:390px;height:390px}.gp-node text{font-size:8px}}</style>'''

HTML='''<section class="gp-graph" id="globalGraph"><div class="gp-graph-head"><div><div class="gp-graph-title">Global System Graph</div><div class="gp-graph-sub">Countries, conflict theaters and cross-border reporting relationships. Built from the current evidence set.</div></div><div class="gp-graph-tools"><button class="active" data-graph-region="ALL">World</button><button data-graph-region="Africa">Africa</button><button data-graph-region="Americas">Americas</button></div></div><div class="gp-graph-body"><svg id="gpGraphSvg" viewBox="0 0 1100 460" preserveAspectRatio="xMidYMid meet"></svg></div><div class="gp-graph-note" id="gpGraphNote"></div></section>'''

JS='''<script id="gp-graph-js">(function(){function draw(region){const svg=document.getElementById('gpGraphSvg'),note=document.getElementById('gpGraphNote'),g=window.DATA&&DATA.globalGraph;if(!svg||!g)return;let ns=g.nodes.filter(n=>region==='ALL'||n.region===region);if(ns.length>75)ns=ns.sort((a,b)=>(b.signalCount||0)-(a.signalCount||0)).slice(0,75);const keep=new Set(ns.map(n=>n.id));const es=g.edges.filter(e=>keep.has(e.source)&&keep.has(e.target));const by=new Map(ns.map(n=>[n.id,n])),W=1100,H=460,cx=W/2,cy=H/2;ns.forEach((n,i)=>{const a=i/ns.length*Math.PI*2,r=n.type==='conflict'?135:205; n.x=cx+Math.cos(a)*r*(region==='ALL'?1.35:1.55);n.y=cy+Math.sin(a)*r*.86});svg.innerHTML=es.map(e=>{const a=by.get(e.source),b=by.get(e.target);return a&&b?`<line class="gp-edge" x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke-width="${Math.max(1,(e.weight||1)/2)}"/>`:''}).join('')+ns.map(n=>{const r=n.type==='conflict'?7:Math.max(4,Math.min(10,4+(n.signalCount||0)/8));return `<g class="gp-node ${n.type}" transform="translate(${n.x.toFixed(1)},${n.y.toFixed(1)})"><circle r="${r}"/><text x="${r+5}" y="3">${String(n.label).replace(/&/g,'&amp;').replace(/</g,'&lt;').slice(0,24)}</text></g>`}).join('');note.textContent=`${ns.length} nodes · ${es.length} evidence-linked relationships · ${region==='ALL'?'world view':region+' view'}`;}document.querySelectorAll('[data-graph-region]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-graph-region]').forEach(x=>x.classList.remove('active'));b.classList.add('active');draw(b.dataset.graphRegion)}));draw('ALL')})();</script>'''

def patch_index():
    s=INDEX.read_text()
    s=re.sub(r'<style id="gp-graph-css">.*?</style>','',s,flags=re.S)
    s=re.sub(r'<script id="gp-graph-js">.*?</script>','',s,flags=re.S)
    s=re.sub(r'<section class="gp-graph" id="globalGraph">.*?</section>','',s,flags=re.S)
    s=s.replace('</main>',HTML+'</main>',1)
    s=s.replace('</head>',CSS+'</head>',1)
    s=s.replace('</body>',JS+'</body>',1)
    INDEX.write_text(s)

def main():
    data=json.loads(SNAP.read_text())
    data['globalGraph']=build_graph(data)
    SNAP.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    patch_index()
    print(f"Global graph built: {len(data['globalGraph']['nodes'])} nodes, {len(data['globalGraph']['edges'])} edges")

if __name__=='__main__': main()
