/* Global Pulse — production front-end enhancements.
 * No API keys. No external analytics. Safe for static GitHub Pages.
 */
(function(){
  "use strict";
  var ready = false;
  var originalRenderStories = null;
  var newsCategory = "all";
  function qs(s){ return document.querySelector(s); }
  function qsa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function esc(v){ return String(v == null ? "" : v).replace(/[&<>\"]/g,function(c){return ({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;"})[c];}); }
  function relativeTime(iso){
    var t = Date.parse(iso || ""); if(!isFinite(t)) return "";
    var d = Math.max(0,Date.now()-t), m=Math.floor(d/60000), h=Math.floor(m/60), day=Math.floor(h/24);
    if(m<1) return "just now"; if(m<60) return m+"m ago"; if(h<24) return h+"h ago"; return day+"d ago";
  }
  function sourceClass(text){
    text=String(text||"").toLowerCase();
    if(/reuters|ap news|bbc|guardian|npr|france24|dw|al jazeera/.test(text)) return "primary";
    if(/crisis group|reliefweb|cfr/.test(text)) return "analysis";
    return "open";
  }
  function addStyles(){
    if(qs("#gp-production-enhancements")) return;
    var st=document.createElement("style"); st.id="gp-production-enhancements";
    st.textContent=""+
      ".gp-statusbar{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin:0 0 12px;padding:9px 11px;border:1px solid var(--line);border-radius:10px;background:#07111b;font-size:10px;color:var(--muted)}"+
      ".gp-statusbar strong{color:var(--text)}.gp-status-live{display:inline-flex;align-items:center;gap:6px}.gp-status-live i{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 3px rgba(72,223,131,.1)}"+
      ".gp-source-badge{display:inline-block;padding:2px 5px;margin-left:5px;border-radius:4px;font-size:8px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--line);color:var(--muted)}"+
      ".gp-source-badge.primary{color:var(--green);border-color:rgba(72,223,131,.3);background:rgba(72,223,131,.06)}.gp-source-badge.analysis{color:var(--amber);border-color:rgba(255,200,87,.3);background:rgba(255,200,87,.06)}"+
      ".gp-confidence{font-size:9px;color:var(--muted);margin-top:6px}.gp-confidence b{color:var(--text)}"+
      ".gp-skip{position:fixed;left:10px;top:10px;z-index:10001;transform:translateY(-160%);padding:9px 12px;border-radius:8px;background:var(--blue);color:#03101c;font-weight:900}.gp-skip:focus{transform:none}"+
      ".gp-news-category{display:flex;gap:6px;flex-wrap:wrap;margin:-2px 0 10px;padding-bottom:2px;border-bottom:1px solid var(--line)}"+
      ".gp-news-category .filter{font-size:10px;min-height:32px;padding:6px 9px}"+
      ".gp-news-count{font-size:9px;color:var(--muted);margin-left:auto;align-self:center}"+
      "@media(max-width:720px){.gp-statusbar{font-size:9px}.gp-source-badge{display:none}.gp-news-category{overflow-x:auto;flex-wrap:nowrap}.gp-news-category .filter{white-space:nowrap}.gp-news-count{display:none}}";
    document.head.appendChild(st);
  }
  function addStatus(){
    if(qs("#gp-production-status")) return;
    var wrap=qs(".wrap"); if(!wrap) return;
    var bar=document.createElement("div"); bar.id="gp-production-status"; bar.className="gp-statusbar";
    var updated=window.DATA&&window.DATA.updatedAt;
    var stories=window.DATA&&Array.isArray(window.DATA.stories)?window.DATA.stories.length:null;
    var markers=window.DATA&&Array.isArray(window.DATA.markers)?window.DATA.markers.length:null;
    bar.innerHTML='<span class="gp-status-live"><i></i><strong>OPEN-DATA MONITOR</strong> <span>auto-checks every 60s</span></span>'+
      '<span><strong>'+esc(relativeTime(updated)||"unknown")+'</strong> · '+esc(stories==null?"—":stories)+" stories · "+esc(markers==null?"—":markers)+" map signals</span>";
    wrap.insertBefore(bar,wrap.firstElementChild);
  }
  function decorateStories(){
    qsa(".story").forEach(function(card){
      if(card.querySelector(".gp-source-badge")) return;
      var source=qs(".source",card);
      if(!source) return;
      var badge=document.createElement("span"); badge.className="gp-source-badge "+sourceClass(source.textContent); badge.textContent=sourceClass(source.textContent)==="primary"?"reported":sourceClass(source.textContent)==="analysis"?"analysis":"open signal";
      source.appendChild(badge);
      var a=card.querySelector("a[href]"); if(a) a.setAttribute("rel","noopener noreferrer");
    });
  }
  function storyCategory(story){
    var label=String(story&&story.sourceLabel||"").toLowerCase();
    var title=String(story&&story.title||"").toLowerCase();
    if(/u\.s\. politics|us politics|npr politics/.test(label)) return "us-politics";
    if(/global economics|economics/.test(label)) return "economics";
    if(/world politics/.test(label)) return "world-politics";
    if(/trump|congress|senate|house of representatives|supreme court|white house|midterms|election|president|parliament|prime minister|diplomacy|summit|sanctions|alliance|coalition|tariff|trade agreement/.test(title)){
      if(/trump|congress|senate|house of representatives|supreme court|white house|midterms/.test(title)) return "us-politics";
      return "world-politics";
    }
    if(/oil|gas prices|inflation|interest rate|central bank|stocks|bonds|currency|dollar|euro|yuan|yen|tariff|trade|market|economy|economic|shipping costs|freight|commodity/.test(title)) return "economics";
    return "other";
  }
  function categoryStories(){
    var all=Array.isArray(window.DATA&&window.DATA.stories)?window.DATA.stories:[];
    if(newsCategory==="all") return all;
    return all.filter(function(s){return storyCategory(s)===newsCategory;});
  }
  function addNewsCategories(){
    var host=qs(".news-tabs"); if(!host||qs("#gp-news-categories")) return;
    var box=document.createElement("div"); box.id="gp-news-categories"; box.className="gp-news-category";
    box.innerHTML='<button type="button" class="filter active" data-gpcat="all">All</button>'+
      '<button type="button" class="filter" data-gpcat="us-politics">U.S. Politics</button>'+
      '<button type="button" class="filter" data-gpcat="world-politics">World Politics</button>'+
      '<button type="button" class="filter" data-gpcat="economics">Economics</button>'+
      '<span class="gp-news-count" id="gp-news-count"></span>';
    host.parentNode.insertBefore(box,host.nextSibling);
    box.querySelectorAll("[data-gpcat]").forEach(function(btn){btn.addEventListener("click",function(){
      newsCategory=btn.dataset.gpcat;
      box.querySelectorAll("[data-gpcat]").forEach(function(x){x.classList.toggle("active",x===btn)});
      if(typeof originalRenderStories==="function") originalRenderStories();
      updateNewsCount();
    })});
    updateNewsCount();
  }
  function updateNewsCount(){
    var el=qs("#gp-news-count"); if(!el)return;
    var all=Array.isArray(window.DATA&&window.DATA.stories)?window.DATA.stories:[];
    var n=newsCategory==="all"?all.length:categoryStories().length;
    el.textContent=n+" matching stories";
  }
  function installNewsFilter(){
    if(typeof window.renderStories!=="function"||window.renderStories.__gpCategoryWrapped) return;
    originalRenderStories=window.renderStories;
    var base=originalRenderStories;
    var wrapped=function(){
      if(newsCategory==="all") base();
      else {
        var originalStories=window.DATA&&window.DATA.stories;
        if(!window.DATA) return base();
        var selected=categoryStories();
        var saved=window.DATA.stories;
        window.DATA.stories=selected;
        try{base();}finally{window.DATA.stories=saved;}
      }
      updateNewsCount();
    };
    wrapped.__gpCategoryWrapped=true;
    window.renderStories=wrapped;
  }
  function addAccessibility(){
    if(!document.querySelector('.gp-skip')){
      var a=document.createElement("a"); a.className="gp-skip"; a.href="#main"; a.textContent="Skip to dashboard"; document.body.prepend(a);
    }
    var main=qs("main")||qs(".wrap"); if(main && !main.id) main.id="main";
    qsa("button").forEach(function(b){ if(!b.getAttribute("aria-label") && !b.textContent.trim()) b.setAttribute("aria-label","Dashboard control"); });
  }
  function addKeyboard(){
    if(window.gpEnhanceKeyboard) return;
    window.gpEnhanceKeyboard=true;
    document.addEventListener("keydown",function(e){
      if(e.target && /input|textarea|select/i.test(e.target.tagName)) return;
      if(e.key==="r" || e.key==="R"){ e.preventDefault(); if(typeof window.gpForceRefresh==="function") window.gpForceRefresh(); else location.reload(); }
      if(e.key==="Escape") qsa(".drawer.open,.drawer-backdrop.open").forEach(function(x){x.classList.remove("open");});
    });
  }
  function run(){
    if(ready) return; ready=true; addStyles(); addAccessibility(); addStatus(); installNewsFilter(); addNewsCategories(); decorateStories(); addKeyboard();
    setInterval(function(){
      var bar=qs("#gp-production-status"), updated=window.DATA&&window.DATA.updatedAt;
      if(bar){var t=bar.querySelector("span:nth-child(2)");if(t){var stories=window.DATA&&Array.isArray(window.DATA.stories)?window.DATA.stories.length:"—";var markers=window.DATA&&Array.isArray(window.DATA.markers)?window.DATA.markers.length:"—";t.innerHTML='<strong>'+esc(relativeTime(updated)||"unknown")+'</strong> · '+stories+" stories · "+markers+" map signals";}}
      installNewsFilter();
      addNewsCategories();
      decorateStories();
      updateNewsCount();
    },15000);
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",run); else setTimeout(run,0);
})();
