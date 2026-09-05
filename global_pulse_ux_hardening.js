/* Global Pulse Phase 3 UX hardening.
 * Keeps event interaction stable on mobile: one modal, locked background scroll,
 * focus return, safe viewport sizing, and no accidental map/page movement while
 * an intelligence dialog is open.
 */
(function(){
  'use strict';
  const modalId='gp-event-modal';
  let lastFocus=null;
  function modal(){return document.getElementById(modalId)}
  function isOpen(){const m=modal();return !!m&&m.classList.contains('open')}
  function lock(){
    document.documentElement.classList.add('gp-dialog-open');
    document.body.classList.add('gp-dialog-open');
    document.body.dataset.gpScrollY=String(window.scrollY||0);
  }
  function unlock(){
    const y=Number(document.body.dataset.gpScrollY||0);
    document.documentElement.classList.remove('gp-dialog-open');
    document.body.classList.remove('gp-dialog-open');
    window.scrollTo(0,y);
  }
  function focusDialog(){
    const m=modal(); if(!m)return;
    const d=m.querySelector('.gp-event-dialog');
    const c=m.querySelector('.gp-event-close');
    if(d)d.setAttribute('tabindex','-1');
    (c||d)?.focus({preventScroll:true});
  }
  function observe(){
    const m=modal(); if(!m||m.dataset.gpUxBound==='1')return;
    m.dataset.gpUxBound='1';
    const sync=()=>{
      if(isOpen()){
        if(!document.documentElement.classList.contains('gp-dialog-open'))lock();
        if(!lastFocus)lastFocus=document.activeElement;
        requestAnimationFrame(focusDialog);
      }else{
        const restore=lastFocus; lastFocus=null; unlock();
        if(restore&&restore.isConnected&&typeof restore.focus==='function')restore.focus({preventScroll:true});
      }
    };
    new MutationObserver(sync).observe(m,{attributes:true,attributeFilter:['class']});
    m.addEventListener('click',e=>{
      if(e.target===m.querySelector('.gp-event-backdrop'))e.preventDefault();
    },{passive:false});
    m.addEventListener('keydown',e=>{
      if(!isOpen()||e.key!=='Tab')return;
      const focusables=Array.from(m.querySelectorAll('button,a[href],input,select,textarea,[tabindex]:not([tabindex="-1"])')).filter(x=>!x.disabled&&x.offsetParent!==null);
      if(!focusables.length)return;
      const first=focusables[0],last=focusables[focusables.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
    });
    sync();
  }
  function scan(){observe()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan);else scan();
  new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('click',e=>{
    const trigger=e.target.closest?.('.gp-event-open,.gp-map-event-link');
    if(trigger&&!isOpen())lastFocus=trigger;
  },true);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&isOpen()){const close=modal()?.querySelector('.gp-event-close');close?.click()}});
})();
