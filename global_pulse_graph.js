/* Global Pulse — evidence web visualization. */
(function(){
  'use strict';
  function esc(v){return String(v==null?'':v).replace(/[&<>\"]/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'})[c]||c})}
  function safeUrl(v){try{var u=new URL(String(v||''),location.href);return /^https?:$/.test(u.protocol)?u.href:''}catch(e){return ''}}
  function boot(){
    if(document.getElementById('gp-intel-web')) return;
    var g=window.DATA&&window.DATA.intelligenceGraph;
    if(!g||!g.nodes||!g.edges) return;
    var wrap=document.querySelector('.wrap'); if(!wrap) return;
    var sec=document.createElement('section'); sec.className='panel wide'; sec.id='gp-intel-web';
    sec.innerHTML='<div class="section-head"><div><h2>INTELLIGENCE WEB</h2><div class="muted">Evidence-linked relationships across politics, conflicts, economics and strategic reporting.</div></div><div class="gp-web-count">'+g.nodes.length+' nodes · '+g.edges.length+' links</div></div><div class="gp-web-controls"><input id="gp-web-search" placeholder="Search actor, country, issue…" aria-label="Search intelligence web"><select id="gp-web-kind" aria-label="Filter intelligence web"><option value="all">All categories</option><option value="actor">Actors</option><option value="political">Politics / alliances</option><option value="economic">Economics</option><option value="strategic">Strategic nodes</option></select><button id="gp-web-reset">Reset</button></div><div class="gp-web" id="gp-web-canvas"></div><div class="gp-web-detail" id="gp-web-detail">Tap a node to inspect its strongest reporting connections.</div><div class="gp-web-note">Connections mean the entities appeared together in public reporting or conflict records. A connection is not proof of causation, coordination, or alliance.</div>';
    var mapSection=document.getElementById('map')&&document.getElementById('map').closest('section');
    wrap.insertBefore(sec,mapSection||wrap.children[1]||null);
    var canvas=sec.querySelector('#gp-web-canvas'), search=sec.querySelector('#gp-web-search'), kind=sec.querySelector('#gp-web-kind');
    var nodes=g.nodes.slice(0,100), edges=g.edges.filter(function(e){return nodes.some(function(n){return n.label===e.source})&&nodes.some(function(n){return n.label===e.target})}).slice(0,190);
    var w=Math.max(320,canvas.clientWidth||900),h=450,cx=w/2,cy=h/2,pos={};
    function layout(){pos={};nodes.forEach(function(n,i){var a=i/Math.max(1,nodes.length)*Math.PI*2,r=Math.min(w,h)*.36;pos[n.label]={x:cx+Math.cos(a)*r,y:cy+Math.sin(a)*r*.72}})}
    layout();
    function render(){
      var q=(search.value||'').toLowerCase().trim(), k=kind.value;
      var visible=nodes.filter(function(n){return (!q||n.label.toLowerCase().indexOf(q)>=0)&& (k==='all'||(n.kind||'actor')===k)});
      var visSet=new Set(visible.map(function(n){return n.label}));
      var svg='<svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="Interactive intelligence relationship web">';
      edges.forEach(function(e){if(!visSet.has(e.source)||!visSet.has(e.target))return;var a=pos[e.source],b=pos[e.target];svg+='<line x1="'+a.x.toFixed(1)+'" y1="'+a.y.toFixed(1)+'" x2="'+b.x.toFixed(1)+'" y2="'+b.y.toFixed(1)+'" stroke="currentColor" stroke-opacity="'+Math.min(.7,.12+e.weight*.05)+'" stroke-width="'+Math.min(4,1+e.weight*.35)+'"/>'});
      visible.forEach(function(n){var p=pos[n.label],size=Math.min(14,5+Math.sqrt(n.mentions)*1.4),kindName=n.kind||'actor';svg+='<g class="gp-node" data-node="'+esc(n.label)+'" tabindex="0" aria-label="'+esc(n.label)+'"><circle cx="'+p.x.toFixed(1)+'" cy="'+p.y.toFixed(1)+'" r="'+size.toFixed(1)+'" class="gp-node-'+esc(kindName)+'"/><text x="'+p.x.toFixed(1)+'" y="'+(p.y+size+12).toFixed(1)+'" text-anchor="middle">'+esc(n.label)+'</text></g>'});
      svg+='</svg>';canvas.innerHTML=svg;
      canvas.querySelectorAll('.gp-node').forEach(function(el){var act=function(){detail(el.getAttribute('data-node'))};el.addEventListener('click',act);el.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();act()}})});
    }
    function detail(name){
      var links=edges.filter(function(e){return e.source===name||e.target===name}).sort(function(a,b){return b.weight-a.weight}).slice(0,8), html='<strong>'+esc(name)+'</strong> · '+links.length+' strongest connections';
      if(!links.length){sec.querySelector('#gp-web-detail').innerHTML=html+'<br><span>No linked evidence in the current snapshot.</span>';return}
      html+='<div class="gp-web-links">'+links.map(function(e){var other=e.source===name?e.target:e.source, ev=e.evidence||[], latest=ev[0], link=latest&&safeUrl(latest.url);return '<div class="gp-link-row"><span>'+esc(other)+' <b>'+e.weight+'×</b></span>'+(link?'<a href="'+esc(link)+'" target="_blank" rel="noopener noreferrer">Evidence ↗</a>':'')+(latest&&latest.title?'<small>'+esc(latest.source||'Public source')+' · '+esc(latest.title)+'</small>':'')+'</div>'}).join('')+'</div>';
      sec.querySelector('#gp-web-detail').innerHTML=html;
    }
    sec.querySelector('#gp-web-reset').onclick=function(){search.value='';kind.value='all';render()};
    search.addEventListener('input',render);kind.addEventListener('change',render);
    window.addEventListener('resize',function(){var nw=canvas.clientWidth;if(nw>300&&Math.abs(nw-w)>40){w=nw;cx=w/2;layout();render()}});
    render();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(boot,900)});else setTimeout(boot,900);
})();
