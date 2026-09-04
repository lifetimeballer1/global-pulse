/* Global Pulse — Evidence Coverage UI
 * Renders underrepresented regional theaters from the live OSINT snapshot.
 * Uses conflictCoverage.watchlist when present and falls back to the canonical
 * osintMaps.regionalPoints dataset so a missing optional coverage layer never
 * makes the regional coverage panel disappear.
 */
(function(){
  'use strict';
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=t=>{const d=new Date(t);return Number.isNaN(d.getTime())?'Updated recently':d.toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});};
  const statusClass=s=>s==='CORROBORATED'?'red':s==='MULTI-SOURCE'?'amber':s==='SINGLE-SOURCE'?'blue':'muted';
  function fromRegional(d){
    const o=d.osintMaps||{};
    const pts=Array.isArray(o.regionalPoints)?o.regionalPoints:[];
    const counts=o.regionalCounts||{};
    const regions=['Africa','South America','South Asia'];
    return regions.map(region=>{
      const rp=pts.filter(p=>String(p.region||'')===region);
      const examples=rp.slice(0,3).map(p=>({url:p.url||p.sourceUrl||'',title:p.title||p.name||region+' OSINT signal'}));
      const n=Number(counts[region]??rp.length)||0;
      return {id:'regional-'+region.toLowerCase().replace(/\s+/g,'-'),title:region+' regional OSINT',region,type:'Regional evidence',articleCount:n,confidence:n?Math.min(1,.55+Math.log10(n+1)*.15):0,status:n>=10?'CORROBORATED':n>0?'SINGLE-SOURCE':'NO CURRENT SIGNAL',sourceDomains:[...new Set(rp.map(p=>p.sourceDomain||p.source).filter(Boolean))],evidence:examples};
    });
  }
  function render(){
    const d=window.DATA||window.data||{};
    const c=d.conflictCoverage&&Array.isArray(d.conflictCoverage.watchlist)?d.conflictCoverage:null;
    const w=c?wFrom(c):fromRegional(d);
    if(!w.length)return;
    let host=document.getElementById('gp-coverage-panel');
    if(!host){
      host=document.createElement('section');host.id='gp-coverage-panel';host.className='panel wide';
      const wrap=document.querySelector('.wrap');
      const map=document.getElementById('map');
      const mapSection=map&&map.closest('section');
      if(mapSection&&mapSection.parentNode) mapSection.parentNode.insertBefore(host,mapSection.nextSibling);
      else if(wrap) wrap.appendChild(host); else return;
    }
    const active=w.filter(x=>x.articleCount>0);
    const updated=c?.updatedAt||d.osintMaps?.updatedAt||d.updatedAt;
    const title=c?'Global Conflict Coverage':'Regional OSINT Coverage';
    const subtitle=c?'Underrepresented Africa & Americas theaters — evidence-driven, not static markers':'Live normalized evidence for Africa, South America and South Asia — sourced map signals, not static markers';
    host.innerHTML='<div class="section-head"><div><h2>'+title+'</h2><div class="muted">'+subtitle+'</div></div><div class="gp-layer-count">'+active.length+'/'+w.length+' regions active</div></div>'+
      '<div class="gp-coverage-grid">'+w.map(x=>{
        const sources=(x.sourceDomains||[]).length, evidence=(x.evidence||[]).slice(0,3);
        const first=evidence[0]||{};
        return '<article class="gp-coverage-card">'+
          '<div><span class="tag '+statusClass(x.status)+'">'+esc(x.status)+'</span><span class="tag">'+esc(x.region)+'</span></div>'+ 
          '<h3>'+esc(x.title)+'</h3>'+ 
          '<div class="muted">'+esc(x.type||'Regional evidence')+' · '+x.articleCount+' current signals · '+sources+' source domains</div>'+ 
          '<div class="gp-coverage-bar"><i style="width:'+Math.round((x.confidence||0)*100)+'%"></i></div>'+ 
          '<div class="muted">Coverage confidence '+Math.round((x.confidence||0)*100)+'% · '+fmt(updated)+'</div>'+ 
          (first.url?'<a class="open" href="'+esc(first.url)+'" target="_blank" rel="noopener">View evidence</a>':'')+
          '</article>';
      }).join('')+'</div>';
  }
  function wFrom(c){return c.watchlist||[]}
  function boot(){try{render();}catch(e){console.warn('Global Pulse coverage UI:',e)}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  document.addEventListener('globalpulse:dataready',boot);
  setInterval(boot,30000);
})();
