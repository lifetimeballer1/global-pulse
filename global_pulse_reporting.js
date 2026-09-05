/* Global Pulse — live reporting bridge with open-data first refresh. */
(function(){
  "use strict";
  var POLL_MS=60000,TIMEOUT_MS=9000,FEED_ID="pulse-reporting-feed",COUNT_ID="pulse-reporting-count",VISIBLE_LIMIT=5;
  var LIVE=["https://api.gdeltproject.org/api/v2/doc/doc?query="+encodeURIComponent('(Russia OR Ukraine OR NATO OR missile OR airstrike OR bombing OR explosion OR invasion OR attack OR ceasefire OR coup OR earthquake OR tsunami OR hurricane OR wildfire OR oil OR sanctions OR tariff)')+"&mode=artlist&format=json&maxrecords=75&timespan=15min&sort=datedesc"];
  var FALLBACK=["data/live_articles.json","data/snapshot.json"];
  function $(id){return document.getElementById(id)}
  function safe(v,d){v=String(v==null?"":v).trim();return v||d||""}
  function url(v){try{var u=new URL(String(v||""),location.href);return /^https?:$/.test(u.protocol)?u.href:""}catch(e){return ""}}
  function parseTime(v){
    if(!v)return NaN;
    var s=String(v).trim();
    /* GDELT ArtList uses seendate like 20260905T181200Z. */
    var gd=s.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/);
    if(gd)s=gd[1]+"-"+gd[2]+"-"+gd[3]+"T"+gd[4]+":"+gd[5]+":"+gd[6]+"Z";
    var t=Date.parse(s);if(isFinite(t))return t;var n=Number(s);if(isFinite(n))return n<2e10?n*1000:n;return NaN
  }
  function ago(v){var t=parseTime(v);if(!isFinite(t))return "Time unavailable";var m=Math.max(0,Math.floor((Date.now()-t)/60000)),h=Math.floor(m/60),d=Math.floor(h/24);return m<1?"just now":m<60?m+"m ago":h<24?h+"h ago":d+"d ago"}
  function normalize(p){
    var a=Array.isArray(p)?p:(p&&p.articles)||(p&&p.results)||(p&&p.stories)||[];
    var now=Date.now(),maxAge=6*60*60*1000;
    return a.map(function(x){
      x=x||{};var c=x.credit||{},t=x.published_date||x.publishedAt||x.pubDate||x.datetime||x.timestamp||x.time||x.seendate||x.seenDate;
      var ts=parseTime(t);
      return {title:safe(x.title||x.headline,"Untitled report"),published_date:safe(t),summary_snippet:safe(x.summary_snippet||x.summary||x.description,"No summary was provided by the source."),original_link:url(x.original_link||x.url||x.link||c.source_url),source:safe(x.source||x.source_name||x.sourceLabel||c.source||x.domain||"Open-data source"),_ts:ts};
    }).filter(function(x){return x.title && isFinite(x._ts) && x._ts<=now+5*60*1000 && now-x._ts<=maxAge});
  }
  function card(a,hidden){
    var card=document.createElement("article");card.className="gp-reporting-card";card.hidden=!!hidden;card.setAttribute("aria-hidden",String(!!hidden));
    var b=document.createElement("div");b.className="gp-reporting-source";b.textContent="◉ "+a.source;card.appendChild(b);
    var t=document.createElement(a.original_link?"a":"div");t.className="gp-reporting-title";t.textContent=a.title;if(a.original_link){t.href=a.original_link;t.target="_blank";t.rel="noopener noreferrer"}card.appendChild(t);
    var tm=document.createElement("time");tm.className="gp-reporting-time";tm.dateTime=a.published_date;tm.textContent=ago(a.published_date);card.appendChild(tm);
    var s=document.createElement("p");s.className="gp-reporting-summary";s.textContent=a.summary_snippet;card.appendChild(s);
    var src=document.createElement("div");src.className="gp-reporting-source-name";src.textContent="Source: "+a.source;card.appendChild(src);
    if(a.original_link){var r=document.createElement("a");r.className="gp-reporting-action";r.href=a.original_link;r.target="_blank";r.rel="noopener noreferrer";r.textContent="Read Full Source Report ↗";card.appendChild(r)}
    return card;
  }
  function render(items,mode){
    var f=$(FEED_ID);if(!f)return;items.sort(function(a,b){return (b._ts||0)-(a._ts||0)});f.replaceChildren();
    var c=$(COUNT_ID);if(c)c.textContent=items.length+" ACTIVE · "+(mode==="live"?"LIVE":"SNAPSHOT");
    if(!items.length){var e=document.createElement("div");e.className="gp-reporting-empty";e.textContent="No current reporting found.";f.appendChild(e);return}
    items.forEach(function(a,i){f.appendChild(card(a,i>=VISIBLE_LIMIT))});
    if(items.length>VISIBLE_LIMIT){
      var actions=document.createElement("div");actions.className="gp-list-actions";
      var btn=document.createElement("button");btn.type="button";btn.className="more-btn gp-list-more";btn.setAttribute("aria-expanded","false");btn.textContent="Show more ("+(items.length-VISIBLE_LIMIT)+")";
      btn.addEventListener("click",function(){var expanded=btn.getAttribute("aria-expanded")==="true";Array.from(f.querySelectorAll(".gp-reporting-card")).forEach(function(x,i){if(i>=VISIBLE_LIMIT){x.hidden=!expanded;x.setAttribute("aria-hidden",String(!expanded))}});btn.setAttribute("aria-expanded",String(!expanded));btn.textContent=expanded?"Show more ("+(items.length-VISIBLE_LIMIT)+")":"Show less"});
      actions.appendChild(btn);f.appendChild(actions);
    }
  }
  async function get(u){var ac=new AbortController(),id=setTimeout(function(){ac.abort()},TIMEOUT_MS);try{var r=await fetch(u+((u.indexOf("?")>=0?"&":"?")+"_="+Date.now()),{cache:"no-store",signal:ac.signal,headers:{Accept:"application/json"}});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(id)}}
  async function fetchPulseReporting(){var f=$(FEED_ID);if(!f)return;f.setAttribute("aria-busy","true");for(var i=0;i<LIVE.length;i++){try{var live=normalize(await get(LIVE[i]));if(live.length){render(live,"live");f.setAttribute("aria-busy","false");return true}}catch(e){}}for(var j=0;j<FALLBACK.length;j++){try{var snap=normalize(await get(FALLBACK[j]));if(snap.length){render(snap,"snapshot");f.setAttribute("aria-busy","false");return true}}catch(e2){}}f.setAttribute("aria-busy","false");return false}
  window.fetchPulseReporting=fetchPulseReporting;function start(){fetchPulseReporting();setInterval(fetchPulseReporting,POLL_MS);setInterval(function(){document.querySelectorAll(".gp-reporting-time").forEach(function(x){if(x.dateTime)x.textContent=ago(x.dateTime)})},30000)}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});else start();
})();
