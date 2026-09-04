/* Global Pulse — stable loader for the intelligence web. */
(function(){
  'use strict';
  if(window.__GP_STABLE_LOADER__) return;
  window.__GP_STABLE_LOADER__=true;
  function load(){
    if(document.querySelector('script[data-gp-stable-renderer]')) return;
    var s=document.createElement('script');
    s.src='global_pulse_graph_stable.js?v=20260904';
    s.async=true;
    s.dataset.gpStableRenderer='1';
    document.head.appendChild(s);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',load,{once:true});
  else load();
})();