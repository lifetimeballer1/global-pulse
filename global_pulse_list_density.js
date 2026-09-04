/* Global Pulse list density guardrail
 * Keep intelligence panels concise: show five items by default, then reveal the rest.
 * Dynamic lists are handled with a MutationObserver so live refreshes stay compact.
 */
(function(){
  'use strict';
  const LIMIT=5;
  const SELECTORS=['.items','.stories','.conflict-list','#gp-ei-content','#gp-assessment-content','#gp-live-reporting-content','.gp-event-list'];
  const esc=v=>String(v??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]||m));
  function directItems(el){
    return Array.from(el.children).filter(n=>n.nodeType===1 && !n.matches('.gp-list-actions'));
  }
  function install(el){
    if(!el || el.dataset.gpDensityBound==='1') return;
    el.dataset.gpDensityBound='1';
    const refresh=()=>{
      const items=directItems(el);
      let actions=el.querySelector(':scope > .gp-list-actions');
      if(items.length<=LIMIT){
        items.forEach(x=>{x.hidden=false;x.removeAttribute('aria-hidden')});
        if(actions) actions.remove();
        return;
      }
      if(!actions){
        actions=document.createElement('div');
        actions.className='gp-list-actions';
        actions.innerHTML='<button type="button" class="more-btn gp-list-more" aria-expanded="false">See more ('+(items.length-LIMIT)+')</button>';
        el.appendChild(actions);
        actions.querySelector('button').addEventListener('click',function(){
          const expanded=this.getAttribute('aria-expanded')==='true';
          items.forEach((x,i)=>{x.hidden=!expanded && i>=LIMIT; x.setAttribute('aria-hidden',String(!expanded && i>=LIMIT))});
          this.setAttribute('aria-expanded',String(!expanded));
          this.textContent=expanded?'See more ('+(items.length-LIMIT)+')':'Show less';
          if(!expanded) actions.scrollIntoView({block:'nearest',behavior:'smooth'});
        });
      }
      const expanded=actions.querySelector('button')?.getAttribute('aria-expanded')==='true';
      items.forEach((x,i)=>{x.hidden=!expanded && i>=LIMIT;x.setAttribute('aria-hidden',String(!expanded && i>=LIMIT))});
      const b=actions.querySelector('button');
      if(b && !expanded) b.textContent='See more ('+(items.length-LIMIT)+')';
    };
    const observer=new MutationObserver(()=>{ if(!el.__gpDensityQueued){el.__gpDensityQueued=true;requestAnimationFrame(()=>{el.__gpDensityQueued=false;refresh()})} });
    observer.observe(el,{childList:true});
    el.__gpDensityRefresh=refresh;
    refresh();
  }
  function scan(root=document){
    SELECTORS.forEach(sel=>root.querySelectorAll(sel).forEach(install));
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>scan()); else scan();
  new MutationObserver(muts=>muts.forEach(m=>m.addedNodes.forEach(n=>{if(n.nodeType===1)scan(n)}))).observe(document.documentElement,{childList:true,subtree:true});
})();
