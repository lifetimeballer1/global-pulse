(function(){
  'use strict';
  var DATA='data/snapshot.json';
  var REGIONS=['Africa','South America','South Asia','Middle East','Europe','Southeast Asia','Central Asia','North America','Oceania'];
  var TYPES={conflict:2.2,military:1.8,terrorism:2.2,attack:2.1,protest:1.2,political:0.8,crime:1.0,disaster:1.1};
  function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function norm(s){return String(s||'').toLowerCase()}
  function sourceName(m){return m.source||m.sourceDomain||'Unknown source'}
  function ageHours(v){var t=Date.parse(v||'');return isNaN(t)?999:Math.max(0,(Date.now()-t)/3600000)}
  function weight(m){
    var text=norm([m.title,m.category,m.type,m.description].join(' ')), w=1;
    Object.keys(TYPES).forEach(function(k){if(text.indexOf(k)>=0) w=Math.max(w,TYPES[k])});
    var age=ageHours(m.observedAt||m.updatedAt||m.publishedAt);
    if(age<6) w*=1.35; else if(age<24) w*=1.15; else if(age>168) w*=.35;
    return w;
  }
  function confidence(markers){
    var urls={}, sources={};
    markers.forEach(function(m){var u=m.url||m.sourceUrl;if(u) urls[u]=1; var s=sourceName(m);sources[s]=1});
    var n=Object.keys(sources).length;
    return n>=4?'HIGH':n>=2?'MEDIUM':'LOW';
  }
  function regionOf(m){
    if(m.region && REGIONS.indexOf(m.region)>=0) return m.region;
    var c=norm(m.country||m.location);
    if(/nigeria|sudan|somalia|ethiopia|kenya|congo|south sudan|mali|burkina|niger|chad|libya|egypt|algeria|morocco|ghana|uganda|tanzania|mozambique|south africa|angola|senegal|guinea|sierra|benin|togo|cameroon/.test(c)) return 'Africa';
    if(/brazil|colombia|venezuela|ecuador|peru|bolivia|paraguay|uruguay|argentina|chile|guyana|suriname/.test(c)) return 'South America';
    if(/india|pakistan|bangladesh|afghanistan|sri lanka|nepal|bhutan|maldives|myanmar/.test(c)) return 'South Asia';
    return m.region||'Other';
  }
  function ensure(){
    if(document.getElementById('gp-intel-panel')) return document.getElementById('gp-intel-panel');
    var map=document.getElementById('map'); if(!map) return null;
    var host=map.closest('.panel')||map.parentElement;
    var p=document.createElement('section'); p.id='gp-intel-panel'; p.className='panel';
    p.innerHTML='<div class="section-head"><div><h2>Global Pulse Intelligence</h2><div class="gp-intel-sub">Derived from current map events and independent source records — activity signal, not a threat prediction.</div></div><div id="gp-intel-updated" class="muted"></div></div><div id="gp-intel-kpis" class="gp-intel-kpis"></div><div id="gp-intel-regions" class="gp-intel-regions"></div><div id="gp-intel-sources" class="gp-intel-sources"></div>';
    host.parentNode.insertBefore(p,host);
    return p;
  }
  function render(d){
    var p=ensure(); if(!p) return;
    var markers=(d.markers||[]).filter(function(m){return m&&m.lat!=null&&m.lng!=null});
    var regional=markers.filter(function(m){return m.layer==='osint-regional'});
    var active=markers.filter(function(m){return ageHours(m.observedAt||m.updatedAt||m.publishedAt)<=24});
    var src={}; markers.forEach(function(m){src[sourceName(m)]=(src[sourceName(m)]||0)+1});
    var sources=Object.keys(src).sort(function(a,b){return src[b]-src[a]});
    var score=Math.min(100,Math.round(markers.reduce(function(a,m){return a+weight(m)},0)/Math.max(1,markers.length)*18 + Math.min(35,active.length*.25)));
    var level=score>=75?'VERY HIGH':score>=55?'HIGH':score>=30?'ELEVATED':'LOW';
    document.getElementById('gp-intel-updated').textContent='Updated '+new Date().toLocaleTimeString();
    document.getElementById('gp-intel-kpis').innerHTML='<div class="gp-intel-kpi"><strong>'+score+'</strong><span>Activity signal</span></div><div class="gp-intel-kpi"><strong>'+active.length+'</strong><span>Events &lt;24h</span></div><div class="gp-intel-kpi"><strong>'+sources.length+'</strong><span>Sources represented</span></div><div class="gp-intel-kpi"><strong>'+regional.length+'</strong><span>Regional OSINT</span></div><div class="gp-intel-kpi"><strong>'+confidence(markers)+'</strong><span>Source diversity</span></div></div>';
    var rs={}; markers.forEach(function(m){var r=regionOf(m); if(!rs[r]) rs[r]={n:0,active:0,score:0}; rs[r].n++; if(ageHours(m.observedAt||m.updatedAt||m.publishedAt)<=24) rs[r].active++; rs[r].score+=weight(m)});
    var names=Object.keys(rs).filter(function(r){return r!=='Other'}).sort(function(a,b){return rs[b].score-rs[a].score});
    document.getElementById('gp-intel-regions').innerHTML='<div class="gp-intel-title">Regional activity</div>'+names.map(function(r){var pct=Math.min(100,Math.round(rs[r].score));return '<div class="gp-intel-row"><b>'+esc(r)+'</b><div class="gp-intel-track"><i style="width:'+pct+'%"></i></div><span>'+rs[r].active+' new / '+rs[r].n+' total</span></div>'}).join('');
    document.getElementById('gp-intel-sources').innerHTML='<div class="gp-intel-title">Source mix</div>'+sources.slice(0,8).map(function(s){return '<span class="gp-intel-source">'+esc(s)+' <b>'+src[s]+'</b></span>'}).join('');
    p.dataset.level=level;
  }
  function load(){fetch(DATA+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok) throw Error(r.status);return r.json()}).then(render).catch(function(e){var p=ensure();if(p) p.querySelector('.gp-intel-sub').textContent='Intelligence panel unavailable: '+e.message})}
  function boot(){load();setInterval(load,60000)}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();
