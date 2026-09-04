/* Global Pulse — canonical page layout. Uses CSS order only; never reparents dynamic modules. */
(function(){
  'use strict';
  if(window.__GLOBAL_PULSE_LAYOUT__) return;
  window.__GLOBAL_PULSE_LAYOUT__=true;

  const sections=[
    ['breaking',10,['#breaking-intelligence','#breaking-news','[data-section="breaking"]']],
    ['changed',20,['#what-changed','[data-section="what-changed"]']],
    ['assessment',30,['#top']],
    ['conflicts',40,['#conflictSection','#active-conflicts','#conflict-watch','[data-section="conflicts"]']],
    ['evidence',50,['#event-intelligence','#investigation','[data-section="evidence"]']],
    ['map',60,['#mapSection','#global-map','#situation-map','[data-section="map"]']],
    ['regional',70,['#regional-intelligence','[data-section="regional"]']],
    ['reporting',80,['#newsSection','#latest-reporting','#news-feed','[data-section="reporting"]']],
    ['history',90,['#event-history','#historical-trends','[data-section="history"]']],
    ['markets',100,['#market-context','#markets','[data-section="markets"]']],
    ['graph',110,['.gp-intel-web-entry','#intelligence-web','#intelligence-graph','[data-section="graph"]']],
    ['watchlist',120,['#gp-watchlist','#watchlist','[data-section="watchlist"]']],
    ['sources',130,['#source-health','#sources-health','[data-section="source-health"]']]
  ];

  function apply(){
    const root=document.querySelector('.wrap');
    if(!root) return false;
    root.classList.add('gp-canonical-layout');
    let found=0;
    for(const [key,order,selectors] of sections){
      let el=null;
      for(const selector of selectors){
        try{el=root.querySelector(selector)}catch(_){el=null}
        if(el) break;
      }
      if(!el) continue;
      found++;
      el.dataset.gpLayoutKey=key;
      el.style.order=String(order);
      el.classList.add('gp-layout-section');
    }
    return found>0;
  }

  function boot(){
    apply();
    let queued=false;
    const schedule=()=>{
      if(queued) return;
      queued=true;
      requestAnimationFrame(()=>{queued=false;apply()});
    };
    const root=document.querySelector('.wrap')||document.body;
    new MutationObserver(schedule).observe(root,{childList:true,subtree:true});
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
