/* Global Pulse — live tension-driver renderer
   Uses backend-calculated driver scores when available and safely falls back to
   transparent story/conflict signals. Never depends on a hard-coded DOM shape.
*/
(function(){
  'use strict';
  var IDS=['Conflict activity','Diplomatic strain','Economic pressure','Market volatility','Military posture','Climate & humanitarian pressure'];
  var META={
    'Conflict activity':{desc:'Active fighting, attacks, clashes and major conflict events.',keys:/\b(war|armed conflict|fighting|battle|offensive|airstrike|shelling|invasion|insurgent|insurgency|militant attack|clash|bombing|hostage crisis)\b/i},
    'Diplomatic strain':{desc:'Sanctions, diplomatic crises, expulsions, ultimatums and negotiation breakdowns.',keys:/\b(sanction|sanctions|diplomatic crisis|expel|expulsion|ultimatum|negotiation|ceasefire talks|treaty|summit|envoy|foreign minister)\b/i},
    'Economic pressure':{desc:'Trade restrictions, inflation, energy/supply disruption and macroeconomic stress.',keys:/\b(inflation|tariff|tariffs|trade war|sanction|recession|supply disruption|oil price|gas price|shipping|freight|central bank|interest rate|gdp|economy)\b/i},
    'Market volatility':{desc:'Large moves or stress in equities, bonds, currencies, commodities and financial markets.',keys:/\b(stock market|stocks|shares|bond yields?|treasury yields?|currency|forex|exchange rate|dollar|euro|yen|yuan|oil prices?|crude prices?|natural gas prices?|market volatility|market selloff|market rally|volatility index|plunge|surge)\b/i},
    'Military posture':{desc:'Military deployments, weapons activity, exercises, mobilization and force posture.',keys:/\b(troops?|forces?|military|missile|missiles|drone|drones|airstrike|air strikes|bombers?|carrier|navy|mobiliz|exercise|weapons?|defense|defence|deployment|offensive)\b/i},
    'Climate & humanitarian pressure':{desc:'Drought, floods, extreme weather, food insecurity and health outbreaks that can create pressure.',keys:/\b(drought|water shortage|water stress|water scarcity|flood|flooding|cyclone|hurricane|typhoon|storm surge|landslide|heatwave|heat wave|extreme heat|wildfire|forest fire|food insecurity|food crisis|famine|acute hunger|crop failure|epidemic|outbreak|cholera|malaria|pandemic|disease outbreak)\b/i}
  };
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function num(v,f){v=Number(v);return Number.isFinite(v)?Math.max(0,Math.min(100,Math.round(v))):f}
  function stories(d){return Array.isArray(d&&d.stories)?d.stories:[]}
  function derive(d,name){
    var m=META[name], pool=stories(d), total=0, hit=0, sources={};
    pool.forEach(function(s){
      var text=[s.title,s.summary,s.tag,s.sourceLabel,s.sourceType].join(' ');
      var w=1;
      if(s.time){var t=Date.parse(s.time);if(Number.isFinite(t)){var age=(Date.now()-t)/3600000;if(age<6)w=1.35;else if(age<24)w=1.15;else if(age>72)w=.7}}
      total+=w;
      if(m.keys.test(text)){hit+=w;sources[s.sourceLabel||s.sourceType||'Public source']=1}
    });
    if(!pool.length)return {score:35,matches:0,sources:0,confidence:'LOW'};
    var share=hit/Math.max(total,.01), score=Math.round(30+Math.min(70,share*100));
    return {score:Math.max(0,Math.min(100,score)),matches:Math.round(hit),sources:Object.keys(sources).length,confidence:share>.35?'HIGH':share>.15?'MEDIUM':'LOW'};
  }
  function render(d){
    var box=document.getElementById('breakdown');
    if(!box)return false;
    var raw=d&&d.breakdownScores||{};
    var meta=d&&d.driverSignals||{};
    box.classList.add('gp-tension-drivers');
    box.innerHTML='';
    IDS.forEach(function(name){
      var fallback=derive(d,name), score=num(raw[name],fallback.score), info=meta[name]||{};
      var matches=Number.isFinite(Number(info.matches))?Number(info.matches):fallback.matches;
      var sourceCount=Number.isFinite(Number(info.sources))?Number(info.sources):fallback.sources;
      var label=score>=75?'HIGH':score>=55?'ELEVATED':score>=40?'WATCH':'LOW';
      var row=document.createElement('div');row.className='gp-driver';
      row.innerHTML='<div class="gp-driver-head"><div><b>'+esc(name)+'</b><span>'+esc(META[name].desc)+'</span></div><strong>'+score+'</strong></div>'+
        '<div class="gp-driver-track"><i style="width:'+score+'%"></i></div>'+
        '<div class="gp-driver-foot"><span class="gp-driver-state">'+label+'</span><span>'+matches+' matching signals · '+sourceCount+' sources</span></div>';
      box.appendChild(row);
    });
    var note=document.getElementById('gp-tension-note');
    if(!note){note=document.createElement('div');note.id='gp-tension-note';box.parentNode.appendChild(note)}
    note.textContent='Live driver model · scores use current public reporting signals, recency and source diversity. A headline count alone does not raise tension.';
    return true;
  }
  function ensureStyle(){
    if(document.getElementById('gp-tension-css'))return;
    var s=document.createElement('style');s.id='gp-tension-css';s.textContent='.gp-tension-drivers{display:grid!important;gap:12px!important;height:auto!important;min-height:0!important}.gp-driver{padding:10px 0;border-bottom:1px solid var(--line)}.gp-driver:last-child{border-bottom:0}.gp-driver-head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:start}.gp-driver-head b{display:block;font-size:12px}.gp-driver-head span{display:block;margin-top:3px;color:var(--muted);font-size:9px;line-height:1.35}.gp-driver-head strong{font-size:19px;line-height:1;font-variant-numeric:tabular-nums;color:var(--amber)}.gp-driver-track{height:8px;margin-top:8px;background:#06101a;border:1px solid #142334;border-radius:99px;overflow:hidden}.gp-driver-track i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--green),var(--amber),var(--red));transition:width .35s ease}.gp-driver-foot{display:flex;justify-content:space-between;gap:8px;margin-top:5px;color:var(--muted);font-size:9px}.gp-driver-state{font-weight:900;letter-spacing:.08em}.gp-tension-drivers .gp-driver:hover{background:rgba(98,160,255,.035)}#gp-tension-note{margin-top:8px;color:var(--muted);font-size:9px;line-height:1.4}@media(max-width:720px){.gp-driver-head span{font-size:8px}.gp-driver-foot{font-size:8px}}';document.head.appendChild(s)
  }
  function run(){ensureStyle();var d=window.DATA;if(d)render(d)}
  document.addEventListener('DOMContentLoaded',run);
  window.addEventListener('globalpulse:dataready',run);
  setTimeout(run,1500);setTimeout(run,5000);setInterval(run,60000);
})();
