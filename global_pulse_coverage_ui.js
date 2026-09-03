/* Global Pulse — Evidence Coverage UI
 * Renders the underrepresented Africa/Americas theaters as a visible dashboard panel.
 * Data source: snapshot.conflictCoverage.watchlist
 */
(function(){
  'use strict';
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=t=>{const d=new Date(t);return Number.isNaN(d.getTime())?'Updated recently':d.toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});};
  const statusClass=s=>s==='CORROBORATED'?'red':s==='MULTI-SOURCE'?'amber':s==='SINGLE-SOURCE'?'blue':'muted';
  function render(){
    const d=window.DATA||window.data||{};
    const w=d.conflictCoverage&&Array.isArray(d.conflictCoverage.watchlist)?d.conflictCoverage.watchlist:[];
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
    host.innerHTML='<div class="section-head"><div><h2>Global Conflict Coverage</h2><div class="muted">Underrepresented Africa & Americas theaters — evidence-driven, not static markers</div></div><div class="gp-layer-count">'+active.length+'/'+w.length+' reporting signals</div></div>'+
      '<div class="gp-coverage-grid">'+w.map(x=>{
        const sources=(x.sourceDomains||[]).length, evidence=(x.evidence||[]).slice(0,3);
        const first=evidence[0]||{};
        return '<article class="gp-coverage-card">'+
          '<div><span class="tag '+statusClass(x.status)+'">'+esc(x.status)+'</span><span class="tag">'+esc(x.region)+'</span></div>'+
          '<h3>'+esc(x.title)+'</h3>'+
          '<div class="muted">'+esc(x.type)+' · '+x.articleCount+' current reports · '+sources+' independent domains</div>'+ 
          '<div class="gp-coverage-bar"><i style="width:'+Math.round((x.confidence||0)*100)+'%"></i></div>'+ 
          '<div class="muted">Confidence '+Math.round((x.confidence||0)*100)+'% · '+fmt(d.conflictCoverage.updatedAt)+'</div>'+
          (first.url?'<a class="open" href="'+esc(first.url)+'" target="_blank" rel="noopener">View evidence</a>':'')+
          '</article>';
      }).join('')+'</div>';
  }
  function boot(){try{render();}catch(e){console.warn('Global Pulse coverage UI:',e)}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setInterval(boot,30000);
})();
