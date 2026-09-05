/* Global Pulse — Mission Control + Active Conflict Watch repair
 * Keeps navigation tied to real sections, removes duplicate Commander Center
 * navigation, and guarantees the conflict watch gets a useful live fallback.
 */
(function(){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
  const targets=[
    ['Overview','#top'],
    ['War Map','#mapSection'],
    ['Intelligence Web','#intelligenceWebSection'],
    ['Conflicts','#conflictSection'],
    ['Live Reporting','#reporting'],
    ['What Changed','#what-changed'],
    ['Event Intelligence','#event-intelligence']
  ];
  function targetExists(sel){try{return !!document.querySelector(sel)}catch(_){return false}}
  function cleanCommander(){
    const all=[...document.querySelectorAll('#commanderCenter')];
    const first=all[0];
    all.slice(1).forEach(x=>x.remove());
    if(!first)return false;
    document.querySelectorAll('.cc-nav').forEach(nav=>{if(!first.contains(nav))nav.remove()});
    const navs=[...first.querySelectorAll('.cc-nav')];
    navs.slice(1).forEach(x=>x.remove());
    let nav=navs[0];
    if(!nav){nav=document.createElement('nav');nav.className='cc-nav';first.appendChild(nav)}
    nav.setAttribute('aria-label','Mission Control navigation');
    nav.innerHTML=targets.filter(x=>targetExists(x[1])).map(([label,href])=>'<a href="'+href+'">'+label+'</a>').join('');
    nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',function(e){
      const el=document.querySelector(this.getAttribute('href'));
      if(!el)return;
      e.preventDefault();
      const header=document.querySelector('header');
      const commander=document.getElementById('commanderCenter');
      const offset=(header?.getBoundingClientRect().height||0)+(commander?.getBoundingClientRect().height||0)+14;
      const y=el.getBoundingClientRect().top+window.scrollY-offset;
      window.scrollTo({top:Math.max(0,y),behavior:'smooth'});
      history.replaceState(null,'',this.getAttribute('href'));
    }));
    return true;
  }
  function conflictRecords(d){
    if(Array.isArray(d.conflicts)&&d.conflicts.length)return d.conflicts;
    const coverage=d.conflictCoverage;
    if(coverage&&Array.isArray(coverage.watchlist)&&coverage.watchlist.length)return coverage.watchlist;
    const brief=d.intelligenceBrief;
    if(brief&&Array.isArray(brief.watchlist)&&brief.watchlist.length)return brief.watchlist;
    const stories=Array.isArray(d.stories)?d.stories:[];
    const rx=/war|conflict|fighting|attack|airstrike|missile|drone|troops|offensive|shelling|invasion|insurgent|militant|coup|cartel|clash/i;
    return stories.filter(s=>rx.test(String(s.title||'')+' '+String(s.summary||''))).slice(0,8).map((s,i)=>({
      id:'live-signal-'+i,name:s.title||'Current conflict signal',title:s.title||'Current conflict signal',
      score:Math.round(70-i*5),activityScore:Math.round(70-i*5),confidence:s.confidence||'DEVELOPING',
      recent:s.title||'',lastSignal:s.time||s.published_date||s.publishedAt||'',
      signalCount:1,sourceCount:1,signals:[{title:s.title||'',time:s.time||s.published_date||'',url:s.url||s.source||'',match:[]}]
    }));
  }
  function renderConflictFallback(){
    const host=document.getElementById('conflictList');
    if(!host)return;
    const d=window.DATA||window.data||{};
    const rows=conflictRecords(d);
    if(!rows.length){host.innerHTML='<div class="empty">Conflict data is still loading. The live refresh pipeline will repopulate this watch automatically.</div>';return}
    if(host.dataset.gpCanonicalConflict==='1'&&host.children.length) return;
    host.innerHTML=rows.slice(0,12).map((c,i)=>{
      const name=esc(c.name||c.title||c.conflict||('Conflict '+(i+1)));
      const score=Number(c.activityScore??c.score??c.tension??c.priority??0);
      const level=score>=75?'HIGH':score>=50?'ELEVATED':'WATCH';
      const recent=esc(c.recent||c.lastSignal||'Current public conflict signal');
      const sources=Number(c.sourceCount||0);
      return '<article class="ccard"><span class="tag '+(level==='HIGH'?'red':level==='ELEVATED'?'amber':'blue')+'">'+level+'</span><h3>'+name+'</h3><div class="muted">'+esc(c.confidence||'MONITORING')+' · '+(sources||1)+' source domain'+(sources===1?'':'s')+'</div><div class="scoreline"><span>Activity</span><b>'+Math.max(0,Math.min(100,Math.round(score)))+'</b></div><div class="track"><div class="fill" style="width:'+Math.max(0,Math.min(100,Math.round(score)))+'%"></div></div><div class="muted" style="margin-top:7px">'+recent+'</div></article>';
    }).join('');
    host.dataset.gpCanonicalConflict='1';
  }
  function boot(){cleanCommander();renderConflictFallback()}
  function onData(){cleanCommander();const host=document.getElementById('conflictList');if(host)delete host.dataset.gpCanonicalConflict;renderConflictFallback()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  document.addEventListener('globalpulse:dataready',onData);
  setInterval(()=>{cleanCommander();const host=document.getElementById('conflictList');if(host&&!host.children.length){delete host.dataset.gpCanonicalConflict;renderConflictFallback()}},15000);
})();
