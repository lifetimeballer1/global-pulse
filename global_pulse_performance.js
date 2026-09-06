/* Global Pulse — Phase 7 mobile performance layer. */
(function(){
'use strict';
if(window.__GP_PERFORMANCE_V1__)return;
window.__GP_PERFORMANCE_V1__=true;

function idle(fn){
  if('requestIdleCallback' in window) window.requestIdleCallback(fn,{timeout:1200});
  else setTimeout(fn,80);
}

function lazyIntelWeb(){
  var frame=document.querySelector('.gp-intelweb-frame');
  if(!frame || frame.dataset.gpLazyReady==='1')return;
  frame.dataset.gpLazyReady='1';
  var src=frame.getAttribute('src');
  if(!src)return;
  frame.removeAttribute('src');
  var load=function(){
    if(frame.getAttribute('src'))return;
    frame.setAttribute('src',src);
  };
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){load();io.disconnect();}
      });
    },{rootMargin:'700px 0px'});
    io.observe(frame);
  }else{
    idle(load);
  }
}

function reduceMotion(){
  if(!window.matchMedia || !window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var style=document.createElement('style');
  style.id='gp-reduced-motion';
  style.textContent='*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}';
  document.head.appendChild(style);
}

function deferBelowFold(){
  var sections=[].slice.call(document.querySelectorAll('.gp-section'));
  if(!sections.length || !('contentVisibility' in document.documentElement.style))return;
  sections.forEach(function(section,i){
    if(i<2)return;
    section.style.contentVisibility='auto';
    section.style.containIntrinsicSize='1px 360px';
  });
}

function mark(){
  try{performance.mark('global-pulse-performance-ready');}catch(_){ }
}

function boot(){
  lazyIntelWeb();
  reduceMotion();
  idle(function(){deferBelowFold();mark();});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
else boot();
})();
