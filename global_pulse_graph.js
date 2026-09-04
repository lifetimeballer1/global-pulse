/* Global Pulse — stable intelligence-web loader + command-center layout cleanup. */
/* Deployment trigger: keep the embedded Intelligence Web renderer changes in production. */
(function(){
  'use strict';
  if(window.__GP_STABLE_LOADER__) return;
  window.__GP_STABLE_LOADER__=true;

  function loadStableRenderer(){
    if(document.querySelector('script[data-gp-stable-renderer]')) return;
    var s=document.createElement('script');
    s.src='global_pulse_graph_pro.js?v=20260903a';
    s.async=true;
    s.dataset.gpStableRenderer='1';
    document.head.appendChild(s);
  }

  function installCommandCenter(){
    if(document.getElementById('gp-command-center')) return;
    var wrap=document.querySelector('.wrap');
    var top=document.getElementById('top');
    if(!wrap || !top) return;

    var style=document.createElement('style');
    style.id='gp-command-center-css';
    style.textContent='\
#gp-command-center{display:grid;gap:10px;margin:0 0 14px;padding:13px 14px;border:1px solid rgba(98,160,255,.28);border-radius:15px;background:linear-gradient(135deg,rgba(10,24,38,.98),rgba(6,15,24,.98));box-shadow:0 12px 38px rgba(0,0,0,.22)}\
.gp-command-head{display:flex;align-items:center;justify-content:space-between;gap:12px}\
.gp-command-kicker{font-size:9px;font-weight:900;letter-spacing:.16em;color:#62a0ff;text-transform:uppercase}\
.gp-command-title{font-size:18px;font-weight:950;line-height:1.1;margin-top:3px}\
.gp-command-sub{font-size:10px;color:#91a4b8;margin-top:4px;line-height:1.45}\
.gp-command-live{display:inline-flex;align-items:center;gap:6px;padding:5px 8px;border-radius:999px;border:1px solid rgba(72,223,131,.22);background:rgba(72,223,131,.06);color:#48df83;font-size:8px;font-weight:900;letter-spacing:.08em;white-space:nowrap}\
.gp-command-live i{width:6px;height:6px;border-radius:50%;background:#48df83;box-shadow:0 0 0 3px rgba(72,223,131,.09)}\
.gp-command-grid{display:grid;grid-template-columns:minmax(0,1.35fr) repeat(4,minmax(90px,1fr));gap:7px}\
.gp-command-link{display:flex;align-items:center;justify-content:space-between;gap:7px;min-height:42px;padding:8px 10px;border:1px solid #1b2b3d;border-radius:9px;background:#08131e;color:#eef5ff;font-size:10px;font-weight:850;transition:transform .14s ease,border-color .14s ease,background .14s ease}\
.gp-command-link:hover{transform:translateY(-1px);border-color:rgba(98,160,255,.55);background:#0b1a29}\
.gp-command-link.primary{border-color:rgba(57,255,136,.35);background:linear-gradient(135deg,rgba(57,255,136,.09),rgba(8,19,30,.96));color:#39ff88}\
.gp-command-link small{display:block;color:#91a4b8;font-size:8px;font-weight:650;margin-top:2px}\
.gp-command-arrow{font-size:14px;color:#62a0ff}\
.gp-intel-web-entry{margin:0!important;width:100%}\
.gp-intel-web-entry>a{display:flex!important;align-items:center;justify-content:space-between;gap:10px;width:100%;min-height:54px;padding:11px 13px!important;border:1px solid rgba(57,255,136,.38)!important;border-radius:11px!important;background:linear-gradient(135deg,rgba(57,255,136,.10),rgba(6,16,24,.98))!important;color:#39ff88!important;box-shadow:0 8px 28px rgba(0,0,0,.18);font-size:11px!important;font-weight:950!important;letter-spacing:.08em!important}\
.gp-intel-web-entry>a:after{content:"OPEN 3D WEB  →";font-size:9px;letter-spacing:.06em;color:#d8ffe8;opacity:.85}\
.gp-priority-label{font-size:8px;color:#91a4b8;letter-spacing:.08em;text-transform:uppercase;margin-top:1px}\
@media(max-width:900px){.gp-command-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.gp-command-link.primary{grid-column:span 2}}\
@media(max-width:620px){#gp-command-center{padding:11px}.gp-command-title{font-size:16px}.gp-command-live{display:none}.gp-command-grid{grid-template-columns:1fr 1fr}.gp-command-link.primary{grid-column:span 2}.gp-command-link{min-height:40px;font-size:9px}.gp-command-link small{display:none}.gp-intel-web-entry>a{min-height:50px;font-size:10px!important}.gp-intel-web-entry>a:after{font-size:8px}}';
    document.head.appendChild(style);

    var intel=document.querySelector('.gp-intel-web-entry');
    if(intel){
      top.parentNode.insertBefore(intel,top.nextSibling);
      intel.innerHTML='<a href="intelligence-web.html" aria-label="Open 3D Intelligence Web"><span>◈ INTELLIGENCE WEB — 3D</span><span class="gp-priority-label">Evidence-linked relationships · draggable nodes · source-backed analysis</span></a>';
    }

    var nav=document.createElement('section');
    nav.id='gp-command-center';
    nav.setAttribute('aria-label','Global Pulse priority navigation');
    nav.innerHTML='<div class="gp-command-head"><div><div class="gp-command-kicker">COMMAND CENTER</div><div class="gp-command-title">What matters now</div><div class="gp-command-sub">Start with the network, then move from global pressure to the map, conflicts and reporting.</div></div><span class="gp-command-live"><i></i>LIVE SNAPSHOT</span></div><div class="gp-command-grid"><a class="gp-command-link primary" href="intelligence-web.html"><span>◈ Intelligence Web<small>Relationships &amp; evidence</small></span><b class="gp-command-arrow">→</b></a><a class="gp-command-link" href="#top"><span>Global Index<small>World pressure</small></span><b class="gp-command-arrow">↗</b></a><a class="gp-command-link" href="#mapSection"><span>Situation Map<small>Geospatial signals</small></span><b class="gp-command-arrow">↗</b></a><a class="gp-command-link" href="#conflictSection"><span>Conflicts<small>Active watch</small></span><b class="gp-command-arrow">↗</b></a><a class="gp-command-link" href="#newsSection"><span>Reporting<small>Current signals</small></span><b class="gp-command-arrow">↗</b></a></div></section>';
    wrap.insertBefore(nav,wrap.firstElementChild===top?top:wrap.firstElementChild);

    var status=document.getElementById('gp-production-status');
    if(status) status.style.marginBottom='0';
  }

  function run(){
    loadStableRenderer();
    installCommandCenter();
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',run,{once:true});
  }else{
    setTimeout(run,0);
  }
})();
