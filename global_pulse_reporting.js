/* Global Pulse — static-first live reporting bridge. */
(function(){
  "use strict";
  var POLL_MS=60000, TIMEOUT_MS=7000, FEED_ID="pulse-reporting-feed", COUNT_ID="pulse-reporting-count";
  var FALLBACK=["data/live_articles.json","data/snapshot.json"];
  function $(id){return document.getElementById(id)}
  function safe(v,d){v=String(v==null?"":v).trim();return v||d||""}
  function url(v){try{var u=new URL(String(v||""),location.href);return /^https?:$/.test(u.protocol)?u.href:""}catch(e){return ""}}
  function ago(v){var t=Date.parse(v||"");if(!isFinite(t))return "Time unavailable";var m=Math.max(0,Math.floor((Date.now()-t)/60000)),h=Math.floor(m/60),d=Math.floor(h/24);return m<1?"just now":m<60?m+"m ago":h<24?h+"h ago":d+"d ago"}
  function normalize(p){
    var a=Array.isArray(p)?p:(p&&p.articles)||(p&&p.stories)||[];
    return a.map(function(x){
      x=x||{};var c=x.credit||{};
      return {title:safe(x.title||x.headline,"Untitled report"),published_date:safe(x.published_date||x.time||x.publishedAt||x.timestamp),summary_snippet:safe(x.summary_snippet||x.summary||x.description,"No summary was provided by the source."),original_link:url(x.original_link||x.url||x.link||c.source_url),source:safe(c.source||x.source_name||x.sourceLabel||x.source,"Open-data source")};
    }).filter(function(x){return x.title})
  }
  function render(items,mode){
    var f=$(FEED_ID);if(!f)return;
    f.replaceChildren();
    var c=$(COUNT_ID);if(c)c.textContent=items.length+" ACTIVE"+(mode==="snapshot"?" · SNAPSHOT":"");
    if(!items.length){var e=document.createElement("div");e.className="gp-reporting-empty";e.textContent="No active reporting is currently available.";f.appendChild(e);return}
    items.slice(0,50).forEach(function(a){
      var card=document.createElement("article");card.className="gp-reporting-card";
      var b=document.createElement("div");b.className="gp-reporting-source";b.textContent="◉ "+a.source;card.appendChild(b);
      var t=document.createElement(a.original_link?"a":"div");t.className="gp-reporting-title";t.textContent=a.title;
      if(a.original_link){t.href=a.original_link;t.target = "_blank";t.rel="noopener noreferrer"}
      card.appendChild(t);
      var tm=document.createElement("time");tm.className="gp-reporting-time";tm.dateTime=a.published_date;tm.textContent=ago(a.published_date);card.appendChild(tm);
      var s=document.createElement("p");s.className="gp-reporting-summary";s.textContent=a.summary_snippet;card.appendChild(s);
      var src=document.createElement("div");src.className="gp-reporting-source-name";src.textContent="Source: "+a.source;card.appendChild(src);
      if(a.original_link){var r=document.createElement("a");r.className="gp-reporting-action";r.href=a.original_link;r.target = "_blank";r.rel="noopener noreferrer";r.textContent="Read Full Source Report ↗";card.appendChild(r)}
      f.appendChild(card)
    })
  }
  function alertBox(){var f=$(FEED_ID);if(!f)return;var a=document.createElement("div");a.className="gp-reporting-alert";a.setAttribute("role","alert");var s=document.createElement("strong");s.textContent="Pipeline Connection Terminated - Retrying...";var d=document.createElement("span");d.textContent="Live API unavailable. Showing repository data when available; retrying automatically.";a.appendChild(s);a.appendChild(d);f.replaceChildren(a);var c=$(COUNT_ID);if(c)c.textContent="RECONNECTING"}
  async function get(u){var ac=new AbortController(),id=setTimeout(function(){ac.abort()},TIMEOUT_MS);try{var r=await fetch(u,{cache:"no-store",signal:ac.signal,headers:{Accept:"application/json"}});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(id)}}
  async function fetchPulseReporting(){
    var f=$(FEED_ID);if(!f)return;f.setAttribute("aria-busy","true");
    for(var i=0;i<FALLBACK.length;i++){
      try{var p=await get(FALLBACK[i]+"?t="+Date.now()),a=normalize(p);if(a.length){render(a,"snapshot");f.classList.add("gp-reporting-fallback");f.setAttribute("aria-busy","false");return true}}
      catch(e){}
    }
    var candidates=[];
    if(window.GLOBAL_PULSE_API)candidates.push(window.GLOBAL_PULSE_API);
    if(location.hostname==="localhost"||location.hostname==="127.0.0.1")candidates.push(location.origin+"/");
    for(var j=0;j<candidates.length;j++){
      try{var q=normalize(await get(candidates[j]));if(q.length){render(q,"live");f.classList.remove("gp-reporting-fallback");f.setAttribute("aria-busy","false");return true}}
      catch(e2){}
    }
    alertBox();f.setAttribute("aria-busy","false");return false;
  }
  window.fetchPulseReporting=fetchPulseReporting;
  function start(){fetchPulseReporting();setInterval(fetchPulseReporting,60000);setInterval(function(){document.querySelectorAll(".gp-reporting-time").forEach(function(x){if(x.dateTime)x.textContent=ago(x.dateTime)})},30000)}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});else start();
})();
