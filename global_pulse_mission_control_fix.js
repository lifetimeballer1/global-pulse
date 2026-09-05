/* Global Pulse — canonical Mission Control + Active Conflict Watch renderer */
(function(){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
  const targets=[['Overview','#top'],['War Map','#mapSection'],['Intelligence Web','#intelligenceWebSection'],['Conflicts','#conflictSection'],['Live Reporting','#reporting'],['What Changed','#what-changed'],['Event Intelligence','#event-intelligence'],['Markets','#marketSection']];

  function cleanCommander(){
    const all=[...document.querySelectorAll('#commanderCenter')],first=all[0];
    all.slice(1).forEach(x=>x.remove());
    if(!first)return;
    document.querySelectorAll('.cc-nav').forEach(n=>{if(!first.contains(n))n.remove()});
    const nav=first.querySelector('.cc-nav')||(()=>{const n=document.createElement('nav');n.className='cc-nav';first.appendChild(n);return n})();
    nav.innerHTML=targets.filter(x=>document.querySelector(x[1])).map(([l,h])=>'<a href="'+h+'">'+l+'</a>').join('');
    nav.querySelectorAll('a').forEach(a=>a.onclick=e=>{const el=document.querySelector(a.getAttribute('href'));if(!el)return;e.preventDefault();const h=document.querySelector('header'),c=document.getElementById('commanderCenter'),off=(h?.offsetHeight||0)+(c?.offsetHeight||0)+14;window.scrollTo({top:Math.max(0,el.getBoundingClientRect().top+window.scrollY-off),behavior:'smooth'});history.replaceState(null,'',a.getAttribute('href'))});
  }

  function records(d){
    if(Array.isArray(d?.conflicts)&&d.conflicts.length)return d.conflicts;
    const w=d?.conflictCoverage?.watchlist;if(Array.isArray(w)&&w.length)return w;
    const b=d?.intelligenceBrief?.watchlist;if(Array.isArray(b)&&b.length)return b;
    const s=Array.isArray(d?.stories)?d.stories:[],rx=/war|conflict|fighting|attack|airstrike|missile|drone|troops|offensive|shelling|invasion|insurgent|militant|coup|cartel|clash/i;
    return s.filter(x=>rx.test(String(x.title||'')+' '+String(x.summary||''))).slice(0,8).map((x,i)=>({name:x.title||'Current conflict signal',activityScore:Math.max(40,70-i*5),confidence:x.confidence||'DEVELOPING',recent:x.title||'',sourceCount:1,signalCount:1,lastSignal:x.time||null,status:'Active signal'}));
  }

  function paint(rows){
    const host=document.getElementById('conflictList');if(!host)return;
    if(!rows.length){host.innerHTML='<div class="empty">Conflict watch is waiting for its first snapshot. No data was received from data/snapshot.json.</div>';return}
    host.innerHTML=rows.slice(0,12).map((c,i)=>{
      const n=esc(c.name||c.title||c.conflict||('Conflict '+(i+1)));
      const score=Math.max(0,Math.min(100,Math.round(Number(c.activityScore??c.score??c.tension??c.priority??0))));
      const active=String(c.status||'').toLowerCase().includes('active')||Number(c.signalCount||0)>0;
      const level=score>=82?'CRITICAL':score>=68?'HIGH':score>=50?'ELEVATED':'WATCH';
      const recent=esc(c.recent&&c.recent!=='No specific current signal in the public feed window.'?c.recent:(active?'Current conflict signal detected in the live reporting window.':'No fresh signal in the current reporting window.'));
      const sources=Number(c.sourceCount||c.sources?.length||0);
      return '<article class="ccard"><span class="tag '+(level==='CRITICAL'||level==='HIGH'?'red':level==='ELEVATED'?'amber':'blue')+'">'+level+'</span><span class="tag '+(active?'red':'blue')+'">'+(active?'ACTIVE':'MONITORING')+'</span><h3>'+n+'</h3><div class="muted">'+esc(c.region||'Global')+' · '+esc(c.category||'CONFLICT')+' · '+esc(c.confidence||'MONITORING')+'</div><div class="scoreline"><span>Activity</span><b>'+score+'</b></div><div class="track"><div class="fill" style="width:'+score+'%"></div></div><div class="muted" style="margin-top:7px">'+recent+'</div><div class="muted" style="margin-top:5px">'+(Number(c.signalCount||0))+' current signal'+(Number(c.signalCount||0)===1?'':'s')+' · '+sources+' source'+(sources===1?'':'s')+'</div></article>';
    }).join('');
  }

  async function load(){
    try{
      const r=await fetch('data/snapshot.json?active_conflict_watch='+Date.now(),{cache:'no-store'});
      if(!r.ok)throw Error('snapshot '+r.status);
      const d=await r.json();
      window.gpActiveConflictData=d;
      paint(records(d));
    }catch(e){paint(records(window.DATA||window.data||{}));}
  }

  function boot(){cleanCommander();load()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  document.addEventListener('globalpulse:dataready',()=>{cleanCommander();load()});
  setInterval(()=>{cleanCommander();load()},30000);
})();
