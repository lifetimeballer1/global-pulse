/* Global Pulse — evidence web visualization. */
(function(){
  'use strict';
  function esc(v){return String(v==null?'':v).replace(/[&<>\"]/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'})[c]})}
  function boot(){
    if(document.getElementById('gp-intel-web')) return;
    var g=window.DATA&&window.DATA.intelligenceGraph;
    if(!g||!g.nodes||!g.edges) return;
    var wrap=document.querySelector('.wrap'); if(!wrap) return;
    var sec=document.createElement('section'); sec.className='panel wide'; sec.id='gp-intel-web';
    sec.innerHTML='<div class="section-head"><div><h2>INTELLIGENCE WEB</h2><div class="muted">Evidence-linked relationships across politics, conflicts, economics and strategic reporting.</div></div><div class="gp-web-count">'+g.nodes.length+' nodes · '+g.edges.length+' links</div></div><div class="gp-web-controls"><input id="gp-web-search" placeholder="Search an actor, country, issue…" aria-label="Search intelligence web"><button id="gp-web-reset">Reset</button></div><div class="gp-web" id="gp-web-canvas"></div><div class="gp-web-detail" id="gp-web-detail">Tap a node to inspect its strongest reporting connections.</div><div class="gp-web-note">Connections mean the entities appeared together in public reporting or conflict records. A connection is not proof of causation, coordination, or alliance.</div>';
    var mapSection=document.getElementById('map')&&document.getElementById('map').closest('section');
    wrap.insertBefore(sec,mapSection||wrap.children[1]||null);
    var canvas=sec.querySelector('#gp-web-canvas'), search=sec.querySelector('#gp-web-search');
    var nodes=g.nodes.slice(0,90), edges=g.edges.filter(function(e){return nodes.some(function(n){return n.label===e.source})&&nodes.some(function(n){return n.label===e.target})}).slice(0,160);
    var w=canvas.clientWidth||900,h=440,cx=w/2,cy=h/2;
    var pos={}; nodes.forEach(function(n,i){var a=i/nodes.length*Math.PI*2; var r=Math.min(w,h)*.36;pos[n.label]={x:cx+Math.cos(a)*r,y:cy+Math.sin(a)*r*.72}});
    function render(filter){
      var q=(filter||'').toLowerCase();
      var visible=nodes.filter(function(n){return !q||n.label.toLowerCase().indexOf(q)>=0});
      var visSet=new Set(visible.map(function(n){return n.label}));
      var svg='<svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="Interactive intelligence relationship web">';
      edges.forEach(function(e){if(!visSet.has(e.source)||!visSet.has(e.target))return;var a=pos[e.source],b=pos[e.target];svg+='<line x1="'+a.x.toFixed(1)+'" y1="'+a.y.toFixed(1)+'" x2="'+b.x.toFixed(1)+'" y2="'+b.y.toFixed(1)+'" stroke="currentColor" stroke-opacity="'+Math.min(.7,.12+e.weight*.05)+'" stroke-width="'+Math.min(4,1+e.weight*.35)+'"/>'});
      visible.forEach(function(n){var p=pos[n.label],size=Math.min(13,5+Math.sqrt(n.mentions)*1.4),kind=n.kind||'actor';svg+='<g class="gp-node" data-node="'+esc(n.label)+'" tabindex="0"><circle cx="'+p.x.toFixed(1)+'" cy="'+p.y.toFixed(1)+'" r="'+size.toFixed(1)+'" class="gp-node-'+esc(kind)+'"/><text x="'+p.x.toFixed(1)+'" y="'+(p.y+size+12).toFixed(1)+'" text-anchor="middle">'+esc(n.label)+'</text></g>'});svg+='</svg>';canvas.innerHTML=svg;
      canvas.querySelectorAll('.gp-node').forEach(function(el){var act=function(){detail(el.getAttribute('data-node'))};el.addEventListener('click',act);el.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();act()}})});
    }
    function detail(name){var links=edges.filter(function(e){return e.source===name||e.target===name}).sort(function(a,b){return b.weight-a.weight}).slice(0,8);var box=sec.querySelector('#gp-web-detail');box.innerHTML='<strong>'+esc(name)+'</strong> · '+links.length+' strongest connections<br>'+links.map(function(e){var other=e.source===name?e.target:e.source;return '<span class="gp-link-row">'+esc(other)+' <b>'+e.weight+'×</b></span>'}).join('')||'<span>No linked evidence in the current snapshot.</span>'}
    sec.querySelector('#gp-web-reset').onclick=function(){search.value='';render('')};search.addEventListener('input',function(){render(search.value)});window.addEventListener('resize',function(){var nw=canvas.clientWidth;if(nw>300&&Math.abs(nw-w)>40){w=nw;cx=w/2;nodes.forEach(function(n,i){var a=i/nodes.length*Math.PI*2,r=Math.min(w,h)*.36;pos[n.label]={x:cx+Math.cos(a)*r,y:cy+Math.sin(a)*r*.72}});render(search.value)}});render('');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(boot,900)});else setTimeout(boot,900);
})();
