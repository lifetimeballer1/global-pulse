#!/usr/bin/env python3
"""Install the source-age filter on the canonical Global Pulse situation map.

The filter uses the timestamp supplied by the source/event record (publishedAt,
published, sourcePublishedAt, timestamp, date, etc.) and never the site's
updatedAt timestamp. Unknown timestamps remain visible under ALL/UNKNOWN.
"""
from pathlib import Path
import re

INDEX = Path(__file__).resolve().parent / "index.html"
STYLE_ID = "gp-source-age-filter-css"
SCRIPT_ID = "gp-source-age-filter-js"

CSS = r'''
<style id="gp-source-age-filter-css">
.gp-age-filter{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin:0 0 9px}.gp-age-filter label{font-size:10px;color:var(--muted);font-weight:750;text-transform:uppercase;letter-spacing:.06em}.gp-age-filter select{border:1px solid var(--line);background:#09121c;color:var(--text);border-radius:9px;padding:8px 10px;min-height:36px}.gp-age-note{font-size:10px;color:var(--muted);margin-left:auto}.gp-age-badge{display:inline-block;margin-top:5px;font-size:9px;color:#91a4b8}.gp-age-badge.fresh{color:var(--green)}.gp-age-badge.old{color:var(--amber)}
@media(max-width:720px){.gp-age-filter{overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px}.gp-age-filter select{min-width:180px}.gp-age-note{min-width:max-content;margin-left:0}}
</style>
'''

JS = r'''
<script id="gp-source-age-filter-js">
(function(){
  "use strict";
  const ID="gp-source-age-filter";
  let maxAge="all";
  const ageFields=["publishedAt","published_at","sourcePublishedAt","source_published_at","published","pubDate","pub_date","timestamp","date","sourceDate","source_date","createdAt","created_at"];
  function timestamp(m){
    for(const k of ageFields){
      const v=m&&m[k];
      if(v===null||v===undefined||v==="")continue;
      const n=Date.parse(String(v));
      if(Number.isFinite(n))return n;
    }
    return NaN;
  }
  function ageMs(m){const t=timestamp(m);return Number.isFinite(t)?Date.now()-t:NaN}
  function label(ms){
    if(!Number.isFinite(ms))return "Source age unknown";
    if(ms<0)return "Source time in future";
    const min=Math.floor(ms/60000),h=Math.floor(min/60),d=Math.floor(h/24);
    if(min<1)return "Source posted just now";
    if(min<60)return "Source posted "+min+"m ago";
    if(h<24)return "Source posted "+h+"h "+(min%60)+"m ago";
    return "Source posted "+d+"d "+(h%24)+"h ago";
  }
  function matches(m){
    if(maxAge==="all")return true;
    const ms=ageMs(m);
    if(maxAge==="unknown")return !Number.isFinite(ms);
    if(!Number.isFinite(ms))return false;
    if(maxAge==="older")return ms>604800000;
    return ms>=0&&ms<=Number(maxAge)*3600000;
  }
  function decorate(){
    const markers=Array.isArray(window.DATA?.markers)?window.DATA.markers:[];
    for(const m of markers)m.__gpSourceAge=label(ageMs(m));
  }
  function install(){
    if(document.getElementById(ID))return true;
    const map=document.getElementById("map");
    if(!map||!map.parentElement)return false;
    const parent=map.parentElement;
    const wrap=document.createElement("div");wrap.id=ID;wrap.className="gp-age-filter";
    wrap.innerHTML='<label for="gpSourceAge">Source age</label><select id="gpSourceAge"><option value="all">All sources</option><option value="1">Last 1 hour</option><option value="6">Last 6 hours</option><option value="24">Last 24 hours</option><option value="72">Last 3 days</option><option value="168">Last 7 days</option><option value="older">Older than 7 days</option><option value="unknown">Unknown source time</option></select><span class="gp-age-note">Uses the source post time, not Global Pulse update time.</span>';
    parent.insertBefore(wrap,map);
    const select=wrap.querySelector("#gpSourceAge");
    select.addEventListener("change",()=>{maxAge=select.value;decorate();window.dispatchEvent(new CustomEvent("gp:source-age-change",{detail:{maxAge}}));if(typeof window.renderMap==="function")window.renderMap();});
    decorate();
    return true;
  }
  window.gpSourceAge={ageMs,label,matches,decorate};
  document.addEventListener("globalpulse:dataready",()=>{decorate();if(typeof window.renderMap==="function")window.renderMap();});
  const t=setInterval(()=>{if(install())clearInterval(t)},100);
  window.addEventListener("gp:map-render-marker",e=>{const m=e.detail?.marker;if(m&&e.detail?.element){const b=document.createElement("div");b.className="gp-age-badge "+(Number.isFinite(ageMs(m))&&ageMs(m)<=86400000?"fresh":"old");b.textContent=label(ageMs(m));e.detail.element.appendChild(b)}});
})();
</script>
'''

html=INDEX.read_text(encoding="utf-8")
html=re.sub(r'\n<style id="'+re.escape(STYLE_ID)+r'">.*?</style>\n?',"\n",html,flags=re.S)
html=re.sub(r'\n<script id="'+re.escape(SCRIPT_ID)+r'">.*?</script>\n?',"\n",html,flags=re.S)
html=html.replace("</head>",CSS+"\n</head>",1)
html=html.replace("</body>",JS+"\n</body>",1)
INDEX.write_text(html,encoding="utf-8")
print("Installed source-age filter")
