/* Global Pulse — stable dashboard helpers + Commander Center navigation. */
(function(){
  'use strict';
  if(window.__GP_STABLE_LOADER__) return;
  window.__GP_STABLE_LOADER__ = true;

  function loadWatchlist(){
    if(document.querySelector('script[data-gp-watchlist]')) return;
    var s=document.createElement('script');
    s.src='global_pulse_watchlist.js?v=1';
    s.async=true;
    s.dataset.gpWatchlist='1';
    document.head.appendChild(s);
  }

  function installRefresh(){
    if(document.getElementById('gp-minute-refresh')) return;
    var top=document.getElementById('top')||document.querySelector('header');
    if(!top) return;
    var style=document.createElement('style');
    style.id='gp-minute-refresh-css';
    style.textContent='#gp-minute-refresh{display:inline-flex;align-items:center;gap:6px;min-height:32px;padding:6px 9px;border:1px solid rgba(72,223,131,.32);border-radius:8px;background:rgba(72,223,131,.07);color:#48df83;font-size:9px;font-weight:900;letter-spacing:.06em;cursor:pointer;white-space:nowrap}#gp-minute-refresh.busy{opacity:.65;pointer-events:none}#gp-minute-refresh i{width:6px;height:6px;border-radius:50%;background:#48df83;box-shadow:0 0 8px #48df83}.gp-refresh-stamp{font-size:8px;color:#91a4b8;margin-left:2px;white-space:nowrap}@media(max-width:620px){#gp-minute-refresh{font-size:8px;padding:6px 7px}.gp-refresh-stamp{display:none}}';
    document.head.appendChild(style);
    var live=top.querySelector('.live'),btn=document.createElement('button');
    btn.id='gp-minute-refresh';btn.type='button';
    btn.innerHTML='<i></i><span>REFRESH DATA</span><span class="gp-refresh-stamp">LIVE SNAPSHOT</span>';
    (live||top).appendChild(btn);
    btn.addEventListener('click',async function(){
      if(btn.classList.contains('busy')) return;
      btn.classList.add('busy');
      var label=btn.querySelector('span');
      if(label) label.textContent='CHECKING…';
      try{
        if(typeof window.gpForceRefresh==='function') await Promise.resolve(window.gpForceRefresh());
        else{
          var r=await fetch('data/snapshot.json?refresh='+Date.now(),{cache:'no-store',headers:{'Cache-Control':'no-cache'}});
          if(!r.ok) throw Error('Snapshot '+r.status);
          window.DATA=await r.json();
          document.dispatchEvent(new CustomEvent('globalpulse:dataready',{detail:window.DATA}));
          if(typeof window.renderStories==='function') window.renderStories();
          if(typeof window.fetchPulseReporting==='function') window.fetchPulseReporting();
        }
        if(label) label.textContent='UPDATED';
        var stamp=btn.querySelector('.gp-refresh-stamp');
        if(stamp) stamp.textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
      }catch(e){
        if(label) label.textContent='RETRY';
        console.error('Global Pulse refresh failed',e);
      }finally{
        setTimeout(function(){btn.classList.remove('busy');if(label)label.textContent='REFRESH DATA'},1200);
      }
    });
  }

  function installCommandCenter(){
    if(document.getElementById('gp-command-center')) return;
    var wrap=document.querySelector('.wrap'),top=document.getElementById('top');
    if(!wrap||!top) return;

    var style=document.createElement('style');
    style.id='gp-command-center-css';
    style.textContent=`html,body{max-width:100%;overflow-x:hidden}
#gp-command-center{position:relative;display:grid;gap:12px;margin:0 0 14px;padding:14px;border:1px solid rgba(98,160,255,.28);border-radius:16px;background:linear-gradient(145deg,rgba(10,24,38,.99),rgba(6,14,23,.98));box-shadow:0 14px 42px rgba(0,0,0,.24);overflow:hidden}
#gp-command-center:before{content:"";position:absolute;inset:0 0 auto;height:2px;background:linear-gradient(90deg,#39ff88,#62a0ff,#aa8df7,#ffc857);opacity:.9}
.gp-command-head{display:flex;align-items:center;justify-content:space-between;gap:14px}.gp-command-kicker{font-size:8px;font-weight:950;letter-spacing:.18em;color:#62a0ff;text-transform:uppercase}.gp-command-title{font-size:19px;font-weight:950;line-height:1.08;margin-top:3px}.gp-command-sub{font-size:10px;color:#91a4b8;margin-top:4px;line-height:1.45;max-width:720px}.gp-command-live{display:inline-flex;align-items:center;gap:6px;padding:6px 9px;border-radius:999px;border:1px solid rgba(72,223,131,.24);background:rgba(72,223,131,.06);color:#48df83;font-size:8px;font-weight:950;letter-spacing:.08em;white-space:nowrap}.gp-command-live i{width:6px;height:6px;border-radius:50%;background:#48df83;box-shadow:0 0 8px #48df83}
.gp-command-label{font-size:8px;font-weight:900;letter-spacing:.13em;color:#91a4b8;text-transform:uppercase;margin:1px 0 0}.gp-command-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:7px}.gp-command-link{display:flex;align-items:center;justify-content:space-between;gap:7px;min-height:45px;padding:8px 9px;border:1px solid #1b2b3d;border-radius:10px;background:#08131e;color:#eef5ff;font-size:9px;font-weight:900;min-width:0;transition:transform .16s ease,border-color .16s ease,background .16s ease}.gp-command-link:hover{transform:translateY(-1px);border-color:rgba(98,160,255,.55);background:#0b1825}.gp-command-link.active{border-color:#62a0ff;background:rgba(98,160,255,.13);box-shadow:inset 0 0 0 1px rgba(98,160,255,.08)}.gp-command-link.primary{border-color:rgba(57,255,136,.38);background:linear-gradient(135deg,rgba(57,255,136,.10),rgba(8,19,30,.96));color:#39ff88}.gp-command-link span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.gp-command-link small{display:block;color:#91a4b8;font-size:7px;font-weight:650;margin-top:2px;overflow:hidden;text-overflow:ellipsis}.gp-command-arrow{font-size:12px;color:#62a0ff;flex:none}.gp-command-link.primary .gp-command-arrow{color:#39ff88}.gp-command-more{display:none}
@media(max-width:1050px){.gp-command-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:720px){#gp-command-center{padding:11px;margin-bottom:10px}.gp-command-title{font-size:16px}.gp-command-live{display:none}.gp-command-label{margin-top:0}.gp-command-grid{display:flex;overflow-x:auto;gap:7px;padding:1px 1px 4px;scroll-snap-type:x proximity;-webkit-overflow-scrolling:touch}.gp-command-link{flex:0 0 132px;min-height:43px;scroll-snap-align:start}.gp-command-link.primary{flex-basis:158px}.gp-command-more{display:block;font-size:8px;color:#91a4b8;text-align:right;margin-top:-3px}}
`;
    document.head.appendChild(style);

    var nav=document.createElement('section');
    nav.id='gp-command-center';
    nav.setAttribute('aria-label','Global Pulse Commander Center');
    nav.innerHTML='<div class="gp-command-head"><div><div class="gp-command-kicker">GLOBAL PULSE / COMMAND CENTER</div><div class="gp-command-title">Mission Control</div><div class="gp-command-sub">Jump directly to every intelligence layer, monitor the live picture, and move through the page without hunting for sections.</div></div><span class="gp-command-live"><i></i>LIVE SNAPSHOT</span></div><div class="gp-command-label">Jump to intelligence layer</div><nav class="gp-command-grid" aria-label="Page sections"></nav><div class="gp-command-more">Swipe horizontally for more sections →</div>';

    var defs=[
      ['assessment','Overview','Global pressure','#top','↗','primary'],
      ['breaking','Breaking','Immediate signals','#breaking-intelligence,#breaking-news,[data-section="breaking"]','↗',''],
      ['changed','What Changed','Latest shifts','#what-changed,[data-section="what-changed"]','↗',''],
      ['conflicts','Conflicts','Active watch','#conflictSection,#active-conflicts,#conflict-watch,[data-section="conflicts"]','↗',''],
      ['evidence','Evidence','Claims & proof','#event-intelligence,#investigation,[data-section="evidence"]','↗',''],
      ['map','War Map','Geospatial picture','#mapSection,#global-map,#situation-map,[data-section="map"]','↗',''],
      ['regional','Regional','Regional intelligence','#regional-intelligence,[data-section="regional"]','↗',''],
      ['reporting','Reporting','Current reporting','#newsSection,#latest-reporting,#news-feed,[data-section="reporting"]','↗',''],
      ['history','History','Trends & timeline','#event-history,#historical-trends,[data-section="history"]','↗',''],
      ['markets','Markets','Economic pressure','#market-context,#markets,[data-section="markets"]','↗',''],
      ['graph','Intelligence Web','Network & relationships','.gp-intel-web-entry,#intelligence-web,#intelligence-graph,[data-section="graph"]','↗','primary'],
      ['watchlist','Watchlist','Priority targets','#gp-watchlist,#watchlist,[data-section="watchlist"]','↗',''],
      ['sources','Sources','Source health','#source-health,#sources-health,[data-section="source-health"]','↗','']
    ];

    var grid=nav.querySelector('.gp-command-grid');
    defs.forEach(function(d){
      var a=document.createElement('a');
      a.className='gp-command-link '+(d[5]||'');
      a.dataset.commandKey=d[0];
      a.innerHTML='<span>'+d[1]+'<small>'+d[2]+'</small></span><b class="gp-command-arrow">'+d[4]+'</b>';
      a.dataset.selectors=d[3];
      a.addEventListener('click',function(ev){
        var selectors=a.dataset.selectors.split(',');
        var target=null;
        for(var i=0;i<selectors.length;i++){try{target=document.querySelector(selectors[i]);}catch(_){target=null}if(target)break}
        if(target){ev.preventDefault();target.scrollIntoView({behavior:'smooth',block:'start'});history.replaceState(null,'','#'+(target.id||d[0]));}
      });
      grid.appendChild(a);
    });

    wrap.insertBefore(nav,wrap.firstElementChild===top?top:wrap.firstElementChild);

    function markActive(){
      var links=[].slice.call(grid.querySelectorAll('.gp-command-link'));
      var best=null,bestDist=Infinity;
      links.forEach(function(a){
        var selectors=a.dataset.selectors.split(','),el=null;
        for(var i=0;i<selectors.length;i++){try{el=document.querySelector(selectors[i]);}catch(_){el=null}if(el)break}
        if(!el)return;
        var r=el.getBoundingClientRect(),dist=Math.abs(r.top-95);
        if(r.top<=150&&dist<bestDist){best=a;bestDist=dist}
      });
      links.forEach(function(a){a.classList.toggle('active',a===best)});
    }
    window.addEventListener('scroll',markActive,{passive:true});
    setTimeout(markActive,300);
  }

  function run(){loadWatchlist();installRefresh();installCommandCenter();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run,{once:true});
  else setTimeout(run,0);
})();
