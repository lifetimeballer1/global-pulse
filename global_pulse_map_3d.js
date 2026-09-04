(function(){
  'use strict';
  if(window.__GP_3D_GLOBE__) return;
  window.__GP_3D_GLOBE__ = true;

  var DATA_URL='data/snapshot.json';
  var state={markers:[],rot:-0.55,tilt:-0.16,zoom:1,drag:false,lastX:0,lastY:0,auto:true,mode:'2d',raf:0,ready:false,pulse:0,hover:null};
  var els={};

  function $(id){return document.getElementById(id)}
  function esc(v){return String(v==null?'':v).replace(/[&<>\"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}
  function num(v){var n=Number(v);return Number.isFinite(n)?n:null}

  function normalizeMarkers(d){
    var out=[];
    function add(m,i,prefix){
      var lat=num(m.lat!=null?m.lat:m.latitude), lng=num(m.lng!=null?m.lng:(m.lon!=null?m.lon:m.longitude));
      if(lat===null||lng===null||lat<-90||lat>90||lng<-180||lng>180)return;
      out.push({id:m.id||((prefix||'m')+'-'+i),lat:lat,lng:lng,title:m.title||m.name||'Intelligence signal',source:m.source||m.sourceLabel||'Global Pulse',type:m.type||m.eventType||m.layer||'signal',region:m.region||'',url:m.url||m.sourceUrl||'',confidence:m.confidence||'',detail:m.detail||m.description||''});
    }
    (Array.isArray(d&&d.markers)?d.markers:[]).forEach(function(m,i){add(m,i,'m')});
    var o=(d&&d.osintMaps)||{};
    ['gdeltPoints','reportedAreaPoints'].forEach(function(k){(Array.isArray(o[k])?o[k]:[]).forEach(function(m,i){add(m,i,'o-'+k)})});
    var seen={};
    return out.filter(function(m){var k=m.id+'|'+m.lat.toFixed(4)+'|'+m.lng.toFixed(4);if(seen[k])return false;seen[k]=1;return true}).slice(0,3000);
  }

  function inject(){
    var map=$('map');if(!map||$('gp-3d-map-wrap'))return;
    var host=map.parentElement;if(!host)return;
    var wrap=document.createElement('div');wrap.id='gp-3d-map-wrap';wrap.className='gp-3d-wrap';
    wrap.innerHTML='<div class="gp-3d-toolbar">'
      +'<button type="button" id="gp-3d-toggle">◉ 3D GLOBE</button>'
      +'<button type="button" id="gp-3d-auto">AUTO ROTATE: ON</button>'
      +'<button type="button" id="gp-3d-reset">RESET</button>'
      +'<span id="gp-3d-count">INITIALIZING GLOBAL GRID…</span>'
      +'</div>'
      +'<div class="gp-3d-stage" id="gp-3d-stage">'
      +'<canvas id="gp-3d-canvas" aria-label="Interactive Matrix-style 3D global intelligence globe"></canvas>'
      +'<div class="gp-3d-hud"><span>GLOBAL PULSE // LIVE INTELLIGENCE</span><span id="gp-3d-clock">--:--:--</span></div>'
      +'<div class="gp-3d-hint">DRAG TO ROTATE · PINCH / SCROLL TO ZOOM · TAP A SIGNAL</div>'
      +'</div>'
      +'<div id="gp-3d-detail" class="gp-3d-detail" hidden></div>';
    host.insertBefore(wrap,map);
    els.wrap=wrap;els.canvas=$('gp-3d-canvas');els.stage=$('gp-3d-stage');els.detail=$('gp-3d-detail');
    bind();resize();requestAnimationFrame(draw);
  }

  function bind(){
    $('gp-3d-toggle').addEventListener('click',function(){
      state.mode=state.mode==='3d'?'2d':'3d';
      this.classList.toggle('active',state.mode==='3d');
      this.textContent=state.mode==='3d'?'◉ 2D MAP':'◉ 3D GLOBE';
      els.stage.classList.toggle('active',state.mode==='3d');
      $('map').classList.toggle('gp-2d-hidden',state.mode==='3d');
      if(state.mode==='3d'){resize();setTimeout(resize,60);setTimeout(resize,300)}
      if(state.mode==='2d'&&window.gpGlobalMap)setTimeout(function(){window.gpGlobalMap.invalidateSize()},60);
    });
    $('gp-3d-auto').addEventListener('click',function(){state.auto=!state.auto;this.textContent='AUTO ROTATE: '+(state.auto?'ON':'OFF');this.classList.toggle('active',state.auto)});
    $('gp-3d-reset').addEventListener('click',function(){state.rot=-0.55;state.tilt=-0.16;state.zoom=1});
    var c=els.canvas;
    c.addEventListener('pointerdown',function(e){state.drag=true;state.lastX=e.clientX;state.lastY=e.clientY;c.setPointerCapture(e.pointerId)});
    c.addEventListener('pointermove',function(e){if(!state.drag)return;var dx=e.clientX-state.lastX,dy=e.clientY-state.lastY;state.rot+=dx*0.006;state.tilt=Math.max(-1.05,Math.min(1.05,state.tilt+dy*0.004));state.lastX=e.clientX;state.lastY=e.clientY;state.auto=false;$('gp-3d-auto').textContent='AUTO ROTATE: OFF';$('gp-3d-auto').classList.remove('active')});
    c.addEventListener('pointerup',function(){state.drag=false});c.addEventListener('pointercancel',function(){state.drag=false});
    c.addEventListener('wheel',function(e){e.preventDefault();state.zoom=Math.max(.72,Math.min(1.55,state.zoom*(e.deltaY<0?1.08:.93)))},{passive:false});
    c.addEventListener('click',pick);
    window.addEventListener('resize',resize,{passive:true});
    if(window.ResizeObserver)new ResizeObserver(resize).observe(els.stage);
    document.addEventListener('globalpulse:dataready',load,{passive:true});
  }

  function resize(){
    if(!els.canvas||!els.stage)return;
    var r=els.stage.getBoundingClientRect();
    var w=Math.max(280,r.width||280),h=Math.max(280,r.height||280),d=Math.min(window.devicePixelRatio||1,2);
    els.canvas.width=Math.floor(w*d);els.canvas.height=Math.floor(h*d);els.canvas.style.width=w+'px';els.canvas.style.height=h+'px';
  }

  function project(m,w,h){
    var lon=(m.lng*Math.PI/180)+state.rot,lat=m.lat*Math.PI/180;
    var x=Math.cos(lat)*Math.sin(lon),y=Math.sin(lat),z=Math.cos(lat)*Math.cos(lon);
    var ct=Math.cos(state.tilt),st=Math.sin(state.tilt),yy=y*ct-z*st,zz=y*st+z*ct;
    var R=Math.min(w,h)*.40*state.zoom;
    return {x:x,y:yy,z:zz,visible:zz>-0.015,px:w/2+x*R,py:h/2-yy*R};
  }

  function typeColor(m){
    var t=String(m.type||'').toLowerCase();
    if(/conflict|attack|war|military|terror|battle/.test(t))return '#ff365f';
    if(/economic|market|finance|trade|energy/.test(t))return '#ffd447';
    if(/politic|diplom|government/.test(t))return '#b77cff';
    if(/hazard|quake|storm|climate|environment/.test(t))return '#49ff9a';
    if(/osint|report|social/.test(t))return '#3fffc7';
    return '#54b8ff';
  }

  function draw(){
    if(!els.canvas){requestAnimationFrame(draw);return}
    var c=els.canvas,ctx=c.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2),w=c.width/d,h=c.height/d;
    if(w<10||h<10){requestAnimationFrame(draw);return}
    ctx.setTransform(d,0,0,d,0,0);ctx.clearRect(0,0,w,h);
    state.pulse+=0.025;
    drawBackground(ctx,w,h);
    var cx=w/2,cy=h/2,R=Math.min(w,h)*.40*state.zoom;
    drawGlow(ctx,cx,cy,R);
    ctx.save();ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.clip();
    drawDigitalSurface(ctx,cx,cy,R);
    drawGrid(ctx,cx,cy,R);
    drawSignalField(ctx,cx,cy,R);
    drawMarkers(ctx,w,h);
    ctx.restore();
    drawRim(ctx,cx,cy,R);
    drawHud(ctx,w,h);
    if(state.auto&&!state.drag)state.rot+=0.00075;
    var clock=$('gp-3d-clock');if(clock)clock.textContent=new Date().toLocaleTimeString([], {hour12:false});
    state.raf=requestAnimationFrame(draw);
  }

  function drawBackground(ctx,w,h){
    ctx.fillStyle='#020706';ctx.fillRect(0,0,w,h);
    var g=ctx.createRadialGradient(w*.5,h*.45,0,w*.5,h*.5,Math.max(w,h)*.75);g.addColorStop(0,'#06251d');g.addColorStop(.45,'#031611');g.addColorStop(1,'#010303');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
    for(var i=0;i<75;i++){var x=(i*83.17)%w,y=(i*47.31)%h,a=.10+.08*Math.sin(state.pulse+i);ctx.fillStyle='rgba(80,255,160,'+a.toFixed(3)+')';ctx.fillRect(x,y,1,1)}
    ctx.strokeStyle='rgba(73,255,154,.025)';ctx.lineWidth=1;
    for(var sy=0;sy<h;sy+=4){ctx.beginPath();ctx.moveTo(0,sy+.5);ctx.lineTo(w,sy+.5);ctx.stroke()}
  }

  function drawGlow(ctx,cx,cy,R){
    var g=ctx.createRadialGradient(cx-R*.2,cy-R*.28,R*.08,cx,cy,R*1.18);g.addColorStop(0,'rgba(25,255,150,.24)');g.addColorStop(.45,'rgba(10,120,80,.12)');g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,R*1.18,0,Math.PI*2);ctx.fill();
  }

  function drawDigitalSurface(ctx,cx,cy,R){
    ctx.fillStyle='#03130f';ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='rgba(70,255,160,.045)';
    for(var i=0;i<220;i++){
      var a=i*2.399963,b=(i%31)/31,rr=R*(.08+.84*b),x=Math.cos(a)*rr,y=Math.sin(a)*rr;
      ctx.fillRect(cx+x,cy+y,1+(i%3),1+(i%2));
    }
  }

  function drawGrid(ctx,cx,cy,R){
    ctx.strokeStyle='rgba(63,255,157,.18)';ctx.lineWidth=1;
    for(var lat=-75;lat<=75;lat+=15){var a=lat*Math.PI/180;ctx.beginPath();ctx.ellipse(cx,cy,R*Math.max(.035,Math.cos(a)),R*Math.max(.035,Math.abs(Math.sin(a))),0,0,Math.PI*2);ctx.stroke()}
    for(var lon=-150;lon<=150;lon+=15){var a=(lon*Math.PI/180)+state.rot;var sx=Math.sin(a),cw=Math.cos(a);ctx.beginPath();ctx.ellipse(cx+sx*R*.012,cy,cw*R,R,0,0,Math.PI*2);ctx.stroke()}
    ctx.strokeStyle='rgba(77,255,170,.32)';ctx.beginPath();ctx.ellipse(cx,cy,R*.99,R*.27,state.tilt,0,Math.PI*2);ctx.stroke();
  }

  function drawSignalField(ctx,cx,cy,R){
    for(var i=0;i<26;i++){
      var a=i*.83+state.pulse*.35,rr=R*(.25+.6*((i*17)%100)/100),x=cx+Math.cos(a)*rr,y=cy+Math.sin(a)*rr*.55;
      ctx.fillStyle='rgba(71,255,160,.16)';ctx.fillRect(x,y,2,2);
    }
  }

  function drawMarkers(ctx,w,h){
    var visible=[];state.markers.forEach(function(m){var p=project(m,w,h);if(p.visible)visible.push({m:m,p:p})});
    visible.sort(function(a,b){return a.p.z-b.p.z});
    visible.forEach(function(o){
      var col=typeColor(o.m),s=Math.max(2.2,Math.min(7,2.6+3.2*Math.max(0,o.p.z))),pulse=(Math.sin(state.pulse*2+o.p.px*.01)+1)*.5;
      ctx.globalAlpha=.10+.10*pulse;ctx.fillStyle=col;ctx.beginPath();ctx.arc(o.p.px,o.p.py,s*(3+pulse*2),0,Math.PI*2);ctx.fill();
      ctx.globalAlpha=.9;ctx.fillStyle=col;ctx.beginPath();ctx.arc(o.p.px,o.p.py,s,0,Math.PI*2);ctx.fill();
      if(s>3.2){ctx.globalAlpha=.32;ctx.strokeStyle=col;ctx.beginPath();ctx.arc(o.p.px,o.p.py,s*(2.2+pulse),0,Math.PI*2);ctx.stroke()}
    });
    ctx.globalAlpha=1;
  }

  function drawRim(ctx,cx,cy,R){
    ctx.shadowBlur=18;ctx.shadowColor='rgba(66,255,156,.55)';ctx.strokeStyle='rgba(75,255,163,.72)';ctx.lineWidth=1.2;ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.stroke();ctx.shadowBlur=0;
    ctx.strokeStyle='rgba(255,255,255,.08)';ctx.beginPath();ctx.arc(cx-R*.13,cy-R*.16,R*1.025,Math.PI*1.05,Math.PI*1.65);ctx.stroke();
  }

  function drawHud(ctx,w,h){
    ctx.fillStyle='rgba(73,255,160,.72)';ctx.font='10px ui-monospace,SFMono-Regular,Menlo,monospace';ctx.fillText('GLOBAL PULSE // 3D SIGNAL MATRIX',12,18);ctx.fillText(String(state.markers.length)+' SIGNALS',12,32);
    ctx.textAlign='right';ctx.fillStyle='rgba(73,255,160,.5)';ctx.fillText(state.ready?'DATA LINK: ONLINE':'DATA LINK: CONNECTING',w-12,18);ctx.textAlign='left';
  }

  function pick(e){
    if(!state.markers.length)return;
    var r=els.canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,best=null,bd=24;
    state.markers.forEach(function(m){var p=project(m,r.width,r.height);if(!p.visible)return;var dist=Math.hypot(p.px-x,p.py-y);if(dist<bd){bd=dist;best=m}});
    if(!best)return;
    els.detail.hidden=false;
    var url=best.url&&/^https?:\/\//i.test(best.url)?'<a href="'+esc(best.url)+'" target="_blank" rel="noopener noreferrer">OPEN SOURCE ↗</a>':'';
    els.detail.innerHTML='<strong>'+esc(best.title)+'</strong><div>'+esc(best.region||'Global')+' · '+esc(best.source)+' · '+esc(best.type)+'</div>'+(best.confidence?'<div>Confidence: '+esc(best.confidence)+'</div>':'')+(best.detail?'<div>'+esc(best.detail)+'</div>':'')+url;
  }

  async function load(){
    try{
      var d=null;
      if(window.DATA&&typeof window.DATA==='object')d=window.DATA;
      if(!d){var r=await fetch(DATA_URL+'?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);d=await r.json()}
      var next=normalizeMarkers(d);
      if(next.length||!state.markers.length)state.markers=next;
      state.ready=true;
      var count=$('gp-3d-count');if(count)count.textContent=state.markers.length+' SIGNALS · NO API KEY';
    }catch(e){
      var count=$('gp-3d-count');if(count)count.textContent=state.markers.length?state.markers.length+' SIGNALS · CACHED':'DATA LINK RETRYING…';
    }
  }

  function start(){inject();load()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
