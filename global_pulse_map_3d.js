(function(){
  'use strict';
  if(window.__GP_3D_GLOBE__) return;
  window.__GP_3D_GLOBE__ = true;

  var DATA_URL='data/snapshot.json';
  var state={markers:[],rot:0,tilt:-0.12,zoom:1,drag:false,lastX:0,lastY:0,auto:true,mode:'2d',raf:0,ready:false};
  var els={};

  function $(id){return document.getElementById(id)}
  function esc(v){return String(v==null?'':v).replace(/[&<>\"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}
  function num(v){var n=Number(v);return Number.isFinite(n)?n:null}
  function normalizeMarkers(d){
    var out=[];
    (Array.isArray(d.markers)?d.markers:[]).forEach(function(m,i){
      var lat=num(m.lat!=null?m.lat:m.latitude), lng=num(m.lng!=null?m.lng:(m.lon!=null?m.lon:m.longitude));
      if(lat===null||lng===null||lat<-90||lat>90||lng<-180||lng>180) return;
      out.push({id:m.id||('m-'+i),lat:lat,lng:lng,title:m.title||m.name||'Intelligence signal',source:m.source||m.sourceLabel||'Global Pulse',type:m.type||m.eventType||'signal',region:m.region||'',url:m.url||m.sourceUrl||'',confidence:m.confidence||''});
    });
    var o=d.osintMaps||{};
    ['gdeltPoints','reportedAreaPoints'].forEach(function(k){
      (Array.isArray(o[k])?o[k]:[]).forEach(function(m,i){
        var lat=num(m.lat),lng=num(m.lng!=null?m.lng:m.lon); if(lat===null||lng===null) return;
        out.push({id:m.id||('o-'+k+'-'+i),lat:lat,lng:lng,title:m.title||m.name||'OSINT report',source:m.source||'OSINT',type:m.type||m.eventType||'osint',region:m.region||'',url:m.url||m.sourceUrl||'',confidence:m.confidence||''});
      });
    });
    var seen={}; return out.filter(function(m){var k=m.id+'|'+m.lat.toFixed(4)+'|'+m.lng.toFixed(4);if(seen[k])return false;seen[k]=1;return true}).slice(0,2500);
  }

  function inject(){
    var map=$('map'); if(!map||$('gp-3d-map-wrap')) return;
    var host=map.parentElement; if(!host) return;
    var wrap=document.createElement('div'); wrap.id='gp-3d-map-wrap'; wrap.className='gp-3d-wrap';
    wrap.innerHTML='<div class="gp-3d-toolbar">'
      +'<button type="button" id="gp-3d-toggle">3D Globe</button>'
      +'<button type="button" id="gp-3d-auto">Auto rotate: ON</button>'
      +'<button type="button" id="gp-3d-reset">Reset view</button>'
      +'<span id="gp-3d-count">Loading globe data…</span>'
      +'</div>'
      +'<div class="gp-3d-stage" id="gp-3d-stage">'
      +'<canvas id="gp-3d-canvas" aria-label="Interactive 3D global intelligence globe"></canvas>'
      +'<div class="gp-3d-hint">Drag to rotate · pinch/scroll to zoom · tap a point for details</div>'
      +'</div>'
      +'<div id="gp-3d-detail" class="gp-3d-detail" hidden></div>';
    host.insertBefore(wrap,map);
    els.wrap=wrap;els.canvas=$('gp-3d-canvas');els.stage=$('gp-3d-stage');els.detail=$('gp-3d-detail');
    bind(); resize(); requestAnimationFrame(draw);
  }

  function bind(){
    $('gp-3d-toggle').addEventListener('click',function(){
      state.mode=state.mode==='3d'?'2d':'3d';
      $('gp-3d-toggle').classList.toggle('active',state.mode==='3d');
      $('gp-3d-toggle').textContent=state.mode==='3d'?'2D Map':'3D Globe';
      els.stage.classList.toggle('active',state.mode==='3d');
      $('map').classList.toggle('gp-2d-hidden',state.mode==='3d');
      if(state.mode==='3d') setTimeout(resize,20);
    });
    $('gp-3d-auto').addEventListener('click',function(){state.auto=!state.auto;this.textContent='Auto rotate: '+(state.auto?'ON':'OFF');this.classList.toggle('active',state.auto)});
    $('gp-3d-reset').addEventListener('click',function(){state.rot=0;state.tilt=-0.12;state.zoom=1});
    var c=els.canvas;
    c.addEventListener('pointerdown',function(e){state.drag=true;state.lastX=e.clientX;state.lastY=e.clientY;c.setPointerCapture(e.pointerId)});
    c.addEventListener('pointermove',function(e){if(!state.drag)return;var dx=e.clientX-state.lastX,dy=e.clientY-state.lastY;state.rot+=dx*0.006;state.tilt=Math.max(-1.05,Math.min(1.05,state.tilt+dy*0.004));state.lastX=e.clientX;state.lastY=e.clientY;state.auto=false;$('gp-3d-auto').textContent='Auto rotate: OFF';$('gp-3d-auto').classList.remove('active')});
    c.addEventListener('pointerup',function(){state.drag=false});c.addEventListener('pointercancel',function(){state.drag=false});
    c.addEventListener('wheel',function(e){e.preventDefault();state.zoom=Math.max(.72,Math.min(1.65,state.zoom*(e.deltaY<0?1.08:.93)))},{passive:false});
    c.addEventListener('click',pick);
    window.addEventListener('resize',resize,{passive:true});
    document.addEventListener('globalpulse:dataready',load,{passive:true});
  }

  function resize(){if(!els.canvas)return;var r=els.stage.getBoundingClientRect(),d=Math.min(window.devicePixelRatio||1,2);els.canvas.width=Math.max(1,Math.floor(r.width*d));els.canvas.height=Math.max(1,Math.floor(r.height*d));els.canvas.style.width=r.width+'px';els.canvas.style.height=r.height+'px'}
  function project(m,w,h){
    var lon=(m.lng*Math.PI/180)+state.rot,lat=m.lat*Math.PI/180;
    var x=Math.cos(lat)*Math.sin(lon), y=Math.sin(lat), z=Math.cos(lat)*Math.cos(lon);
    var ct=Math.cos(state.tilt),st=Math.sin(state.tilt), yy=y*ct-z*st, zz=y*st+z*ct;
    return {x:x,y:yy,z:zz,visible:zz>0,px:w/2+x*Math.min(w,h)*.42*state.zoom,py:h/2-yy*Math.min(w,h)*.42*state.zoom};
  }
  function draw(){
    if(!els.canvas){requestAnimationFrame(draw);return}
    var c=els.canvas,ctx=c.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2),w=c.width/d,h=c.height/d;ctx.setTransform(d,0,0,d,0,0);ctx.clearRect(0,0,w,h);
    var cx=w/2,cy=h/2,R=Math.min(w,h)*.42*state.zoom;
    var g=ctx.createRadialGradient(cx-R*.35,cy-R*.45,R*.05,cx,cy,R*1.2);g.addColorStop(0,'#173b5a');g.addColorStop(.55,'#0a2032');g.addColorStop(1,'#03080d');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
    ctx.save();ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.clip();
    ctx.fillStyle='#071723';ctx.fillRect(cx-R,cy-R,R*2,R*2);
    grid(ctx,cx,cy,R); dots(ctx,cx,cy,R); markers(ctx,w,h);
    ctx.restore();
    ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.strokeStyle='rgba(98,160,255,.45)';ctx.lineWidth=1.5;ctx.stroke();
    ctx.beginPath();ctx.arc(cx-R*.12,cy-R*.16,R*1.04,Math.PI*1.05,Math.PI*1.65);ctx.strokeStyle='rgba(255,255,255,.12)';ctx.stroke();
    if(state.auto&&!state.drag)state.rot+=0.0008;
    state.raf=requestAnimationFrame(draw);
  }
  function grid(ctx,cx,cy,R){
    ctx.strokeStyle='rgba(98,160,255,.12)';ctx.lineWidth=1;
    for(var lat=-60;lat<=60;lat+=30){var rr=R*Math.cos(lat*Math.PI/180);ctx.beginPath();ctx.ellipse(cx,cy,R*Math.max(.08,Math.cos(lat*Math.PI/180)),rr,0,0,Math.PI*2);ctx.stroke()}
    for(var lon=-150;lon<=150;lon+=30){var x=R*Math.sin((lon*Math.PI/180)+state.rot);var width=R*Math.cos((lon*Math.PI/180)+state.rot);ctx.beginPath();ctx.ellipse(cx+x,cy,width*.18,R,0,0,Math.PI*2);ctx.stroke()}
    ctx.strokeStyle='rgba(72,223,131,.15)';ctx.beginPath();ctx.ellipse(cx,cy,R*.98,R*.28,state.tilt,0,Math.PI*2);ctx.stroke();
  }
  function dots(ctx,cx,cy,R){for(var i=0;i<90;i++){var a=i*2.399,b=(i%13)/13;var x=Math.cos(a)*R*(.2+.75*b),y=Math.sin(a)*R*(.2+.75*b);ctx.fillStyle='rgba(150,190,220,'+(0.06+.05*(i%4))+')';ctx.fillRect(cx+x,cy+y,1,1)}}
  function markerColor(m){var t=String(m.type).toLowerCase();if(/conflict|attack|war|military|terror/.test(t))return '#ff6678';if(/economic|market|finance/.test(t))return '#ffc857';if(/politic|diplom/.test(t))return '#aa8df7';if(/hazard|quake|storm|climate/.test(t))return '#48df83';return '#62a0ff'}
  function markers(ctx,w,h){
    var visible=[];state.markers.forEach(function(m){var p=project(m,w,h);if(!p.visible)return;visible.push({m:m,p:p});});
    visible.sort(function(a,b){return a.p.z-b.p.z});visible.forEach(function(o){var m=o.m,p=o.p,s=Math.max(2.2,Math.min(7,3.2*(.72+p.z)));ctx.globalAlpha=.25;ctx.fillStyle=markerColor(m);ctx.beginPath();ctx.arc(p.px,p.py,s*2.8,0,Math.PI*2);ctx.fill();ctx.globalAlpha=.9;ctx.fillStyle=markerColor(m);ctx.beginPath();ctx.arc(p.px,p.py,s,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1});
    ctx.fillStyle='#91a4b8';ctx.font='10px system-ui';ctx.fillText('LIVE INTELLIGENCE GLOBE',12,18);ctx.fillText((state.markers.length||0)+' mapped signals',12,33);
  }
  function pick(e){if(!state.markers.length)return;var r=els.canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,best=null,bd=18;state.markers.forEach(function(m){var p=project(m,r.width,r.height);if(!p.visible)return;var dist=Math.hypot(p.px-x,p.py-y);if(dist<bd){bd=dist;best=m}});if(!best)return;els.detail.hidden=false;els.detail.innerHTML='<strong>'+esc(best.title)+'</strong><div>'+esc(best.region||'Global')+' · '+esc(best.source)+' · '+esc(best.type)+'</div>'+(best.confidence?'<div>Confidence: '+esc(best.confidence)+'</div>':'')+(best.url?'<a href="'+esc(best.url)+'" target="_blank" rel="noopener">Open source →</a>':'')}
  async function load(){try{var r=await fetch(DATA_URL+'?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);var d=await r.json();state.markers=normalizeMarkers(d);state.ready=true;var count=$('gp-3d-count');if(count)count.textContent=state.markers.length+' mapped signals · no API key';}catch(e){var count=$('gp-3d-count');if(count)count.textContent='Globe waiting for snapshot data';}}

  function start(){inject();load()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
