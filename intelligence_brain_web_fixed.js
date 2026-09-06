(()=>{
  'use strict';
  const $=id=>document.getElementById(id);
  const DATA='data/intelligence_brain.json';
  const COLORS={country:'#64a7ff',cartel:'#ff5268',conflict:'#ff5268',market:'#ffc857',economic:'#ffc857',chokepoint:'#43d4ff',default:'#8ea7c4'};
  const POS={"United States":[39,-98],Mexico:[23,-102],Canada:[57,-106],Colombia:[5,-74],Venezuela:[7,-66],Brazil:[-10,-52],Ecuador:[-1.4,-78],Peru:[-9,-75],Russia:[61,90],Ukraine:[49,32],Germany:[51,10],France:[46,2],"United Kingdom":[55,-3],Turkey:[39,35],Israel:[31.5,34.8],Iran:[32,53],Iraq:[33,44],"Saudi Arabia":[24,45],Yemen:[15.5,48],Egypt:[27,30],Sudan:[15,30],Nigeria:[9,8],Somalia:[6,46],"South Africa":[-30,25],China:[35,103],India:[22,79],Pakistan:[30,70],Japan:[36,138],"South Korea":[36,128],Taiwan:[23.7,121],Australia:[-25,134]};
  const GROUP={oil:[26,25],"natural gas":[30,10],food:[12,0],energy:[35,5],minerals:[-8,5],shipping:[20,60],finance:[40,-20],markets:[40,-20],trade:[30,15],inflation:[35,-5],"supply chains":[30,85]};
  const ESC=v=>String(v??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
  const safeUrl=v=>{try{const u=new URL(String(v||''));return /^https?:$/.test(u.protocol)?u.href:''}catch(_){return ''}};
  async function load(){const r=await fetch(DATA+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
  function normalize(d){
    const raw=Array.isArray(d.nodes)?d.nodes:[];
    const nodes=raw.map((n,i)=>({id:String(n.id??i),label:String(n.label||n.name||n.id||'Unknown'),kind:String(n.kind||'default').toLowerCase(),country:String(n.country||''),group:String(n.group||''),mentions:Number(n.mentions||n.weight||0),evidence:Array.isArray(n.evidence)?n.evidence:[],confidence:String(n.confidence||''),summary:String(n.summary||n.description||''),lat:Number(n.lat),lng:Number(n.lng)})).filter(n=>n.evidence.length>0);
    const ids=new Set(nodes.map(n=>n.id));
    const links=(Array.isArray(d.edges)?d.edges:[]).map(e=>({source:String(e.source?.id??e.source),target:String(e.target?.id??e.target),weight:Number(e.weight||1),relationship:String(e.relationship||''),types:Array.isArray(e.types)?e.types:[],evidence:Array.isArray(e.evidence)?e.evidence:[]})).filter(e=>ids.has(e.source)&&ids.has(e.target)&&e.source!==e.target&&e.evidence.length>0);
    return {nodes,links,stats:d.stats||{},updatedAt:d.updatedAt||'',caution:d.caution||'Relationships are contextual evidence links and do not prove causation.'};
  }
  function country(n){if(POS[n.label])return n.label;const c=n.country.toLowerCase();return Object.keys(POS).find(k=>k.toLowerCase()===c)||null}
  function pos(n){if(Number.isFinite(n.lat)&&Number.isFinite(n.lng))return[n.lat,n.lng];const c=country(n);if(c)return POS[c];const g=n.group.toLowerCase();for(const k in GROUP)if(g.includes(k))return GROUP[k];return null}
  function rank(n){const k=n.kind;return (k==='country'||k==='cartel'?5:k==='conflict'?4:k==='chokepoint'?3:k==='market'||k==='economic'?2:1)*1000000+(n.mentions||0)*100+n.evidence.length*10}
  function kindLabel(k){return({country:'COUNTRY',cartel:'ORGANIZATION',conflict:'CONFLICT',market:'MARKET',economic:'ECONOMIC FACTOR',chokepoint:'STRATEGIC LOCATION'}[k]||'INTELLIGENCE')}
  function project(lat,lng,w,h){return[(lng+180)/360*w,(90-lat)/180*h]}
  function install(){
    if($('gp-fixed-style'))return;
    const s=document.createElement('style');s.id='gp-fixed-style';s.textContent=`
      #graph{position:relative!important;height:560px!important;min-height:560px!important;border:1px solid #203449;border-radius:15px;overflow:hidden;background:#06101a;box-shadow:inset 0 0 70px rgba(0,0,0,.45)}
      #gp-board{position:absolute;inset:0;background:radial-gradient(circle at 52% 42%,rgba(31,75,110,.16),transparent 42%),linear-gradient(180deg,#071522,#040a10)}
      #gp-board svg{width:100%;height:100%;display:block}
      .gp-ocean{fill:#06131f}.gp-grid{stroke:#173047;stroke-width:.7;opacity:.48}.gp-land{fill:#12283a;stroke:#23465e;stroke-width:1.1}.gp-connection{stroke:#62a7ff;stroke-width:1.4;opacity:.38;stroke-dasharray:5 7;fill:none}.gp-connection.active{opacity:.95;stroke-width:2}.gp-node-wrap{cursor:pointer}.gp-node-ring{fill:none;stroke-width:1.5;opacity:.55}.gp-node-dot{stroke:#eaf2ff;stroke-width:1.5}.gp-node-label{font:800 11px system-ui,-apple-system,sans-serif;fill:#edf5ff;paint-order:stroke;stroke:#040a10;stroke-width:4px;stroke-linejoin:round}.gp-node-sub{font:700 8px system-ui,-apple-system,sans-serif;fill:#8fa6ba;letter-spacing:1px;paint-order:stroke;stroke:#040a10;stroke-width:3px}.gp-selected .gp-node-ring{stroke:#fff;opacity:1}.gp-selected .gp-node-dot{stroke:#fff;stroke-width:2.5}.gp-dim{opacity:.12}.gp-topbar{position:absolute;left:12px;right:12px;top:12px;display:flex;justify-content:space-between;pointer-events:none}.gp-title,.gp-badge{background:rgba(4,10,16,.9);border:1px solid #21384d;border-radius:9px}.gp-title{padding:8px 10px}.gp-title b{display:block;font-size:10px;letter-spacing:.16em}.gp-title span{font-size:9px;color:#7f96aa}.gp-badges{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}.gp-badge{padding:6px 8px;font-size:8px;font-weight:850;color:#9db0c1}.gp-focus{position:absolute;right:12px;top:68px;width:min(360px,calc(100% - 24px));max-height:calc(100% - 105px);overflow:auto;background:rgba(5,11,17,.97);border:1px solid #2b435a;border-radius:12px;padding:14px;box-shadow:0 20px 70px rgba(0,0,0,.6);z-index:20}.gp-focus h3{margin:0;font-size:19px}.gp-focus .kind{font-size:9px;letter-spacing:.13em;color:#8fa6ba;font-weight:850;margin:3px 0 10px}.gp-focus .close{float:right;border:0;background:none;color:#8fa6ba;font-size:22px;line-height:1;padding:0;min-height:0}.gp-pills{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.gp-pill{font-size:9px;border:1px solid #263d52;border-radius:7px;padding:5px 7px;color:#b5c3d0}.gp-rel{border-top:1px solid #1a2d3f;padding:9px 0}.gp-rel b{font-size:12px}.gp-rel .why{font-size:9px;color:#8298ab;margin:2px 0 6px}.gp-source{padding:7px;border:1px solid #1b3043;background:#08141f;border-radius:7px;margin-top:5px;font-size:9px}.gp-source a{display:block;margin-top:4px;font-weight:850;color:#62a7ff}.gp-empty{text-align:center;padding:18px;color:#8196aa;font-size:11px}.gp-reset{position:absolute;right:12px;bottom:12px;z-index:5;padding:7px 9px!important;min-height:30px!important;font-size:9px!important;background:rgba(4,10,16,.9)!important;color:#d9e7f3!important;border:1px solid #21384d!important;border-radius:7px}.gp-econ{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);font-size:8px;letter-spacing:.13em;color:#71889c;pointer-events:none;max-width:55%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}@media(max-width:720px){#graph{height:500px!important;min-height:500px!important}.gp-title{padding:7px 8px}.gp-badges{display:none}.gp-node-label{font-size:9px}.gp-node-sub{font-size:7px}.gp-focus{left:8px;right:8px;bottom:8px;top:auto;width:auto;max-height:55%}.gp-econ{display:none}}
    `;document.head.appendChild(s);
  }
  function land(){return `<path class="gp-land" d="M80 150L160 110 260 125 330 170 410 210 455 260 410 300 350 280 300 315 240 290 190 250 135 240 95 205z"/><path class="gp-land" d="M390 315l55 10 40 55-15 80-35 65-30-55 12-55-25-55z"/><path class="gp-land" d="M650 145l75-25 110 10 95 35 110-5 80 45-45 40 20 45-95 0-70-35-90 20-80-20-75 15-55-35z"/><path class="gp-land" d="M610 245l65 10 25 50-30 35-55-15-30-40z"/><path class="gp-land" d="M955 420l70-20 70 30-15 45-80 15-55-30z"/>`}
  function grid(w,h){let s='';for(let lng=-150;lng<=150;lng+=30){const x=project(0,lng,w,h)[0];s+=`<line class="gp-grid" x1="${x}" y1="0" x2="${x}" y2="${h}"/>`}for(let lat=-60;lat<=60;lat+=30){const y=project(lat,0,w,h)[1];s+=`<line class="gp-grid" x1="0" y1="${y}" x2="${w}" y2="${y}"/>`}return s}
  function showError(err){const l=$('loading');if(l){l.classList.add('error');l.innerHTML='INTELLIGENCE BRAIN UNAVAILABLE<br><small>'+ESC(err?.message||String(err))+'</small>'}}
  function boot(data){
    install();
    const state=normalize(data),host=$('graph');
    host.innerHTML='<div id="gp-board"></div>';
    const board=$('gp-board'),w=1200,h=560;
    const candidates=state.nodes.filter(n=>pos(n)).sort((a,b)=>rank(b)-rank(a)).slice(0,50);
    const visible=new Set(candidates.map(n=>n.id)),positions=new Map(),occupied=[];
    candidates.forEach(n=>{let p=project(...pos(n),w,h),tries=0;while(occupied.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<30)&&tries<10){p=[p[0]+(tries%2?1:-1)*(12+tries*4),p[1]+(tries%3-1)*10];tries++}occupied.push(p);positions.set(n.id,p)});
    const links=state.links.filter(e=>visible.has(e.source)&&visible.has(e.target));
    let svg=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-label="Global Pulse Intelligence Web"><rect class="gp-ocean" x="0" y="0" width="${w}" height="${h}"/>${grid(w,h)}${land()}<g id="gp-links">`;
    links.forEach(e=>{const a=positions.get(e.source),b=positions.get(e.target);if(a&&b)svg+=`<line class="gp-connection" data-source="${ESC(e.source)}" data-target="${ESC(e.target)}" x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}"/>`});
    svg+='</g><g id="gp-nodes">';
    candidates.forEach(n=>{const p=positions.get(n.id),color=COLORS[n.kind]||COLORS.default,r=Math.max(5,Math.min(13,5+Math.log1p(n.mentions||0)*1.7));svg+=`<g class="gp-node-wrap" data-id="${ESC(n.id)}" tabindex="0" role="button" aria-label="${ESC(n.label)}"><circle class="gp-node-ring" cx="${p[0]}" cy="${p[1]}" r="${r+5}" stroke="${color}"/><circle class="gp-node-dot" cx="${p[0]}" cy="${p[1]}" r="${r}" fill="${color}"/><text class="gp-node-label" x="${p[0]+r+6}" y="${p[1]-2}">${ESC(n.label.length>25?n.label.slice(0,24)+'…':n.label)}</text><text class="gp-node-sub" x="${p[0]+r+6}" y="${p[1]+10}">${ESC(kindLabel(n.kind))}</text></g>`});
    svg+='</g></svg><div class="gp-topbar"><div class="gp-title"><b>GLOBAL PULSE // INTELLIGENCE WEB</b><span>Evidence-backed relationships · consolidated canonical graph</span></div><div class="gp-badges"><span class="gp-badge">'+candidates.length+' NODES</span><span class="gp-badge">'+links.length+' LINKS</span></div></div><button class="gp-reset" id="gp-reset" type="button">RESET VIEW</button><div class="gp-econ">'+ESC(state.caution)+'</div><div class="gp-focus" id="gp-focus" hidden></div>`;
    board.innerHTML=svg;
    const nodesG=board.querySelectorAll('.gp-node-wrap'),focus=board.querySelector('#gp-focus'),lines=board.querySelectorAll('.gp-connection');
    const by=new Map(candidates.map(n=>[n.id,n]));
    function reset(){nodesG.forEach(g=>g.classList.remove('gp-selected','gp-dim'));lines.forEach(l=>l.classList.remove('active'));if(focus){focus.hidden=true;focus.innerHTML=''}}
    function select(n){
      const connected=new Set([n.id]);links.forEach(e=>{if(e.source===n.id)connected.add(e.target);if(e.target===n.id)connected.add(e.source)});
      nodesG.forEach(g=>g.classList.toggle('gp-dim',!connected.has(g.dataset.id)),g.classList.toggle('gp-selected',g.dataset.id===n.id));
      lines.forEach(l=>l.classList.toggle('active',l.dataset.source===n.id||l.dataset.target===n.id));
      const rel=links.filter(e=>e.source===n.id||e.target===n.id).sort((a,b)=>b.weight-a.weight);
      let html=`<button class="close" id="gp-close" aria-label="Close">×</button><h3>${ESC(n.label)}</h3><div class="kind">${kindLabel(n.kind)}${country(n)?' · '+ESC(country(n)):''}</div><div class="gp-pills"><span class="gp-pill">${rel.length} connections</span><span class="gp-pill">${n.mentions||0} signals</span><span class="gp-pill">${n.evidence.length} sources</span>${n.confidence?`<span class="gp-pill">${ESC(n.confidence).toUpperCase()} CONFIDENCE</span>`:''}</div>`;
      if(n.summary)html+=`<div class="gp-source" style="margin-bottom:9px">${ESC(n.summary)}</div>`;
      if(!rel.length)html+='<div class="gp-empty">No source-backed relationships are currently attached.</div>';
      rel.slice(0,8).forEach(e=>{const other=by.get(e.source===n.id?e.target:e.source);if(!other)return;html+=`<div class="gp-rel"><b>${ESC(other.label)}</b><div class="why">${ESC(e.relationship||'Source-backed relationship')}</div>`;e.evidence.slice(0,2).forEach(ev=>{const u=safeUrl(ev.url);html+=`<div class="gp-source"><b>${ESC(ev.source||'Public source')}</b><div>${ESC(ev.title||'Evidence record')}</div>${u?`<a target="_blank" rel="noopener noreferrer" href="${ESC(u)}">OPEN SOURCE ↗</a>`:''}</div>`});html+='</div>'});
      focus.innerHTML=html;focus.hidden=false;const close=$('gp-close');if(close)close.onclick=reset;
    }
    nodesG.forEach(g=>{const n=by.get(g.dataset.id);g.addEventListener('click',()=>select(n));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(n)}})});
    const resetBtn=board.querySelector('#gp-reset');if(resetBtn)resetBtn.onclick=reset;
    const l=$('loading');if(l)l.style.display='none';
    const stats=$('stats');if(stats)stats.textContent=`${candidates.length} major nodes · ${links.length} evidence-backed relationships · refreshed ${state.updatedAt?new Date(state.updatedAt).toLocaleString(): 'unknown'}`;
  }
  load().then(boot).catch(showError);
})();
