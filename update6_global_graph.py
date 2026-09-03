#!/usr/bin/env python3
"""Global Pulse Update 6: expand regional coverage and build a clean relationship graph."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "update_snapshot.py"
INDEX = ROOT / "index.html"

# Additional no-key feeds with stronger Africa / Latin America coverage.
EXTRA_FEEDS = '''    ("Africanews", "https://www.africanews.com/feed/", "africa"),
    ("InSight Crime", "https://insightcrime.org/feed/", "americas"),
    ("UN News", "https://news.un.org/feed/subscribe/en/news/region/africa/feed/rss.xml", "africa"),
    ("UN News Americas", "https://news.un.org/feed/subscribe/en/news/region/americas/feed/rss.xml", "americas"),
    ("UN News Latin America", "https://news.un.org/feed/subscribe/en/news/region/americas/feed/rss.xml", "americas"),
'''

WATCH_COUNTRIES = '''
WATCH_COUNTRIES = [
    ("dz", "Algeria", "Africa", ["algeria", "algerian", "algiers"]), ("ao", "Angola", "Africa", ["angola", "angolan", "luanda"]),
    ("bj", "Benin", "Africa", ["benin", "beninese"]), ("bw", "Botswana", "Africa", ["botswana", "gaborone"]),
    ("bf", "Burkina Faso", "Africa", ["burkina faso", "burkinabe"]), ("bi", "Burundi", "Africa", ["burundi", "burundian", "bujumbura"]),
    ("cm", "Cameroon", "Africa", ["cameroon", "cameroonian"]), ("cf", "Central African Republic", "Africa", ["central african republic", "bangui"]),
    ("td", "Chad", "Africa", ["chad", "chadian", "n'djamena"]), ("ci", "Côte d'Ivoire", "Africa", ["cote d'ivoire", "ivory coast", "abidjan"]),
    ("cd", "DR Congo", "Africa", ["democratic republic of congo", "drc", "eastern congo", "goma", "m23"]),
    ("eg", "Egypt", "Africa", ["egypt", "egyptian", "cairo", "sinai"]), ("er", "Eritrea", "Africa", ["eritrea", "eritrean", "asmara"]),
    ("et", "Ethiopia", "Africa", ["ethiopia", "ethiopian", "addis ababa", "amhara", "oromia", "tigray"]),
    ("gh", "Ghana", "Africa", ["ghana", "ghanaian", "accra"]), ("gn", "Guinea", "Africa", ["guinea", "guinean", "conakry"]),
    ("ke", "Kenya", "Africa", ["kenya", "kenyan", "nairobi"]), ("ly", "Libya", "Africa", ["libya", "libyan", "tripoli", "benghazi"]),
    ("mg", "Madagascar", "Africa", ["madagascar", "malagasy", "antananarivo"]), ("mw", "Malawi", "Africa", ["malawi", "malawian"]),
    ("ml", "Mali", "Africa", ["mali", "malian", "bamako", "jnim"]), ("mr", "Mauritania", "Africa", ["mauritania", "mauritanian"]),
    ("mz", "Mozambique", "Africa", ["mozambique", "mozambican", "cabo delgado"]), ("na", "Namibia", "Africa", ["namibia", "namibian"]),
    ("ne", "Niger", "Africa", ["niger", "nigerien", "niamey", "islamic state sahel"]), ("ng", "Nigeria", "Africa", ["nigeria", "nigerian", "abuja", "boko haram", "iswap"]),
    ("rw", "Rwanda", "Africa", ["rwanda", "rwandan", "kigali"]), ("sn", "Senegal", "Africa", ["senegal", "senegalese", "dakar"]),
    ("so", "Somalia", "Africa", ["somalia", "somali", "mogadishu", "al-shabaab"]), ("za", "South Africa", "Africa", ["south africa", "south african", "johannesburg", "cape town"]),
    ("ss", "South Sudan", "Africa", ["south sudan", "south sudanese", "juba"]), ("sd", "Sudan", "Africa", ["sudan", "sudanese", "khartoum", "darfur", "rsf"]),
    ("tz", "Tanzania", "Africa", ["tanzania", "tanzanian", "dar es salaam"]), ("ug", "Uganda", "Africa", ["uganda", "ugandan", "kampala"]),
    ("zm", "Zambia", "Africa", ["zambia", "zambian", "lusaka"]), ("zw", "Zimbabwe", "Africa", ["zimbabwe", "zimbabwean", "harare"]),
    ("bz", "Belize", "Americas", ["belize", "belizean"]), ("cr", "Costa Rica", "Americas", ["costa rica", "costa rican"]),
    ("cu", "Cuba", "Americas", ["cuba", "cuban", "havana"]), ("do", "Dominican Republic", "Americas", ["dominican republic", "dominican"]),
    ("sv", "El Salvador", "Americas", ["el salvador", "salvadoran"]), ("gt", "Guatemala", "Americas", ["guatemala", "guatemalan"]),
    ("gy", "Guyana", "Americas", ["guyana", "guyanese", "georgetown"]), ("hn", "Honduras", "Americas", ["honduras", "honduran"]),
    ("jm", "Jamaica", "Americas", ["jamaica", "jamaican", "kingston"]), ("ni", "Nicaragua", "Americas", ["nicaragua", "nicaraguan", "managua"]),
    ("pa", "Panama", "Americas", ["panama", "panamanian", "panama canal"]), ("py", "Paraguay", "Americas", ["paraguay", "paraguayan", "asuncion"]),
    ("pe", "Peru", "Americas", ["peru", "peruvian", "lima"]), ("sr", "Suriname", "Americas", ["suriname", "surinamese"]),
    ("uy", "Uruguay", "Americas", ["uruguay", "uruguayan", "montevideo"]), ("ve", "Venezuela", "Americas", ["venezuela", "venezuelan", "caracas"]),
    ("bo", "Bolivia", "Americas", ["bolivia", "bolivian", "la paz"]), ("br", "Brazil", "Americas", ["brazil", "brazilian", "amazonas", "rio de janeiro", "sao paulo"]),
    ("ar", "Argentina", "Americas", ["argentina", "argentine", "buenos aires"]), ("cl", "Chile", "Americas", ["chile", "chilean", "santiago"]),
]

GRAPH_FUNCTION = r'''

def _alias_hit(alias, blob):
    return re.search(r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])", blob.lower()) is not None


def build_global_graph(stories):
    nodes, edges = [], []
    node_seen = set()
    for cid, name, region, aliases in WATCH_COUNTRIES:
        hits = []
        for story in stories:
            blob = f"{story['title']} {story['summary']}"
            if any(_alias_hit(a, blob) for a in aliases):
                hits.append(story)
        nodes.append({"id": cid, "label": name, "region": region, "type": "country", "signalCount": len(hits)})
        node_seen.add(cid)
    # Existing conflict theaters become higher-level graph nodes.
    for c in CONFLICTS:
        cid, name, region, *_ = c
        nodes.append({"id": "conflict:" + cid, "label": name, "region": region, "type": "conflict"})
    # Country-to-country edges are evidence-weighted by shared story co-occurrence.
    country_hits = {}
    for cid, name, region, aliases in WATCH_COUNTRIES:
        country_hits[cid] = [s for s in stories if any(_alias_hit(a, f"{s['title']} {s['summary']}") for a in aliases)]
    for i, a in enumerate(WATCH_COUNTRIES):
        for b in WATCH_COUNTRIES[i+1:]:
            common_ids = {s['id'] for s in country_hits[a[0]]} & {s['id'] for s in country_hits[b[0]]}
            if len(common_ids) >= 2:
                edges.append({"source": a[0], "target": b[0], "weight": min(8, len(common_ids)), "basis": "shared current reporting", "confidence": "LOW–MODERATE"})
    # Conflict-to-country edges are only added when a current story matches the theater and country.
    for cid, cname, cregion, ccat, clevel, caliases in CONFLICTS:
        for country_id, country_name, region, aliases in WATCH_COUNTRIES:
            if region != cregion: continue
            count = 0
            for story in stories:
                blob = f"{story['title']} {story['summary']}"
                if any(_alias_hit(x, blob) for x in caliases) and any(_alias_hit(x, blob) for x in aliases): count += 1
            if count >= 1:
                edges.append({"source": "conflict:" + cid, "target": country_id, "weight": min(6, count), "basis": "shared conflict reporting", "confidence": "MODERATE" if count >= 2 else "LOW"})
    return {"nodes": nodes, "edges": edges, "method": "Edges are generated from current public-source co-occurrence. They are analytical relationships, not proof of causation."}
'''

UI_CSS = r'''<style id="gp-graph-css">
.gp-graph{margin:22px 0;border:1px solid rgba(148,163,184,.14);border-radius:18px;background:linear-gradient(180deg,rgba(15,23,42,.98),rgba(9,14,26,.98));overflow:hidden}.gp-graph-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;padding:18px 20px;border-bottom:1px solid rgba(148,163,184,.12)}.gp-graph-title{font-size:18px;font-weight:800}.gp-graph-sub{margin-top:5px;color:#94a3b8;font-size:12px;line-height:1.5}.gp-graph-tools{display:flex;gap:6px;flex-wrap:wrap}.gp-graph-tools button{border:1px solid rgba(148,163,184,.18);background:#111827;color:#cbd5e1;border-radius:999px;padding:7px 10px;font-size:11px;cursor:pointer}.gp-graph-tools button.active{background:#1e293b;color:#fff;border-color:rgba(96,165,250,.5)}.gp-graph-body{position:relative;min-height:460px}.gp-graph svg{width:100%;height:460px;display:block}.gp-edge{stroke:rgba(148,163,184,.22);stroke-width:1}.gp-node{cursor:pointer}.gp-node circle{stroke:rgba(255,255,255,.18);stroke-width:1.2}.gp-node text{fill:#cbd5e1;font-size:9px;pointer-events:none}.gp-graph-note{padding:11px 20px;color:#64748b;font-size:10px;border-top:1px solid rgba(148,163,184,.1)}
@media(max-width:700px){.gp-graph-head{display:block}.gp-graph-tools{margin-top:12px}.gp-graph-body,.gp-graph svg{min-height:390px;height:390px}.gp-node text{font-size:8px}}
</style>'''

UI_HTML = r'''<section class="gp-graph" id="globalGraph"><div class="gp-graph-head"><div><div class="gp-graph-title">Global System Graph</div><div class="gp-graph-sub">Regional signals, conflict theaters and cross-border reporting relationships. The graph shows where current reporting overlaps; it does not claim causation.</div></div><div class="gp-graph-tools"><button class="active" data-graph-region="ALL">World</button><button data-graph-region="Africa">Africa</button><button data-graph-region="Americas">Americas</button></div></div><div class="gp-graph-body"><svg id="gpGraphSvg" viewBox="0 0 1100 460" preserveAspectRatio="xMidYMid meet"></svg></div><div class="gp-graph-note" id="gpGraphNote">Building relationships from the current public-source evidence set.</div></section>'''

UI_JS = r'''<script id="gp-graph-js">(function(){
function renderGraph(region){const box=document.getElementById('gpGraphSvg'),note=document.getElementById('gpGraphNote');if(!box||!window.DATA||!DATA.globalGraph)return;const g=DATA.globalGraph;let nodes=g.nodes.filter(n=>region==='ALL'||n.region===region);const ids=new Set(nodes.map(n=>n.id));let edges=g.edges.filter(e=>ids.has(e.source)&&ids.has(e.target));if(nodes.length>95){nodes=nodes.filter(n=>n.signalCount>0||n.type==='conflict');}if(nodes.length>70){nodes=nodes.sort((a,b)=>(b.signalCount||0)-(a.signalCount||0)).slice(0,70);const keep=new Set(nodes.map(n=>n.id));edges=edges.filter(e=>keep.has(e.source)&&keep.has(e.target));}
const W=1100,H=460,cx=W/2,cy=H/2;nodes.forEach((n,i)=>{const angle=(i/nodes.length)*Math.PI*2;const ring=n.type==='conflict'?120:Math.min(190,120+((n.signalCount||0)%5)*18);n.x=cx+Math.cos(angle)*ring*(region==='ALL'?1.45:1.7);n.y=cy+Math.sin(angle)*ring*.9;});const by=new Map(nodes.map(n=>[n.id,n]));box.innerHTML=edges.map(e=>{const a=by.get(e.source),b=by.get(e.target);return a&&b?`<line class="gp-edge" x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke-width="${Math.max(1,e.weight/2)}"/>`:''}).join('')+nodes.map(n=>{const r=n.type==='conflict'?7:Math.max(4,Math.min(10,4+(n.signalCount||0)/5));return `<g class="gp-node" transform="translate(${n.x.toFixed(1)},${n.y.toFixed(1)})"><circle r="${r}"/><text x="${r+5}" y="3">${String(n.label).replace(/&/g,'&amp;').replace(/</g,'&lt;').slice(0,22)}</text></g>`}).join('');note.textContent=`${nodes.length} nodes · ${edges.length} evidence-linked relationships · ${region==='ALL'?'global view':region+' view'}. Relationships are generated from current public-source co-occurrence.`;}
document.querySelectorAll('[data-graph-region]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-graph-region]').forEach(x=>x.classList.remove('active'));b.classList.add('active');renderGraph(b.dataset.graphRegion)}));renderGraph('ALL');})();</script>'''


def patch_snapshot():
    s = SNAP.read_text()
    # Add feeds only if not already present.
    marker = '    ("ReliefWeb", "https://reliefweb.int/updates/rss.xml", "humanitarian"),\n'
    if '"Africanews"' not in s:
        s = s.replace(marker, marker + EXTRA_FEEDS)
    # Add graph country registry and graph builder before BREAKING_RE.
    if 'WATCH_COUNTRIES = [' not in s:
        s = s.replace('BREAKING_RE = re.compile', WATCH_COUNTRIES + '\n' + GRAPH_FUNCTION + '\nBREAKING_RE = re.compile')
    # Increase story retention from 120 to 300.
    s = s.replace('stories = unique[:120]', 'stories = unique[:300]')
    # Add graph to snapshot.
    old = '"markers": old.get("markers", []), "social": old.get("social", []), "stories": stories, "sourceHealth":'
    new = '"markers": old.get("markers", []), "social": old.get("social", []), "globalGraph": build_global_graph(stories), "stories": stories, "sourceHealth":'
    if '"globalGraph": build_global_graph(stories)' not in s:
        s = s.replace(old, new)
    SNAP.write_text(s)


def patch_index():
    s = INDEX.read_text()
    for token in ('gp-graph-css','gp-graph-js','id="globalGraph"'):
        if token in s:
            return
    s = s.replace('</head>', UI_CSS + '\n</head>', 1)
    s = s.replace('</main>', UI_HTML + '\n</main>', 1)
    s = s.replace('</body>', UI_JS + '\n</body>', 1)
    INDEX.write_text(s)


if __name__ == '__main__':
    patch_snapshot()
    patch_index()
    print('Update 6 graph layer patched.')
'''
